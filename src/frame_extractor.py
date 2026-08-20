"""抽帧引擎核心（纯逻辑，无 Qt 依赖，可独立测试）。

设计要点：
- 单帧"读→编码→写盘→释放"，零内存累积，应对 4K 大帧。
- 帧级 seek（CAP_PROP_POS_FRAMES）保证精确。
- 回调解耦进度/日志/取消，UI 层用 Qt 信号桥接。
"""
from __future__ import annotations

import math
import os
import time

import cv2

from .extraction_params import (
    ExtractionCallbacks,
    ExtractionParams,
    ExtractionResult,
)


def _imwrite_safe(path: str, img, ext: str, enc_params=None) -> bool:
    """安全保存图片，兼容 Windows 中文路径。

    cv2.imwrite 在 Windows 上遇到非 ASCII 路径会静默失败（返回 False），
    且不抛出异常。改用 cv2.imencode 编码到内存缓冲区，再用
    numpy.ndarray.tofile 写盘，后者正确处理 Unicode 路径。
    """
    ok, buf = cv2.imencode(ext, img, enc_params or [])
    if not ok:
        return False
    try:
        buf.tofile(path)
    except OSError:
        return False
    return True


def extract_frames(params: ExtractionParams, cb: ExtractionCallbacks) -> ExtractionResult:
    """按时间范围逐帧抽取并保存图片。

    Returns:
        ExtractionResult: 包含是否成功、已保存帧数、耗时、错误信息。
    """
    t0 = time.time()
    cap = cv2.VideoCapture(params.video_path)
    if not cap.isOpened():
        return ExtractionResult(
            success=False, saved_count=0, elapsed=0.0,
            error="无法打开视频（可能缺少解码器或文件损坏）",
        )

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        start_frame = max(0, int(round(params.start_sec * fps)))
        desired_end = int(round(params.end_sec * fps))
        # 总帧数已知时不超过它，未知时直接用时间换算
        end_frame = min(total_frames, desired_end) if total_frames > 0 else desired_end

        if end_frame <= start_frame:
            return ExtractionResult(
                success=False, saved_count=0, elapsed=time.time() - t0,
                error="结束时间须大于起始时间",
            )

        interval = max(1, params.interval)
        total_to_save = math.ceil((end_frame - start_frame) / interval)
        pad = max(6, len(str(end_frame)))

        ext = ".png" if params.format.upper() == "PNG" else ".jpg"
        enc_params = (
            [cv2.IMWRITE_JPEG_QUALITY, int(params.quality)]
            if params.format.upper() == "JPG"
            else []
        )

        os.makedirs(params.output_dir, exist_ok=True)

        # 帧级精确 seek
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        saved = 0
        failed = 0
        current = start_frame
        cancelled = False

        cb.on_log(
            f"开始抽帧：第 {start_frame}~{end_frame} 帧，"
            f"间隔 {interval}，预计保存 {total_to_save} 帧，格式 {params.format}"
        )

        while current < end_frame:
            if cb.should_cancel():
                cb.on_log("用户已取消，已保存的部分文件保留")
                cancelled = True
                break

            ret, frame = cap.read()
            if not ret or frame is None:
                cb.on_log(f"读取结束或失败，停止于第 {current} 帧")
                break

            if (current - start_frame) % interval == 0:
                fname = f"frame_{current:0{pad}d}{ext}"
                fpath = os.path.join(params.output_dir, fname)
                if _imwrite_safe(fpath, frame, ext, enc_params):
                    saved += 1
                    cb.on_progress(saved, total_to_save)
                    # 日志节流：每 50 帧或每 5% 或最后一帧
                    if saved % 50 == 0 or saved == total_to_save or saved % max(1, total_to_save // 20) == 0:
                        cb.on_log(f"已保存 {saved}/{total_to_save} 帧（当前第 {current} 帧）")
                else:
                    failed += 1
                    cb.on_log(f"警告：保存失败 {fname}，已跳过")

            current += 1

        elapsed = time.time() - t0
        if saved == 0 and failed > 0 and not cancelled:
            cb.on_log(f"抽帧失败：全部 {failed} 帧保存失败")
            return ExtractionResult(
                success=False, saved_count=0, elapsed=elapsed,
                error=f"所有帧保存失败（共 {failed} 次），请检查输出目录路径或权限",
            )
        if failed > 0:
            cb.on_log(f"抽帧结束：共保存 {saved} 帧（{failed} 帧失败），用时 {elapsed:.1f}s")
        else:
            cb.on_log(f"抽帧结束：共保存 {saved} 帧，用时 {elapsed:.1f}s")
        return ExtractionResult(
            success=True, saved_count=saved, elapsed=elapsed,
            cancelled=cancelled,
        )
    except Exception as exc:  # noqa: BLE001
        return ExtractionResult(
            success=False, saved_count=0, elapsed=time.time() - t0,
            error=f"抽帧异常：{exc}",
        )
    finally:
        cap.release()

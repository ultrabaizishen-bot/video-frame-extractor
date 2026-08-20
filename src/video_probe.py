"""视频探测与缩略图生成（纯逻辑，无 Qt 依赖）。"""
from __future__ import annotations

import contextlib
import os
import shutil
import tempfile

import cv2

from .extraction_params import VideoInfo


@contextlib.contextmanager
def _open_video(path: str):
    """打开视频捕获，兼容 Windows 中文路径。

    cv2.VideoCapture 在部分 Windows 环境下无法打开含非 ASCII 字符的路径。
    先直接尝试打开；若失败且路径含非 ASCII 字符，则复制到临时 ASCII 路径再打开。
    退出上下文时自动释放捕获并清理临时文件。

    Yields:
        cv2.VideoCapture 对象（调用方需检查 isOpened()）。
    """
    cap = cv2.VideoCapture(path)
    tmp_path: str | None = None

    if not cap.isOpened():
        # 检测是否为非 ASCII 路径导致的打开失败
        try:
            path.encode("ascii")
        except UnicodeEncodeError:
            # 非 ASCII 路径：复制到临时 ASCII 文件重试
            ext = os.path.splitext(path)[1] or ".mp4"
            fd, tmp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            try:
                shutil.copy2(path, tmp_path)
                cap.release()
                cap = cv2.VideoCapture(tmp_path)
            except Exception:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                tmp_path = None

    try:
        yield cap
    finally:
        cap.release()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def probe_video(path: str) -> VideoInfo:
    """读取视频基本信息：fps、总帧数、分辨率、时长。"""
    with _open_video(path) as cap:
        if not cap.isOpened():
            raise RuntimeError("无法打开视频，可能缺少解码器或文件损坏")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps else 0.0
        return VideoInfo(
            path=path, fps=fps, frame_count=frame_count,
            width=width, height=height, duration=duration,
        )


def generate_thumbnail(path: str, time_sec: float, max_width: int = 360) -> bytes | None:
    """在指定时刻取一帧并降采样为 JPEG bytes，供预览显示。

    返回 None 表示取帧失败（如超出时长）。
    """
    with _open_video(path) as cap:
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
        h, w = frame.shape[:2]
        scale = max_width / w if w else 1.0
        if scale < 1.0:
            frame = cv2.resize(frame, (max_width, max(1, int(h * scale))))
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buf.tobytes() if ok else None

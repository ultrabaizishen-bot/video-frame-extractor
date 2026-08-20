"""核心抽帧逻辑测试用例（用刑具.mp4 真实验证）。

已知参数：fps=60、frame_count=711、2160x3840、约11.85秒。
"""
import glob
import math
import os

import cv2
import numpy as np
import pytest

from src.extraction_params import ExtractionCallbacks, ExtractionParams
from src.frame_extractor import extract_frames
from src.video_probe import probe_video, generate_thumbnail

VIDEO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "刑具.mp4",
)


class NoOpCB(ExtractionCallbacks):
    """无操作回调，用于不关心进度/日志的测试。"""
    pass


class CancelCB(ExtractionCallbacks):
    """在第 N 次进度回调后触发取消。"""
    def __init__(self, cancel_after: int = 30):
        self.n = 0
        self.cancel_after = cancel_after

    def on_progress(self, current: int, total: int) -> None:
        self.n += 1

    def should_cancel(self) -> bool:
        return self.n > self.cancel_after


def _imread_safe(path: str):
    """兼容中文路径的图片读取。

    cv2.imread 在 Windows 上不支持非 ASCII 路径，
    改用 np.fromfile + cv2.imdecode。
    """
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


# ---------- 视频探测 ----------

def test_probe_known_values():
    info = probe_video(VIDEO)
    assert info.fps == pytest.approx(60.0)
    assert info.frame_count == 711
    assert (info.width, info.height) == (2160, 3840)
    assert info.duration == pytest.approx(11.85, abs=0.05)


def test_probe_resolution_string():
    info = probe_video(VIDEO)
    assert info.resolution == "2160x3840"


# ---------- 抽帧：全范围每帧 ----------

def test_extract_full_range_every_frame(tmp_path):
    p = ExtractionParams(
        video_path=VIDEO, start_sec=0.0, end_sec=11.85,
        interval=1, format="PNG", quality=95, output_dir=str(tmp_path),
    )
    res = extract_frames(p, NoOpCB())
    assert res.success
    assert res.saved_count == 711
    files = sorted(glob.glob(str(tmp_path / "*.png")))
    assert len(files) == 711
    # 校验首帧为有效图像且尺寸正确
    img = cv2.imread(files[0])
    assert img is not None
    assert img.shape[:2] == (3840, 2160)


# ---------- 抽帧：子范围 + 间隔 + JPG ----------

def test_extract_subrange_interval(tmp_path):
    start_sec, end_sec = 1.0, 3.0
    interval = 6
    p = ExtractionParams(
        video_path=VIDEO, start_sec=start_sec, end_sec=end_sec,
        interval=interval, format="JPG", quality=90, output_dir=str(tmp_path),
    )
    res = extract_frames(p, NoOpCB())
    assert res.success
    info = probe_video(VIDEO)
    start_frame = int(round(start_sec * info.fps))
    end_frame = min(info.frame_count, int(round(end_sec * info.fps)))
    expected = math.ceil((end_frame - start_frame) / interval)
    assert res.saved_count == expected
    assert len(glob.glob(str(tmp_path / "*.jpg"))) == expected
    # 不应有 png
    assert len(glob.glob(str(tmp_path / "*.png"))) == 0


# ---------- 抽帧：中文路径输出目录（回归测试）----------

def test_extract_chinese_output_dir_png(tmp_path):
    """中文路径输出目录下 PNG 抽帧（cv2.imwrite 中文路径 bug 回归测试）。

    修复前：cv2.imwrite 静默失败，saved_count 虚高但磁盘无文件。
    修复后：imencode + tofile 正确写入，saved_count == 实际文件数。
    """
    chinese_dir = tmp_path / "抽帧输出" / "测试目录"
    chinese_dir.mkdir(parents=True)
    p = ExtractionParams(
        video_path=VIDEO, start_sec=0.0, end_sec=1.0,
        interval=1, format="PNG", quality=95, output_dir=str(chinese_dir),
    )
    res = extract_frames(p, NoOpCB())
    assert res.success
    assert res.saved_count > 0
    # 关键断言：磁盘实际文件数 == saved_count（修复前此处会失败）
    files = sorted(glob.glob(str(chinese_dir / "*.png")))
    assert len(files) == res.saved_count
    # 验证文件为有效图像（imdecode + fromfile 兼容中文路径读取）
    img = _imread_safe(files[0])
    assert img is not None
    assert img.shape[:2] == (3840, 2160)


def test_extract_chinese_output_dir_jpg(tmp_path):
    """中文路径输出目录下 JPG 抽帧 + quality 参数验证。"""
    chinese_dir = tmp_path / "JPG输出" / "质量测试"
    chinese_dir.mkdir(parents=True)
    p = ExtractionParams(
        video_path=VIDEO, start_sec=0.0, end_sec=1.0,
        interval=1, format="JPG", quality=50, output_dir=str(chinese_dir),
    )
    res = extract_frames(p, NoOpCB())
    assert res.success
    assert res.saved_count > 0
    files = sorted(glob.glob(str(chinese_dir / "*.jpg")))
    assert len(files) == res.saved_count
    # 不应有 png 文件
    assert len(glob.glob(str(chinese_dir / "*.png"))) == 0
    # 验证文件可正确解码
    img = _imread_safe(files[0])
    assert img is not None


# ---------- 抽帧：取消 ----------

def test_cancel_midway(tmp_path):
    p = ExtractionParams(
        video_path=VIDEO, start_sec=0.0, end_sec=11.85,
        interval=1, format="PNG", quality=95, output_dir=str(tmp_path),
    )
    res = extract_frames(p, CancelCB(cancel_after=30))
    assert 0 < res.saved_count < 711
    assert res.cancelled


# ---------- 抽帧：无效范围 ----------

def test_invalid_range(tmp_path):
    p = ExtractionParams(
        video_path=VIDEO, start_sec=5.0, end_sec=2.0,
        interval=1, format="PNG", quality=95, output_dir=str(tmp_path),
    )
    res = extract_frames(p, NoOpCB())
    assert not res.success
    assert res.error is not None


# ---------- 缩略图 ----------

def test_generate_thumbnail_returns_bytes():
    data = generate_thumbnail(VIDEO, 2.0, max_width=360)
    assert data is not None
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 0


def test_generate_thumbnail_out_of_range():
    # 超出时长的时刻应返回 None 或空
    data = generate_thumbnail(VIDEO, 999.0, max_width=360)
    assert data is None or len(data) == 0

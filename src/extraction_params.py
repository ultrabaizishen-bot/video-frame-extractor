"""参数与结果数据类（纯逻辑，无 Qt 依赖）。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VideoInfo:
    """视频探测结果。"""
    path: str
    fps: float
    frame_count: int
    width: int
    height: int
    duration: float  # 秒

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass
class ExtractionParams:
    """一次抽帧任务的输入参数。"""
    video_path: str
    start_sec: float
    end_sec: float
    interval: int = 1        # 每 N 帧保存 1 帧，1 = 每帧
    format: str = "PNG"      # "PNG" 或 "JPG"
    quality: int = 95        # JPG 质量 1-100
    output_dir: str = "."


@dataclass
class ExtractionResult:
    """一次抽帧任务的结果。"""
    success: bool
    saved_count: int
    elapsed: float = 0.0
    error: str | None = None
    cancelled: bool = False


class ExtractionCallbacks:
    """回调接口基类。worker 用 Qt 信号实现，测试用 mock 实现。"""

    def on_progress(self, current: int, total: int) -> None:
        pass

    def on_log(self, message: str) -> None:
        pass

    def should_cancel(self) -> bool:
        return False

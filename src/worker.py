"""QThread 工作线程（Qt 适配层）。

把抽帧引擎的回调桥接为 Qt 信号，保证 UI 线程安全更新。
"""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from .extraction_params import (
    ExtractionCallbacks,
    ExtractionParams,
)
from .frame_extractor import extract_frames


class ExtractionWorker(QThread):
    """后台抽帧线程。

    信号:
        progress(int): 0-100 百分比。
        log(str): 日志文本。
        finished_signal(bool, str, int): 成功标志、消息、已保存帧数。
    """

    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, int)

    def __init__(self, params: ExtractionParams):
        super().__init__()
        self._params = params
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        worker = self

        class CB(ExtractionCallbacks):
            def on_progress(self, current: int, total: int) -> None:
                pct = int(current / total * 100) if total else 0
                worker.progress.emit(pct)

            def on_log(self, message: str) -> None:
                worker.log.emit(message)

            def should_cancel(self) -> bool:
                return worker._cancel

        res = extract_frames(self._params, CB())

        if res.cancelled:
            msg = f"已取消：保存了 {res.saved_count} 帧"
        elif res.success:
            msg = f"完成：共保存 {res.saved_count} 帧，用时 {res.elapsed:.1f}s"
        else:
            msg = f"失败：{res.error}"

        self.finished_signal.emit(res.success, msg, res.saved_count)

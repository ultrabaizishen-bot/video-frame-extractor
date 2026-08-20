"""预览缩略图控件（带降采样 + 防抖）。

拖动滑块时延迟 150ms 才真正 seek 取帧，避免高频卡顿。
"""
from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel

from ..video_probe import generate_thumbnail


class VideoPreview(QLabel):
    """视频预览控件，接收视频路径与时刻，显示降采样缩略图。"""

    DEBOUNCE_MS = 150

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path: str | None = None
        self._pending_time: float | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._doUpdate)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 300)
        self.setText("选择视频后在此预览")
        self.setStyleSheet("background-color: #1e1e2e; color: #888; border-radius: 8px;")
        self.setScaledContents(False)

    def setVideoPath(self, path: str) -> None:
        self._video_path = path
        self.setText("")
        self.setPixmap(QPixmap())

    def requestFrame(self, time_sec: float) -> None:
        """请求显示指定时刻的帧（防抖）。"""
        if not self._video_path:
            return
        self._pending_time = time_sec
        self._timer.start(self.DEBOUNCE_MS)

    def _doUpdate(self) -> None:
        if self._pending_time is None or not self._video_path:
            return
        t = self._pending_time
        data = generate_thumbnail(self._video_path, t, max_width=360)
        if data:
            pix = QPixmap()
            pix.loadFromData(QByteArray(data), "JPG")
            if not pix.isNull():
                # 等比缩放到控件尺寸
                scaled = pix.scaled(
                    self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.setPixmap(scaled)
        else:
            self.setText("无法读取该时刻的帧")

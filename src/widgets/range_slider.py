"""自定义双滑块时间范围选择器。

两个可独立拖动的手柄，保证 low <= high，发 rangeChanged(low, high) 信号（单位秒）。
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QWidget


class RangeSlider(QWidget):
    """双滑块范围选择器。

    Args:
        minimum: 最小值（秒）。
        maximum: 最大值（秒）。
    """

    rangeChanged = pyqtSignal(float, float)

    HANDLE_RADIUS = 9
    TRACK_HEIGHT = 6

    def __init__(self, minimum: float = 0.0, maximum: float = 100.0, parent=None):
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._low = minimum
        self._high = maximum
        self._dragging: str | None = None  # "low" / "high" / None
        self.setMinimumHeight(36)
        self.setMouseTracking(True)

    # --- 公共接口 ---

    def setRange(self, minimum: float, maximum: float) -> None:
        self._minimum = minimum
        self._maximum = maximum
        self._low = minimum
        self._high = maximum
        self.update()

    def values(self) -> tuple[float, float]:
        return self._low, self._high

    def setValues(self, low: float, high: float) -> None:
        low = max(self._minimum, min(low, self._high))
        high = min(self._maximum, max(high, self._low))
        self._low = low
        self._high = high
        self.update()

    # --- 坐标换算 ---

    def _valueToX(self, value: float) -> float:
        if self._maximum <= self._minimum:
            return self.HANDLE_RADIUS
        span = self.width() - 2 * self.HANDLE_RADIUS
        return self.HANDLE_RADIUS + (value - self._minimum) / (self._maximum - self._minimum) * span

    def _xToValue(self, x: float) -> float:
        if self._maximum <= self._minimum:
            return self._minimum
        span = self.width() - 2 * self.HANDLE_RADIUS
        if span <= 0:
            return self._minimum
        v = self._minimum + (x - self.HANDLE_RADIUS) / span * (self._maximum - self._minimum)
        return max(self._minimum, min(v, self._maximum))

    def _handleRect(self, which: str) -> QRectF:
        x = self._valueToX(self._low if which == "low" else self._high)
        cy = self.height() / 2
        return QRectF(x - self.HANDLE_RADIUS, cy - self.HANDLE_RADIUS,
                      2 * self.HANDLE_RADIUS, 2 * self.HANDLE_RADIUS)

    # --- 绘制 ---

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cy = self.height() / 2
        track = QRectF(self.HANDLE_RADIUS, cy - self.TRACK_HEIGHT / 2,
                       self.width() - 2 * self.HANDLE_RADIUS, self.TRACK_HEIGHT)

        # 背景轨道
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#d0d5dd"))
        p.drawRoundedRect(track, self.TRACK_HEIGHT / 2, self.TRACK_HEIGHT / 2)

        # 选中区间
        x_low = self._valueToX(self._low)
        x_high = self._valueToX(self._high)
        sel = QRectF(x_low, cy - self.TRACK_HEIGHT / 2, x_high - x_low, self.TRACK_HEIGHT)
        p.setBrush(QColor("#2563eb"))
        p.drawRoundedRect(sel, self.TRACK_HEIGHT / 2, self.TRACK_HEIGHT / 2)

        # 手柄
        for which in ("low", "high"):
            r = self._handleRect(which)
            p.setPen(QPen(QColor("#2563eb"), 2))
            p.setBrush(QBrush(QColor("#ffffff")))
            p.drawEllipse(r)

    # --- 鼠标交互 ---

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        # 判断点中哪个手柄（取最近的）
        d_low = abs(pos.x() - self._valueToX(self._low))
        d_high = abs(pos.x() - self._valueToX(self._high))
        self._dragging = "low" if d_low <= d_high else "high"
        self._updateFromMouse(pos.x())

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            self._updateFromMouse(event.position().x())

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging:
            self._dragging = None
            self.rangeChanged.emit(self._low, self._high)

    def _updateFromMouse(self, x: float) -> None:
        v = self._xToValue(x)
        if self._dragging == "low":
            self._low = min(v, self._high)
        elif self._dragging == "high":
            self._high = max(v, self._low)
        self.update()
        self.rangeChanged.emit(self._low, self._high)

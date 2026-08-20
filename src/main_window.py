"""主窗口 UI 与事件逻辑。"""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .extraction_params import ExtractionParams, VideoInfo
from .video_probe import probe_video
from .worker import ExtractionWorker
from .widgets.range_slider import RangeSlider
from .widgets.video_preview import VideoPreview

VIDEO_FILTER = "视频文件 (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm *.m4v);;所有文件 (*.*)"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频抽帧工具")
        self.resize(960, 680)
        self._video_info: VideoInfo | None = None
        self._worker: ExtractionWorker | None = None
        self._syncing = False  # 防止滑块/数值框循环同步
        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        # === 左侧控制面板 ===
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 8, 0)
        left_l.setSpacing(12)

        # 视频选择
        vgroup, vform = self._group("视频选择")
        vrow = QHBoxLayout()
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setReadOnly(True)
        self.video_path_edit.setPlaceholderText("点击右侧按钮选择视频…")
        btn_browse_video = QPushButton("浏览…")
        btn_browse_video.setObjectName("browseBtn")
        btn_browse_video.clicked.connect(self._onBrowseVideo)
        vrow.addWidget(self.video_path_edit)
        vrow.addWidget(btn_browse_video)
        vform.addRow(vrow)
        left_l.addWidget(vgroup)

        # 视频信息
        igroup, info_form = self._group("视频信息")
        self.lbl_duration = QLabel("—")
        self.lbl_fps = QLabel("—")
        self.lbl_resolution = QLabel("—")
        self.lbl_frames = QLabel("—")
        info_form.addRow("时长：", self.lbl_duration)
        info_form.addRow("帧率：", self.lbl_fps)
        info_form.addRow("分辨率：", self.lbl_resolution)
        info_form.addRow("总帧数：", self.lbl_frames)
        left_l.addWidget(igroup)

        # 时间范围
        tgroup, tform = self._group("时间范围（秒）")
        self.range_slider = RangeSlider(0.0, 1.0)
        self.range_slider.rangeChanged.connect(self._onSliderChanged)
        tform.addRow(self.range_slider)
        range_row = QHBoxLayout()
        self.spin_start = self._makeTimeSpin("起始秒")
        self.spin_end = self._makeTimeSpin("结束秒")
        self.spin_start.valueChanged.connect(self._onStartSpin)
        self.spin_end.valueChanged.connect(self._onEndSpin)
        range_row.addWidget(QLabel("起始"))
        range_row.addWidget(self.spin_start)
        range_row.addWidget(QLabel("结束"))
        range_row.addWidget(self.spin_end)
        tform.addRow(range_row)
        left_l.addWidget(tgroup)

        # 输出设置
        ogroup, oform = self._group("输出设置")
        out_row = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择或输入输出目录…")
        self.btn_browse_out = QPushButton("浏览…")
        self.btn_browse_out.setObjectName("browseBtn")
        self.btn_browse_out.clicked.connect(self._onBrowseOutput)
        out_row.addWidget(self.output_dir_edit)
        out_row.addWidget(self.btn_browse_out)
        oform.addRow("输出目录：", out_row)

        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG", "JPG"])
        self.combo_format.currentTextChanged.connect(self._onFormatChanged)
        oform.addRow("图片格式：", self.combo_format)

        self.spin_quality = QSpinBox()
        self.spin_quality.setRange(1, 100)
        self.spin_quality.setValue(95)
        oform.addRow("JPG 质量：", self.spin_quality)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 9999)
        self.spin_interval.setValue(1)
        self.spin_interval.setToolTip("每 N 帧保存 1 帧，1 = 保存每一帧")
        oform.addRow("抽帧间隔：", self.spin_interval)
        left_l.addWidget(ogroup)

        # 操作按钮
        op_row = QHBoxLayout()
        self.btn_start = QPushButton("开始抽帧")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.clicked.connect(self._onStart)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._onCancel)
        op_row.addWidget(self.btn_start)
        op_row.addWidget(self.btn_cancel)
        left_l.addLayout(op_row)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.lbl_status = QLabel("就绪")
        left_l.addWidget(self.progress_bar)
        left_l.addWidget(self.lbl_status)
        left_l.addStretch()

        # === 右侧预览 ===
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(8, 0, 0, 0)
        right_l.setSpacing(8)
        preview_title = QLabel("预览")
        preview_title.setStyleSheet("font-weight: 600; color: #2b2b2b;")
        self.preview = VideoPreview()
        right_l.addWidget(preview_title)
        right_l.addWidget(self.preview, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([560, 380])

        # === 日志区 ===
        log_title = QLabel("日志")
        log_title.setStyleSheet("font-weight: 600; color: #2b2b2b; margin-top: 4px;")
        root.addWidget(log_title)
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(130)
        root.addWidget(self.log_edit)

        self._onFormatChanged(self.combo_format.currentText())

    def _group(self, title: str) -> tuple[QWidget, QFormLayout]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: 600; color: #2b2b2b;")
        lay.addWidget(title_lbl)
        form = QFormLayout()
        form.setSpacing(6)
        lay.addLayout(form)
        w.setProperty("isGroup", True)
        return w, form

    def _makeTimeSpin(self, _placeholder: str) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setDecimals(3)
        s.setRange(0.0, 999999.0)
        s.setSingleStep(0.1)
        s.setSuffix(" s")
        return s

    # ------------------------------------------------------------------ 事件

    def _onBrowseVideo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", VIDEO_FILTER,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not path:
            return
        self.video_path_edit.setText(path)
        try:
            info = probe_video(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "错误", f"无法读取视频信息：\n{exc}")
            return
        self._video_info = info
        self.lbl_duration.setText(f"{info.duration:.3f} s")
        self.lbl_fps.setText(f"{info.fps:.2f} fps")
        self.lbl_resolution.setText(info.resolution)
        self.lbl_frames.setText(str(info.frame_count))

        # 重置范围
        self._syncing = True
        self.range_slider.setRange(0.0, info.duration)
        self.spin_start.setRange(0.0, info.duration)
        self.spin_end.setRange(0.0, info.duration)
        self.spin_start.setValue(0.0)
        self.spin_end.setValue(info.duration)
        self._syncing = False

        # 预览首帧
        self.preview.setVideoPath(path)
        self.preview.requestFrame(0.0)
        self._appendLog(f"已加载视频：{os.path.basename(path)}（{info.resolution}, {info.fps:.1f}fps, {info.frame_count}帧）")

        # 默认输出目录 = 视频同目录/frames
        default_out = os.path.join(os.path.dirname(path), "frames")
        if not self.output_dir_edit.text():
            self.output_dir_edit.setText(default_out)

    def _onBrowseOutput(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", "",
            QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ShowDirsOnly,
        )
        if path:
            self.output_dir_edit.setText(path)

    def _onSliderChanged(self, low: float, high: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        self.spin_start.setValue(low)
        self.spin_end.setValue(high)
        self._syncing = False
        # 预览结束时刻
        self.preview.requestFrame(high)

    def _onStartSpin(self, val: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        if val > self.spin_end.value():
            self.spin_end.setValue(val)
        low, high = self.spin_start.value(), self.spin_end.value()
        self.range_slider.setValues(low, high)
        self._syncing = False
        self.preview.requestFrame(val)

    def _onEndSpin(self, val: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        if val < self.spin_start.value():
            self.spin_start.setValue(val)
        low, high = self.spin_start.value(), self.spin_end.value()
        self.range_slider.setValues(low, high)
        self._syncing = False
        self.preview.requestFrame(val)

    def _onFormatChanged(self, fmt: str) -> None:
        self.spin_quality.setEnabled(fmt.upper() == "JPG")

    def _onStart(self) -> None:
        if not self._video_info:
            QMessageBox.warning(self, "提示", "请先选择视频文件。")
            return
        start = self.spin_start.value()
        end = self.spin_end.value()
        if end <= start:
            QMessageBox.warning(self, "提示", "结束时间须大于起始时间。")
            return
        out_dir = self.output_dir_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "提示", "请选择输出目录。")
            return

        params = ExtractionParams(
            video_path=self._video_info.path,
            start_sec=start,
            end_sec=end,
            interval=self.spin_interval.value(),
            format=self.combo_format.currentText(),
            quality=self.spin_quality.value(),
            output_dir=out_dir,
        )

        self._setRunning(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("正在提取…")
        self._appendLog(f"输出目录：{out_dir}")

        self._worker = ExtractionWorker(params)
        self._worker.progress.connect(self._onProgress)
        self._worker.log.connect(self._appendLog)
        self._worker.finished_signal.connect(self._onFinished)
        self._worker.start()

    def _onCancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._appendLog("正在取消…")
            self.btn_cancel.setEnabled(False)

    def _onProgress(self, pct: int) -> None:
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"正在提取：{pct}%")

    def _onFinished(self, success: bool, message: str, saved: int) -> None:
        self._appendLog(message)
        self.progress_bar.setValue(100 if success else self.progress_bar.value())
        self.lbl_status.setText(message)
        self._setRunning(False)
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "未完成", message)

    # ------------------------------------------------------------------ 辅助

    def _setRunning(self, running: bool) -> None:
        self.btn_start.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        # 运行时禁用关键输入和浏览按钮
        for w in (self.video_path_edit, self.output_dir_edit,
                  self.spin_start, self.spin_end, self.spin_interval,
                  self.combo_format, self.spin_quality,
                  self.btn_browse_out):
            w.setEnabled(not running)

    def _appendLog(self, msg: str) -> None:
        self.log_edit.appendPlainText(msg)
        sb = self.log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        event.accept()

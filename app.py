"""视频抽帧工具 — 程序入口。"""
from __future__ import annotations

import os
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from src.main_window import MainWindow


def resource_path(rel: str) -> str:
    """兼容 PyInstaller 打包后的资源路径。

    打包后资源解压到 sys._MEIPASS 临时目录；开发运行时用当前目录。
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)


def load_stylesheet(app: QApplication) -> None:
    qss_path = resource_path("src/resources/style.qss")
    try:
        with open(qss_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except (FileNotFoundError, OSError):
        # 样式文件缺失时静默降级，不阻止启动
        pass


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("视频抽帧工具")
    app.setFont(QFont("Microsoft YaHei UI", 9))
    load_stylesheet(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

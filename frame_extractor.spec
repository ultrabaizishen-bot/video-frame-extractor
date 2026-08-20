# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 视频抽帧工具（单 exe 文件模式）。

关键点：
1. --onefile 模式：所有依赖打包进单个 exe，双击即用。
2. 显式捆绑 opencv ffmpeg DLL（解决陌生机器无法解码视频的 #1 坑）。
3. 仅收集实际使用的 PyQt6 模块（QtCore/QtGui/QtWidgets），排除数十个无用模块以减小体积。
4. console=False：无黑窗。
"""
import glob
import os

from PyInstaller.utils.hooks import collect_data_files

# 动态定位 opencv ffmpeg DLL，glob 兜底匹配任意版本号
import cv2

cv2_dir = os.path.dirname(cv2.__file__)
ffmpeg_dlls = glob.glob(os.path.join(cv2_dir, "opencv_videoio_ffmpeg*_64.dll"))
print(f"[spec] 发现 ffmpeg DLL: {ffmpeg_dlls}")

datas = [(dll, "cv2") for dll in ffmpeg_dlls]  # 关键：放进 cv2 目录
datas += collect_data_files("PyQt6")            # Qt 插件/资源（含平台插件 qwindows.dll）
datas += [
    ("src/resources/style.qss", "src/resources"),
    ("src/resources/icon.ico", "src/resources"),
]

# 排除的无用 PyQt6 模块（本应用仅用 QtCore/QtGui/QtWidgets）
pyqt6_excludes = [
    "PyQt6.QtQuick", "PyQt6.QtQml", "PyQt6.QtQmlWorkerScript",
    "PyQt6.QtQuickWidgets", "PyQt6.QtQuick3D", "PyQt6.QtQuickControls2",
    "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets", "PyQt6.QtWebEngineQuick",
    "PyQt6.QtWebChannel", "PyQt6.QtWebSockets",
    "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
    "PyQt6.Qt3DCore", "PyQt6.Qt3DRender", "PyQt6.Qt3DInput",
    "PyQt6.Qt3DLogic", "PyQt6.Qt3DExtras", "PyQt6.Qt3DAnimation",
    "PyQt6.QtCharts", "PyQt6.QtDataVisualization",
    "PyQt6.QtBluetooth", "PyQt6.QtNetwork", "PyQt6.QtNetworkAuth",
    "PyQt6.QtPositioning", "PyQt6.QtLocation",
    "PyQt6.QtSensors", "PyQt6.QtSerialPort", "PyQt6.QtSerialBus",
    "PyQt6.QtSql", "PyQt6.QtTest", "PyQt6.QtTextToSpeech",
    "PyQt6.QtSvg", "PyQt6.QtSvgWidgets",
    "PyQt6.QtPdf", "PyQt6.QtPdfWidgets",
    "PyQt6.QtDesigner", "PyQt6.QtHelp", "PyQt6.QtNfc",
    "PyQt6.QtRemoteObjects", "PyQt6.QtScxml", "PyQt6.QtSpatialAudio",
    "PyQt6.QtOpenGL", "PyQt6.QtOpenGLWidgets",
    "PyQt6.QtPrintSupport", "PyQt6.QtShaderTools",
    "PyQt6.QtStateMachine", "PyQt6.QtUiTools",
    "PyQt6.QtAxContainer", "PyQt6.QtDBus",
    "PyQt6.QtChartsQml", "PyQt6.QtDataVisualizationQml",
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter", "PyQt5", "PySide6", "matplotlib", "scipy", "pytest",
        "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets", "PyQt6.QtMultimedia", "PyQt6.Qt3DCore",
        "PyQt6.QtNetwork", "PyQt6.QtSql", "PyQt6.QtTest", "PyQt6.QtSvg",
        "PyQt6.QtPdf", "PyQt6.QtBluetooth", "PyQt6.QtPositioning",
        "PyQt6.QtSensors", "PyQt6.QtSerialPort", "PyQt6.QtTextToSpeech",
        "PyQt6.QtWebChannel", "PyQt6.QtWebSockets", "PyQt6.QtDesigner",
        "PyQt6.QtHelp", "PyQt6.QtCharts", "PyQt6.QtDataVisualization",
        "PyQt6.QtRemoteObjects", "PyQt6.QtScxml", "PyQt6.QtSpatialAudio",
        "PyQt6.QtOpenGL", "PyQt6.QtPrintSupport", "PyQt6.QtNfc",
        "PyQt6.QtLocation", "PyQt6.QtQuick3D", "PyQt6.QtQuickWidgets",
        "PyQt6.QtShaderTools", "PyQt6.QtStateMachine", "PyQt6.QtSvgWidgets",
        "PyQt6.QtUiTools", "PyQt6.QtWebEngineQuick", "PyQt6.QtQmlWorkerScript",
        "PyQt6.QtPdfWidgets", "PyQt6.QtOpenGLWidgets",
        "PyQt6.QtMultimediaWidgets", "PyQt6.Qt3DRender", "PyQt6.Qt3DInput",
        "PyQt6.Qt3DLogic", "PyQt6.Qt3DExtras", "PyQt6.Qt3DAnimation",
        "PyQt6.QtSerialBus", "PyQt6.QtNetworkAuth", "PyQt6.QtAxContainer",
        "PyQt6.QtDBus", "PyQt6.QtQuickControls2",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="视频抽帧工具",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="src/resources/icon.ico",
)

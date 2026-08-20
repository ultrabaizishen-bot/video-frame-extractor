# 🎬 视频抽帧工具 Video Frame Extractor

> 将视频中指定时间范围内的**每一帧**保存为图片的桌面端软件。
> 无需安装 Python，双击即用，在任意 Windows 系统上流畅运行。

一款简单、快速、开箱即用的桌面工具：选择视频 → 设置时间范围 → 一键抽取全部帧，导出为 PNG / JPG 图片。后台线程处理，界面不卡顿，可随时取消。

---

## ✨ 功能特性

| 特性 | 说明 |
|------|------|
| 🎞️ **多格式支持** | mp4 / avi / mkv / mov / flv / wmv / webm / m4v 等常见格式 |
| 📅 **灵活的时间范围** | 命令行级精度，滑块 + 数值双重方式设置起始/结束秒 |
| 🖼️ **两种输出格式** | PNG 无损 / JPG 压缩可调，JPG 质量 1–100 自由调节 |
| 🔢 **抽帧间隔** | 每 N 帧保存 1 帧，1 = 保存每一帧 |
| ⚡ **后台抽取** | QThread 后台线程，界面不卡顿，可随时取消 |
| 👁️ **实时预览** | 拖动滑块即预览所选时间点的画面 |
| 📊 **实时进度与日志** | 进度条 + 完整日志，全程透明可视化 |
| 🌏 **中文路径兼容** | 修复 OpenCV 在 Windows 中文路径下静默无法写图的问题 |
| 📦 **开箱即用** | 单 exe 打包，无需 Python / 任何运行时依赖 |

---

## 🚀 快速开始

### 方式一：下载单 exe（推荐）

从 [Releases](https://github.com/ultrabaizishen-bot/video-frame-extractor/releases) 下载 `视频抽帧工具.exe`，双击即可运行，无需任何安装。

搜索 `dist` 目录下的可执行文件亦可直接使用。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/ultrabaizishen-bot/video-frame-extractor.git
cd video-frame-extractor

# 安装依赖（建议使用虚拟环境）
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 运行
python app.py
```

### 方式三：自己打包单 exe

```bat
:: 一键打包，生成 dist\视频抽帧工具.exe
build.bat
```

---

## 🖱️ 使用步骤

1. 点击 **「浏览…」** 选择视频文件
2. 查看视频信息（时长、帧率、分辨率、总帧数）
3. 拖动滑块或输入数值，设置 **起始秒** 和 **结束秒**
4. 选择 **输出目录**
5. 选择图片格式（PNG 无损 / JPG 压缩）
6. 如选 JPG，调整质量（默认 95）
7. 如不需每帧，设置**抽帧间隔**（1 = 每帧）
8. 点击 **「开始抽帧」**
9. 等待完成，图片自动保存在输出目录

### 输出文件命名

帧图片按序号零填充命名，便于排序合并：

```
frame_000000.png
frame_000001.png
frame_000002.png
...
```

---

## 🔧 技术栈

- **语言**：Python 3.10
- **界面**：PyQt6
- **视频编解码**：OpenCV (opencv-python-headless)
- **科学计算**：NumPy
- **打包分发**：PyInstaller / Inno Setup
- **测试**：pytest

---

## 📂 项目结构

```
video-frame-extractor/
├── app.py                  # 程序入口
├── requirements.txt        # 依赖清单
├── build.bat               # 一键打包脚本
├── frame_extractor.spec    # PyInstaller 打包配置
├── installer.iss           # Inno Setup 安装包脚本
├── src/
│   ├── main_window.py      # 主窗口 UI 与交互逻辑
│   ├── frame_extractor.py  # 抽帧引擎核心（纯逻辑）
│   ├── extraction_params.py# 参数与结果数据类
│   ├── video_probe.py      # 视频信息探测与缩略图
│   ├── worker.py           # QThread 后台工作线程
│   ├── widgets/
│   │   ├── range_slider.py # 时间范围滑杆控件
│   │   └── video_preview.py# 视频预览控件
│   └── resources/
│       ├── style.qss       # 全局样式表
│       └── icon.ico        # 应用图标
└── tests/
    └── test_frame_extractor.py  # 核心逻辑 + 中文路径回归测试
```

---

## 🧪 运行测试

```bash
python -m pytest tests/ -v
```

覆盖：视频探测、全范围逐帧抽取、子范围 + 间隔 + JPG、**中文路径输出目录回归**、取消操作、无效范围、缩略图生成。

---

## ⚙️ 底层设计

- **零内存累积**：单帧「读 → 编码 → 写盘 → 释放」，从容应对 4K 大帧。
- **帧级精确 seek**：使用 `CAP_PROP_POS_FRAMES` 精确定位起始帧。
- **回调解耦**：进度 / 日志 / 取消通过回调接口解耦，UI 层用 Qt 信号桥接，核心逻辑可独立测试。
- **中文路径免疫**：写盘改用 `cv2.imencode` + `numpy.tofile`，规避 Windows 下 `cv2.imwrite` 对非 ASCII 路径静默失灵的已知缺陷。

---

## 📝 更新日志

### v1.0.0
- 首个正式版本
- 支持多格式视频、时间范围抽帧、PNG/JPG 输出、自定义间隔与质量
- 修复 Windows 中文路径下图片无法保存的问题

---

## 📄 许可证

本项目基于 [MIT](LICENSE) 协议开源，欢迎使用、修改与二次开发。

**做得开心 👍 觉得好用就点个 ⭐ Star 吧！**
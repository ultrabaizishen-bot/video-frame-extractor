@echo off
chcp 65001 >nul
REM ============================================================
REM  视频抽帧工具 — 一键打包脚本（单 exe 文件）
REM  生成 dist\视频抽帧工具.exe
REM ============================================================

echo [1/2] 清理旧构建产物...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/2] 执行 PyInstaller 打包（单文件模式）...
python -m PyInstaller frame_extractor.spec --noconfirm
if errorlevel 1 (
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo   单 exe 文件: dist\视频抽帧工具.exe
echo   双击即可运行，无需安装。
echo ========================================
pause

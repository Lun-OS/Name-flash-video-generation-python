@echo off
REM ==============================================================
REM  install_deps.bat
REM  一键：升级 pip → 逐个安装包 → 最终检查
REM  默认使用清华 PyPI 镜像
REM ==============================================================

:: 让中文不乱码
chcp 65001 >nul
title Python 依赖安装/检查工具
color 0A

:: 统一镜像地址，方便以后改
set "INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"

echo ===== 步骤 1：更新 pip =====
python -m pip install --upgrade pip -i %INDEX%
if errorlevel 1 (
    echo [ERROR] pip 升级失败，请检查网络或 Python 环境
    pause
    exit /b 1
)

echo.
echo ===== 步骤 2：逐个安装第三方包 =====
REM 想加包/删包，直接改下面几行即可
REM （每行一个包，写一行就装一行，非常直观）
python -m pip install opencv-python -i %INDEX%
if errorlevel 1 goto :install_fail

python -m pip install pillow -i %INDEX%
if errorlevel 1 goto :install_fail

python -m pip install numpy -i %INDEX%
if errorlevel 1 goto :install_fail

REM 示例：再加一个包
REM python -m pip install requests -i %INDEX%
REM if errorlevel 1 goto :install_fail

echo.
echo ===== 步骤 3：最终检查 =====
python -c "import cv2, PIL.Image, numpy" 2>nul
if errorlevel 1 (
    echo [ERROR] 仍有包未成功导入
    goto :install_fail
)

echo.
echo ===== 全部完成！可按需关闭窗口 =====
echo By：Lun.
pause
exit /b 0

:install_fail
echo.
echo [ERROR] 安装或检查过程中出错，请查看上方报错信息
pause
exit /b 1
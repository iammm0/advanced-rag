@echo off
REM 下载GitHub依赖到本地vendor目录 - Windows CMD版本
REM 用于在构建Docker镜像前预先下载依赖，避免构建时从GitHub拉取

setlocal enabledelayedexpansion

REM 设置脚本目录
set SCRIPT_DIR=%~dp0
set VENDOR_DIR=%SCRIPT_DIR%vendor

echo ========================================
echo 开始下载GitHub依赖到本地...
echo ========================================
echo.

REM 检查Git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Git，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    exit /b 1
)

REM 创建vendor目录
if not exist "%VENDOR_DIR%" (
    echo [信息] 创建vendor目录...
    mkdir "%VENDOR_DIR%"
)

REM 下载 PaddleOCR
set PADDLEOCR_DIR=%VENDOR_DIR%\PaddleOCR
if exist "%PADDLEOCR_DIR%" (
    echo [信息] PaddleOCR 已存在，跳过下载
    echo [提示] 如需更新，请删除 %PADDLEOCR_DIR% 后重新运行此脚本
    echo.
) else (
    echo [信息] 正在克隆 PaddleOCR...
    cd /d "%VENDOR_DIR%"
    if errorlevel 1 (
        echo [错误] 无法切换到vendor目录
        exit /b 1
    )
    
    git clone --depth 1 https://github.com/PaddlePaddle/PaddleOCR.git
    if errorlevel 1 (
        echo [错误] PaddleOCR 克隆失败
        echo [提示] 请检查网络连接或GitHub访问权限
        exit /b 1
    )
    
    echo [成功] PaddleOCR 下载完成
    echo.
)

echo ========================================
echo 所有依赖下载完成！
echo ========================================
echo.
echo [提示] 现在可以运行 docker build 构建镜像了
echo.

exit /b 0

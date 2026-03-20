@echo off
REM 快速启动脚本 - Windows PowerShell

echo ========================================
echo 警情分类系统 - 快速启动
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到 PATH
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
pip list | findstr fastapi >nul 2>&1
if errorlevel 1 (
    echo [2/4] 安装依赖...
    pip install -r requirements.txt
) else (
    echo [2/4] 依赖已安装
)

echo.
echo [3/4] 检查数据库...
if not exist "chroma_db" (
    echo [警告] 数据库不存在，请先运行：
    echo   python ingest.py --input data/sample_incidents.csv
    echo.
)

echo [4/4] 启动 FastAPI 服务...
echo.
echo ========================================
echo 服务已启动！
echo API 文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo ========================================
echo.

python api_server.py

pause


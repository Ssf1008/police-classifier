# 快速启动脚本 - Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "警情分类系统 - 快速启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    python --version | Out-Null
} catch {
    Write-Host "[错误] Python 未安装或未添加到 PATH" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}

# 检查依赖
Write-Host "[1/4] 检查依赖..." -ForegroundColor Yellow
$hasFastAPI = pip list | Select-String "fastapi"
if (-not $hasFastAPI) {
    Write-Host "[2/4] 安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
} else {
    Write-Host "[2/4] 依赖已安装" -ForegroundColor Green
}

# 检查数据库
Write-Host "[3/4] 检查数据库..." -ForegroundColor Yellow
if (-not (Test-Path "chroma_db")) {
    Write-Host "[警告] 数据库不存在，请先运行：" -ForegroundColor Yellow
    Write-Host "  python ingest.py --input data/sample_incidents.csv" -ForegroundColor Yellow
    Write-Host ""
}

# 启动服务
Write-Host "[4/4] 启动 FastAPI 服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "服务已启动！" -ForegroundColor Green
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "健康检查: http://localhost:8000/health" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

python api_server.py


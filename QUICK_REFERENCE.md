# 快速参考 - PyCharm vs Dify

## 🎯 核心概念

你的系统分为两部分：

```
PyCharm (后端服务)          Dify (前端工作流)
    ↓                           ↓
api_server.py          →    HTTP 请求节点
(FastAPI)                   (调用 API)
    ↓                           ↓
rag_classifier.py      →    输出结果
(分类逻辑)                  (展示给用户)
```

---

## 📋 PyCharm 中要做的事

### 1️⃣ 第一次设置（只需一次）

```bash
# 打开终端，进入项目目录
cd "E:\QQ\新建文件夹\新建文件夹"

# 安装依赖
pip install -r requirements.txt

# 准备数据（如果没有 police_cases_labeled.csv）
python ingest.py --input data/sample_incidents.csv
```

### 2️⃣ 每次使用前启动服务

**方式 A：直接运行脚本**
```bash
python start_api.ps1
```

**方式 B：在 PyCharm 中运行**
1. 打开 `api_server.py`
2. 点击右上角的 ▶️ **Run** 按钮
3. 看到 `Uvicorn running on http://0.0.0.0:8000` 就表示成功

**方式 C：手动运行**
```bash
python api_server.py
```

### 3️⃣ 配置 API 密钥

创建 `.env` 文件（项目根目录）：
```
OPENAI_API_KEY=你的硅基流动API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

---

## 🎨 Dify 中要做的事

### 1️⃣ 创建工作流

1. 打开 Dify
2. 点击 **"创建"** → **"工作流"**
3. 输入名称：`警情分类系统`
4. 点击 **"创建"**

### 2️⃣ 添加输入变量

1. 点击左侧 **"开始"** 节点
2. 右侧面板 → **"添加变量"**
3. 配置：
   - 名称：`incident_text`
   - 类型：文本
   - 标签：警情文本
   - 必填：✓

### 3️⃣ 添加 HTTP 请求节点

1. 点击 **"+"** 添加节点
2. 选择 **"HTTP 请求"**
3. 配置：

| 字段 | 值 |
|------|-----|
| 名称 | 调用分类API |
| URL | http://localhost:8000/classify |
| 方法 | POST |
| Content-Type | application/json |

4. 请求体（Body）：
```json
{
  "query": "{{incident_text}}",
  "top_k": 5,
  "llm_provider": "openai"
}
```

### 4️⃣ 添加输出节点

1. 点击 **"+"** 添加节点
2. 选择 **"输出"**
3. 添加以下输出字段：

| 字段名 | 值 |
|--------|-----|
| category | {{调用分类API.body.category}} |
| confidence | {{调用分类API.body.confidence}} |
| reason | {{调用分类API.body.reason}} |
| similar_cases | {{调用分类API.body.similar_cases}} |

### 5️⃣ 连接节点

用鼠标拖动连接：
```
开始 → 调用分类API → 输出
```

### 6️⃣ 测试

1. 点击右上角 **"运行"**
2. 输入测试文本：`小区内两人发生争执并有肢体冲突`
3. 点击 **"运行"**
4. 查看结果

### 7️⃣ 发布

1. 点击右上角 **"发布"**
2. 选择发布方式：
   - **作为应用**：生成可分享的 Web 应用
   - **作为 API**：生成 REST API 端点

---

## 🔍 测试 API（可选）

### 在浏览器中测试

访问：http://localhost:8000/docs

你会看到 Swagger UI，可以直接测试 API。

### 用 curl 测试

```bash
curl -X POST http://localhost:8000/classify ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"小区内两人发生争执并有肢体冲突\",\"top_k\":5,\"llm_provider\":\"openai\"}"
```

---

## ⚠️ 常见问题

| 问题 | 解决方案 |
|------|--------|
| Dify 连接不到 API | 确保 PyCharm 中的 `api_server.py` 正在运行 |
| API 返回 500 错误 | 检查 PyCharm 终端的错误日志 |
| 找不到数据库 | 运行 `python ingest.py --input data/sample_incidents.csv` |
| API 密钥错误 | 检查 `.env` 文件中的 `OPENAI_API_KEY` |

---

## 📊 工作流数据流

```
用户输入（Dify）
    ↓
incident_text = "小区内两人发生争执..."
    ↓
HTTP POST 到 http://localhost:8000/classify
    ↓
FastAPI 接收请求
    ↓
RAGIncidentClassifier.classify()
    ↓
返回 JSON：
{
  "category": "治安案件",
  "confidence": 0.95,
  "reason": "...",
  "similar_cases": [...]
}
    ↓
Dify 解析响应
    ↓
输出结果给用户
```

---

## 🚀 快速启动命令

```bash
# 1. 进入项目目录
cd "E:\QQ\新建文件夹\新建文件夹"

# 2. 安装依赖（第一次）
pip install -r requirements.txt

# 3. 准备数据（第一次）
python ingest.py --input data/sample_incidents.csv

# 4. 启动 API 服务
python api_server.py

# 5. 在 Dify 中创建工作流并测试
```

---

## 📝 文件说明

| 文件 | 位置 | 用途 |
|------|------|------|
| `api_server.py` | PyCharm | FastAPI 服务入口 |
| `rag_classifier.py` | PyCharm | 分类逻辑 |
| `config.py` | PyCharm | 配置文件 |
| `.env` | PyCharm | API 密钥 |
| 工作流 | Dify | 调用 API 的流程 |

---

## 💡 提示

- **PyCharm 的 `api_server.py` 必须一直运行**，Dify 才能调用它
- **Dify 中的 URL 必须是 `http://localhost:8000/classify`**（如果在同一台机器上）
- **如果 Dify 和 PyCharm 在不同机器上**，改为 `http://你的IP:8000/classify`


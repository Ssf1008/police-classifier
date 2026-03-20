# Dify 部署指南 - 警情分类系统

## 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                        Dify 工作流                            │
│  (在浏览器中使用，不需要写代码)                              │
└──────────────────────────────────────────────────────────────┘
                              ↓
                    [HTTP 请求节点]
                              ↓
┌──────────────────────────────────────────────────────────────┐
│              FastAPI 服务 (api_server.py)                    │
│         在 PyCharm 中运行，监听 http://localhost:8000        │
└──────────────────────────────────────────────────────────────┘
                              ↓
                    [调用 RAG 分类器]
                              ↓
┌──────────────────────────────────────────────────────────────┐
│  ChromaDB 向量数据库 + LLM (OpenAI/Ollama)                   │
│         (本地数据库 + 硅基流动 API)                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 第一部分：PyCharm 中的代码准备

### 步骤 1：安装依赖

在 PyCharm 的终端中运行：

```bash
cd "E:\QQ\新建文件夹\新建文件夹"
pip install -r requirements.txt
```

### 步骤 2：准备数据（如果还没有）

确保你有 `police_cases_labeled.csv` 文件，包含以下列：
- `id`: 案例 ID
- `text`: 警情文本
- `label`: 分类标签（如：诈骗、盗窃、交通事故等）

如果没有，可以用示例数据：

```bash
python ingest.py --input data/sample_incidents.csv
```

### 步骤 3：配置 API 密钥

在 PyCharm 中，创建 `.env` 文件（项目根目录）：

```
OPENAI_API_KEY=你的硅基流动API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

或者在 PyCharm 的运行配置中设置环境变量。

### 步骤 4：启动 FastAPI 服务

在 PyCharm 中打开 `api_server.py`，点击右上角的 **Run** 按钮，或在终端运行：

```bash
python api_server.py
```

你会看到输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**此时服务已启动，监听在 http://localhost:8000**

### 步骤 5：测试 API（可选）

在另一个终端测试：

```bash
curl -X POST http://localhost:8000/classify ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"小区内两人发生争执并有肢体冲突\"}"
```

或者在浏览器访问 http://localhost:8000/docs 查看 API 文档。

---

## 第二部分：Dify 中的工作流配置

### 前置条件

- Dify 已安装并运行（本地或云端）
- PyCharm 中的 FastAPI 服务正在运行

### 详细步骤

#### 1. 创建新工作流

1. 打开 Dify 界面
2. 点击左侧 **"创建"** → **"工作流"**
3. 输入工作流名称：`警情分类系统`
4. 点击 **"创建"**

#### 2. 添加输入节点

1. 在工作流编辑器中，点击左侧 **"开始"** 节点
2. 在右侧面板中，点击 **"添加变量"**
3. 配置输入变量：
   - **变量名**: `incident_text`
   - **类型**: 文本
   - **标签**: 警情文本
   - **描述**: 输入要分类的警情文本
   - **必填**: 是

#### 3. 添加 HTTP 请求节点

1. 在工作流编辑器中，点击 **"+"** 按钮添加节点
2. 选择 **"HTTP 请求"** 节点
3. 配置如下：

**基本信息：**
- **节点名称**: `调用分类API`
- **URL**: `http://localhost:8000/classify`
- **方法**: `POST`

**请求头：**
- 点击 **"添加请求头"**
- **Key**: `Content-Type`
- **Value**: `application/json`

**请求体（Body）：**
- 选择 **"JSON"** 格式
- 点击 **"编辑 JSON"**，输入：

```json
{
  "query": "{{incident_text}}",
  "top_k": 5,
  "llm_provider": "openai"
}
```

**响应处理：**
- 保持默认（自动解析 JSON）

#### 4. 添加输出节点

1. 点击 **"+"** 添加节点
2. 选择 **"输出"** 节点
3. 配置输出内容：

点击 **"添加输出"**，配置以下字段：

**输出 1 - 分类类别：**
- **字段名**: `category`
- **值**: `{{调用分类API.body.category}}`

**输出 2 - 置信度：**
- **字段名**: `confidence`
- **值**: `{{调用分类API.body.confidence}}`

**输出 3 - 分类理由：**
- **字段名**: `reason`
- **值**: `{{调用分类API.body.reason}}`

**输出 4 - 相似案例：**
- **字段名**: `similar_cases`
- **值**: `{{调用分类API.body.similar_cases}}`

#### 5. 连接节点

1. 从 **"开始"** 节点的输出口拖到 **"调用分类API"** 节点的输入口
2. 从 **"调用分类API"** 节点的输出口拖到 **"输出"** 节点的输入口

最终工作流应该是这样：

```
[开始] → [调用分类API] → [输出]
```

#### 6. 测试工作流

1. 点击右上角 **"运行"** 按钮
2. 在弹出的输入框中输入测试文本，例如：
   ```
   小区内两人发生争执并有肢体冲突
   ```
3. 点击 **"运行"**
4. 查看输出结果

#### 7. 发布工作流

1. 点击右上角 **"发布"** 按钮
2. 选择发布方式：
   - **作为应用**: 生成可分享的 Web 应用
   - **作为 API**: 生成 REST API 端点

---

## 常见问题排查

### 问题 1：Dify 无法连接到 FastAPI 服务

**症状**: 工作流运行时报错 `Connection refused` 或 `Cannot reach server`

**解决方案**:
1. 确保 PyCharm 中的 `api_server.py` 正在运行
2. 检查 URL 是否正确：`http://localhost:8000/classify`
3. 如果 Dify 和 FastAPI 在不同机器上，改为：`http://你的IP地址:8000/classify`

### 问题 2：API 返回 500 错误

**症状**: 工作流运行时返回 `Internal Server Error`

**解决方案**:
1. 查看 PyCharm 终端的错误日志
2. 检查 `OPENAI_API_KEY` 是否正确设置
3. 确保 ChromaDB 数据库已初始化（运行过 `ingest.py`）

### 问题 3：响应格式不对

**症状**: Dify 无法解析 API 响应

**解决方案**:
1. 在浏览器访问 `http://localhost:8000/docs` 查看 API 文档
2. 手动测试 API 响应格式
3. 检查 Dify 中的 JSON 路径是否正确（如 `{{调用分类API.body.category}}`）

---

## 完整工作流示例

### 工作流 JSON（可直接导入）

如果你想快速导入，可以在 Dify 中使用以下 JSON：

```json
{
  "version": "0.1",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "position": [100, 100],
      "data": {
        "variables": [
          {
            "name": "incident_text",
            "type": "string",
            "required": true,
            "label": "警情文本"
          }
        ]
      }
    },
    {
      "id": "http_request",
      "type": "http_request",
      "position": [300, 100],
      "data": {
        "name": "调用分类API",
        "url": "http://localhost:8000/classify",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "query": "{{incident_text}}",
          "top_k": 5,
          "llm_provider": "openai"
        }
      }
    },
    {
      "id": "output",
      "type": "output",
      "position": [500, 100],
      "data": {
        "outputs": [
          {
            "name": "category",
            "value": "{{http_request.body.category}}"
          },
          {
            "name": "confidence",
            "value": "{{http_request.body.confidence}}"
          },
          {
            "name": "reason",
            "value": "{{http_request.body.reason}}"
          },
          {
            "name": "similar_cases",
            "value": "{{http_request.body.similar_cases}}"
          }
        ]
      }
    }
  ],
  "edges": [
    {
      "source": "start",
      "target": "http_request"
    },
    {
      "source": "http_request",
      "target": "output"
    }
  ]
}
```

---

## 总结

| 位置 | 任务 | 工具 |
|------|------|------|
| **PyCharm** | 1. 安装依赖 | 终端 |
| **PyCharm** | 2. 准备数据 | `ingest.py` |
| **PyCharm** | 3. 设置 API 密钥 | `.env` 文件 |
| **PyCharm** | 4. 启动 FastAPI 服务 | `api_server.py` |
| **Dify** | 5. 创建工作流 | 可视化编辑器 |
| **Dify** | 6. 配置 HTTP 请求 | 节点配置 |
| **Dify** | 7. 测试和发布 | 运行/发布按钮 |

---

## 下一步

- 如果需要更复杂的工作流（如多步骤处理、条件判断等），可以在 Dify 中添加更多节点
- 如果需要自定义 LLM 提示词，可以在 `rag_classifier.py` 中修改
- 如果需要部署到生产环境，可以使用 Docker 容器化 FastAPI 服务


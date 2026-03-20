# RAG 警情分类（LangChain + ChromaDB）

## 功能
- 读取带标签历史警情（`police_cases_labeled.csv`）
- Embedding 向量化并写入 ChromaDB（本地持久化目录 `./chroma_police_cases`）
- 对新警情进行 Top-K 检索（RAG）
- LangChain 组装提示词（使用你提供的模板）
- 调用“模拟大模型”（离线可跑通），输出：分类类别 + 分类理由 + 置信度

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python rag_police_classifier.py
```

运行后会对内置的测试案例逐条输出：
- RAG 检索到的相似案例及其标签
- 模型输出（按模板的 3 行格式）
- 解析后的结构化 JSON（category/reason/confidence）

## 后续对接真实大模型（百川/通义千问）
- 只需要把 `rag_police_classifier.py` 里的 `SimulatedPoliceLLM` 替换为对应的真实 LLM（LangChain Chat/LLM 封装）
- 其余流程（Chroma 检索、提示词模板、输出解析）可保持不变

# RAG 警情分类系统（LangChain + ChromaDB）

实现功能：
- 读取历史警情数据（CSV/JSONL）
- 文本向量化（默认 HuggingFace 本地嵌入）
- 建立/持久化向量数据库（ChromaDB）
- 输入新警情，检索相似案例（TopK）
- 调用大模型输出：分类类别、分类理由、置信度（0-1）

## 1) 环境准备

建议 Python 3.10+。

安装依赖：

```bash
pip install -r requirements.txt
```

## 2) 准备历史数据

支持两种格式（字段名建议保持一致）：

### CSV

必须包含列：
- `id`：唯一 ID
- `text`：警情文本（会被向量化）
- `label`：历史分类标签（用于给相似案例展示与可选的候选类别）

示例见 `data/sample_incidents.csv`。

### JSONL

每行一个 JSON，字段同上：`id`/`text`/`label`。

## 3) 建库（向量入库）

```bash
python ingest.py --input data/sample_incidents.csv --persist_dir chroma_db --collection incidents
```

## 4) 对新警情做 RAG 分类

### 4.1 使用 OpenAI 兼容接口（推荐）

设置环境变量（PowerShell 示例）：

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
# 如使用兼容网关/私有部署，也可设置
# $env:OPENAI_BASE_URL="https://your-openai-compatible-endpoint/v1"
```

运行：

```bash
python app_cli.py --persist_dir chroma_db --collection incidents --query "小区内两人发生争执并有肢体冲突" --top_k 5
```

### 4.2 使用 Ollama 本地模型（可选）

安装并启动 Ollama 后：

```bash
python app_cli.py --llm_provider ollama --ollama_model qwen2.5:7b --query "..." --top_k 5
```

## 5) 输出说明

输出包含：
- `category`：分类类别
- `confidence`：置信度（0-1）
- `reason`：简要理由（会引用相似案例的关键信息）
- `similar_cases`：检索到的相似案例（id/label/score/text 摘要）

## 6) 常见问题

- **第一次运行很慢**：HuggingFace 嵌入模型会首次下载（`sentence-transformers/all-MiniLM-L6-v2`）。
- **中文效果**：可改嵌入模型为中文向量（见 `config.py` 的 `EMBEDDING_MODEL_NAME`）。


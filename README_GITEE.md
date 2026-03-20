# 警情分类系统 - RAG + LLM

基于检索增强生成（RAG）和大语言模型的智能警情分类系统。

## 🎯 功能

- 📝 输入新的警情文本
- 🔍 从历史案例库中检索相似案例
- 🤖 调用大模型进行智能分类
- 📊 返回分类结果、置信度和分类理由
- 🔗 与 Dify 工作流无缝集成

## 🏗️ 系统架构

```
Dify 工作流 (用户界面)
    ↓ HTTP 请求
FastAPI 服务 (api_server.py)
    ↓
RAG 分类器 (rag_classifier.py)
    ↓
ChromaDB + LLM (数据库 + 大模型)
```

## 🚀 快速开始

### 本地运行

#### 1. 克隆仓库
```bash
git clone https://gitee.com/你的用户名/police-classifier.git
cd police-classifier
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置 API 密钥
创建 `.env` 文件：
```
OPENAI_API_KEY=你的硅基流动API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

#### 4. 准备数据
```bash
python ingest.py --input data/sample_incidents.csv
```

#### 5. 启动服务
```bash
python api_server.py
```

服务将运行在 `http://localhost:8000`

### 云端部署（Render）

1. **Fork 本仓库到你的 Gitee**
2. **访问** https://render.com
3. **创建 Web Service**
   - 连接你的 Gitee 仓库
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python api_server.py`
4. **获得公网 URL**

## 📚 文档

- [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - 部署完成总结
- [DIFY_DEPLOYMENT_GUIDE.md](./DIFY_DEPLOYMENT_GUIDE.md) - 详细部署指南
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 快速参考
- [WORKFLOW_DIAGRAM.md](./WORKFLOW_DIAGRAM.md) - 完整流程图
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - 部署检查清单

## 🔌 API 文档

### 分类端点

**POST** `/classify`

请求体：
```json
{
  "query": "小区内两人发生争执并有肢体冲突",
  "top_k": 5,
  "llm_provider": "openai"
}
```

响应：
```json
{
  "category": "治安案件",
  "confidence": 0.95,
  "reason": "新警情与参考案例在语义上相近...",
  "similar_cases": [...]
}
```

### 健康检查

**GET** `/health`

响应：
```json
{
  "status": "ok",
  "message": "服务正常运行"
}
```

## 🔗 与 Dify 集成

1. **在 Dify 中创建工作流**
2. **添加 HTTP 请求节点**
   - URL: `https://police-classifier.onrender.com/classify`（云端）或 `http://localhost:8000/classify`（本地）
   - 方法: POST
   - 请求体:
     ```json
     {
       "query": "{{incident_text}}",
       "top_k": 5,
       "llm_provider": "openai"
     }
     ```
3. **添加输出节点**
   - 展示分类结果

详见 [DIFY_DEPLOYMENT_GUIDE.md](./DIFY_DEPLOYMENT_GUIDE.md)

## 📁 项目结构

```
police-classifier/
├── api_server.py              # FastAPI 服务入口
├── rag_classifier.py          # RAG 分类逻辑
├── rag_core.py                # ChromaDB 操作
├── config.py                  # 配置文件
├── ingest.py                  # 数据导入脚本
├── requirements.txt           # 依赖列表
├── .env                       # API 密钥（需要创建）
├── data/
│   └── sample_incidents.csv   # 示例数据
├── chroma_db/                 # 向量数据库（自动创建）
└── docs/
    ├── DEPLOYMENT_SUMMARY.md
    ├── DIFY_DEPLOYMENT_GUIDE.md
    ├── QUICK_REFERENCE.md
    ├── WORKFLOW_DIAGRAM.md
    └── DEPLOYMENT_CHECKLIST.md
```

## 🛠️ 技术栈

- **后端**: FastAPI + Python 3.11
- **向量数据库**: ChromaDB
- **LLM**: OpenAI 兼容接口（硅基流动）
- **前端**: Dify 工作流
- **部署**: Render（免费）

## 📊 分类类别

系统支持以下警情分类：
- 诈骗
- 盗窃
- 抢劫抢夺
- 交通事故
- 急救求助
- 救援求助
- 安全隐患
- 噪音扰民
- 财物损坏
- 治安案件

## ⚙️ 配置

### 环境变量

在 `.env` 文件中配置：

```
# LLM 配置
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1

# ChromaDB 配置
CHROMA_PERSIST_DIR=chroma_db
CHROMA_COLLECTION=incidents

# 嵌入模型
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

## 🧪 测试

### 本地测试

```bash
# 启动服务
python api_server.py

# 在另一个终端测试
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"query":"小区内两人发生争执并有肢体冲突","top_k":5,"llm_provider":"openai"}'
```

### 查看 API 文档

访问 `http://localhost:8000/docs` 查看 Swagger UI

## 🐛 故障排查

### 问题：无法连接到 API

**解决**：
- 确保 FastAPI 服务正在运行
- 检查 URL 是否正确
- 检查防火墙设置

### 问题：API 返回 500 错误

**解决**：
- 检查 `.env` 文件中的 API 密钥
- 查看服务日志
- 确保 ChromaDB 数据库已初始化

### 问题：找不到数据库

**解决**：
```bash
python ingest.py --input data/sample_incidents.csv
```

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请提交 Issue 或联系维护者。

---

**快速链接**：
- [部署指南](./DIFY_DEPLOYMENT_GUIDE.md)
- [快速参考](./QUICK_REFERENCE.md)
- [API 文档](http://localhost:8000/docs)


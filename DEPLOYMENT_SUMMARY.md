# 📚 完整部署指南总结

## 🎯 你的项目是什么？

一个**警情分类系统**，使用 RAG（检索增强生成）技术：
- 输入：新的警情文本
- 输出：分类类别、置信度、分类理由、相似案例

---

## 🏗️ 系统架构（简化版）

```
┌─────────────────┐
│   Dify 工作流   │  ← 用户界面（在浏览器中）
│  (可视化编辑)   │
└────────┬────────┘
         │ HTTP 请求
         ↓
┌─────────────────┐
│  FastAPI 服务   │  ← 后端服务（在 PyCharm 中运行）
│ (api_server.py) │
└────────┬────────┘
         │ 调用
         ↓
┌─────────────────┐
│  RAG 分类器     │  ← 分类逻辑
│ (rag_classifier)│
└────────┬────────┘
         │ 使用
         ↓
┌─────────────────┐
│ ChromaDB + LLM  │  ← 数据库 + 大模型
│ (本地 + 云端)   │
└─────────────────┘
```

---

## 📋 完整步骤清单

### ✅ PyCharm 中的步骤（后端）

#### 第 1 次设置（只需一次）

- [ ] **步骤 1**：打开终端，进入项目目录
  ```bash
  cd "E:\QQ\新建文件夹\新建文件夹"
  ```

- [ ] **步骤 2**：安装依赖
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **步骤 3**：准备数据（如果没有 police_cases_labeled.csv）
  ```bash
  python ingest.py --input data/sample_incidents.csv
  ```

- [ ] **步骤 4**：创建 `.env` 文件，配置 API 密钥
  ```
  OPENAI_API_KEY=你的硅基流动API密钥
  OPENAI_BASE_URL=https://api.siliconflow.cn/v1
  ```

#### 每次使用前

- [ ] **步骤 5**：启动 FastAPI 服务
  - 方式 A：打开 `api_server.py`，点击右上角 ▶️ **Run**
  - 方式 B：终端运行 `python api_server.py`
  - 看到 `Uvicorn running on http://0.0.0.0:8000` 表示成功

- [ ] **步骤 6**：验证服务（可选）
  - 在浏览器访问 http://localhost:8000/docs
  - 看到 Swagger UI 文档表示成功

### ✅ Dify 中的步骤（前端）

#### 创建工作流

- [ ] **步骤 7**：创建新工作流
  1. 打开 Dify
  2. 点击 **"创建"** → **"工作流"**
  3. 输入名称：`警情分类系统`
  4. 点击 **"创建"**

- [ ] **步骤 8**：添加输入变量
  1. 点击左侧 **"开始"** 节点
  2. 右侧面板 → **"添加变量"**
  3. 配置：
     - 名称：`incident_text`
     - 类型：文本
     - 标签：警情文本
     - 必填：✓

- [ ] **步骤 9**：添加 HTTP 请求节点
  1. 点击 **"+"** 添加节点
  2. 选择 **"HTTP 请求"**
  3. 配置：
     - 名称：`调用分类API`
     - URL：`http://localhost:8000/classify`
     - 方法：`POST`
     - 请求头：`Content-Type: application/json`
     - 请求体：
       ```json
       {
         "query": "{{incident_text}}",
         "top_k": 5,
         "llm_provider": "openai"
       }
       ```

- [ ] **步骤 10**：添加输出节点
  1. 点击 **"+"** 添加节点
  2. 选择 **"输出"**
  3. 添加输出字段：
     - `category`: `{{调用分类API.body.category}}`
     - `confidence`: `{{调用分类API.body.confidence}}`
     - `reason`: `{{调用分类API.body.reason}}`
     - `similar_cases`: `{{调用分类API.body.similar_cases}}`

- [ ] **步骤 11**：连接节点
  - 用鼠标拖动连接：`开始` → `调用分类API` → `输出`

#### 测试和发布

- [ ] **步骤 12**：测试工作流
  1. 点击右上角 **"运行"**
  2. 输入测试文本：`小区内两人发生争执并有肢体冲突`
  3. 点击 **"运行"**
  4. 查看结果

- [ ] **步骤 13**：发布工作流
  1. 点击右上角 **"发布"**
  2. 选择发布方式：
     - **作为应用**：生成可分享的 Web 应用
     - **作为 API**：生成 REST API 端点

---

## 🔑 关键概念

### PyCharm 中的代码

| 文件 | 用途 |
|------|------|
| `api_server.py` | FastAPI 服务，提供 HTTP 接口 |
| `rag_classifier.py` | 分类逻辑，调用 LLM 和向量数据库 |
| `rag_core.py` | ChromaDB 操作 |
| `config.py` | 配置文件 |
| `.env` | API 密钥（需要创建） |

### Dify 中的工作流

| 节点 | 用途 |
|------|------|
| 开始 | 接收用户输入 |
| HTTP 请求 | 调用 PyCharm 中的 API |
| 输出 | 展示结果给用户 |

---

## 🚀 快速启动（3 步）

### 第 1 步：启动后端服务（PyCharm）

```bash
cd "E:\QQ\新建文件夹\新建文件夹"
python api_server.py
```

看到这个输出表示成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 第 2 步：创建 Dify 工作流

按照上面的 **"Dify 中的步骤"** 创建工作流。

### 第 3 步：测试

在 Dify 中点击 **"运行"**，输入警情文本，查看结果。

---

## 📊 数据流示例

### 用户输入
```
"小区内两人发生争执并有肢体冲突"
```

### Dify 发送请求
```json
POST http://localhost:8000/classify
{
  "query": "小区内两人发生争执并有肢体冲突",
  "top_k": 5,
  "llm_provider": "openai"
}
```

### PyCharm 处理
1. 从 ChromaDB 检索相似案例
2. 调用硅基流动 API（LLM）进行分类
3. 返回结果

### API 返回响应
```json
{
  "category": "治安案件",
  "confidence": 0.95,
  "reason": "新警情与参考案例在语义上相近，且符合'治安案件'的典型特征。",
  "similar_cases": [
    {
      "id": "case_001",
      "label": "治安案件",
      "score": 0.876,
      "text": "两人在小区内发生肢体冲突..."
    }
  ]
}
```

### Dify 展示结果
```
分类类别：治安案件
置信度：0.95
分类理由：新警情与参考案例在语义上相近，且符合'治安案件'的典型特征。
相似案例：[...]
```

---

## ⚠️ 常见问题

### Q1：Dify 连接不到 API

**A**：确保 PyCharm 中的 `api_server.py` 正在运行。

检查清单：
- [ ] 终端显示 `Uvicorn running on http://0.0.0.0:8000`
- [ ] URL 是 `http://localhost:8000/classify`
- [ ] 如果 Dify 和 PyCharm 在不同机器上，改为 `http://你的IP:8000/classify`

### Q2：API 返回 500 错误

**A**：查看 PyCharm 终端的错误日志。

常见原因：
- [ ] API 密钥未设置或错误
- [ ] ChromaDB 数据库未初始化
- [ ] LLM 调用失败

### Q3：找不到数据库

**A**：运行数据导入脚本：

```bash
python ingest.py --input data/sample_incidents.csv
```

### Q4：如何修改分类类别？

**A**：修改 `rag_classifier.py` 中的提示词或规则。

---

## 📁 文件结构

```
项目根目录/
├── api_server.py                    ← 启动这个文件
├── rag_classifier.py                ← 分类逻辑
├── rag_core.py                      ← 数据库操作
├── config.py                        ← 配置
├── .env                             ← API 密钥（需要创建）
├── requirements.txt                 ← 依赖
├── ingest.py                        ← 数据导入
├── data/
│   └── sample_incidents.csv         ← 示例数据
├── chroma_db/                       ← 数据库（自动创建）
├── DIFY_DEPLOYMENT_GUIDE.md         ← 详细指南
├── QUICK_REFERENCE.md               ← 快速参考
└── WORKFLOW_DIAGRAM.md              ← 流程图
```

---

## 🎓 学习路径

1. **理解架构**：阅读本文档的 "系统架构" 部分
2. **按步骤操作**：按照 "完整步骤清单" 逐步执行
3. **测试系统**：在 Dify 中运行工作流
4. **查看详细文档**：
   - `DIFY_DEPLOYMENT_GUIDE.md` - 详细部署指南
   - `QUICK_REFERENCE.md` - 快速参考
   - `WORKFLOW_DIAGRAM.md` - 完整流程图

---

## 💡 提示

- **PyCharm 的 `api_server.py` 必须一直运行**，Dify 才能调用它
- **Dify 中的 URL 必须是 `http://localhost:8000/classify`**（如果在同一台机器上）
- **第一次运行会比较慢**，因为需要下载 LLM 模型
- **可以在 Dify 中创建多个工作流**，都调用同一个 API

---

## 🔗 相关文档

- [DIFY_DEPLOYMENT_GUIDE.md](./DIFY_DEPLOYMENT_GUIDE.md) - 详细部署指南
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 快速参考卡片
- [WORKFLOW_DIAGRAM.md](./WORKFLOW_DIAGRAM.md) - 完整流程图

---

## 📞 需要帮助？

如果遇到问题，请：
1. 查看 "常见问题" 部分
2. 查看 PyCharm 终端的错误日志
3. 访问 http://localhost:8000/docs 查看 API 文档
4. 检查 `.env` 文件中的 API 密钥

---

**祝你使用愉快！** 🎉


# ✅ 部署检查清单

## 📋 Pre-Deployment 检查

### 环境检查
- [ ] Python 3.10+ 已安装
- [ ] PyCharm 已安装
- [ ] Dify 已安装或可访问
- [ ] 硅基流动 API 密钥已获取

### 文件检查
- [ ] `api_server.py` 存在
- [ ] `rag_classifier.py` 存在
- [ ] `requirements.txt` 存在
- [ ] `config.py` 存在
- [ ] `police_cases_labeled.csv` 或 `data/sample_incidents.csv` 存在

---

## 🔧 PyCharm 部署检查

### 步骤 1：依赖安装
- [ ] 打开 PyCharm 终端
- [ ] 运行 `pip install -r requirements.txt`
- [ ] 所有包安装成功（无错误）
- [ ] 验证：`pip list | findstr fastapi` 返回结果

### 步骤 2：数据准备
- [ ] 运行 `python ingest.py --input data/sample_incidents.csv`
- [ ] 看到 `✅ Ingested X records` 消息
- [ ] `chroma_db/` 目录已创建
- [ ] 验证：`ls chroma_db/` 有文件

### 步骤 3：API 密钥配置
- [ ] 创建 `.env` 文件在项目根目录
- [ ] 添加 `OPENAI_API_KEY=你的密钥`
- [ ] 添加 `OPENAI_BASE_URL=https://api.siliconflow.cn/v1`
- [ ] 保存文件

### 步骤 4：启动服务
- [ ] 打开 `api_server.py`
- [ ] 点击右上角 ▶️ **Run** 按钮
- [ ] 看到 `Uvicorn running on http://0.0.0.0:8000`
- [ ] 没有错误信息

### 步骤 5：验证服务
- [ ] 打开浏览器访问 http://localhost:8000/docs
- [ ] 看到 Swagger UI 文档
- [ ] 看到 `/classify` 端点
- [ ] 看到 `/health` 端点

### 步骤 6：测试 API（可选）
- [ ] 在 Swagger UI 中点击 `/classify` 的 "Try it out"
- [ ] 输入测试数据：
  ```json
  {
    "query": "小区内两人发生争执并有肢体冲突",
    "top_k": 5,
    "llm_provider": "openai"
  }
  ```
- [ ] 点击 "Execute"
- [ ] 看到 200 响应和分类结果

---

## 🎨 Dify 部署检查

### 步骤 7：创建工作流
- [ ] 打开 Dify
- [ ] 点击 **"创建"** → **"工作流"**
- [ ] 输入名称：`警情分类系统`
- [ ] 点击 **"创建"**
- [ ] 工作流编辑器已打开

### 步骤 8：添加输入变量
- [ ] 点击左侧 **"开始"** 节点
- [ ] 右侧面板显示节点配置
- [ ] 点击 **"添加变量"**
- [ ] 配置变量：
  - [ ] 名称：`incident_text`
  - [ ] 类型：文本
  - [ ] 标签：警情文本
  - [ ] 必填：✓
- [ ] 点击 **"确认"**

### 步骤 9：添加 HTTP 请求节点
- [ ] 点击 **"+"** 添加节点
- [ ] 搜索并选择 **"HTTP 请求"**
- [ ] 节点已添加到画布
- [ ] 配置节点：
  - [ ] 名称：`调用分类API`
  - [ ] URL：`http://localhost:8000/classify`
  - [ ] 方法：`POST`
  - [ ] 请求头 Content-Type：`application/json`
  - [ ] 请求体：
    ```json
    {
      "query": "{{incident_text}}",
      "top_k": 5,
      "llm_provider": "openai"
    }
    ```
- [ ] 点击 **"保存"**

### 步骤 10：添加输出节点
- [ ] 点击 **"+"** 添加节点
- [ ] 搜索并选择 **"输出"**
- [ ] 节点已添加到画布
- [ ] 配置输出字段：
  - [ ] 点击 **"添加输出"**
  - [ ] 字段 1：
    - [ ] 名称：`category`
    - [ ] 值：`{{调用分类API.body.category}}`
  - [ ] 字段 2：
    - [ ] 名称：`confidence`
    - [ ] 值：`{{调用分类API.body.confidence}}`
  - [ ] 字段 3：
    - [ ] 名称：`reason`
    - [ ] 值：`{{调用分类API.body.reason}}`
  - [ ] 字段 4：
    - [ ] 名称：`similar_cases`
    - [ ] 值：`{{调用分类API.body.similar_cases}}`
- [ ] 点击 **"保存"**

### 步骤 11：连接节点
- [ ] 从 **"开始"** 节点的输出口拖到 **"调用分类API"** 节点
- [ ] 从 **"调用分类API"** 节点的输出口拖到 **"输出"** 节点
- [ ] 三个节点已连接成一条线

### 步骤 12：测试工作流
- [ ] 点击右上角 **"运行"** 按钮
- [ ] 输入框出现
- [ ] 输入测试文本：`小区内两人发生争执并有肢体冲突`
- [ ] 点击 **"运行"**
- [ ] 等待响应（可能需要 5-10 秒）
- [ ] 看到输出结果：
  - [ ] `category`: 治安案件
  - [ ] `confidence`: 0.95 左右
  - [ ] `reason`: 包含分类理由
  - [ ] `similar_cases`: 包含相似案例列表

### 步骤 13：发布工作流
- [ ] 点击右上角 **"发布"** 按钮
- [ ] 选择发布方式：
  - [ ] **作为应用**：生成 Web 应用链接
  - [ ] **作为 API**：生成 API 端点
- [ ] 点击 **"发布"**
- [ ] 看到发布成功提示
- [ ] 获取应用链接或 API 端点

---

## 🧪 功能测试

### 测试用例 1：基础分类
- [ ] 输入：`小区内两人发生争执并有肢体冲突`
- [ ] 预期输出：`category` = 治安案件
- [ ] 验证：✓ 通过

### 测试用例 2：诈骗分类
- [ ] 输入：`有人冒充客服让我点退款链接，结果验证码被套走了`
- [ ] 预期输出：`category` = 诈骗
- [ ] 验证：✓ 通过

### 测试用例 3：交通事故
- [ ] 输入：`我在路口被追尾了，没有人受伤，但对方不愿意赔偿`
- [ ] 预期输出：`category` = 交通事故
- [ ] 验证：✓ 通过

### 测试用例 4：急救求助
- [ ] 输入：`我父亲突然胸口疼痛出汗，呼吸困难，需要马上急救`
- [ ] 预期输出：`category` = 急救求助
- [ ] 验证：✓ 通过

### 测试用例 5：置信度检查
- [ ] 所有测试的 `confidence` 都在 0-1 之间
- [ ] 验证：✓ 通过

### 测试用例 6：相似案例检查
- [ ] 所有测试都返回 `similar_cases` 列表
- [ ] 每个案例都有 `id`, `label`, `score`, `text`
- [ ] 验证：✓ 通过

---

## 🔍 故障排查检查

### 如果 Dify 无法连接到 API

检查清单：
- [ ] PyCharm 中的 `api_server.py` 正在运行
- [ ] 终端显示 `Uvicorn running on http://0.0.0.0:8000`
- [ ] Dify 中的 URL 是 `http://localhost:8000/classify`
- [ ] 防火墙允许 8000 端口
- [ ] 如果在不同机器上，改为 `http://你的IP:8000/classify`

### 如果 API 返回 500 错误

检查清单：
- [ ] `.env` 文件中的 `OPENAI_API_KEY` 正确
- [ ] `OPENAI_BASE_URL` 是 `https://api.siliconflow.cn/v1`
- [ ] ChromaDB 数据库已初始化（运行过 `ingest.py`）
- [ ] 查看 PyCharm 终端的错误日志
- [ ] 尝试在 Swagger UI 中手动测试 API

### 如果找不到数据库

检查清单：
- [ ] 运行 `python ingest.py --input data/sample_incidents.csv`
- [ ] 看到 `✅ Ingested X records` 消息
- [ ] `chroma_db/` 目录已创建
- [ ] 重启 `api_server.py`

### 如果响应格式不对

检查清单：
- [ ] 访问 http://localhost:8000/docs 查看 API 文档
- [ ] 检查 Dify 中的 JSON 路径是否正确
- [ ] 例如：`{{调用分类API.body.category}}` 而不是 `{{调用分类API.category}}`
- [ ] 在 Swagger UI 中手动测试 API 响应格式

---

## 📊 性能检查

- [ ] API 响应时间 < 10 秒
- [ ] 没有内存泄漏（长时间运行不会占用越来越多内存）
- [ ] 可以处理多个并发请求
- [ ] 错误处理正确（返回有意义的错误信息）

---

## 📝 文档检查

- [ ] `DEPLOYMENT_SUMMARY.md` 已阅读
- [ ] `DIFY_DEPLOYMENT_GUIDE.md` 已阅读
- [ ] `QUICK_REFERENCE.md` 已保存
- [ ] `WORKFLOW_DIAGRAM.md` 已参考

---

## ✨ 最终检查

- [ ] 所有步骤都已完成
- [ ] 所有测试都已通过
- [ ] 没有错误或警告
- [ ] 工作流已发布
- [ ] 可以分享给其他用户使用

---

## 🎉 部署完成！

如果所有检查都通过了，恭喜你！系统已成功部署。

### 下一步

1. **分享工作流**：将 Dify 应用链接分享给其他用户
2. **监控系统**：定期检查 PyCharm 终端是否有错误
3. **优化性能**：根据实际使用情况调整参数
4. **扩展功能**：添加更多分类类别或改进 LLM 提示词

---

## 📞 常见问题快速链接

- [Dify 无法连接到 API](#如果-dify-无法连接到-api)
- [API 返回 500 错误](#如果-api-返回-500-错误)
- [找不到数据库](#如果找不到数据库)
- [响应格式不对](#如果响应格式不对)

---

**祝你使用愉快！** 🚀


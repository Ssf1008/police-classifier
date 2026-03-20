# 云部署指南 - Gitee + Render

## 📋 完整步骤

### 第 1 步：上传到 Gitee

#### 1.1 创建 Gitee 仓库

1. 访问 https://gitee.com
2. 点击右上角 **"+"** → **"新建仓库"**
3. 填写信息：
   - **仓库名称**: `police-classifier`
   - **仓库描述**: 警情分类系统
   - **选择开源**: 公开
   - **不要初始化 README**（我们已经有了）
4. 点击 **"创建"**

#### 1.2 本地上传代码

在 PyCharm 终端中运行：

```bash
cd "E:\QQ\新建文件夹\新建文件夹"

# 初始化 Git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Police incident classifier with RAG"

# 添加远程仓库（替换你的用户名）
git remote add origin https://gitee.com/你的用户名/police-classifier.git

# 推送到 Gitee
git push -u origin master
```

#### 1.3 验证上传

访问你的 Gitee 仓库 URL：
```
https://gitee.com/你的用户名/police-classifier
```

看到所有文件已上传 ✓

---

### 第 2 步：部署到 Render（免费）

#### 2.1 注册 Render 账号

1. 访问 https://render.com
2. 点击 **"Sign up"**
3. 选择 **"Sign up with GitHub"** 或 **"Sign up with Email"**
4. 完成注册

#### 2.2 创建 Web Service

1. 登录 Render 后，点击 **"New +"** → **"Web Service"**

2. 选择 **"Public Git repository"**

3. 输入你的 Gitee 仓库 URL：
   ```
   https://gitee.com/你的用户名/police-classifier.git
   ```

4. 点击 **"Continue"**

#### 2.3 配置部署参数

填写以下信息：

| 字段 | 值 |
|------|-----|
| **Name** | `police-classifier` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python api_server.py` |
| **Instance Type** | `Free` |

#### 2.4 添加环境变量

点击 **"Advanced"** → **"Add Environment Variable"**

添加以下变量：

```
OPENAI_API_KEY=你的硅基流动API密钥
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

#### 2.5 部署

1. 点击 **"Create Web Service"**
2. 等待部署完成（大约 5-10 分钟）
3. 看到 **"Live"** 状态表示成功
4. 获得公网 URL，例如：
   ```
   https://police-classifier.onrender.com
   ```

---

### 第 3 步：在 Dify 中配置

#### 3.1 创建工作流

1. 打开学校的 Dify
2. 点击 **"创建"** → **"工作流"**
3. 输入名称：`警情分类系统`
4. 点击 **"创建"**

#### 3.2 添加输入变量

1. 点击左侧 **"开始"** 节点
2. 右侧面板 → **"添加变量"**
3. 配置：
   - 名称：`incident_text`
   - 类型：文本
   - 标签：警情文本
   - 必填：✓

#### 3.3 添加 HTTP 请求节点

1. 点击 **"+"** 添加节点
2. 选择 **"HTTP 请求"**
3. 配置：
   - **名称**: `调用分类API`
   - **URL**: `https://police-classifier.onrender.com/classify`
   - **方法**: `POST`
   - **请求头**: `Content-Type: application/json`
   - **请求体**:
     ```json
     {
       "query": "{{incident_text}}",
       "top_k": 5,
       "llm_provider": "openai"
     }
     ```

#### 3.4 添加输出节点

1. 点击 **"+"** 添加节点
2. 选择 **"输出"**
3. 添加输出字段：
   - `category`: `{{调用分类API.body.category}}`
   - `confidence`: `{{调用分类API.body.confidence}}`
   - `reason`: `{{调用分类API.body.reason}}`
   - `similar_cases`: `{{调用分类API.body.similar_cases}}`

#### 3.5 连接节点

用鼠标拖动连接：
```
开始 → 调用分类API → 输出
```

#### 3.6 测试

1. 点击右上角 **"运行"**
2. 输入测试文本：`小区内两人发生争执并有肢体冲突`
3. 点击 **"运行"**
4. 查看结果 ✓

#### 3.7 发布

1. 点击右上角 **"发布"**
2. 选择 **"作为应用"** 或 **"作为 API"**
3. 点击 **"发布"**
4. 分享链接给其他人

---

## 🔄 更新代码

如果需要更新代码：

### 本地更新

```bash
cd "E:\QQ\新建文件夹\新建文件夹"

# 修改代码...

# 提交更改
git add .
git commit -m "Update: 描述你的更改"
git push origin master
```

### Render 自动更新

Render 会自动检测 Gitee 的更新，自动重新部署。

---

## 📊 监控和日志

### 查看部署日志

1. 登录 Render
2. 点击你的 Web Service
3. 点击 **"Logs"** 查看实时日志

### 常见问题

#### 部署失败

检查日志中的错误信息，常见原因：
- 依赖安装失败：检查 `requirements.txt`
- 启动命令错误：检查 `api_server.py`
- 环境变量缺失：检查 API 密钥配置

#### 服务超时

Render 免费版本可能会在 15 分钟无请求后休眠，首次请求会比较慢。

---

## 💰 成本

- **Render**: 完全免费（有限制）
- **Gitee**: 完全免费
- **Dify**: 取决于学校部署方式

### Render 免费版限制

- 每月 750 小时运行时间（足够全天运行）
- 0.5GB RAM
- 共享 CPU
- 15 分钟无请求后自动休眠

---

## 🔐 安全建议

1. **不要提交 `.env` 文件**（已在 `.gitignore` 中）
2. **在 Render 中配置环境变量**，不要在代码中硬编码
3. **定期更新依赖**，防止安全漏洞
4. **监控 API 使用情况**

---

## 📱 分享给其他人

### 方式 1：分享 Dify 应用链接

1. 在 Dify 中发布工作流
2. 获得应用链接
3. 分享给其他人
4. 其他人可以直接使用，无需配置

### 方式 2：分享 Gitee 仓库

1. 分享 Gitee 仓库 URL
2. 其他人可以 Fork 或 Clone
3. 其他人可以自己部署到 Render

### 方式 3：分享 API 端点

1. 分享 Render 的 API URL：`https://police-classifier.onrender.com/classify`
2. 其他人可以在自己的应用中调用

---

## 🚀 完整工作流

```
你的代码 (本地)
    ↓ git push
Gitee 仓库
    ↓ webhook
Render 自动部署
    ↓
公网 URL: https://police-classifier.onrender.com
    ↓
Dify 工作流调用
    ↓
学校工作室的其他人使用
```

---

## 📝 检查清单

- [ ] 创建 Gitee 仓库
- [ ] 上传代码到 Gitee
- [ ] 注册 Render 账号
- [ ] 创建 Web Service
- [ ] 配置环境变量
- [ ] 部署成功（看到 "Live" 状态）
- [ ] 获得公网 URL
- [ ] 在 Dify 中配置 HTTP 请求节点
- [ ] 测试工作流
- [ ] 发布工作流
- [ ] 分享给其他人

---

## 🎉 完成！

现在你的工作流可以在任何地方使用了！

### 下一步

1. **监控系统**：定期检查 Render 日志
2. **收集反馈**：从其他人那里获得使用反馈
3. **优化性能**：根据实际使用情况调整参数
4. **扩展功能**：添加更多分类类别或改进 LLM 提示词

---

## 📞 常见问题

### Q: 为什么 Render 上的服务这么慢？

A: 免费版本会在 15 分钟无请求后休眠，首次请求需要唤醒。可以升级到付费版本获得更好的性能。

### Q: 如何更新代码？

A: 在本地修改代码，然后 `git push` 到 Gitee，Render 会自动重新部署。

### Q: 其他人可以看到我的 API 密钥吗？

A: 不会。API 密钥存储在 Render 的环境变量中，不会暴露在代码中。

### Q: 可以用其他云服务吗？

A: 可以。支持任何支持 Python 的云服务（如 Heroku、Railway、Vercel 等）。

---

**祝你部署顺利！** 🚀


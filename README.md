# 🤖 AI & 经济日报自动化工作流

每日自动生成包含 GitHub 热门项目、AI 行业新闻、经济要闻的智能简报，通过邮件发送。

------

## ✨ 功能特性

### 1. **GitHub 热门项目** 💻

- 自动抓取最近 7 天内创建的 AI 相关热门项目
- 筛选条件：AI/LLM/GPT/机器学习相关，Star > 10
- 按 Star 数量排序，取前 10 个

### 2. **AI 行业新闻** 🤖

- 抓取最近 2 天的 AI 行业新闻
- 关键词：ChatGPT、OpenAI、Google AI、Claude、Gemini 等
- 来源：全球主流媒体（通过 NewsAPI）

### 3. **经济新闻** 💰

- 抓取最近 2 天的经济要闻
- 关键词：经济、股市、美联储、通胀、GDP 等
- 覆盖宏观经济动态

### 4. **智能整合与去重** 🧠

- 使用智谱 AI (GLM-4) 进行内容整合
- 自动识别并去除重复新闻
- 生成结构化的每日简报（500 字以内）

------

## 🚀 快速开始

### 第一步：准备 API Key

你需要注册并获取以下服务的 API Key：

#### 1. **GitHub Token**

- 访问：https://github.com/settings/tokens
- 点击 "Generate new token (classic)"
- 勾选权限：`public_repo`
- 生成并保存 Token

#### 2. **智谱 AI API Key**

- 访问：https://open.bigmodel.cn/
- 注册并创建 API Key
- 免费额度足够日常使用

#### 3. **NewsAPI Key**

- 访问：https://newsapi.org/
- 注册免费账户
- 获取 API Key（免费版每天 100 次请求）

#### 4. **QQ 邮箱授权码**

- 登录 QQ 邮箱网页版
- 设置 → 账户 → 开启 SMTP 服务
- 生成授权码（不是邮箱密码！）

------

### 第二步：配置 GitHub Secrets

1. 进入你的 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. 依次添加以下 6 个 Secret：

| Secret 名称     | 说明                  | 示例值                     |
| --------------- | --------------------- | -------------------------- |
| `GH_TOKEN`      | GitHub Personal Token | `ghp_xxxxxxxxxxxx`         |
| `ZHIPU_API_KEY` | 智谱 AI API Key       | `xxxxxxxxxx.xxxxxxx`       |
| `NEWS_API_KEY`  | NewsAPI Key           | `xxxxxxxxxxxxxxxxxxxxxxxx` |
| `SMTP_USER`     | 发件邮箱（QQ邮箱）    | `your_email@qq.com`        |
| `SMTP_PASS`     | QQ 邮箱授权码         | `xxxxxxxxxxxxxx`           |
| `TO_EMAIL`      | 收件邮箱              | `your_email@qq.com`        |

> ⚠️ **注意**: `SMTP_PASS` 是授权码，不是邮箱密码！

------

### 第三步：上传文件到 GitHub

将以下文件上传到你的仓库：

```
your-repo/
├── .github/
│   └── workflows/
│       └── daily_report.yml    # GitHub Actions 配置
└── ai_daily_report.py          # 主程序
```

------

### 第四步：运行测试

#### 方法一：手动触发（推荐首次使用）

1. 进入仓库的 `Actions` 标签页
2. 点击左侧 `AI Daily Report`
3. 点击右侧 `Run workflow` → `Run workflow`
4. 等待运行完成，检查邮箱

#### 方法二：等待自动运行

- 工作流默认每天 UTC 08:00 (北京时间 16:00) 自动运行
- 首次配置后建议先手动测试

------

## 📧 邮件样式预览

```
============================================================
🤖 AI & 经济日报 | 2024-01-15
============================================================

## 🔥 今日要点
1. Meta 发布 Llama 3.1 开源模型，性能超越 GPT-4
2. 特斯拉股价上涨 5%，受益于 AI 自动驾驶技术进展
3. GitHub 热门项目：新型 AI 代码助手获 2000+ Star

## 💻 GitHub 热门项目
1. **ai-code-assistant** (⭐ 2,341)
   创新的 AI 编程助手，支持多语言代码生成和重构

2. **llm-training-toolkit** (⭐ 1,892)
   简化大模型训练的工具包，适合初学者

## 🤖 AI 行业动态
- Meta 开源 Llama 3.1，推动 AI 民主化进程
- OpenAI 更新 GPT-4 API，新增多模态能力
- 谷歌 Gemini 在编程任务上取得突破

## 💰 经济要闻
- 美联储维持利率不变，通胀持续回落
- 科技股集体上涨，纳指创今年新高
- 中国 GDP 增长超预期，消费复苏明显

## 📊 趋势洞察
开源 AI 模型持续进步，与闭源模型差距缩小。科技板块受 AI 热潮驱动保持强势。

============================================================
📬 本报告由自动化工作流生成
⏰ 生成时间: 2024-01-15 16:05:23
============================================================
```

------

## 🛠️ 自定义配置

### 调整时间范围

编辑 `ai_daily_report.py`：

```python
# GitHub 项目查询时间范围（默认 7 天）
date_from = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

# 新闻查询时间范围（默认 2 天）
date_from = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
```

### 调整数量

```python
# GitHub 项目数量（默认 10 个）
"per_page": 10,

# 新闻数量（默认 15 条）
"pageSize": 15,
```

### 调整运行时间

编辑 `.github/workflows/daily_report.yml`：

```yaml
schedule:
  # 每天早上 8:00 UTC (北京时间 16:00)
  - cron: '0 8 * * *'
  
  # 改为北京时间早上 9:00 (UTC 01:00)
  - cron: '0 1 * * *'
```

### 修改邮件发送方式

**使用 Gmail:**

```python
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
# 需要开启 Gmail 的"不够安全的应用访问权限"或使用应用专用密码
```

**使用 163 邮箱:**

```python
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465  # 或 25
```

------

## 🐛 常见问题

### 1. 邮件内容为空？

**可能原因：**

- API Key 配置错误或过期
- 查询条件过严，当天无符合条件的数据
- 网络请求超时

**解决方法：**

- 检查 GitHub Actions 日志，查看具体错误
- 降低筛选条件（减少 stars 要求、扩大时间范围）
- 检查 API 配额是否用完

### 2. GitHub Actions 运行失败？

**检查清单：**

- [ ] 所有 6 个 Secrets 都已正确配置
- [ ] Secret 名称拼写正确（区分大小写）
- [ ] QQ 邮箱授权码正确（不是密码）
- [ ] GitHub Token 权限包含 `public_repo`

### 3. NewsAPI 请求失败？

**免费版限制：**

- 每天 100 次请求
- 只能获取最近 30 天的新闻
- 部分高级功能不可用

**解决方法：**

- 减少查询次数
- 使用更精确的关键词
- 考虑升级到付费版

### 4. 智谱 AI 调用失败？

**可能原因：**

- API Key 错误
- 免费额度用完
- 模型名称错误

**解决方法：**

- 检查 API Key 是否正确
- 登录智谱 AI 控制台查看余额
- 当前使用的是 `glm-4-flash`（免费且快速）

------

## 📊 日志查看

### 在线查看日志：

1. 进入 GitHub 仓库
2. 点击 `Actions` 标签
3. 选择最近的运行记录
4. 查看详细日志

### 日志示例：

```
✅ 环境变量检查通过

🔍 开始获取 GitHub 热门项目...
✅ 成功获取 10 个 GitHub 项目

🔍 开始获取 AI 行业新闻...
✅ 成功获取 15 条 AI 新闻

🔍 开始获取经济新闻...
✅ 成功获取 15 条经济新闻

🤖 开始使用 LLM 进行内容整合...
✅ LLM 总结完成

📧 开始发送邮件...
✅ 邮件发送成功！

✅ 全部流程执行完成！
```

------

## 🔐 安全建议

1. **永远不要**将 API Key 直接写在代码中
2. **始终使用** GitHub Secrets 存储敏感信息
3. **定期更换** API Key 和邮箱授权码
4. **限制** GitHub Token 的权限范围
5. **不要**将包含 Secrets 的代码公开到互联网

------

## 📝 更新日志

### v2.0 - 2024-01-15

- ✨ 新增经济新闻板块
- 🔧 优化 LLM 整合逻辑，支持智能去重
- 📧 改进邮件格式，支持 HTML 渲染
- 🐛 修复数据为空时的错误处理
- 📊 新增详细日志输出

### v1.0 - 2024-01-10

- 🎉 初始版本发布
- ✨ 支持 GitHub 项目和 AI 新闻获取

------

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

------

## 📄 许可证

MIT License

------

## 💡 灵感来源

这个项目旨在帮助技术从业者和投资者快速了解 AI 和经济领域的最新动态，节省信息筛选时间。

------

**享受你的每日 AI 简报！** 🎉
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from zhipuai import ZhipuAI
import os
import json

# ========== 环境变量 ==========
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 587


# ========== 环境变量自检 ==========
def check_env():
    """检查必需的环境变量是否配置"""
    required = [
        "GITHUB_TOKEN",
        "SMTP_USER",
        "SMTP_PASS",
        "TO_EMAIL",
        "ZHIPU_API_KEY",
        "NEWS_API_KEY",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"❌ 缺少环境变量: {', '.join(missing)}")
    print("✅ 环境变量检查通过")


# ========== 1. GitHub 热门项目获取（多策略）==========
def fetch_github_trending_repos():
    """
    策略1: 获取最近活跃的AI项目（过去30天有更新，按stars排序）
    这是主要策略，更可靠
    """
    print("\n🔍 策略1: 获取最近活跃的 GitHub AI 项目...")

    # 查询最近 30 天有更新的项目（pushed，不是created）
    date_from = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    query = (
        f"(AI OR LLM OR GPT OR agent OR machine-learning OR deep-learning) "
        f"pushed:>{date_from} "
        f"stars:>100 "
        f"language:Python"
    )

    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 15,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        repos = r.json().get("items", [])
        print(f"✅ 策略1成功获取 {len(repos)} 个活跃项目")
        return repos
    except Exception as e:
        print(f"❌ 策略1失败: {e}")
        return []


def fetch_github_new_stars():
    """
    策略2: 获取最近star增长快的项目（按最近更新时间排序）
    作为补充策略
    """
    print("\n🔍 策略2: 获取最近更新的热门 AI 项目...")

    # 查询最近 7 天有更新的项目
    date_from = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    query = (
        f"(Claude OR ChatGPT OR Gemini OR agent OR RAG OR vector) "
        f"pushed:>{date_from} "
        f"stars:>50"
    )

    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": 10,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        repos = r.json().get("items", [])
        print(f"✅ 策略2成功获取 {len(repos)} 个最近更新项目")
        return repos
    except Exception as e:
        print(f"❌ 策略2失败: {e}")
        return []


def fetch_github_trending_topics():
    """
    策略3: 查询特定热门AI话题（作为兜底策略）
    """
    print("\n🔍 策略3: 获取特定 AI 话题项目...")

    # 最近30天的项目，按stars排序
    date_from = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    # 2026年的热门话题
    topics = [
        "agentic-ai",
        "llm-agent",
        "ai-assistant",
        "code-agent",
        "rag",
    ]

    query = f"topics:{' OR '.join(topics)} pushed:>{date_from} stars:>20"

    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        repos = r.json().get("items", [])
        print(f"✅ 策略3成功获取 {len(repos)} 个话题项目")
        return repos
    except Exception as e:
        print(f"❌ 策略3失败: {e}")
        return []


def merge_and_deduplicate_repos(repos_list):
    """合并多个仓库列表并去重"""
    seen = set()
    merged = []

    for repos in repos_list:
        for repo in repos:
            repo_id = repo.get('id')
            if repo_id and repo_id not in seen:
                seen.add(repo_id)
                merged.append(repo)

    # 按stars排序
    merged.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)

    # 取前15个
    return merged[:15]


def fetch_github_all_strategies():
    """执行所有GitHub获取策略并合并结果"""
    print("\n" + "=" * 60)
    print("🚀 开始多策略获取 GitHub 项目")
    print("=" * 60)

    # 执行三个策略
    trending_repos = fetch_github_trending_repos()
    new_stars = fetch_github_new_stars()
    topic_repos = fetch_github_trending_topics()

    # 合并去重
    all_repos = merge_and_deduplicate_repos([trending_repos, new_stars, topic_repos])

    print(f"\n✅ 总计获取 {len(all_repos)} 个去重后的项目")
    return all_repos


def format_github_data(repos):
    """格式化 GitHub 数据为文本"""
    if not repos:
        return ""

    blocks = []
    for i, repo in enumerate(repos[:10], 1):  # 只取前10个展示
        # 计算更新时间
        updated_at = repo.get('updated_at', '')
        if updated_at:
            try:
                updated_date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                days_ago = (datetime.utcnow() - updated_date).days
                update_info = f"更新于 {days_ago} 天前"
            except:
                update_info = "最近更新"
        else:
            update_info = ""

        blocks.append(f"""
{i}. 【{repo.get('full_name', repo.get('name'))}】
   ⭐ Stars: {repo.get('stargazers_count', 0):,}
   🔥 {update_info}
   📝 {repo.get('description', '暂无描述')[:150]}
   🔗 {repo.get('html_url')}
""")
    return "\n".join(blocks)


# ========== 2. AI 行业新闻获取 ==========
def fetch_ai_news():
    """获取 AI 相关新闻"""
    print("\n🔍 开始获取 AI 行业新闻...")

    url = "https://newsapi.org/v2/everything"

    date_from = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")

    params = {
        "q": "artificial intelligence OR ChatGPT OR OpenAI OR Google AI OR Claude OR Gemini OR DeepMind",
        "language": "en",
        "from": date_from,
        "sortBy": "publishedAt",
        "pageSize": 15,
        "apiKey": NEWS_API_KEY,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        print(f"✅ 成功获取 {len(articles)} 条 AI 新闻")
        return articles
    except Exception as e:
        print(f"❌ AI 新闻获取失败: {e}")
        return []


def fetch_economics_news():
    """获取经济相关新闻"""
    print("\n🔍 开始获取经济新闻...")

    url = "https://newsapi.org/v2/everything"

    date_from = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")

    params = {
        "q": "economics OR stock market OR Federal Reserve OR inflation OR GDP OR economy OR tech stocks",
        "language": "en",
        "from": date_from,
        "sortBy": "publishedAt",
        "pageSize": 15,
        "apiKey": NEWS_API_KEY,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        print(f"✅ 成功获取 {len(articles)} 条经济新闻")
        return articles
    except Exception as e:
        print(f"❌ 经济新闻获取失败: {e}")
        return []


def format_news_data(articles, category=""):
    """格式化新闻数据为文本"""
    if not articles:
        return ""

    blocks = []
    for i, a in enumerate(articles[:10], 1):  # 只取前10条
        published = a.get('publishedAt', '')[:10]  # 只取日期部分
        blocks.append(f"""
{i}. 【{a.get('title', '无标题')}】
   📰 来源: {a.get('source', {}).get('name', '未知')}
   📅 日期: {published}
   📝 摘要: {a.get('description', '无摘要')[:200]}
   🔗 {a.get('url')}
""")
    return "\n".join(blocks)


# ========== 3. LLM 整合、去重、总结 ==========
def llm_integrate_and_summarize(github_data, ai_news_data, econ_news_data):
    """使用智谱 AI 进行内容整合、去重和总结"""
    print("\n🤖 开始使用 LLM 进行内容整合...")

    if not ZHIPU_API_KEY:
        print("❌ 缺少 ZHIPU_API_KEY，跳过 LLM 总结")
        return generate_fallback_summary(github_data, ai_news_data, econ_news_data)

    try:
        client = ZhipuAI(api_key=ZHIPU_API_KEY)

        prompt = f"""
你是一名资深的 AI 和经济分析师。请根据以下三部分原始素材，生成一份精炼的每日简报。

**任务要求：**
1. **去重**: 识别并合并重复或高度相似的内容
2. **整合**: 将三个板块的信息有机整合
3. **总结**: 提炼关键信息，突出重点
4. **突出价值**: 重点介绍真正有价值、有创新性的项目和新闻

**输出格式（中文）：**

## 🔥 今日要点
（3-5条最重要的信息，每条1-2句话）

## 💻 GitHub 热门项目
（挑选3-5个最值得关注的项目，每个项目包括：
- 项目名称和简介
- 为什么值得关注
- Stars数量）

## 🤖 AI 行业动态
（整合AI新闻，去除重复内容，提炼3-4个核心趋势或事件）

## 💰 经济要闻
（整合经济新闻，去除重复内容，提炼2-3个关键信息）

## 📊 趋势洞察
（1-2句话的综合判断或趋势预测）

**注意：**
- 总字数控制在 600 字以内
- 理性、专业的分析视角
- 去除明显重复的新闻
- 突出最有价值的信息
- 如果某个板块数据较少，可以适当简化

---

**原始素材：**

### GitHub 项目：
{github_data if github_data else "暂无数据"}

### AI 行业新闻：
{ai_news_data if ai_news_data else "暂无数据"}

### 经济新闻：
{econ_news_data if econ_news_data else "暂无数据"}
"""

        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        summary = response.choices[0].message.content
        print("✅ LLM 总结完成")
        return summary

    except Exception as e:
        print(f"❌ LLM 总结失败: {e}")
        return generate_fallback_summary(github_data, ai_news_data, econ_news_data)


def generate_fallback_summary(github_data, ai_news_data, econ_news_data):
    """当 LLM 调用失败时的备用总结方案"""
    print("⚠️ 使用备用总结方案")

    summary = f"""
## 📋 今日简报（未经 AI 处理）

### 💻 GitHub 热门项目
{github_data if github_data else "暂无数据"}

### 🤖 AI 行业新闻
{ai_news_data if ai_news_data else "暂无数据"}

### 💰 经济新闻
{econ_news_data if econ_news_data else "暂无数据"}

---
⚠️ 注：本次简报未经 AI 整合去重，为原始数据展示
"""
    return summary


# ========== 4. 发送邮件 ==========
def send_email(content):
    """发送邮件"""
    print("\n📧 开始发送邮件...")

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🤖 AI & 经济日报 | {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = SMTP_USER
        msg['To'] = TO_EMAIL

        # 纯文本版本
        text_part = MIMEText(content, 'plain', 'utf-8')
        msg.attach(text_part)

        # HTML 版本（格式更美观）
        html_content = content.replace('\n', '<br>').replace('##', '<h2>').replace('###', '<h3>')
        html_part = MIMEText(f"<html><body style='font-family: Arial, sans-serif;'>{html_content}</body></html>",
                             'html', 'utf-8')
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print("✅ 邮件发送成功！")

    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        raise


# ========== 主流程 ==========
def main():
    """主流程"""
    print("=" * 60)
    print("🚀 AI & 经济日报生成器启动")
    print("=" * 60)

    # 1. 环境检查
    check_env()

    # 2. 数据收集（多策略）
    github_repos = fetch_github_all_strategies()
    ai_news = fetch_ai_news()
    econ_news = fetch_economics_news()

    # 3. 格式化数据
    github_text = format_github_data(github_repos)
    ai_news_text = format_news_data(ai_news, "AI")
    econ_news_text = format_news_data(econ_news, "经济")

    # 检查是否有数据
    if not github_text and not ai_news_text and not econ_news_text:
        print("⚠️ 警告：所有数据源均为空，无法生成报告")
        fallback_content = f"""
🤖 AI & 经济日报 | {datetime.now().strftime('%Y-%m-%d')}

⚠️ 抱歉，今日数据获取失败，可能原因：
- API 配额已用完
- 网络连接问题
- 查询条件未匹配到结果

请检查环境变量配置和网络连接。
"""
        send_email(fallback_content)
        return

    # 数据统计
    print("\n" + "=" * 60)
    print("📊 数据收集统计：")
    print(f"   GitHub 项目: {len(github_repos)} 个")
    print(f"   AI 新闻: {len(ai_news)} 条")
    print(f"   经济新闻: {len(econ_news)} 条")
    print("=" * 60)

    # 4. LLM 整合与总结
    final_summary = llm_integrate_and_summarize(github_text, ai_news_text, econ_news_text)

    # 5. 生成最终邮件内容
    final_content = f"""
{'=' * 60}
🤖 AI & 经济日报 | {datetime.now().strftime('%Y-%m-%d')}
{'=' * 60}

{final_summary}

{'=' * 60}
📬 本报告由自动化工作流生成
⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 数据来源: GitHub ({len(github_repos)}项目) + NewsAPI ({len(ai_news) + len(econ_news)}条新闻)
{'=' * 60}
"""

    # 6. 预览内容
    print("\n" + "=" * 60)
    print("📄 邮件内容预览：")
    print("=" * 60)
    print(final_content[:800] + "..." if len(final_content) > 800 else final_content)
    print("=" * 60)

    # 7. 发送邮件
    send_email(final_content)

    print("\n✅ 全部流程执行完成！")


# ========== 入口 ==========
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        raise
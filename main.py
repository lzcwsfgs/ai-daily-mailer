import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from zhipuai import ZhipuAI
import os


# ========== 环境变量 ==========
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 587


# ========== LLM ==========
client = ZhipuAI(api_key=ZHIPU_API_KEY)


# ========== 主题配置 ==========
TOPICS = [
    {
        "name": "AI 技术 & 开源项目",
        "type": "github",
    },
    {
        "name": "AI 行业新闻",
        "type": "news",
    }
]


# ========== 环境变量自检 ==========
def check_env():
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


# ========== NewsAPI ==========
def fetch_ai_news():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "ChatGPT OR OpenAI OR generative AI OR AI model",
        "language": "en",
        "from": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "to": datetime.utcnow().strftime("%Y-%m-%d"),
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY,
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("articles", [])

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["articles"]


def news_to_text(articles):
    blocks = []
    for a in articles:
        blocks.append(
            f"""
标题：{a.get('title')}
来源：{a.get('source', {}).get('name')}
摘要：{a.get('description')}
链接：{a.get('url')}
"""
        )
    return "\n".join(blocks)


# ========== GitHub 搜索 ==========
def fetch_github_ai_repos():
    yesterday = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")

    query = (
        f"AI OR LLM OR agent "
        f"created:>{yesterday} "
        f"stars:>20 "
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
        "per_page": 5,
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["items"]


def repos_to_text(repos):
    blocks = []
    for repo in repos:
        blocks.append(
            f"""
项目名：{repo.get('name')}
Stars：{repo.get('stargazers_count')}
描述：{repo.get('description')}
链接：{repo.get('html_url')}
"""
        )
    return "\n".join(blocks)


# ========== LLM 总结 ==========
def llm_summarize_topic(topic_name, material):
    prompt = f"""
你是一名资深 AI 分析师，请根据以下素材，
整理【{topic_name}】的每日简报，要求：

1. 中文
2. 包含：
   - 今日要点（2-3 条）
   - 值得关注内容（简述）
   - 一句话趋势判断
3. 偏理性、技术 / 行业视角
4. 总字数不超过 200 字

素材如下：
{material}
"""

    response = client.chat.completions.create(
        model="glm-4-air",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content


# ========== 发邮件 ==========
def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"🤖 AI 日报｜{datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


# ========== 主流程 ==========
def main():
    sections = []

    for topic in TOPICS:
        try:
            if topic["type"] == "github":
                repos = fetch_github_ai_repos()
                material = repos_to_text(repos)

            elif topic["type"] == "news":
                news = fetch_ai_news()
                material = news_to_text(news)

            summary = llm_summarize_topic(topic["name"], material)

        except Exception as e:
            summary = f"⚠️ 今日该部分生成失败：{e}"

        sections.append(
            f"====================\n【{topic['name']}】\n{summary}\n"
        )

    final_content = (
        f"🤖 每日 AI 日报｜{datetime.now().strftime('%Y-%m-%d')}\n\n"
        + "\n".join(sections)
    )

    send_email(final_content)


# ========== 入口 ==========
if __name__ == "__main__":
    check_env()
    main()

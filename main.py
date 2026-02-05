import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

# ========== 配置区 ==========
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 587

# ========== 搜 GitHub AI 项目 ==========
def fetch_github_ai_repos():
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    query = (
        f"AI OR LLM OR agent "
        f"created:>{yesterday} "
        f"stars:>20 "
        f"language:Python"
    )

    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
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


# ========== 生成邮件内容 ==========
def build_email_content(repos):
    lines = []
    lines.append(f"📌 AI GitHub 日报（{datetime.now().strftime('%Y-%m-%d')}）\n")

    if not repos:
        lines.append("今天没有发现新的高热度 AI 项目。")
        return "\n".join(lines)

    for i, repo in enumerate(repos, 1):
        lines.append(
            f"{i}. {repo['name']} ⭐ {repo['stargazers_count']}\n"
            f"   {repo['description']}\n"
            f"   {repo['html_url']}\n"
        )

    return "\n".join(lines)


# ========== 发送邮件 ==========
def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = "🤖 每日 AI GitHub 项目速览"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def main():
    repos = fetch_github_ai_repos()
    content = build_email_content(repos)
    send_email(content)


if __name__ == "__main__":
    main()

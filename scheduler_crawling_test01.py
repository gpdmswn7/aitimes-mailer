
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re

BASE_URL = "https://www.aitimes.kr"
POPULAR_URL = f"{BASE_URL}/news/articleList.html?box_idxno=20&view_type=sm"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_popular_articles(top_n=5):
    """인기기사 페이지에서 상위 N개 기사(제목, 링크)를 가져옴"""
    res = requests.get(POPULAR_URL, headers=HEADERS, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    # idxno가 포함된 기사 링크를 전부 찾은 뒤, 순서대로 상위 N개만 사용
    # (사이트 구조가 바뀔 수 있어 href 패턴 기반으로 견고하게 탐색)
    seen_idxno = set()
    for a in soup.select("a[href*='articleView.html?idxno=']"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        match = re.search(r"idxno=(\d+)", href)
        if not match or not title:
            continue
        idxno = match.group(1)

        if idxno in seen_idxno:
            continue
        seen_idxno.add(idxno)

        full_url = href if href.startswith("http") else BASE_URL + href
        articles.append({"title": title, "url": full_url})

        if len(articles) >= top_n:
            break

    return articles


def build_email_body(articles):
    lines = ["📰 인공지능신문(AI Times) 최근 인기기사 TOP 5\n"]
    for i, a in enumerate(articles, start=1):
        lines.append(f"{i}. {a['title']}\n   {a['url']}\n")
    return "\n".join(lines)


def send_email(subject, body, sender, app_password, recipient):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.send_message(msg)

    print(f"이메일 발송 완료 → {recipient}")


if __name__ == "__main__":
    # GitHub Secrets에서 환경변수로 주입 (코드에 직접 쓰지 않음!)
    sender = os.environ["EMAIL_ADDRESS"]
    app_password = os.environ["EMAIL_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    articles = get_popular_articles(top_n=5)
    if not articles:
        raise RuntimeError("기사를 가져오지 못했습니다. 사이트 구조가 바뀌었는지 확인하세요.")

    body = build_email_body(articles)
    send_email(
        subject="[AI Times] 오늘의 인기기사 TOP 5",
        body=body,
        sender=sender,
        app_password=app_password,
        recipient=recipient,
    )
    
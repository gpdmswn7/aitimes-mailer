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
    res = requests.get(POPULAR_URL, headers=HEADERS, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
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


def build_email_body_html(articles):
    """HTML 형식 이메일 본문 생성 - 제목 크게/굵게 표시"""
    items_html = ""
    for i, a in enumerate(articles, start=1):
        items_html += f"""
        <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 15px; color: #888888; margin-bottom: 4px;">
                #{i}
            </div>
            <a href="{a['url']}" style="
                font-size: 20px;
                font-weight: bold;
                color: #1a1a1a;
                text-decoration: none;
                line-height: 1.4;
            ">
                {a['title']}
            </a>
        </div>
        """

    html = f"""
    <html>
    <body style="font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="font-size: 24px; color: #2c3e50; border-bottom: 3px solid #2c3e50; padding-bottom: 12px;">
            📰 AI Times 인기기사 TOP 5
        </h2>
        {items_html}
        <p style="font-size: 13px; color: #aaaaaa; margin-top: 30px;">
            매일 오후 10시 15분 자동 발송 · aitimes.kr
        </p>
    </body>
    </html>
    """
    return html


def send_email_html(subject, html_body, sender, app_password, recipient):
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    # HTML을 못 읽는 메일 클라이언트를 위한 대체 텍스트 (선택이지만 권장)
    plain_fallback = "이 메일은 HTML 형식입니다. HTML을 지원하는 메일 앱에서 확인해주세요."
    msg.attach(MIMEText(plain_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.send_message(msg)

    print(f"이메일 발송 완료 → {recipient}")


if __name__ == "__main__":
    sender = os.environ["EMAIL_ADDRESS"]
    app_password = os.environ["EMAIL_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    articles = get_popular_articles(top_n=5)
    if not articles:
        raise RuntimeError("기사를 가져오지 못했습니다. 사이트 구조가 바뀌었는지 확인하세요.")

    html_body = build_email_body_html(articles)
    send_email_html(
        subject="[AI Times] 오늘의 인기기사 TOP 5",
        html_body=html_body,
        sender=sender,
        app_password=app_password,
        recipient=recipient,
    )

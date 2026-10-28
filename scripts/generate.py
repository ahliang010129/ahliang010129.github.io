import os, json, requests, datetime

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
LEAGUE_ID = "4328"  # 英超

def fetch_finished_matches():
    url = "https://www.thesportsdb.com/api/v1/json/123/eventspastleague.php"
    resp = requests.get(url, params={"id": LEAGUE_ID}, timeout=30)
    resp.raise_for_status()
    events = resp.json().get("events") or []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=720)
    fresh = []
    for e in events:
        try:
            dt = datetime.datetime.strptime(
                e["dateEvent"] + " " + (e.get("strTime") or "00:00:00"),
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            continue
        if dt >= cutoff:
            fresh.append(e)
    return fresh

SYSTEM_PROMPT = """你是专职体育战报作者。严格按以下规则写作：
1. 事实锚定：只使用输入 JSON 中的比分、事件、数据。没有的数据不提。
2. 结构：导语(1-2句) → 比赛进程(3-4段，每段围绕一个转折) → 数据切片(1段) → 收束(1句)。
3. 禁用动词：战胜、获得、取得、赢得、击败。使用：轰出、逆转、崩盘、苦战、惜败、横扫、绝杀、压制、反扑、锁定、撕开、终结。
4. 固定“现场观察者”第三人称视角。禁止“我认为”“值得一提的是”。每段至少一个来自输入数据的画面细节，不得虚构。
5. 输出 JSON：{"title": "...", "slug": "...", "body_markdown": "..."}
"""

def generate_article(event):
    facts = {
        "home": event.get("strHomeTeam"),
        "away": event.get("strAwayTeam"),
        "home_score": event.get("intHomeScore"),
        "away_score": event.get("intAwayScore"),
        "date": event.get("dateEvent"),
        "league": event.get("strLeague"),
        "venue": event.get("strVenue"),
        "events": []
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": SYSTEM_PROMPT + "\n\n【事实清单】\n" + json.dumps(facts, ensure_ascii=False, indent=2)
            }]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)

def write_markdown(article, event):
    slug = article["slug"]
    os.makedirs("src/content/matches", exist_ok=True)
    frontmatter = f"""---
title: "{article['title']}"
date: {event.get('dateEvent') or datetime.date.today().isoformat()}
home: "{event.get('strHomeTeam')}"
away: "{event.get('strAwayTeam')}"
homeScore: {event.get('intHomeScore') or 0}
awayScore: {event.get('intAwayScore') or 0}
league: "{event.get('strLeague') or ''}"
venue: "{event.get('strVenue') or ''}"
---

{article['body_markdown']}
"""
    path = f"src/content/matches/{slug}.md"
    if os.path.exists(path):
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    return True

if __name__ == "__main__":
    for event in fetch_finished_matches():
        try:
            article = generate_article(event)
            write_markdown(article, event)
        except Exception as e:
            print(f"跳过 {event.get('strEvent')}: {e}")

import os, json, requests, datetime, re

GEMINI_KEY = os.environ["GEMINI_API_KEY"]

LEAGUE_IDS = ["4328", "4335", "4332", "4387"]

def fetch_finished_matches():
    # 保持不变
    all_fresh_matches = []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=720)
    for league_id in LEAGUE_IDS:
        url = "https://www.thesportsdb.com/api/v1/json/123/eventspastleague.php"
        try:
            resp = requests.get(url, params={"id": league_id}, timeout=30)
            events = resp.json().get("events") or []
            for e in events:
                try:
                    dt_str = e["dateEvent"] + " " + (e.get("strTime") or "00:00:00")
                    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    if dt >= cutoff:
                        all_fresh_matches.append(e)
                except Exception:
                    continue
        except Exception as ex:
            print(f"抓取联赛 {league_id} 失败: {ex}")
    return all_fresh_matches

SYSTEM_PROMPT = """你是资深体育战报作者。你需要根据输入的【事实清单】写一篇赛事战报。
【判断运动类型】如果是足球，用足球术语；篮球，用篮球术语。
【事实锚定】只使用输入数据，没有的绝不编造。
【结构】导语 → 比赛进程(3段) → 数据切片 → 收束。
【动词】禁用：战胜、获得、取得、赢得、击败。使用：轰出、逆转、绝杀、压制等。
【输出格式】请直接输出纯净的 JSON 字符串，不要包含任何 markdown 代码块符号（不要 ```json），格式如下：
{"title": "文章标题", "slug": "英文短链接", "body_markdown": "Markdown格式正文"}
"""

def generate_article(event):
    facts = {
        "home": event.get("strHomeTeam"), "away": event.get("strAwayTeam"),
        "home_score": event.get("intHomeScore"), "away_score": event.get("intAwayScore"),
        "date": event.get("dateEvent"), "league": event.get("strLeague"),
        "sport": event.get("strSport", "Soccer"), "venue": event.get("strVenue")
    }
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n【事实清单】\n" + json.dumps(facts, ensure_ascii=False, indent=2)}]}],
        "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_KEY}"
    resp = requests.post(url, json=payload, timeout=60)
    
    # 如果 API 报错，打印出具体的错误
    if resp.status_code != 200:
        raise Exception(f"API 报错: {resp.status_code} - {resp.text}")

    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    
    # 强力清洗：把 AI 可能乱加的 ```json 和 ``` 去掉
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
    
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
sport: "{event.get('strSport') or 'Soccer'}"
venue: "{event.get('strVenue') or ''}"
---

{article['body_markdown']}
"""
    path = f"src/content/matches/{slug}.md"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter)
        print(f"✅ 成功生成文件: {slug}.md")

if __name__ == "__main__":
    test_events = [
        {"strEvent": "曼城 vs 阿森纳", "strHomeTeam": "曼城", "strAwayTeam": "阿森纳", "intHomeScore": "2", "intAwayScore": "1", "dateEvent": "2026-10-28", "strLeague": "英格兰超级联赛", "strSport": "Soccer", "strVenue": "伊蒂哈德球场"},
        {"strEvent": "湖人 vs 勇士", "strHomeTeam": "洛杉矶湖人", "strAwayTeam": "金州勇士", "intHomeScore": "112", "intAwayScore": "108", "dateEvent": "2026-10-28", "strLeague": "NBA", "strSport": "Basketball", "strVenue": "斯台普斯中心"}
    ]
    for event in test_events:
        try:
            print(f"正在处理: {event['strEvent']}...")
            article = generate_article(event)
            write_markdown(article, event)
        except Exception as e:
            print(f"❌ 处理失败 {event['strEvent']}: {e}")

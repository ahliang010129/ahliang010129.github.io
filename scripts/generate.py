import os, json, requests, datetime

GEMINI_KEY = os.environ["GEMINI_API_KEY"]

# 这里我配置了多个联赛的 ID（TheSportsDB 的免费接口支持）
# 4328: 英超, 4335: 西甲, 4332: 意甲
# 4387: NBA, 4516: CBA (篮球)
# 4424: 英雄联盟 LEC (电竞，免费版可能数据较少)
LEAGUE_IDS = ["4328", "4335", "4332", "4387"]

def fetch_finished_matches():
    all_fresh_matches = []
    # 把时间放宽到 720 小时（30天），方便测试
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

# AI 提示词升级：让它根据联赛名称自动适配运动术语
SYSTEM_PROMPT = """你是资深体育战报作者。你需要根据输入的【事实清单】写一篇赛事战报。

【第一步：判断运动类型】
查看 facts 里的 "sport" 和 "league" 字段。如果是足球，请使用专业的足球术语（如射门、控球、绝杀）；如果是篮球，请使用篮球术语（如篮板、三分、罚球）；如果是电竞，请使用电竞术语（如团战、推塔、经济差）。

【第二步：事实锚定】
只使用输入 JSON 中的比分、队伍。没有的数据绝对不要编造。

【第三步：结构锁死】
严格按以下四段式写作：
1. 导语（1-2句）：交代赛事、结果、最关键的转折点。
2. 比赛进程（3-4段）：按“开局 / 中局 / 决胜阶段”拆分，每段围绕一个转折事件展开。
3. 数据/战术切片（1段）：根据运动类型，分析决定胜负的关键点。
4. 收束（1句）：落到赛事形势或下一轮对手。

【第四步：动词与视角】
禁用动词：战胜、获得、取得、赢得、击败。使用：轰出、逆转、崩盘、苦战、惜败、横扫、绝杀、压制、反扑。
固定“现场观察者”第三人称视角。禁止使用“我认为”“我们可以看到”。
每段至少包含一个画面细节。不得虚构事实。

【输出格式】
直接输出 JSON：{"title": "文章标题", "slug": "英文短链接", "body_markdown": "Markdown格式正文"}
"""

def generate_article(event):
    facts = {
        "home": event.get("strHomeTeam"),
        "away": event.get("strAwayTeam"),
        "home_score": event.get("intHomeScore"),
        "away_score": event.get("intAwayScore"),
        "date": event.get("dateEvent"),
        "league": event.get("strLeague"),
        "sport": event.get("strSport", "Soccer"), # 足球 / Basketball 等
        "venue": event.get("strVenue")
    }
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n【事实清单】\n" + json.dumps(facts, ensure_ascii=False, indent=2)}]}],
        "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)

def write_markdown(article, event):
    slug = article["slug"]
    os.makedirs("src/content/matches", exist_ok=True)
    # 这里我们多加了一个 sport 字段
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
        print(f"生成成功: {article['title']}")

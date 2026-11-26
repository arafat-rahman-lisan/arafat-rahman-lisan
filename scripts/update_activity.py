"""Generate a self-hosted contribution map using GitHub's GraphQL API."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

login = os.environ["PROFILE_LOGIN"]
query = """query($login:String!) { user(login:$login) { repositories(privacy:PUBLIC,ownerAffiliations:OWNER) { totalCount } contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date weekday contributionCount } } } } } }"""
req = Request("https://api.github.com/graphql", data=json.dumps({"query":query,"variables":{"login":login}}).encode(), headers={"Authorization":"Bearer "+os.environ["GITHUB_TOKEN"],"Content-Type":"application/json","User-Agent":"developer-quest"}, method="POST")
with urlopen(req, timeout=30) as response:
    result = json.load(response)
if result.get("errors"):
    raise RuntimeError("GitHub GraphQL query failed")
user = result["data"]["user"]
cal = user["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
if not weeks or len(weeks)>54:
    raise ValueError("Unexpected calendar length")
last = max(d["date"] for w in weeks for d in w["contributionDays"])
total = int(cal["totalContributions"])
repos = int(user["repositories"]["totalCount"])
out = Path(__file__).resolve().parents[1]/"assets"
for theme in ("dark","light"):
    bg,fg,muted,border,colors = ("#18232b","#f4e7cf","#b8cdb9","#53665c",["#26382f","#3e6249","#63845d","#95ad73","#e5b778"]) if theme=="dark" else ("#f8f5ed","#25332d","#52665a","#d4d8cd",["#e1e5db","#c1d4ad","#93b483","#60885e","#365e44"])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 248" role="img"><title>{total} contributions through {last}</title><rect x="1" y="1" width="998" height="246" rx="12" fill="{bg}" stroke="{border}"/><g font-family="monospace" fill="{fg}"><text x="24" y="31" font-size="16" font-weight="bold">ACTIVITY MAP / LAST 12 MONTHS</text><text x="24" y="61" font-size="21" font-weight="bold">{total:,} contributions</text><text x="976" y="61" text-anchor="end" font-size="15">{repos} public repositories</text></g>']
    for i,w in enumerate(weeks):
        for d in w["contributionDays"]:
            count=int(d["contributionCount"])
            level=0 if count==0 else 1 if count<=2 else 2 if count<=5 else 3 if count<=9 else 4
            parts.append(f'<rect x="{42+i*17}" y="{82+int(d["weekday"])*17}" width="13" height="13" rx="2" fill="{colors[level]}"><title>{d["date"]}: {count} contributions</title></rect>')
    parts.append(f'<rect x="40" y="79" width="17" height="121" rx="3" fill="none" stroke="{muted}" opacity=".75"><animate attributeName="x" values="40;{40+(len(weeks)-1)*17};40" dur="20s" repeatCount="indefinite"/></rect><text x="24" y="228" font-family="monospace" font-size="13" fill="{muted}">Through {last} · GitHub data</text>')
    for i,color in enumerate(colors):
        parts.append(f'<rect x="{807+i*18}" y="216" width="13" height="13" rx="2" fill="{color}"/>')
    parts.append(f'<text x="797" y="228" font-family="monospace" font-size="12" fill="{muted}" text-anchor="end">Less</text><text x="904" y="228" font-family="monospace" font-size="12" fill="{muted}">More</text></svg>')
    (out/f"activity-{theme}.svg").write_text("".join(parts)+"\n",encoding="utf-8")

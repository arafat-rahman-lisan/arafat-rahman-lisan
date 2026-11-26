"""Build self-hosted Pac-Man contribution animations from real GitHub activity.

No third-party SVG hosts; output is readable, standalone SVG for GitHub READMEs.
Run by the scheduled workflow. Original design remains on the backup branch.
"""
import json
import os
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

LOGIN = os.environ["GITHUB_REPOSITORY"].split("/")[0]
TOKEN = os.environ["GITHUB_TOKEN"]
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date weekday contributionCount }
        }
      }
    }
  }
}"""

def get_calendar():
    payload = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={"Authorization": "Bearer " + TOKEN,
                 "Content-Type": "application/json",
                 "User-Agent": "profile-arcade-generator"},
        method="POST",
    )
    with urlopen(req, timeout=40) as response:
        body = json.load(response)
    if body.get("errors") or not body.get("data", {}).get("user"):
        raise RuntimeError("GitHub GraphQL could not retrieve contribution data: "
                           + str(body.get("errors", "missing user")))
    cal = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    if not 50 <= len(weeks) <= 54:
        raise ValueError("Invalid contribution calendar week count")
    days = []
    for col, week in enumerate(weeks):
        for day in week["contributionDays"]:
            row = int(day["weekday"])
            count = int(day["contributionCount"])
            if row not in range(7) or count < 0:
                raise ValueError("Invalid contribution day")
            days.append((col, row, day["date"], count))
    if not 350 <= len(days) <= 378:
        raise ValueError("Incomplete contribution calendar")
    return days, len(weeks), int(cal["totalContributions"])

def route_css(weeks):
    x0, dx, y0, dy = 38, 17.3, 58, 18.3
    far = x0 + (weeks - 1) * dx
    segments = []
    for row in range(7):
        y = y0 + row * dy
        forward = row % 2 == 0
        start_x, end_x = (x0, far) if forward else (far, x0)
        direction = 1 if forward else -1
        segments.append(
            f'{row * 100 / 7:.2f}%{{transform:translate({start_x:.1f}px,{y:.1f}px) scaleX({direction})}}'
        )
        segments.append(
            f'{(row + .92) * 100 / 7:.2f}%{{transform:translate({end_x:.1f}px,{y:.1f}px) scaleX({direction})}}'
        )
        if row < 6:
            segments.append(
                f'{(row + 1) * 100 / 7:.2f}%{{transform:translate({end_x:.1f}px,{y + dy:.1f}px) scaleX({-direction})}}'
            )
    segments.append(f'99.9%{{transform:translate({far:.1f}px,{y0 + 6 * dy:.1f}px) scaleX(1)}}')
    segments.append(f'100%{{transform:translate({x0}px,{y0}px) scaleX(1)}}')
    return "".join(segments)

def render(days, weeks, total, dark):
    bg = "#111b22" if dark else "#f4f8f5"
    line = "#395554" if dark else "#a8c9c0"
    fg = "#f3e9d7" if dark else "#273b39"
    muted = "#a8c4bf" if dark else "#506c66"
    colors = (["#23323a", "#31544c", "#497766", "#6eac91", "#ace0b6"]
              if dark else
              ["#e2ece7", "#b6d5c4", "#86b7a0", "#52957a", "#276e59"])
    yellow = "#ffd66d" if dark else "#e9ad3e"
    pink = "#f49caa" if dark else "#e57888"
    first_day = min(day[2] for day in days)
    last_day = max(day[2] for day in days)
    style = (
        ".runner{animation:route 34s linear infinite}"
        ".chaser{animation:route 34s linear infinite;animation-delay:-.48s}"
        ".mouth{animation:chomp .27s ease-in-out infinite;transform-origin:0 0}"
        "@keyframes route{" + route_css(weeks) + "}"
        "@keyframes chomp{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.14)}}"
        "@media(prefers-reduced-motion:reduce){"
        ".runner,.chaser,.mouth{animation:none}"
        ".runner{transform:translate(38px,58px)}"
        ".chaser{transform:translate(10px,58px)}}"
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="225" '
        'viewBox="0 0 1000 225" role="img">',
        f'<title>Pac-Man-style contribution animation with {total} actual GitHub contributions, through {escape(last_day)}</title>',
        f'<defs><style>{style}</style></defs>',
        f'<rect x="2" y="2" width="996" height="221" rx="13" fill="{bg}" stroke="{line}"/>',
        f'<path d="M23 39H976" stroke="{line}" stroke-opacity=".62"/>',
        f'<text x="22" y="28" font-family="monospace" font-size="17" font-weight="bold" letter-spacing="1.1" fill="{fg}">ARCADE RUN</text>',
        f'<circle cx="183" cy="22" r="5" fill="{yellow}"/>',
        f'<text x="197" y="28" font-family="monospace" font-size="17" font-weight="bold" fill="{fg}">CONTRIBUTION TRAIL</text>',
        f'<text x="976" y="28" text-anchor="end" font-family="monospace" font-size="14" fill="{muted}">{total} CONTRIBUTIONS</text>',
    ]
    for col, row, date, count in days:
        level = 0 if count == 0 else 1 if count < 3 else 2 if count < 6 else 3 if count < 10 else 4
        x, y = 38 + col * 17.3 - 6, 58 + row * 18.3 - 6
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="12" height="12" rx="3" fill="{colors[level]}">'
            f'<title>{escape(date)}: {count} contributions</title></rect>'
        )
    parts.extend([
        f'<g class="chaser"><path d="M-9 8V-1A9 9 0 0 1 9 -1V8L5 5L2 8L-2 5L-5 8Z" fill="{pink}"/>'
        '<ellipse cx="-3.5" cy="-1" rx="2.8" ry="3.4" fill="white"/>'
        '<ellipse cx="3.5" cy="-1" rx="2.8" ry="3.4" fill="white"/>'
        '<circle cx="-2.5" cy="-.5" r="1.4" fill="#203843"/>'
        '<circle cx="4.5" cy="-.5" r="1.4" fill="#203843"/></g>',
        f'<g class="runner"><circle r="11" fill="{yellow}"/>'
        f'<path class="mouth" d="M0 0 L17 -9 L17 9 Z" fill="{bg}"/>'
        '<circle cx="1.5" cy="-6.6" r="1.65" fill="#5a421e"/></g>',
        f'<text x="24" y="210" font-family="monospace" font-size="12" fill="{muted}">CHOMP THE COMMITS</text>',
        f'<circle cx="822" cy="206" r="4" fill="{yellow}"/>',
        f'<text x="835" y="211" font-family="monospace" font-size="12" fill="{muted}">PAC RUNNER</text>',
        f'<text x="978" y="211" text-anchor="end" font-family="monospace" font-size="12" fill="{muted}">{escape(first_day)} / {escape(last_day)}</text>',
        '</svg>\n',
    ])
    output = "".join(parts)
    ET.fromstring(output)  # Fail the workflow if the generated SVG is malformed.
    return output

def main():
    days, weeks, total = get_calendar()
    assets = Path(__file__).resolve().parents[1] / "assets"
    assets.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        output = render(days, weeks, total, dark=(theme == "dark"))
        path = assets / f"pacman-{theme}.svg"
        path.write_text(output, encoding="utf-8")
        print(f"Updated {path.name}: {len(days)} actual calendar cells, {total} contributions")

if __name__ == "__main__":
    main()

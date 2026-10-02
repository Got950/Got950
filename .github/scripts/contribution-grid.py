"""Write a static contribution grid from GitHub's own calendar."""

import json
import os
import urllib.request
from pathlib import Path

DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
LEVEL = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_weeks():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "got950-contribution-grid", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    query = {
        "query": """
        query {
          user(login: "Got950") {
            contributionsCollection {
              contributionCalendar {
                weeks {
                  contributionDays {
                    contributionLevel
                    date
                  }
                }
              }
            }
          }
        }
        """
    }
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(query).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    if payload.get("errors"):
        raise SystemExit(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def render(weeks, colors, label):
    cell = 12
    gap = 3
    step = cell + gap
    left = 0
    top = 20
    cols = len(weeks)
    width = left + cols * step - gap
    height = top + 7 * step - gap
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img">',
        f'<title>GitHub contributions for Got950</title>',
    ]
    seen = set()
    last_label = -4
    active = 0
    for col, week in enumerate(weeks):
        days = week["contributionDays"]
        month = int(days[0]["date"][5:7])
        key = days[0]["date"][:7]
        if key not in seen and col - last_label >= 4:
            seen.add(key)
            last_label = col
            x = left + col * step
            parts.append(
                f'<text x="{x}" y="11" fill="{label}" font-family="ui-monospace, Menlo, Consolas, monospace" font-size="11">{MONTHS[month - 1]}</text>'
            )
        elif key not in seen:
            seen.add(key)
        for row, day in enumerate(days):
            level = LEVEL[day["contributionLevel"]]
            if level:
                active += 1
            x = left + col * step
            y = top + row * step
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{colors[level]}"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts), active


def main():
    weeks = fetch_weeks()
    out = Path("dist")
    out.mkdir(exist_ok=True)
    dark, active = render(weeks, DARK, "#8b949e")
    light, _ = render(weeks, LIGHT, "#57606a")
    (out / "contributions-dark.svg").write_text(dark, encoding="utf-8")
    (out / "contributions.svg").write_text(light, encoding="utf-8")
    print(f"weeks={len(weeks)} active_days={active}")


if __name__ == "__main__":
    main()

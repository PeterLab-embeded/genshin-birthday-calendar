"""Build a Chinese Genshin birthday calendar from a cited public birthday index.

Standard-library only.  Run locally with --refresh to scan for new birthdays.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SOURCE_URL = "https://fansupport.joelin.cc/en/group/genshin-impact/"
MONTHS = {name: number for number, name in enumerate(calendar.month_name) if name}
DATE_RE = re.compile(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\b")


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json = False
        self.parts: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.in_json = True
            self.parts = []

    def handle_data(self, data):
        if self.in_json:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_json:
            self.scripts.append("".join(self.parts))
            self.in_json = False


def fetch_birthdays() -> list[dict[str, str]]:
    request = Request(SOURCE_URL, headers={"User-Agent": "GenshinBirthdayCalendar/1.0"})
    with urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")
    return parse_birthdays(page)


def parse_birthdays(page: str) -> list[dict[str, str]]:
    parser = Scripts()
    parser.feed(page)
    for raw in parser.scripts:
        data = json.loads(raw)
        if data.get("@type") != "FAQPage":
            continue
        for question in data["mainEntity"]:
            answer = question["acceptedAnswer"]["text"]
            if "Birthdays of Genshin Impact" not in answer:
                continue
            matches = list(DATE_RE.finditer(answer))
            result = []
            prior = answer.find(":") + 1
            for match in matches:
                name = answer[prior:match.start()].strip(" ,.;:\n")
                if not name:
                    raise ValueError("Source contains a birthday without a name")
                month, day = MONTHS[match.group(1)], int(match.group(2))
                dt.date(2024, month, day)
                result.append({"name": name, "date": f"{month:02d}-{day:02d}"})
                prior = match.end()
            if len(result) < 100 or len({x["name"] for x in result}) != len(result):
                raise ValueError("Source parse failed or lost characters")
            return result
    raise ValueError("Birthday list not found in source")


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def fold(line: str) -> list[str]:
    # RFC 5545 limits content lines to 75 octets, including UTF-8 text.
    chunks = []
    current = ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            chunks.append(current)
            current = " " + char
        else:
            current += char
    chunks.append(current)
    return chunks


def event(uid: str, start: str, end: str, summary: str, description: str,
          *, all_day: bool = False, repeat: bool = False, alarm: bool = False) -> list[str]:
    lines = ["BEGIN:VEVENT", f"UID:{uid}@genshin-calendar.local", "DTSTAMP:20261017T000000Z"]
    if all_day:
        lines += [f"DTSTART;VALUE=DATE:{start}", f"DTEND;VALUE=DATE:{end}"]
    else:
        lines += [f"DTSTART;TZID=Asia/Shanghai:{start}", f"DTEND;TZID=Asia/Shanghai:{end}"]
    lines += [f"SUMMARY:{escape(summary)}", f"DESCRIPTION:{escape(description)}", "TRANSP:TRANSPARENT"]
    if repeat:
        lines.append("RRULE:FREQ=YEARLY")
    if alarm:
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{escape(summary)}", "TRIGGER:PT0S", "END:VALARM"]
    lines.append("END:VEVENT")
    return lines


def build(rows: list[dict[str, str]], names: dict[str, str], start_year: int, years: int) -> tuple[str, int]:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "PRODID:-//Genshin Birthday Calendar//ZH-CN//EN", "X-WR-CALNAME:原神角色生日与周年庆",
             "X-WR-TIMEZONE:Asia/Shanghai", "X-PUBLISHED-TTL:PT24H",
             "BEGIN:VTIMEZONE", "TZID:Asia/Shanghai", "BEGIN:STANDARD", "DTSTART:19700101T000000",
             "TZOFFSETFROM:+0800", "TZOFFSETTO:+0800", "TZNAME:CST", "END:STANDARD", "END:VTIMEZONE"]
    by_day: dict[str, list[tuple[str, str]]] = {}
    for row in rows:
        by_day.setdefault(row["date"], []).append((row["name"], names.get(row["name"], row["name"])))
    by_day.setdefault("09-28", []).append(("anniversary", "原神周年庆"))
    count = 0
    for month_day, entries in sorted(by_day.items()):
        month, day = map(int, month_day.split("-"))
        first_year = 2024 if month_day == "02-29" else start_year
        birthday = dt.date(first_year, month, day)
        next_day = birthday + dt.timedelta(days=1)
        for english, person in entries:
            title = f"🎂 {person}生日" if person != "原神周年庆" else "🎉 原神周年庆"
            key = re.sub(r"[^a-z0-9]+", "-", english.lower()).strip("-")
            lines += event(f"birthday-{key}", birthday.strftime("%Y%m%d"),
                           next_day.strftime("%Y%m%d"), title, "每年重复；角色生日以游戏内公告为准。", all_day=True, repeat=True)
            count += 1
        # One reminder per date, even when multiple characters share it.
        for year in range(start_year, start_year + years):
            try:
                date = dt.date(year, month, day)
            except ValueError:
                continue
            evening = date - dt.timedelta(days=1)
            labels = "、".join(person for _, person in entries)
            title = f"🔔 明天：{labels}"
            lines += event(f"eve-{month_day}-{year}", evening.strftime("%Y%m%d") + "T200000",
                           evening.strftime("%Y%m%d") + "T200500", title,
                           f"明天是{labels}的纪念日。", alarm=True)
            count += 1
    # Friday 20:00 summarizes the following Monday through Sunday.
    date = dt.date(start_year, 1, 1)
    date += dt.timedelta(days=(4 - date.weekday()) % 7)
    final_date = dt.date(start_year + years, 1, 1)
    while date < final_date:
        monday = date + dt.timedelta(days=3)
        next_week = [(monday + dt.timedelta(days=i)) for i in range(7)]
        forthcoming = [f"{d.month}/{d.day} {'、'.join(person for _, person in by_day[f'{d.month:02d}-{d.day:02d}'])}"
                       for d in next_week if f"{d.month:02d}-{d.day:02d}" in by_day]
        if forthcoming:
            title = "📅 下周生日预告：" + "；".join(forthcoming)
            lines += event(f"week-{date:%Y%m%d}", date.strftime("%Y%m%d") + "T200000",
                           date.strftime("%Y%m%d") + "T200500", title,
                           "下周一至周日：\n" + "\n".join(forthcoming), alarm=True)
            count += 1
        date += dt.timedelta(days=7)
    lines.append("END:VCALENDAR")
    content = "\r\n".join(part for line in lines for part in fold(line)) + "\r\n"
    return content, count


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--refresh", action="store_true", help="Fetch source and scan for new characters")
    cli.add_argument("--years", type=int, default=11)
    args = cli.parse_args()
    snapshot = ROOT / "birthdays.json"
    previous = json.loads(snapshot.read_text(encoding="utf-8")) if snapshot.exists() else []
    rows = fetch_birthdays() if args.refresh else previous
    if not rows:
        raise SystemExit("No birthday data: run --refresh first")
    if args.refresh:
        before = {(item["name"], item["date"]) for item in previous}
        after = {(item["name"], item["date"]) for item in rows}
        changes = {"added": sorted(after - before), "removed_or_changed": sorted(before - after)}
        (ROOT / "scan-report.json").write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        snapshot.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    names = json.loads((ROOT / "names_zh.json").read_text(encoding="utf-8"))
    content, count = build(rows, names, dt.date.today().year, args.years)
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "genshin-birthdays.ics").write_bytes(content.encode("utf-8"))
    print(f"Characters: {len(rows)}; calendar events: {count}; file: {docs / 'genshin-birthdays.ics'}")


if __name__ == "__main__":
    main()

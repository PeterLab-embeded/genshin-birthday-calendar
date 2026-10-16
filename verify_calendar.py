"""Validate the generated calendar's structure and reminder dates."""

from pathlib import Path
import datetime as dt
import re

data = (Path(__file__).parent / "docs" / "genshin-birthdays.ics").read_bytes()
assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b"")
for line in data.split(b"\r\n"):
    assert len(line) <= 75, f"Overlong iCalendar line: {len(line)} bytes"

text = data.decode("utf-8").replace("\r\n ", "").replace("\r\n\t", "")
events = [part for part in text.split("BEGIN:VEVENT\r\n")[1:]]
uids = [re.search(r"^UID:(.+)$", e, re.M).group(1) for e in events]
assert len(uids) == len(set(uids))
assert sum("RRULE:FREQ=YEARLY" in e for e in events) == 121

def find(uid: str) -> str:
    return next(e for e in events if f"UID:{uid}@genshin-calendar.local" in e)

year = dt.date.today().year
sayu = dt.date(year, 10, 19)
assert f"DTSTART;TZID=Asia/Shanghai:{sayu - dt.timedelta(days=1):%Y%m%d}T200000" in find(f"eve-10-19-{year}")
assert "SUMMARY:🔔 明天：早柚" in find(f"eve-10-19-{year}")
friday = sayu - dt.timedelta(days=sayu.weekday() + 3)
assert "10/19 早柚" in find(f"week-{friday:%Y%m%d}")
january_3 = dt.date(year + 1, 1, 3)
previous_friday = january_3 - dt.timedelta(days=january_3.weekday() + 3)
assert "1/3 流浪者" in find(f"week-{previous_friday:%Y%m%d}")
leap_year = next(y for y in range(year, year + 11) if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))
assert f"DTSTART;TZID=Asia/Shanghai:{leap_year}0228T200000" in find(f"eve-02-29-{leap_year}")
print(f"Verified {len(events)} events, unique UIDs, Friday digest, leap day, and UTF-8 line folding.")

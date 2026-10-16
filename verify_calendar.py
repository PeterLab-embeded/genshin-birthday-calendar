"""Validate the generated calendar's structure and reminder dates."""

from pathlib import Path
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

assert "DTSTART;TZID=Asia/Shanghai:20261018T200000" in find("eve-10-19-2026")
assert "SUMMARY:🔔 明天：早柚" in find("eve-10-19-2026")
assert "DTSTART;TZID=Asia/Shanghai:20261016T200000" in find("week-20261016")
assert "10/19 早柚" in find("week-20261016")
assert "10/25 优菈" in find("week-20261016")
assert "1/3 流浪者" in find("week-20261225")
assert "UID:eve-02-29-2027" not in text
assert "DTSTART;TZID=Asia/Shanghai:20280228T200000" in find("eve-02-29-2028")
print(f"Verified {len(events)} events, unique UIDs, Friday digest, leap day, and UTF-8 line folding.")

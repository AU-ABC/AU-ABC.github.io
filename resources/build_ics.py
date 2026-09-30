"""Build the subscribable calendar feed events/abc-events.ics from events/events.json.

Runs automatically before every Quarto render (see `pre-render` in _quarto.yml).
Only uses the Python standard library.
"""
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "events" / "events.json"
FEED = ROOT / "events" / "abc-events.ics"
SITE = "https://abc.au.dk"
CONTACT = "abc.focus@au.dk"


LOCAL = ZoneInfo("Europe/Copenhagen")


def check_offset(event, key):
    """Fail if the UTC offset doesn't match Danish time on that date (+02:00 summer, +01:00 winter)."""
    value = event.get(key)
    if not value:
        return
    dt = datetime.fromisoformat(value)
    expected = dt.replace(tzinfo=LOCAL).utcoffset()
    if dt.utcoffset() != expected:
        hours = int(expected.total_seconds() // 3600)
        fixed = value[:19] + f"+{hours:02d}:00"
        raise SystemExit(
            f"events.json: event '{event['id']}' has {key}={value}, but Denmark is at UTC+{hours} "
            f"on that date (summer/winter time). Use {fixed} instead."
        )


def utc(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def plain(text):
    text = re.sub(r"<br\s*/?>", "\n", text or "", flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def escape(text):
    return text.replace("\\", "\\\\").replace(";", "\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold lines longer than 75 bytes, as required by RFC 5545."""
    out, current = [], b""
    for char in line:
        encoded = char.encode("utf-8")
        if len(current) + len(encoded) > (75 if not out else 74):
            out.append(current.decode("utf-8"))
            current = b""
        current += encoded
    out.append(current.decode("utf-8"))
    return "\r\n ".join(out)


def vevent(event, stamp):
    start = event["start"]
    end = event.get("end") or (datetime.fromisoformat(start) + timedelta(hours=1)).isoformat()
    signup = event.get("signup")
    description = plain(event.get("description"))
    if signup:
        description += f"\n\nSign up: {signup}"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{event['id']}@abc.au.dk",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{utc(start)}",
        f"DTEND:{utc(end)}",
        f"SUMMARY:{escape(event['title'])}",
        f"DESCRIPTION:{escape(description)}",
    ]
    if event.get("location"):
        lines.append(f"LOCATION:{escape(event['location'])}")
    if event.get("tags"):
        lines.append("CATEGORIES:" + ",".join(escape(t) for t in event["tags"]))
    lines.append(f"URL:{signup or SITE + '/calendar.html'}")
    lines.append("END:VEVENT")
    return lines


def main():
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AU-ABC//Events calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:ABC - AI\\, Bioinformatics and Computing",
        f"X-WR-CALDESC:Events of the ABC focus group ({CONTACT})",
        "X-WR-TIMEZONE:Europe/Copenhagen",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    for event in events:
        check_offset(event, "start")
        check_offset(event, "end")
        lines += vevent(event, stamp)
    lines.append("END:VCALENDAR")
    FEED.write_bytes(("\r\n".join(fold(l) for l in lines) + "\r\n").encode("utf-8"))
    print(f"Wrote {FEED.relative_to(ROOT)} with {len(events)} event(s)")


if __name__ == "__main__":
    main()

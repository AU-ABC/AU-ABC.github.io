"""Build the subscribable calendar feed events/abc-events.ics from events/events.json.

Runs automatically before every Quarto render (see `pre-render` in _quarto.yml).
Only uses the Python standard library.
"""
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "events" / "events.json"
FEED = ROOT / "events" / "abc-events.ics"
SITE = "https://abc.au.dk"
CONTACT = "abc.focus@au.dk"


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
        lines += vevent(event, stamp)
    lines.append("END:VCALENDAR")
    FEED.write_bytes(("\r\n".join(fold(l) for l in lines) + "\r\n").encode("utf-8"))
    print(f"Wrote {FEED.relative_to(ROOT)} with {len(events)} event(s)")


if __name__ == "__main__":
    main()

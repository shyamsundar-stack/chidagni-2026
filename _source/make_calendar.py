"""
Write assets/cal/<slug>.ics, one per "Add to calendar" button in index.html.

    pip install beautifulsoup4
    python _source/make_calendar.py

iPhones and Macs open these in Calendar directly; Android gets a Google
Calendar link built in main.js (section 4) instead. Both use the same title and
text, so if you change the wording here, change calEntry() in main.js too.
Re-run after editing any time or name in the schedule.

The link in each event goes through the Switchy link with a tracked fragment,
?go=calendar.<slug>.yt-<date> (Switchy forwards the query). Tapped from the reminder, the page records the
visit (utm_source=calendar, utm_content=<slug>) and forwards to that evening's
YouTube stream, looked up at that moment. The files never need the stream links.
"""
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://live.svmf.in/chidagni'
ZOOM = 'https://us02web.zoom.us/j/87692135267?pwd=UmNlTGhVVkhBdHpMM05aWkNSUXRwZz09'
VENUE = 'Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, East Mada Street, Mylapore, Chennai 600004'


def txt(node):
    return ' '.join(node.get_text(' ', strip=True).split()) if node else ''


def utc(iso):
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def esc(t):
    return t.replace('\\', '\\\\').replace(';', '\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    """RFC 5545: fold at 75 octets, never inside a UTF-8 sequence."""
    out, cur, limit = [], '', 75
    for ch in line:
        if len((cur + ch).encode()) > limit:
            out.append(cur)
            cur, limit = ch, 74
        else:
            cur += ch
    out.append(cur)
    return '\r\n '.join(out)


soup = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8'), 'html.parser')
out = ROOT / 'assets' / 'cal'
out.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

for btn in soup.select('[data-cal]'):
    box = btn.find_parent(attrs={'data-start': True})
    slug = btn['data-cal']
    who, kind = txt(box.select_one('.event__who')), txt(box.select_one('.event__kind'))
    title = btn.get('data-cal-title') or f'Chidagni: {who}' + (f', {kind}' if kind else '')
    day = box['data-start'][:10]
    link = f'{SITE}?go=calendar.{slug}.yt-{day}'
    desc = (f"{btn.get('data-cal-kind') or kind}\n\n"
            f'Watch live on YouTube: {link}\n'
            f'Or join on Zoom: {ZOOM} (Meeting ID 876 9213 5267, password Krishna)\n\n'
            f'Chidagni 2026, the Fire of Consciousness Festival. {VENUE}. All are welcome.')
    lines = [
        'BEGIN:VCALENDAR', 'VERSION:2.0', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
        'PRODID:-//SVMF//Chidagni 2026//EN',
        'BEGIN:VEVENT',
        f'UID:{slug}-2026@chidagni.svmf.in',
        f'DTSTAMP:{now}',
        f"DTSTART:{utc(box['data-start'])}",
        f"DTEND:{utc(box['data-end'])}",
        f'SUMMARY:{esc(title)}',
        f'DESCRIPTION:{esc(desc)}',
        f'LOCATION:{esc(VENUE)}',
        f'URL:{link}',
        'BEGIN:VALARM', 'ACTION:DISPLAY', 'TRIGGER:-PT15M', f'DESCRIPTION:{esc(title)}', 'END:VALARM',
        'END:VEVENT', 'END:VCALENDAR',
    ]
    (out / f'{slug}.ics').write_bytes(('\r\n'.join(fold(l) for l in lines) + '\r\n').encode())
    print(f'  cal/{slug}.ics  {title}')

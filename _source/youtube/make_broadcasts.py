"""
Builds BROADCASTS.md and broadcasts.json (the YouTube "Schedule stream" fields for the
five Chidagni 2026 evenings) from the schedule in index.html.

    python _source/youtube/make_broadcasts.py

Session names, times, roles and accompanists are read from the <article class="event">
blocks in index.html (data-start / data-end in IST), so the kit cannot drift from the
page. Titles, tags and hashtags are curated below. Each stream is scheduled
LEAD_MIN minutes before the evening's first item (the page mounts the embed
25 minutes before, so viewers see the YouTube waiting room, then the stream).
"""
import html
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
LEAD_MIN = 15

EVENT_URL = 'https://live.svmf.in/chidagni'
ZOOM_URL = 'https://us02web.zoom.us/j/87692135267?pwd=UmNlTGhVVkhBdHpMM05aWkNSUXRwZz09'
VENUE = 'Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, East Mada Street, Mylapore, Chennai 600004'
PLAYLIST = 'Chidagni 2026'
SEP = ' \u00b7 '
CATEGORY = ('Music', 10)          # YouTube categoryId 10

TITLES = {
    1: 'Chidagni 2026 · Day 1 · Inauguration | Carnatic Vocal Concert by Vid. Ritvik Y V',
    2: 'Chidagni 2026 · Day 2 · Dr. Priya Ramachandran on Sita Devi | Namasankirtanam by Dr. R. Ganesh',
    3: 'Chidagni 2026 · Day 3 · Moksha-Pradayini: Prof. K. Srinivasan | Devotional Music: Dr. Radha Bhaskar',
    4: 'Chidagni 2026 · Day 4 · Harikatha: Meena Lochani, Paasha Mochani by Vid. U. E. Sinddhuja',
    5: 'Chidagni 2026 · Day 5 · Carnatic Violin Concert by Dr. M. Narmadha',
}
COMMON_TAGS = ['Chidagni', 'Chidagni 2026', 'Fire of Consciousness Festival', 'Sri Vishnu Mohan Foundation',
               'SVMF', 'Bharatiya Vidya Bhavan', 'Sri Gnana Advaitha Peetam', 'Mylapore', 'Chennai',
               'Carnatic music', 'Sri Sathguru Swami Gnanananda Sarasvathi Ma']
DAY_TAGS = {
    1: ['Chidagni inauguration', 'Ritvik Y V', 'Carnatic vocal concert', 'Nalli Kuppuswami Chetti',
        'Swami Shrihariprasad'],
    2: ['Priya Ramachandran', 'Sita Devi', 'R. Ganesh', 'Namasankirtanam', 'bhajan'],
    3: ['K. Srinivasan', 'Moksha Pradayini', 'Radha Bhaskar', 'devotional music concert', 'discourse'],
    4: ['U. E. Sinddhuja', 'Harikatha', 'Meena Lochani Paasha Mochani', 'Meenakshi'],
    5: ['M. Narmadha', 'Narmadha violin', 'Carnatic violin concert', 'violin'],
}
HASHTAGS = {
    1: '#Chidagni2026 #CarnaticMusic #Chennai',
    2: '#Chidagni2026 #Namasankirtanam #Chennai',
    3: '#Chidagni2026 #CarnaticMusic #Chennai',
    4: '#Chidagni2026 #Harikatha #Chennai',
    5: '#Chidagni2026 #CarnaticViolin #Chennai',
}


# ── read the schedule out of index.html ────────────────────────────────
def text(fragment):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def grab(cls, block):
    m = re.search(rf'<(\w+) class="{cls}[^"]*"[^>]*>(.*?)</\1>', block, re.S)
    return text(m.group(2)) if m else ''


def parse_days():
    src = (ROOT / 'index.html').read_text(encoding='utf-8')
    days = []
    for m in re.finditer(r'<li class="day" id="day-(\d)">(.*?)</li>\s*(?=<li class="day"|</ol>)', src, re.S):
        n, body = int(m.group(1)), m.group(2)
        label = grab('day__n', body)
        date_long = re.search(r'<time datetime="([\d-]+)">([^<]+)</time>', body)
        events = []
        for a in re.finditer(r'<article class="(event[^"]*)" data-start="([^"]+)" data-end="([^"]+)">(.*?)</article>',
                             body, re.S):
            cls, start, end, ab = a.groups()
            team = [(text(i), text(r)) for i, r in re.findall(
                r'<li><span>(.*?)</span>(.*?)</li>', ab, re.S)]
            events.append(dict(
                start=datetime.fromisoformat(start), end=datetime.fromisoformat(end),
                star='event--star' in cls,
                kind=grab('event__kind', ab), who=grab('event__who', ab),
                role=grab('event__role', ab), team=team))
        days.append(dict(n=n, label=label, date=date_long.group(1), weekday_date=date_long.group(2),
                         events=events))
    assert len(days) == 5, f'expected 5 days in index.html, found {len(days)}'
    return days


def clock(dt):
    return dt.strftime('%I:%M %p').lstrip('0').lower()


def session_line(e):
    kind, who = e['kind'], e['who']
    if not kind:                                   # the rites: lamp lighting, vote of thanks
        return who
    return f'{kind}: {who}'


# ── description ────────────────────────────────────────────────────────
def description(day, all_days, stream_start):
    L = []
    L.append('Chidagni 2026, The Fire of Consciousness Festival (16th edition)')
    head = 'Inauguration' if day['n'] == 1 else f"Day {day['n']}"
    L.append(f"{head} · {day['weekday_date']} 2026 · Live from Bharatiya Vidya Bhavan, Mylapore, Chennai")
    L.append('')
    L.append(f"This evening (all times IST; the stream opens at {clock(stream_start)}):")
    for e in day['events']:
        L.append(f"{clock(e['start'])}  {session_line(e)}")
        if e['role']:
            L.append(f"      {e['role']}")
        for inst, name in e['team']:
            L.append(f"      {inst}: {name}")
    L.append('')
    L.append('Venue: ' + VENUE + '. All are welcome.')
    L.append('')
    L.append('Join on Zoom: ' + ZOOM_URL)
    L.append('Meeting ID 876 9213 5267, password Krishna')
    L.append('')
    L.append('Schedule, countdown and the stream for every evening: ' + EVENT_URL)
    L.append('')
    L.append('The five evenings (IST):')
    for d in all_days:
        items = [f"{clock(e['start'])} {e['kind']}, {e['who']}" for e in d['events'] if e['star']]
        if d['label'] == 'Inauguration':
            items.insert(0, f"{clock(d['events'][0]['start'])} Inauguration")
        what = '; '.join(items)
        tag = f"Day {d['n']}"
        L.append(f"{tag}, {d['weekday_date'].split()[0][:3]} {' '.join(d['weekday_date'].split()[1:])}: {what}")
    L.append('')
    L.append('Jointly organised by Sri Vishnu Mohan Foundation, Bharatiya Vidya Bhavan (Chennai Kendra) '
             'and Sri Gnana Advaitha Peetam. The Sri Vishnu Mohan Foundation and Sri Gnana Advaitha Peetam '
             'are not-for-profit organisations guided by the philosophy of Her Holiness Sri Sathguru Swami '
             'Gnanananda Sarasvathi Ma.')
    L.append('Queries: Smt. Saraswati Janakiraman, +91 98415 98263')
    L.append('www.srisathguru.com · www.svmf.in')
    L.append('')
    L.append('Chapters: timestamps for each session will be added here after the stream.')
    L.append('')
    L.append(HASHTAGS[day['n']])
    out = '\n'.join(L)
    assert '<' not in out and '>' not in out, 'YouTube rejects < and > in descriptions'
    return out


def chapters(day, stream_start):
    """A chapter list with offsets from the scheduled start; correct them against the recording."""
    L = ['00:00 Stream opens']
    for e in day['events']:
        off = int((e['start'] - stream_start).total_seconds())
        h, r = divmod(off, 3600)
        stamp = f'{h}:{r // 60:02d}:00' if h else f'{r // 60:02d}:00'
        L.append(f'{stamp} {session_line(e)}')
    off = int((day['events'][-1]['end'] - stream_start).total_seconds())
    h, r = divmod(off, 3600)
    L.append(f'{h}:{r // 60:02d}:00 Close of the evening')
    return '\n'.join(L)


def tags_len(tags):
    return sum(len(t) + (2 if ' ' in t else 0) for t in tags) + len(tags) - 1


# ── build ─────────────────────────────────────────────────────────────
def build():
    days = parse_days()
    out = []
    for d in days:
        first, last = d['events'][0], d['events'][-1]
        stream_start = first['start'] - timedelta(minutes=LEAD_MIN)
        title = TITLES[d['n']]
        tags = COMMON_TAGS + DAY_TAGS[d['n']]
        desc = description(d, days, stream_start)
        assert len(title) <= 100, (d['n'], len(title))
        assert len(desc) <= 5000, (d['n'], len(desc))
        assert tags_len(tags) <= 500, (d['n'], tags_len(tags))
        out.append(dict(
            day=d['n'],
            date=d['date'],
            label=d['label'],
            weekdayDate=d['weekday_date'],
            scheduledStartTime=stream_start.isoformat(),
            firstItemTime=first['start'].isoformat(),
            scheduledEndTime=last['end'].isoformat(),
            title=title,
            description=desc,
            thumbnail=f"day-{d['n']}.jpg",
            tags=tags,
            categoryName=CATEGORY[0],
            categoryId=str(CATEGORY[1]),
            privacyStatus='public',
            madeForKids=False,
            defaultLanguage='en',
            defaultAudioLanguage='ta',
            playlist=PLAYLIST,
            embeddable=True,
            enableDvr=True,
            enableAutoStart=False,
            enableAutoStop=False,
            latencyPreference='normal',
            liveChat=True,
            chapterTemplate=chapters(d, stream_start),
            sessions=[dict(start=e['start'].isoformat(), end=e['end'].isoformat(), kind=e['kind'],
                           who=e['who'], role=e['role'],
                           team=[dict(instrument=i, name=n) for i, n in e['team']]) for e in d['events']],
        ))
    return out


def md_cell(s):
    return s.replace('|', '\\|')


def fence(s):
    return '```text\n' + s + '\n```'


def markdown(bs):
    L = []
    w = L.append
    w('# Chidagni 2026: YouTube Live kit')
    w('')
    w('Everything needed to schedule the five evening streams on the **SVMF** channel '
      '(https://www.youtube.com/@svmf5987). Every field below is ready to paste into YouTube Studio. '
      'Generated by `make_broadcasts.py` from the schedule in `index.html`; thumbnails by '
      '`make_thumbnails.py`. Do not hand-edit this file: change the script and re-run it.')
    w('')
    w('| Day | Date | Stream starts (IST) | First item | Thumbnail | Title |')
    w('|---|---|---|---|---|---|')
    for b in bs:
        st = datetime.fromisoformat(b['scheduledStartTime'])
        fi = datetime.fromisoformat(b['firstItemTime'])
        w(f"| {b['day']} | {b['weekdayDate']} | **{clock(st)}** | {clock(fi)} | `{b['thumbnail']}` | {md_cell(b['title'])} |")
    w('')
    w('## Before you start (once)')
    w('')
    w('1. **Channel checks.** In YouTube Studio, Settings, Channel, Feature eligibility: the channel must be '
      'phone-verified (custom thumbnails need it) and live streaming must be enabled. If live streaming has '
      'never been used on this channel, turning it on takes up to 24 hours, so do it today.')
    w('2. **Ingest is Restream, not a YouTube key.** Each broadcast below is attached to its own Restream '
      'event (app.restream.io/shows/…), which also sends the feed to Facebook (Sripeetam Chennai). The '
      'technician streams to Restream: in OBS, Service *Restream.io* and that day\'s event, or '
      '`rtmp://live.restream.io/live` with that day\'s Restream key from the printed technician sheet. Do '
      '**not** stream to `rtmp://a.rtmp.youtube.com/live2`. (Originally a shared YouTube key `Chidagni 2026` '
      'was created; it is no longer used.)')
    w(f'3. **Playlist.** Content, Playlists, New playlist: `{PLAYLIST}`, Public. Each stream is added to it '
      'in the Details step below.')
    w('')
    w('## Doing it in YouTube Studio')
    w('')
    w('For each day, in this order (Day 1 first, then Days 2 to 5):')
    w('')
    w('1. Go to https://studio.youtube.com signed in as SVMF.')
    w('2. **Create** (camera icon with +, top right) → **Go live**. The Live Control Room opens.')
    w('3. In the left rail click **Manage** (calendar icon) → **Schedule stream** (top right).')
    w('4. Day 1: choose **Create new**. Days 2 to 5: choose **Reuse settings** and pick the Day 1 '
      'stream. Reuse copies everything, so on every field below **replace** what was copied '
      '(title, description, thumbnail, tags, date and time).')
    w('5. **Details** step: paste Title and Description; **Upload thumbnail** → the day\'s `day-N.jpg` from '
      'this folder; Playlists → tick `Chidagni 2026`; Audience → *No, it\'s not made for kids*. '
      'Click **Show more**: paste Tags; Language and captions certification → Video language **Tamil** (English if the evening\'s speaker uses English), Title and description language **English**, Captions certification None; '
      '**Allow embedding: ON** (the event page embeds the stream; without it the page shows an error); '
      f'Category → **{CATEGORY[0]}**.')
    w('6. **Customization** step: Live chat ON, Live chat replay ON, Participants mode *Anyone*, '
      'Slow mode ON (30 seconds), Reactions ON.')
    w('7. **Visibility** step: **Public**. Under *Schedule*, set the date and the start time from the '
      'table above. Check the time zone next to the time says **India Standard Time (GMT+05:30)**; '
      'if the account is set to another zone, change it there. Click **Done**.')
    w('8. The stream opens in the Live Control Room. On the **Stream settings** tab: Stream key → '
      '`Chidagni 2026`; **Enable DVR ON**; **Auto-start OFF**; **Auto-stop OFF**; Stream latency '
      '**Normal**; 360 off; Unlist live replay once stream ends OFF.')
    w('9. Click **Share** (arrow icon, top right) → copy the link. Keep it for the list below.')
    w('')
    w('### Why these settings')
    w('')
    w(f'- **Start {LEAD_MIN} minutes before the first item.** The event page mounts each evening\'s embed '
      '25 minutes before the first item, so viewers first see YouTube\'s *upcoming* card with the custom '
      f'thumbnail, then the stream goes live {LEAD_MIN} minutes early with the hall settling in.')
    w('- **Auto-start OFF.** All five streams share one key. With auto-start on, YouTube warns about '
      '"multiple streams using the same stream key" and the feed can land on the wrong day\'s stream '
      '(a different URL from the one on the page). With it off, the technician opens *that evening\'s* '
      'stream in Manage, starts the encoder, sees the preview, and clicks **Go live** at the scheduled time.')
    w('- **Auto-stop OFF.** Venue internet drops for a few seconds are common. With auto-stop on, a drop '
      'can end the broadcast, and an ended broadcast cannot restart on the same URL. With it off, the '
      'stream waits for the encoder to reconnect. The technician clicks **End stream** after the last item.')
    w('- **DVR ON** so late joiners can rewind to the start of the lecture. **Normal latency** gives '
      'the steadiest picture for viewers on mobile data; chat does not need low latency.')
    w(f'- **Category {CATEGORY[0]}.** Every evening has music at its core (Carnatic vocal and violin '
      'concerts, namasankirtanam, a harikatha with violin and mridangam), and Music is where YouTube '
      'surfaces Carnatic content. The category only affects discovery, not any stream feature; '
      '*Nonprofits & Activism* is the alternative if the channel prefers it.')
    w('- **Live chat ON with slow mode.** Diaspora viewers like to send pranams; slow mode keeps it calm. '
      'If nobody can watch the chat during the evening, switch Live chat OFF in the Customization step.')
    w('- **Language.** Titles and descriptions are English (the audience includes the diaspora); the '
      'talks, harikatha and namasankirtanam are most likely in Tamil, so the video (audio) language is '
      'Tamil. Confirm with the organisers if a speaker lectures in English.')
    w('- **If Zoom is the encoder:** in Zoom use *More → Live on Custom Live Streaming Service* with server '
      '`rtmp://live.restream.io/live` and that day\'s Restream key (technician sheet), and the day\'s watch URL as '
      'the *Live streaming page URL*. Do **not** use Zoom\'s one-click *Live on YouTube*: it creates a brand new '
      'broadcast with a different URL, which the event page does not know about.')
    w('')
    w('## After scheduling')
    w('')
    w('Copy each stream\'s watch URL, in the form `https://www.youtube.com/watch?v=XXXXXXXXXXX` or '
      '`https://youtube.com/live/XXXXXXXXXXX`, and **send the five links**, labelled by day. Each link goes '
      'into `STREAMS` in `assets/js/main.js` as is (any YouTube link form works), keyed by date:')
    w('')
    w('```js')
    w('var STREAMS = {')
    for b in bs:
        what = b['title'].split(SEP, 2)[2]
        w(f"  '{b['date']}': '',   // Day {b['day']}: {what}")
    w('};')
    w('```')
    w('')
    w('Scheduled streams can be re-timed or re-titled later without changing the URL. Deleting and '
      're-creating one does change it, so edit rather than delete.')
    w('')
    for b in bs:
        st = datetime.fromisoformat(b['scheduledStartTime'])
        w(f"## Day {b['day']}: {b['weekdayDate']}")
        w('')
        w(f"- **Scheduled start:** {b['weekdayDate']} 2026, **{clock(st)} IST** (`{b['scheduledStartTime']}`)")
        w(f"- **Thumbnail:** `{b['thumbnail']}`")
        w(f"- **Category:** {b['categoryName']} · **Visibility:** Public · **Made for kids:** No · "
          f"**Playlist:** {b['playlist']}")
        w(f"- **Ingest:** that day's Restream event · **DVR:** on · **Auto-start:** off · **Auto-stop:** off · "
          f"**Latency:** normal · **Allow embedding:** on · **Live chat:** on, slow mode 30 s")
        w(f"- **Key for STREAMS:** `'{b['date']}'`")
        w('')
        w(f"**Title** ({len(b['title'])}/100)")
        w('')
        w(fence(b['title']))
        w('')
        w(f"**Description** ({len(b['description'])}/5000)")
        w('')
        w(fence(b['description']))
        w('')
        w(f"**Tags** (paste as one line; {tags_len(b['tags'])}/500)")
        w('')
        w(fence(', '.join(b['tags'])))
        w('')
        w('**After the stream: chapters.** Offsets below assume the stream went live on time; correct them '
          'against the replay, then replace the "Chapters: ..." line in the description with this block '
          '(YouTube needs the first line at 00:00 and at least three entries).')
        w('')
        w(fence(b['chapterTemplate']))
        w('')
    return '\n'.join(L)


if __name__ == '__main__':
    bs = build()
    (HERE / 'broadcasts.json').write_text(json.dumps(
        {'channel': 'https://www.youtube.com/@svmf5987', 'timezone': 'Asia/Kolkata',
         'leadMinutes': LEAD_MIN, 'broadcasts': bs}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (HERE / 'BROADCASTS.md').write_text(markdown(bs) + '\n', encoding='utf-8')
    for b in bs:
        print(f"  day {b['day']}  {b['scheduledStartTime']}  {len(b['title']):3d}  {b['title']}")
    print('  wrote broadcasts.json, BROADCASTS.md')

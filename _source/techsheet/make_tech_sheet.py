"""
The printed sheet for the person running the live stream, one box per evening.
Same layout as the Sri Krishna Utsavam 2026 sheet.

    pip install reportlab
    python _source/techsheet/make_tech_sheet.py tech-sheet.local.json Chidagni-2026-tech-sheet.pdf

The JSON holds live stream keys: keep it as *.local.json (git-ignored) and never
commit it or the PDF. Start from tech-sheet.example.json.
"""
import json
import sys
from xml.sax.saxutils import escape as x

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

data = json.load(open(sys.argv[1], encoding='utf-8'))
missing = [f"day {d['n']}: {k}" for d in data['days'] for k, v in d.items() if v == 'REPLACE_ME']
if missing:
    sys.exit('Fill these first: ' + ', '.join(missing))

INK, BAND, EDGE = colors.HexColor('#2B1F66'), colors.HexColor('#ECEAF8'), colors.HexColor('#A9A3DA')
base = ParagraphStyle('b', fontName='Helvetica', fontSize=8.9, leading=11.3)
bold = ParagraphStyle('h', parent=base, fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=INK)
title = ParagraphStyle('t', parent=base, fontName='Helvetica-Bold', fontSize=16, leading=20, alignment=1)
small = ParagraphStyle('s', parent=base, fontSize=8.4, leading=10.8)
mono = lambda s: f'<font face="Courier">{x(s)}</font>'

story = [Paragraph(x(data['title']), title), Spacer(1, 3),
         Paragraph(x(data['subtitle']), small)]
line = f"YouTube channel: <b>{x(data['channel'])}</b> · Channel ID: {mono(data['channel_id'])}"
if data.get('facebook'):
    line += f" · Facebook: <b>{x(data['facebook'])}</b> (goes live automatically when the stream starts)"
story += [Paragraph(line, small),
          Paragraph('Website player: ' + mono(data['website_player']), small), Spacer(1, 6)]

for d in data['days']:
    vid = d['video_id']
    rows = [[Paragraph(f"Day {d['n']} — {x(d['date'])} — go live {x(d['go_live'])} IST", bold)],
            [Paragraph('<b>Programme:</b> ' + x(d['programme']), base)],
            [Paragraph('<b>YouTube watch URL:</b> ' + mono('https://www.youtube.com/watch?v=' + vid) +
                       '&nbsp;&nbsp;<b>Video ID:</b> ' + mono(vid) +
                       ('<br/><i>Careful: this video ID starts with a hyphen — select the whole ID when copying.</i>'
                        if vid.startswith('-') else ''), base)],
            [Paragraph('<b>Restream event page:</b> ' + mono(d['restream_event']), base)],
            [Paragraph('<b>RTMP URL:</b> ' + mono(data['rtmp_url']), base)],
            [Paragraph('<b>Stream key:</b> ' + mono(d['stream_key']), base)]]
    t = Table(rows, colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.6, EDGE), ('LINEBELOW', (0, 0), (-1, 0), 0.6, EDGE),
        ('BACKGROUND', (0, 0), (-1, 0), BAND),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 2.1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.1)]))
    story += [KeepTogether(t), Spacer(1, 3.5)]

zoom = 'https://us02web.zoom.us/j/87692135267?pwd=UmNlTGhVVkhBdHpMM05aWkNSUXRwZz09'
story += [KeepTogether([
    Paragraph('<b>Zoom (same link all days):</b> ' + mono(zoom) +
              '<br/>Meeting ID: <b>876 9213 5267</b>&nbsp;&nbsp;|&nbsp;&nbsp;Meeting password: <b>Krishna</b>', small),
    Spacer(1, 4),
    Paragraph('<b>How to stream:</b> Preferred — in OBS go to Settings &gt; Stream, choose Service: <b>Restream.io</b>, '
              "sign in, and select that day's event; no key needed. Manual fallback — Service: Custom, use the RTMP URL "
              "and that day's stream key above. Each day has its OWN key: double-check you are on the right day before "
              'going live. Starting a little earlier or later than the go-live time is fine — the YouTube link never '
              'changes. After going live, open the website player and check the stream is playing there. '
              '<b>This sheet contains live credentials — do not photograph, share, or leave it at the venue.</b>', small),
    Spacer(1, 4),
    Paragraph('<b>Zoom audio — must be checked every day:</b> the audio setting needs to be '
              '<b>"Original sound for musicians"</b>. In Zoom: Settings &gt; Audio &gt; Audio profile &gt; select '
              '<b>Original sound for musicians</b>, then in the meeting confirm the "Original sound for musicians: On" '
              'indicator at the top-left of the Zoom window before the programme starts.', small),
])]

SimpleDocTemplate(sys.argv[2], pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                  topMargin=9 * mm, bottomMargin=8 * mm,
                  title=data['title'], author='SVMF').build(story)
print('wrote', sys.argv[2])

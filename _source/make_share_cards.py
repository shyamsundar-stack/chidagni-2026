"""
Square share cards, one per billed session, for forwarding on WhatsApp.

    pip install pillow fonttools brotli
    python _source/make_share_cards.py              # writes assets/img/cards/<slug>.jpg
    python _source/make_share_cards.py sheet.png    # also writes a contact sheet

Same family as the YouTube thumbnails (_source/youtube/make_thumbnails.py), whose
font and text helpers this imports: the cover fire (fire.webp), the wordmark lockup,
a red day pill, an orange "TIME · KIND" label and a big white name. 1080 x 1080,
progressive JPEG, each under 250 KB. A card is usually seen about 360 px wide in a
chat, so nothing that matters is set smaller than ~30 px here (~10 px there), and
names and times are far larger. Line-ups mirror the schedule in index.html; if a
name or time changes there, change it here and re-run.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'youtube'))
from make_thumbnails import (BAR_RED, EMBER, FLAME, IMG, IVORY, ROOT,  # noqa: E402
                             draw_tracked, fit, font, mulish, shadowed, text_w)

OUT = ROOT / 'assets' / 'img' / 'cards'
S = 1080                                   # square
M = 72                                     # outer margin
COL = S - 2 * M                            # text column
WHITE = (255, 255, 255)
MAX_KB = 250

VENUE = 'Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, Mylapore, Chennai'
WELCOME = 'All are welcome'
LIVE = 'live.svmf.in/chidagni'

DAY = {
    1: ('Inauguration', 'Tuesday 6 October'),
    2: ('Day 2', 'Wednesday 7 October'),
    3: ('Day 3', 'Thursday 8 October'),
    4: ('Day 4', 'Friday 9 October'),
    5: ('Day 5', 'Saturday 10 October'),
}

# slug: day, time, kind, honorific (above name) or None, name, topic (below name) or None,
#       accompanists [(instrument, artist)]
SESSIONS = {
    'ritvik': (1, '6:45 pm', 'Carnatic vocal concert', None, 'Vid. Ritvik Y V', None, [
        ('Violin', 'Vid. Parur M K Ananthabalasubramaniam'),
        ('Mridangam', 'Vid. Sriram Srinivasan'),
        ('Ghatam', 'Vid. Ganapathy'),
    ]),
    'priya': (2, '5:30 pm', 'Lecture', None, 'Dr. Priya Ramachandran', 'on “Sita Devi”', []),
    'ganesh': (2, '6:45 pm', 'Namasankirtanam', None, 'Dr. R. Ganesh and Party', None, []),
    'srinivasan': (3, '5:30 pm', 'Lecture', None, 'Prof. K. Srinivasan',
                   'on “Moksha-Pradayini”', []),
    'radha': (3, '6:45 pm', 'Carnatic vocal concert', None, 'Dr. Radha Bhaskar and disciples', None, [
        ('Harmonium', 'Vid. R. Arvindh'),
        ('Mridangam', 'Vid. Aravind Davay'),
    ]),
    'sinddhuja': (4, '6:00 pm', 'Harikatha', 'Kalarathna', 'Vid. U. E. Sinddhuja',
                  'on “Meena Lochani, Paasha Mochani”', [
        ('Violin', 'Thirumarugal Dr. S. Dinesh Kumar'),
        ('Mridangam', 'Vid. S. Anand'),
    ]),
    'narmadha': (5, '6:00 pm', 'Carnatic violin concert',
                 'Kalaimamani · Kalasri · Tantri Gnana Tapasvi', 'Dr. M. Narmadha', None, [
        ('Mridangam', 'Vid. Nagaraj Narayanan'),
        ('Ghatam', 'Vid. J. Ramadas'),
    ]),
}

# The inauguration, 5:00 pm onwards: (role or None, name)
INAUGURATION = [
    (None, 'Welcome and lighting of the lamp'),
    ('Anugraha Bhashanam', 'Swami Shrihariprasad'),
    ('Chief Guest', 'Padma Shri Dr. Nalli Kuppuswami Chetti'),
    ('Address', 'Sri K. N. Ramaswamy'),
    ('Inaugural Address', 'Sri K. Giridhara Sarma'),
]


def yatra(size):
    return font('yatra-one-400.woff2', size)


def almendra(size):
    return font('almendra-400-italic.woff2', size)


def black(size):
    return mulish(size, 900)


def shrink(text, make, size, max_w, tracking=0):
    while size > 20 and text_w(text, make(size), tracking) > max_w:
        size -= 1
    return make(size), size


def asc(f):
    return f.getmetrics()[0]


# ── background: the cover fire, low and to the right, graded dark behind the type ──
def background():
    fire = Image.open(IMG / 'fire.webp').convert('RGB')
    s = S * 1.25 / fire.height
    big = fire.resize((round(fire.width * s), round(fire.height * s)), Image.LANCZOS)
    fx = round(585 * s)                                   # the flame's centre in the photo
    x0 = max(0, min(big.width - S, fx - round(S * 0.62)))  # flame sits right of centre
    y0 = big.height - S - round(0.02 * big.height)
    bg = big.crop((x0, y0, x0 + S, y0 + S)).filter(ImageFilter.GaussianBlur(1.4)).convert('RGBA')

    shade = Image.new('RGBA', (S, S))
    px = shade.load()
    for x in range(S):
        t = x / S
        horiz = 0.90 - 0.62 * max(0.0, (t - 0.30) / 0.70) ** 0.9
        for y in range(S):
            u = y / S
            top = 0.35 * max(0.0, 1 - u / 0.40)
            foot = 0.55 * max(0.0, (u - 0.80) / 0.20)
            a = min(1.0, horiz + top + foot)
            px[x, y] = (*EMBER, round(255 * a))
    bg.alpha_composite(shade)

    glow = Image.new('RGBA', (S, S))
    ImageDraw.Draw(glow).ellipse((S - 520, S - 640, S + 160, S - 40), fill=(*FLAME, 60))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    return bg


def header(im, badge, date):
    """Wordmark top left, then the red pill and the date. Returns the y below them."""
    wm = fit(Image.open(IMG / 'wordmark.webp').convert('RGBA'), max_w=460)
    wx, wy = M - 8, 40
    mask = Image.new('L', im.size)
    mask.paste(wm.getchannel('A'), (wx, wy))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(12)).point(lambda v: v * 0.8))
    im.alpha_composite(shadow)
    im.alpha_composite(wm, (wx, wy))
    y = wy + wm.height + 24

    fb, fd = yatra(56), mulish(52, 800)
    pad_x, bh = 24, 78
    bw = round(fb.getlength(badge)) + 2 * pad_x
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((M, y, M + bw, y + bh), 12, fill=(*BAR_RED, 255))
    d.text((M + pad_x, y + bh // 2 + 3), badge, font=fb, fill=IVORY, anchor='lm')
    shadowed(im, lambda dd, c: dd.text((M + bw + 24, y + bh // 2), date, font=fd,
                                       fill=c or IVORY, anchor='lm'), blur=8)
    return y + bh


def footer(im):
    """Dark strip along the foot: venue, welcome, the live link; then the red rule."""
    fh = 150
    top = S - fh
    strip = Image.new('RGBA', (S, fh), (*EMBER, 215))
    im.alpha_composite(strip, (0, top))
    d = ImageDraw.Draw(im)
    d.rectangle((0, top, S, top + 3), fill=(*BAR_RED, 255))
    fv, _ = shrink(VENUE, lambda s: mulish(s, 700), 34, COL)
    d.text((M, top + 54), VENUE, font=fv, fill=IVORY, anchor='ls')
    fw = mulish(34, 800)
    d.text((M, top + 104), WELCOME, font=fw, fill=IVORY, anchor='ls')
    lab, fl, fu = 'Watch live: ', mulish(34, 700), mulish(34, 900)
    xr = S - M
    d.text((xr, top + 104), LIVE, font=fu, fill=FLAME, anchor='rs')
    d.text((xr - fu.getlength(LIVE), top + 104), lab, font=fl, fill=IVORY, anchor='rs')
    d.rectangle((0, S - 14, S, S), fill=(*EMBER, 255))
    d.rectangle((0, S - 10, S, S - 4), fill=(*BAR_RED, 255))
    return top


def wrap_name(name, max_w, hi=130, one_line_min=104):
    """Name on one line if it holds at a big size, else two balanced lines."""
    f1, s1 = shrink(name, black, hi, max_w)
    if s1 >= one_line_min:
        return [name], f1
    words = name.split()
    best = None
    for i in range(1, len(words)):
        if words[i - 1].endswith('.'):                  # never break after "Vid." / "Prof. K."
            continue
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        f, s = shrink(max(a, b, key=lambda t: black(100).getlength(t)), black, hi, max_w)
        if best is None or s > best[0]:
            best = (s, [a, b], f)
    if best is None or best[0] <= s1:
        return [name], f1
    return best[1], best[2]


# ── one session card ──────────────────────────────────────────────────
def card(day, time, kind, hon, name, topic, team, bg):
    im = bg.copy()
    badge, date = DAY[day]
    y0 = header(im, badge, date)
    y1 = footer(im) - 26

    label = f'{time.upper()}  ·  {kind.upper()}'
    fk, _ = shrink(label, black, 50, COL, tracking=2)
    fh = shrink(hon, almendra, 50, COL)[0] if hon else None
    ft = shrink(topic, almendra, 62, COL)[0] if topic else None
    fi = black(26)
    room = y1 - y0 - 20
    for hi in range(130, 83, -4):                        # biggest name that leaves room
        lines, fn = wrap_name(name, COL, hi=hi)
        lead = round(asc(fn) * 1.02)
        parts = [('label', asc(fk))]
        if hon:
            parts.append(('hon', 18 + asc(fh)))
        parts.append(('name', (20 if hon else 22) + asc(fn) + lead * (len(lines) - 1)))
        if topic:
            parts.append(('topic', 26 + asc(ft)))
        if team:
            parts.append(('team', 40 + 50 * len(team) - 16))
        total = sum(h for _, h in parts) + fn.getmetrics()[1] // 3
        if total <= room:
            break
    else:
        raise SystemExit(f'{name}: layout overflows by {total - room}px')
    room += 20
    y = y0 + (room - total) // 2 + 6

    for kind_, h in parts:
        y += h
        if kind_ == 'label':
            yy = y
            shadowed(im, lambda dd, c: draw_tracked(dd, (M, yy), label, fk, c or FLAME, 2), blur=6)
        elif kind_ == 'hon':
            yy = y
            shadowed(im, lambda dd, c: dd.text((M, yy), hon, font=fh, fill=c or IVORY, anchor='ls'),
                     blur=8)
        elif kind_ == 'name':
            base = y - lead * (len(lines) - 1)
            for i, ln in enumerate(lines):
                yy = base + i * lead
                shadowed(im, lambda dd, c: dd.text((M - 4, yy), ln, font=fn, fill=c or WHITE,
                                                   anchor='ls'), blur=12)
        elif kind_ == 'topic':
            yy = y
            shadowed(im, lambda dd, c: dd.text((M, yy), topic, font=ft, fill=c or IVORY, anchor='ls'),
                     blur=8)
        elif kind_ == 'team':
            yy = y - h + 40 + 34
            iw = max(fi.getlength(i.upper()) + 2 * (len(i) - 1) for i, _ in team) + 22
            for inst, who in team:
                yl = yy
                fw, _ = shrink(who, lambda s: mulish(s, 700), 34, COL - iw)
                shadowed(im, lambda dd, c: (
                    draw_tracked(dd, (M, yl), inst.upper(), fi, c or FLAME, 2),
                    dd.text((M + iw, yl), who, font=fw, fill=c or IVORY, anchor='ls')), blur=6)
                yy += 50
    return im.convert('RGB')


# ── the inauguration card ─────────────────────────────────────────────
def inauguration(bg):
    im = bg.copy()
    y0 = header(im, '5:00 pm', 'Tuesday 6 October')
    y1 = footer(im) - 14
    fH = yatra(104)
    fr, fn = black(30), mulish(46, 900)
    fwel = almendra(46)
    gap = 20
    rows = []
    for role, who in INAUGURATION:
        if role is None:
            rows.append(('wel', who, asc(fwel)))
        else:
            fw, _ = shrink(who, lambda s: mulish(s, 900), 46, COL)
            rows.append((role, (who, fw), asc(fr) + 8 + asc(fw)))
    total = asc(fH) + 18 + sum(r[2] for r in rows) + gap * len(rows)
    room = y1 - y0
    if total > room:
        raise SystemExit(f'inauguration: layout overflows by {total - room}px')
    y = y0 + (room - total) // 2 + asc(fH) + 4
    yy = y
    shadowed(im, lambda dd, c: dd.text((M - 4, yy), 'Inauguration', font=fH, fill=c or WHITE,
                                       anchor='ls'), blur=12)
    y += 18
    for role, who, h in rows:
        y += gap
        if role == 'wel':
            yy = y + h
            shadowed(im, lambda dd, c: dd.text((M, yy), who, font=fwel, fill=c or IVORY, anchor='ls'),
                     blur=8)
        else:
            name, fw = who
            yr, yn = y + asc(fr), y + h
            shadowed(im, lambda dd, c: (
                draw_tracked(dd, (M, yr), role.upper(), fr, c or FLAME, 2),
                dd.text((M, yn), name, font=fw, fill=c or WHITE, anchor='ls')), blur=8)
        y += h
    return im.convert('RGB')


def save(im, path):
    for q in (88, 86, 84, 82, 80, 78, 76):
        im.save(path, 'JPEG', quality=q, optimize=True, progressive=True, subsampling=0)
        kb = path.stat().st_size / 1024
        if kb < MAX_KB:
            break
    else:
        for q in (86, 82, 78):
            im.save(path, 'JPEG', quality=q, optimize=True, progressive=True, subsampling=2)
            kb = path.stat().st_size / 1024
            if kb < MAX_KB:
                break
    assert kb < MAX_KB, f'{path.name} is {kb:.0f} KB'
    print(f'  {path.name}  {im.width}x{im.height}  q{q}  {kb:.0f} KB')


def contact_sheet(cards, out):
    """Each card at 540 px beside its 360 px downscale (a phone chat bubble)."""
    gap = 24
    cols = 2
    cw = 540 + 360 + 3 * gap
    rows = (len(cards) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw, rows * (540 + gap) + gap), (40, 40, 40))
    for i, c in enumerate(cards):
        x = (i % cols) * cw + gap
        y = gap + (i // cols) * (540 + gap)
        sheet.paste(c.resize((540, 540), Image.LANCZOS), (x, y))
        sheet.paste(c.resize((360, 360), Image.LANCZOS), (x + 540 + gap, y))
    sheet.save(out)
    print(f'  contact sheet  {out}')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    bg = background()
    made = []
    im = inauguration(bg)
    save(im, OUT / 'inauguration.jpg')
    made.append(im)
    for slug, spec in SESSIONS.items():
        im = card(*spec, bg)
        save(im, OUT / f'{slug}.jpg')
        made.append(im)
    if len(sys.argv) > 1:
        contact_sheet(made, Path(sys.argv[1]))

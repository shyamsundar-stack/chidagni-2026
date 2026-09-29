"""
YouTube custom thumbnails for the five Chidagni 2026 live streams.

    pip install pillow fonttools brotli
    python _source/youtube/make_thumbnails.py            # writes day-1.jpg ... day-5.jpg here
    python _source/youtube/make_thumbnails.py sheet.png  # also writes a contact sheet

Everything comes from the site's own assets: the cover photograph (fire.webp), the
wordmark lockup (wordmark.webp) and the self-hosted woff2 fonts, loaded into PIL the
same way _source/extract_assets.py does. Nothing is drawn by hand. 1280 x 720, JPEG,
well under YouTube's 2 MB limit. The line-ups below mirror the schedule in index.html;
if a name or time changes there, change it here and re-run.

Layout keeps the bottom-right corner clear, because YouTube lays its LIVE / duration
badge over it.
"""
import io
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
IMG = ROOT / 'assets' / 'img'
FONTS = ROOT / 'assets' / 'fonts'

W, H = 1280, 720
EMBER, RUST, FLAME = (23, 5, 1), (127, 41, 5), (241, 145, 52)
BAR_RED, MAROON, IVORY = (158, 31, 13), (140, 0, 26), (255, 244, 230)
M = 64                                    # outer margin

# day, badge, date line, sessions: (time, kind, name, subtitle or None)
DAYS = [
    (1, 'Inauguration', 'Tuesday 6 October', [
        ('5:00 pm', 'Chief guest', 'Dr. Nalli Kuppuswami Chetti', None),
        ('6:45 pm', 'Carnatic vocal concert', 'Vid. Ritvik Y V', None),
    ]),
    (2, 'Day 2', 'Wednesday 7 October', [
        ('5:30 pm', 'Lecture on “Sita Devi”', 'Dr. Priya Ramachandran', None),
        ('6:45 pm', 'Namasankirtanam', 'Dr. R. Ganesh & Party', None),
    ]),
    (3, 'Day 3', 'Thursday 8 October', [
        ('5:30 pm', 'Lecture on “Moksha-Pradayini”', 'Prof. K. Srinivasan', None),
        ('6:45 pm', 'Carnatic vocal concert', 'Dr. Radha Bhaskar & disciples', None),
    ]),
    (4, 'Day 4', 'Friday 9 October', [
        ('6:00 pm', 'Harikatha', 'Vid. U. E. Sinddhuja', '“Meena Lochani, Paasha Mochani”'),
    ]),
    (5, 'Day 5', 'Saturday 10 October', [
        ('6:00 pm', 'Carnatic violin concert', 'Dr. M. Narmadha',
         'Kalaimamani \u00b7 Kalasri \u00b7 Tantri Gnana Tapasvi'),
    ]),
]


# ── helpers ────────────────────────────────────────────────────────────
_font_bytes = {}


def font(woff2, size, weight=None):
    """A woff2 from assets/fonts as a PIL font (decompressed to TTF in memory)."""
    if woff2 not in _font_bytes:
        t = TTFont(FONTS / woff2)
        t.flavor = None
        buf = io.BytesIO()
        t.save(buf)
        _font_bytes[woff2] = buf.getvalue()
    f = ImageFont.truetype(io.BytesIO(_font_bytes[woff2]), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


def mulish(size, weight):
    return font('mulish-var.woff2', size, weight)


def fit(im, max_w=None, max_h=None):
    s = min((max_w or 1e9) / im.width, (max_h or 1e9) / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def fit_font(text, make, size, max_w, min_size=40, tracking=0):
    """Largest size <= size at which text fits max_w."""
    while size > min_size and text_w(text, make(size), tracking) > max_w:
        size -= 2
    return make(size)


def text_w(text, f, tracking=0):
    return f.getlength(text) + tracking * max(len(text) - 1, 0)


def draw_tracked(d, xy, text, f, fill, tracking=0, anchor='ls'):
    if not tracking:
        d.text(xy, text, font=f, fill=fill, anchor=anchor)
        return
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor=anchor)
        x += f.getlength(ch) + tracking


def shadowed(base, painter, blur=10, alpha=235, spread=2):
    """Paint text twice: a blurred ember shadow under it, then the text itself."""
    sh = Image.new('RGBA', base.size)
    painter(ImageDraw.Draw(sh), (0, 0, 0, alpha))
    if spread:
        sh = sh.filter(ImageFilter.MaxFilter(spread * 2 + 1))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh)
    painter(ImageDraw.Draw(base), None)


# ── background: the cover fire, pushed right and graded dark on the left ──
def background():
    fire = Image.open(IMG / 'fire.webp').convert('RGB')
    s = 1.8
    big = fire.resize((round(fire.width * s), round(fire.height * s)), Image.LANCZOS)
    fx = big.width // 2                                  # the fire sits mid-photo
    x0 = max(0, min(big.width - W, fx - 1000))            # move it towards the right
    y0 = big.height - H - 40
    bg = big.crop((x0, y0, x0 + W, y0 + H)).filter(ImageFilter.GaussianBlur(1.2)).convert('RGBA')

    shade = Image.new('RGBA', (W, H))
    px = shade.load()
    for x in range(W):
        t = x / W                                        # 0 at left edge, 1 at right
        horiz = 0.92 - 0.74 * max(0.0, (t - 0.42) / 0.58) ** 0.8
        for y in range(H):
            u = y / H
            top = 0.25 * max(0.0, 1 - u / 0.35)          # a little extra dark at the very top
            a = min(1.0, horiz + top)
            px[x, y] = (*EMBER, round(255 * a))
    bg.alpha_composite(shade)

    # warm the fire a touch so it reads as flame, not orange mush, at small sizes
    glow = Image.new('RGBA', (W, H))
    ImageDraw.Draw(glow).ellipse((W - 470, H - 470, W + 170, H + 110), fill=(*FLAME, 70))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(110)))

    # black-red-black bar along the foot, as on the invitation
    d = ImageDraw.Draw(bg)
    d.rectangle((0, H - 14, W, H), fill=(*EMBER, 255))
    d.rectangle((0, H - 10, W, H - 4), fill=(*BAR_RED, 255))
    return bg


# ── one thumbnail ─────────────────────────────────────────────────────
def thumbnail(n, badge, date, sessions, bg):
    im = bg.copy()
    col = W - 2 * M - 40                                 # usable text width

    # wordmark, top left, with a soft shadow so it holds over the glow
    wm = fit(Image.open(IMG / 'wordmark.webp').convert('RGBA'), max_w=440)
    wx, wy = M - 6, 32
    mask = Image.new('L', im.size)
    mask.paste(wm.getchannel('A'), (wx, wy))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(12)).point(lambda v: v * 0.8))
    im.alpha_composite(shadow)
    im.alpha_composite(wm, (wx, wy))
    y = wy + wm.height + 26

    # day badge: red pill with the day in Yatra One, then the date in Mulish
    fb = font('yatra-one-400.woff2', 50)
    fd = mulish(46, 800)
    pad_x, bh = 22, 70
    bw = round(fb.getlength(badge)) + 2 * pad_x
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((M, y, M + bw, y + bh), 10, fill=(*BAR_RED, 255))
    d.text((M + pad_x, y + bh // 2 + 3), badge, font=fb, fill=IVORY, anchor='lm')
    shadowed(im, lambda dd, c: dd.text((M + bw + 22, y + bh // 2), date, font=fd,
                                       fill=c or IVORY, anchor='lm'), blur=8)
    y += bh

    # session blocks: small flame-coloured "TIME · KIND" over a big white name
    single = len(sessions) == 1
    name_size = 108 if single else 80
    kind_size = 44 if single else 38
    gap = 34
    blocks = []
    for time, kind, name, sub in sessions:
        label = f'{time.upper()}  \u00b7  {kind.upper()}'
        fk = fit_font(label, lambda s: mulish(s, 900), kind_size, col, 24, tracking=2)
        fn = fit_font(name, lambda s: mulish(s, 900), name_size, col, 52)
        fs = fit_font(sub, lambda s: font('almendra-400-italic.woff2', s), 60, col, 36) if sub else None
        h = fk.getmetrics()[0] + 12 + round(fn.getmetrics()[0] * 0.92) + fn.getmetrics()[1] // 2
        if sub:
            h += 16 + sum(fs.getmetrics())
        blocks.append((label, fk, name, fn, sub, fs, h))
    total = sum(b[-1] for b in blocks) + gap * (len(blocks) - 1)
    room = (H - 34) - y
    if total > room:
        raise SystemExit(f'day {n}: layout overflows by {total - room}px')
    y += (room - total) // 2                             # centre the line-up in the space left

    for label, fk, name, fn, sub, fs, h in blocks:
        yk = y + fk.getmetrics()[0]
        shadowed(im, lambda dd, c: draw_tracked(dd, (M, yk), label, fk, c or FLAME, 2), blur=6)
        yn = yk + 12 + round(fn.getmetrics()[0] * 0.92)
        shadowed(im, lambda dd, c: dd.text((M - 3, yn), name, font=fn, fill=c or (255, 255, 255),
                                           anchor='ls'), blur=12)
        if sub:
            ys = yn + fn.getmetrics()[1] // 2 + 16 + fs.getmetrics()[0]
            shadowed(im, lambda dd, c: dd.text((M, ys), sub, font=fs, fill=c or IVORY, anchor='ls'),
                     blur=8)
        y += h + gap
    return im.convert('RGB')


def save(im, path):
    im.save(path, 'JPEG', quality=88, optimize=True, progressive=True, subsampling=0)
    kb = path.stat().st_size / 1024
    assert kb < 2048, f'{path.name} is {kb:.0f} KB, over the 2 MB YouTube limit'
    print(f'  {path.name}  {im.width}x{im.height}  {kb:.0f} KB')


def contact_sheet(thumbs, out):
    """Full-size thumbnails beside their 320 x 180 downscales (how most people see them)."""
    small = [t.resize((320, 180), Image.LANCZOS) for t in thumbs]
    half = [t.resize((640, 360), Image.LANCZOS) for t in thumbs]
    gap = 24
    sheet = Image.new('RGB', (640 + 320 + 3 * gap, len(thumbs) * (360 + gap) + gap), (40, 40, 40))
    for i, (h, s) in enumerate(zip(half, small)):
        y = gap + i * (360 + gap)
        sheet.paste(h, (gap, y))
        sheet.paste(s, (640 + 2 * gap, y))
    sheet.save(out)
    print(f'  contact sheet  {out}')


if __name__ == '__main__':
    print('thumbnails')
    bg = background()
    thumbs = []
    for n, badge, date, sessions in DAYS:
        im = thumbnail(n, badge, date, sessions, bg)
        save(im, HERE / f'day-{n}.jpg')
        thumbs.append(im)
    if len(sys.argv) > 1:
        contact_sheet(thumbs, Path(sys.argv[1]))

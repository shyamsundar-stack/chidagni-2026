"""
Pull every asset the site uses out of the Canva invitation PDF.

    pip install pymupdf pillow fonttools brotli
    python _source/extract_assets.py path/to/Chidagni-2026.pdf

Run from anywhere; it writes into assets/img/ next to this folder. Re-run it
whenever the client sends a new proof: every image, ornament and poster on the
page comes from here, so nothing is redrawn by hand. Boxes are PDF points on
the 297.75 x 419.25 pt Canva pages, read with page.get_image_info().

The folder starts with an underscore so GitHub Pages (Jekyll) does not publish it.
"""
import io
import sys
from pathlib import Path

import pymupdf
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'assets' / 'img'
POST = IMG / 'posters'
FONTS = ROOT / 'assets' / 'fonts'
POST.mkdir(parents=True, exist_ok=True)

pdf = pymupdf.open(sys.argv[1])
cover, sched1, sched2 = pdf[0], pdf[1], pdf[2]


# ── helpers ────────────────────────────────────────────────────────────
def xref_rgba(xref):
    """An embedded image with its soft mask applied, as a PIL RGBA image."""
    smask = next((i[1] for p in pdf for i in p.get_images(full=True) if i[0] == xref), 0)
    pix = pymupdf.Pixmap(pdf, xref)
    if pix.colorspace and pix.colorspace.n > 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    if smask:
        pix = pymupdf.Pixmap(pix, pymupdf.Pixmap(pdf, smask))
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA')


def trim(im, pad=0):
    l, t, r, b = im.getchannel('A').getbbox()
    return im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height)))


def fit(im, max_w=None, max_h=None):
    s = min((max_w or 1e9) / im.width, (max_h or 1e9) / im.height, 1)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS) if s < 1 else im


def webp(im, name, q=82):
    im.save(IMG / f'{name}.webp', 'WEBP', quality=q, method=6)
    print(f'  {name}.webp  {im.width}x{im.height}')


def drawing_svg(page, pick, pad=0.5):
    """Vector paths from the PDF as a standalone SVG, cropped to their bounds."""
    paths, box = [], None
    for dr in page.get_drawings():
        if not pick(dr):
            continue
        d, pen = [], None
        for it in dr['items']:
            op = it[0]
            if op in ('l', 'c'):
                a = it[1]
                if pen is None or abs(pen.x - a.x) > .01 or abs(pen.y - a.y) > .01:
                    d.append(f'M{a.x:.2f} {a.y:.2f}')
                if op == 'l':
                    d.append(f'L{it[2].x:.2f} {it[2].y:.2f}')
                    pen = it[2]
                else:
                    d.append(f'C{it[2].x:.2f} {it[2].y:.2f} {it[3].x:.2f} {it[3].y:.2f} {it[4].x:.2f} {it[4].y:.2f}')
                    pen = it[4]
            elif op == 're':
                r = it[1]
                d.append(f'M{r.x0:.2f} {r.y0:.2f}H{r.x1:.2f}V{r.y1:.2f}H{r.x0:.2f}Z')
                pen = None
            elif op == 'qu':
                q = it[1]
                d.append(f'M{q.ul.x:.2f} {q.ul.y:.2f}L{q.ur.x:.2f} {q.ur.y:.2f}'
                         f'L{q.lr.x:.2f} {q.lr.y:.2f}L{q.ll.x:.2f} {q.ll.y:.2f}Z')
                pen = None
        fill = '#%02x%02x%02x' % tuple(round(c * 255) for c in dr['fill'])
        rule = 'evenodd' if dr.get('even_odd') else 'nonzero'
        paths.append(f'<path fill="{fill}" fill-rule="{rule}" d="{"".join(d)}"/>')
        box = pymupdf.Rect(dr['rect']) if box is None else box | dr['rect']
    x, y, w, h = box.x0 - pad, box.y0 - pad, box.width + 2 * pad, box.height + 2 * pad
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}" '
            f'width="{w:.2f}" height="{h:.2f}">' + ''.join(paths) + '</svg>'), box


def svg_rgba(svg, width_px):
    page = pymupdf.open(stream=svg.encode(), filetype='svg')[0]
    z = width_px / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=True)
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA')


def filled(rgb):
    return lambda dr: bool(dr.get('fill')) and dr.get('fill_opacity', 1) > 0 and \
        all(abs(a - b) < .01 for a, b in zip(dr['fill'], rgb))


def font(woff2, size, weight=None):
    t = TTFont(FONTS / woff2)
    t.flavor = None
    buf = io.BytesIO()
    t.save(buf)
    buf.seek(0)
    f = ImageFont.truetype(buf, size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


# ── 1. vector ornaments ────────────────────────────────────────────────
print('ornaments')
RED, ORN, FLOURISH = (1, 0, 0), (0.6863, 0, 0), (0.8118, 0.149, 0.1843)

flame_svg, flame_box = drawing_svg(cover, lambda d: filled(RED)(d) and d['rect'].y1 < 60, pad=0)
(IMG / 'flame.svg').write_text(flame_svg)
(IMG / 'key.svg').write_text(drawing_svg(sched1, lambda d: filled(RED)(d) and d['rect'].x0 < 0, pad=0)[0])
(IMG / 'knot.svg').write_text(drawing_svg(
    sched1, lambda d: filled(ORN)(d) and len(d['items']) > 100 and d['rect'].y1 < 60 and d['rect'].x0 < 40)[0])
(IMG / 'flourish.svg').write_text(drawing_svg(sched2, filled(FLOURISH))[0])
print('  flame.svg key.svg knot.svg flourish.svg')

# ── 2. the wordmark lockup: brush lettering + flame dot + "2026" ──────
print('wordmark')
info = {i['xref']: pymupdf.Rect(i['bbox']) for i in cover.get_image_info(xrefs=True)}
WM = info[267]
wm = xref_rgba(267)
k = wm.width / WM.width                                  # px per pt
to_px = lambda x, y: (round((x - WM.x0) * k), round((y - WM.y0) * k))
wm.alpha_composite(svg_rgba(flame_svg, round(flame_box.width * k)), to_px(flame_box.x0, flame_box.y0))
year = next(s for b in cover.get_text('dict')['blocks'] for l in b.get('lines', [])
            for s in l['spans'] if s['text'].strip() == '2026')
ImageDraw.Draw(wm).text(to_px(*year['origin']), '2026', anchor='ls', fill='white',
                        font=font('yatra-one-400.woff2', round(year['size'] * k)))
wm = trim(wm, 6)
webp(wm, 'wordmark', 90)

# ── 3. hero photograph ────────────────────────────────────────────────
print('photography')
fire = xref_rgba(261).convert('RGB')
webp(fire, 'fire', 80)

# ── 4. the three gurus, composed exactly as on the cover ─────────────
order = [i['xref'] for i in cover.get_image_info(xrefs=True) if i['xref'] in (160, 161, 162)]
area = info[160] | info[161] | info[162]
area.y1 = 403.0                                          # where the footer bar starts
S = 4.2                                                  # px per pt
canvas = Image.new('RGBA', (round(area.width * S), round(area.height * S)))
for x in order:
    r = info[x]
    im = xref_rgba(x).resize((round(r.width * S), round(r.height * S)), Image.LANCZOS)
    canvas.alpha_composite(im, (round((r.x0 - area.x0) * S), round((r.y0 - area.y0) * S)))
webp(trim(canvas), 'gurus', 84)

# ── 5. marks and deities ─────────────────────────────────────────────
print('marks and deities')
webp(fit(trim(xref_rgba(153), 4), 600), 'logo-svmf', 90)
webp(fit(trim(xref_rgba(154), 4), 560), 'logo-sgap', 90)
webp(trim(xref_rgba(158), 2), 'logo-bvb', 92)
webp(fit(trim(xref_rgba(182)), max_h=620), 'durga', 84)
webp(fit(trim(xref_rgba(170)), max_h=620), 'lakshmi', 84)
webp(fit(trim(xref_rgba(171)), max_h=620), 'saraswati', 84)

# ── 6. the printed pages, for the share strip ────────────────────────
print('posters')
for page, name in ((cover, 'cover'), (sched1, 'schedule-1'), (sched2, 'schedule-2')):
    z = 900 / page.rect.width
    im = Image.open(io.BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(z, z)).tobytes('png'))).convert('RGB')
    im.save(POST / f'{name}.webp', 'WEBP', quality=80, method=6)
    im.save(POST / f'{name}.jpg', 'JPEG', quality=84, optimize=True, progressive=True)
    print(f'  posters/{name}  {im.width}x{im.height}')

# ── 7. share card (1200 x 630) and favicon ───────────────────────────
# WhatsApp shows og:image either as the full landscape card or, often, as a
# small square cropped from its CENTRE. So everything that matters is a
# stacked, centred lockup kept inside the middle 630 x 630: wordmark, dates,
# venue. The photograph's diyas fill the sides, which the square loses.
# Keep the JPEG well under 300 KB (WhatsApp drops heavier images) and bump
# ?v= on og:image in index.html whenever this card changes.
print('share card and favicon')
W, H = 1200, 630
SQ = (W - H) // 2                                        # the centre square: x SQ .. SQ + H
s = max(W / fire.width, H / fire.height)
card = fire.resize((round(fire.width * s), round(fire.height * s)), Image.LANCZOS)
card = card.crop(((card.width - W) // 2, card.height - H, (card.width - W) // 2 + W, card.height)).convert('RGBA')
shade = Image.new('RGBA', (W, H))
g = ImageDraw.Draw(shade)
for y in range(H):                                       # ember dark at the top, where the wordmark sits
    g.line([(0, y), (W, y)], fill=(16, 4, 3, round(235 * max(0, 1 - y / (H * .62)) ** 1.2)))
card.alpha_composite(shade)
pool = Image.new('RGBA', (W, H))                         # a soft dark pool right behind the lettering
ImageDraw.Draw(pool).ellipse((SQ - 20, -60, SQ + H + 20, 300), fill=(16, 4, 3, 150))
card.alpha_composite(pool.filter(ImageFilter.GaussianBlur(50)))
lock = fit(wm, H - 70, 230)                              # 560 px wide, inside the centre square
card.alpha_composite(lock, ((W - lock.width) // 2, 34))
band = Image.new('RGBA', (W, 240))                       # the cover's red glow under the dates
ImageDraw.Draw(band).rectangle((SQ - 150, 40, SQ + H + 150, 200), fill=(158, 18, 8, 225))
card.alpha_composite(band.filter(ImageFilter.GaussianBlur(26)), (0, H - 250))
text = Image.new('RGBA', (W, H))
d = ImageDraw.Draw(text)
d.text((W // 2, H - 150), '6\u201310 October 2026', font=font('mulish-var.woff2', 60, 900),
       fill='white', anchor='mm')                        # 555 px wide
d.text((W // 2, H - 88), 'Bharatiya Vidya Bhavan, Mylapore, Chennai', font=font('mulish-var.woff2', 25, 700),
       fill=(255, 244, 230), anchor='mm')                # 527 px wide
halo = Image.new('RGBA', (W, H), (16, 4, 3, 0))          # a dark halo so the type holds when shrunk
halo.putalpha(text.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda a: min(255, a * 1.4)))
card.alpha_composite(halo)
card.alpha_composite(text)
card.convert('RGB').save(IMG / 'share.jpg', 'JPEG', quality=88, optimize=True, progressive=True)
print(f"  share.jpg 1200x630  {(IMG / 'share.jpg').stat().st_size // 1024} KB")

fav = Image.new('RGBA', (192, 192))
ImageDraw.Draw(fav).rounded_rectangle((0, 0, 191, 191), 40, fill=(23, 5, 1, 255))
fl = fit(svg_rgba(flame_svg, 600), 140, 150)
fav.alpha_composite(fl, ((192 - fl.width) // 2, (192 - fl.height) // 2))
fav.save(IMG / 'favicon.png', optimize=True)
print('  favicon.png 192x192')

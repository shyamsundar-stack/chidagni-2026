# Chidagni 2026

Landing page for the 16th edition of Chidagni, The Fire of Consciousness Festival,
6 to 10 October 2026 at the Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, Mylapore,
Chennai. Jointly organised by the Sri Vishnu Mohan Foundation, Bharatiya Vidya Bhavan
and Sri Gnana Advaitha Peetam.

**Public link: https://live.svmf.in/chidagni** (the "Event page" link printed in the
invitation; a Switchy redirect to the GitHub Pages site below, with click tracking).
**GitHub Pages: https://shyamsundar-stack.github.io/chidagni-2026/**

Plain HTML, CSS and JavaScript. No build step, no dependencies, no framework. Built the
same way as the Sri Krishna Utsavam 2026 page. Colours, artwork, ornaments and schedule
all come from the printed invitation PDF.

```
index.html
assets/css/fonts.css      self-hosted @font-face rules
assets/css/styles.css
assets/js/main.js
assets/fonts/             Mulish, Almendra and Yatra One, woff2, 67 KB
assets/img/               photograph, wordmark, gurus, Devis, marks, ornaments, share card
assets/img/posters/       the 3 invitation pages
_source/extract_assets.py pulls every image above out of the PDF (not published)
```

## Running it locally

Open `index.html` directly, or serve the folder:

```
python -m http.server 4321
```

## Where the assets came from

Everything in `assets/img/` is lifted out of the Canva PDF by
`_source/extract_assets.py`, not redrawn:

| File | From the invitation |
|---|---|
| `fire.webp` | the cover photograph |
| `wordmark.webp` | the brush lettering, with the vector flame dot on the i and "2026" set in Yatra One at their printed positions |
| `gurus.webp` | the three cut-outs, recomposed exactly as they overlap on the cover |
| `durga`, `lakshmi`, `saraswati` | the Devis along the foot of the schedule pages |
| `logo-*.webp` | the three organisation marks |
| `flame.svg`, `key.svg`, `knot.svg`, `flourish.svg` | the vector ornaments, converted straight from the PDF paths |
| `posters/` | the three pages, rendered at 900 px wide |
| `share.jpg`, `favicon.png` | built from the photograph, wordmark and flame |

When the client sends a new proof, re-run it:

```
pip install pymupdf pillow fonttools brotli
python _source/extract_assets.py path/to/Chidagni-2026.pdf
```

The palette is sampled from the same PDF: ember `#170501` and rust `#7F2905` from the
photograph, flame `#F19134` from the fire, `#9E1F0D` from the black-red-black bar,
maroon `#8C001A` and ornament red `#AF0000` from the schedule pages. Type is Mulish
(the invitation's Muli, renamed on Google Fonts), Yatra One as printed, and Almendra
standing in for Canva's "Codex", which is not licensed for the web.

## The live stream

`assets/js/main.js` has one entry per evening, keyed by the festival date in IST:

```js
var STREAMS = {
  '2026-10-06': '',   // paste the YouTube video id for each evening here
  ...
};
```

Once the technician sends the scheduled broadcast links, paste each video id (the part
after `watch?v=`). The player then mounts that evening's embed by itself, `EARLY_MIN`
minutes before the first item, and the "Open the stream on YouTube" link follows the
current day. **Until an id is in**, a live session shows "Open the Zoom room" and
"Watch on YouTube" buttons in the player instead of an empty frame, so the page works
as it stands.

| State | When | Shown |
|---|---|---|
| soon | before and between sessions | countdown, next session |
| live | during a scheduled session | red "Live now" badge, the embed (or the Zoom and YouTube buttons), that row lit up in the schedule |
| ended | after 10 October | closing message |

## Editing the schedule

The schedule lives **only** in `index.html`. Each session is one `<article class="event">`:

```html
<article class="event event--star"
         data-start="2026-10-07T17:30:00+05:30"
         data-end="2026-10-07T18:45:00+05:30">
```

Those timestamps drive the countdown, the live highlight, the player and the
*Add to calendar* download. There is no second copy of the schedule in the JavaScript.

- `event--star` marks a billed session: tinted card and a calendar button.
- `event--rite` marks a formality such as the lamp lighting or the vote of thanks.
- The visible `<time>` is only a label. Edit it to match `data-start`.
- Keep the `+05:30`. It is what makes the countdown correct for viewers abroad.

## Sharing a poster

Tapping any page in the "Send the invitation" strip opens a share sheet with that page,
a note already written for it, and the ways to send it. On phones it hands the OS share
sheet the **image itself**, so WhatsApp sends the picture, not a bare link. Elsewhere
there are WhatsApp, email, copy and download actions.

The note lives on the button (`data-msg`); the venue line and the closing invitation are
shared by every card and live in `main.js` as `TAIL` and `ASK`. Each poster exists as
`.webp` for the page and `.jpg` for sharing; the JPEG is only fetched when the sheet opens.

## Before the client shares it

The PDF is marked "Proofread". Points to confirm with the organisers:

1. **The gap on Day 1.** The inaugural address is at 5:20 pm and the concert at 6:45 pm,
   with nothing printed in between. The site treats the address as running until 6:45.
2. **"Sinddhuja".** Printed with a double d (Kalarathna Vid. U. E. Sinddhuja). The site
   follows the print; correct it in `index.html` and the share note if it is a typo.
3. **Session end times** are estimates used for the live state and the calendar files
   (75 to 105 minutes per session). Adjust `data-end` if the organisers have timings.
4. **Entry.** The invitation says "All are welcome" and nothing about tickets or
   registration, so the page says the same. If entry is free and unregistered, say so in
   the Visit card and the facts row.
5. **About copy.** The two paragraphs under "The fire of consciousness" are ours: the
   invitation has no prose. The foundation description is reused from the Sri Krishna
   Utsavam page.
6. **YouTube ids.** Fill in `STREAMS` (above) once the broadcasts are scheduled.
7. **Switchy link.** Point `https://live.svmf.in/chidagni` at the GitHub Pages URL above.
8. **Analytics.** No tag is installed. The Krishna Utsavam page used GTM container
   `GTM-5XK8XFPK`; add that snippet (or a new container) to the `<head>` if wanted.

## Notes on the build

- Fonts are self-hosted, so there is no render-blocking third-party request.
- Body text is weight 400 or heavier. Text on paper is near-black `#1B0B08` and maroon
  `#8C001A`; text on ember is ivory `#FFF4E6` and flame `#F19134`, all above WCAG AA.
- Motion is limited to scroll reveals, the countdown and a slow glow on the wordmark,
  and all of it collapses under `prefers-reduced-motion`.
- Calendar files are folded at 75 octets per RFC 5545 and carry the Zoom link.
- A JSON-LD `Festival` block describes the event for search engines.
- **Custom domain.** If you point a domain at this, update the absolute URLs in the
  `<head>` and in the JSON-LD block at the foot of `index.html`.

## Credits

Artwork, photography and the printed invitation are the property of the Sri Vishnu Mohan
Foundation. Map data from OpenStreetMap contributors. Typefaces are Mulish, Almendra and
Yatra One, all SIL Open Font License.

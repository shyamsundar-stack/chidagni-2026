# Chidagni 2026

Landing page for the 16th edition of Chidagni, The Fire of Consciousness Festival,
6 to 10 October 2026 at the Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, Mylapore,
Chennai. Jointly organised by the Sri Vishnu Mohan Foundation, Bharatiya Vidya Bhavan
and Sri Gnana Advaitha Peetam.

**Public link: https://live.svmf.in/chidagni** (the "Event page" link printed in the
invitation; a Switchy redirect to the GitHub Pages site below, with click tracking).
The GitHub Pages address is under Settings, Pages in this repo. Nothing on the page
links to it: every link the page hands out uses live.svmf.in/chidagni.

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
  '2026-10-06': '',   // paste each evening's YouTube link (or bare video id) here
  ...
};
```

Once the broadcasts are scheduled, paste each evening's link as YouTube gives it
(`watch?v=`, `youtu.be/` or `/live/` all work; `main.js` pulls the id out). The player then mounts that evening's embed by itself, `EARLY_MIN`
minutes before the first item, and the "Open the stream on YouTube" link follows the
current day. **Until an id is in**, a live session shows "Open the Zoom room" and
"Watch on YouTube" buttons in the player instead of an empty frame, so the page works
as it stands.

| State | When | Shown |
|---|---|---|
| soon | before and between sessions | countdown, next session |
| live | from `EARLY_MIN` before the day's first item to the end of its last | the player moves to the top of the page under the wordmark, with the embed (or the Zoom and YouTube buttons); red "Live now" badge and that row lit up in the schedule during a session |
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

## Sharing

Two kinds of button open the same share sheet:

- **Share** beside *Add to calendar* on every session: sends that artist's square card
  from `assets/img/cards/` (built by `_source/make_share_cards.py` from the page's own
  photograph, wordmark and fonts) with a note about that session.
- The three printed pages in "Send the invitation": the cover and the two schedule
  pages, each with a note describing what the page covers.

On phones the sheet hands the OS share menu the **image itself**, so WhatsApp sends the
picture, not a bare link. Elsewhere there are WhatsApp, email, copy and download
actions. Each note lives on its button (`data-msg`); the venue line and the closing
invitation are shared and live in `main.js` as `TAIL` and `ASK`.

## Add to calendar

One entry per session, and one for the whole inauguration (lamp to inaugural address,
5:00 to 6:45 pm). The button opens the phone's own calendar with the event filled in:

| Device | What opens |
|---|---|
| Android | Google Calendar's new-event screen (the app, when installed) |
| iPhone, iPad, Mac Safari | `assets/cal/<slug>.ics`, which Safari hands to Calendar |
| Other desktops | a small menu: Google Calendar, or Apple / Outlook (.ics) |

Each entry has a 15-minute reminder (the .ics files; Google uses the person's default)
and the link `live.svmf.in/chidagni?go=calendar.<slug>.yt-<date>`. Tapped from the
reminder, the page records the visit and goes straight on to that evening's YouTube
stream, looked up from `STREAMS` at that moment.

The .ics files are written by `_source/make_calendar.py` (`pip install beautifulsoup4`).
**Re-run it after changing any time or name.** The Google link is built live in
`main.js` (`calEntry`) with the same wording; change both together.

## Tracked links and the debrief

Every link the page hands out is the Switchy link plus a fragment:
`live.svmf.in/chidagni?go=<source>.<item>[.<target>]`. A query parameter, because
Switchy's redirect is a small script that forwards the query string (an incoming
`utm_source` even overrides Switchy's own) but drops any `#fragment`. The page also
still reads `#go=` for links handed out before this change. A small script at the top
of the `<head>` turns it into UTM tags before Tag Manager loads, so
GA4 files each visit under the right source:

| Link | utm_source | utm_medium | utm_content | Lands on |
|---|---|---|---|---|
| Share note from a session card | `share` | `social` | card slug (`ritvik`, `priya`...) | that day |
| Share note from a printed page | `share` | `social` | `cover`, `schedule-1`, `schedule-2` | that day |
| Calendar reminder | `calendar` | `reminder` | session slug | YouTube, that evening's stream |
| The invitation link itself | set in Switchy | set in Switchy | | the page |

All carry `utm_campaign=chidagni2026`. Arrivals also push a `tracked_link_open` event
(`link_source`, `link_item`, `link_target`, `festival_day`, `redirect`: youtube or page).

## Link previews

The Open Graph and Twitter tags near the top of the `<head>` give WhatsApp, Facebook,
Telegram, iMessage and X their preview. `og:url` and `canonical` point at
live.svmf.in/chidagni. The image tags have to name the real host until a custom domain
is set up; set Switchy's own link preview to the same image, title and description.

- `assets/img/share.jpg` (1200 x 630, about 106 KB) is built by section 7 of
  `_source/extract_assets.py`. WhatsApp often shows only a small square cut from the
  **centre** of the image, so the wordmark, dates and venue all sit inside the middle
  630 x 630. Keep the file under 300 KB, or WhatsApp drops the image.
- **To refresh a cached thumbnail**, bump the `?v=` number on the image URL in
  `og:image`, `og:image:secure_url` and `twitter:image` (currently `share.jpg?v=2`).
  For Facebook and WhatsApp, also run the page URL through the
  [Sharing Debugger](https://developers.facebook.com/tools/debug/) and click
  "Scrape Again". Chats that already show the old preview keep it.

## Analytics

Google Tag Manager container **`GTM-5XK8XFPK`**, the one the Sri Krishna Utsavam page
uses (same client, same host; GA4 tells the two sites apart by page path,
`/chidagni-2026/` vs `/sri-krishna-utsavam-2026/`). The snippet sits at the top of the
`<head>` and the `noscript` iframe straight after `<body>`.

`main.js` pushes the events below onto `window.dataLayer` through one `track()` helper
that never throws. Every push lists every parameter, unset ones as `undefined`, so a value
from one event never leaks into the next through GTM's data model.

| Event | When | Parameters |
|---|---|---|
| `live_state` | once per page view, on load | `phase` (before, live, between, ended), `festival_day` (IST date of the visit), `session_title` (when live), `days_to_start` (before only) |
| `cta_click` | any in-page link: nav, hero buttons, logo, the countdown's "Watch the stream", skip link | `label`, `destination` (`#schedule`), `location` |
| `nav_menu_open` | the phone menu is opened | `location` |
| `outbound_click` | Zoom, YouTube, Google Maps, `tel:`, srisathguru.com, svmf.in, OpenStreetMap | `link_type` (zoom, youtube, maps, phone, website), `link_url` (first 100 characters), `link_domain`, `label`, `location` |
| `calendar_add` | an *Add to calendar* choice | `session_title`, `session_kind`, `festival_day`, `session_start` (ISO), `method` (google, ics), `label` (session slug) |
| `share_open` | a card or poster is tapped | `poster_id` (card slug, or cover, schedule-1, schedule-2) |
| `share_method` | a button in the share sheet is tapped | `method` (native, whatsapp, email, copy, download), `poster_id` |
| `share_complete` | the OS share sheet reports success | `method` (native), `poster_id`, `share_payload` (image or link) |
| `stream_mount` | the player mounts the day's embed, or the Zoom and YouTube buttons | `festival_day`, `mode` (embed, fallback), `video_id` |
| `stream_play` | the embed starts playing, once per mount | `festival_day`, `video_id`, `mode` |
| `section_view` | about, schedule, watch, visit or invite is half on screen (or fills half the screen), once each | `section_id` |
| `scroll_depth` | the bottom of the screen passes 25, 50, 75 and 100% of the page, once each | `percent_scrolled` |

`location` is the nearest `data-track-section` (`links_bar`, `player`), else the id of
the enclosing section (`nav`, `home`, `schedule`, `watch`, `visit`, `invite`), else
`footer`. `label` is `data-track-label`, else the link text. One delegated listener
reads every click; a new link is tracked with no code, `data-track="<link_type>"`
overrides the type, and `data-track="none"` opts a link out. `stream_play` uses the
YouTube player's postMessage channel (`enablejsapi=1&origin=` on the embed), which
also lets GTM's built-in YouTube Video trigger work.

Links the page hands out are tagged as described under "Tracked links and the debrief".

### What the container still needs

As published on 29 September 2026 the container holds only a Google tag
(`G-FTZY5GBWTR`, on Initialization) and a Custom HTML Meta Pixel (`477887163693452`,
PageView on every page), so page views reach GA4 but none of the events above do yet.
The Meta Pixel fires on this page too. In tagmanager.google.com:

1. **Variables.** One Data Layer Variable (version 2) per parameter: `label`,
   `destination`, `location`, `link_type`, `link_url`, `link_domain`, `section_id`,
   `percent_scrolled`, `poster_id`, `method`, `share_payload`, `festival_day`,
   `day_label`, `session_title`, `session_kind`, `session_start`, `mode`, `video_id`,
   `phase`, `days_to_start`, `link_source`, `link_item`, `link_target`, `redirect`.
2. **Trigger.** Custom Event, "Use regex matching", event name
   `^(live_state|cta_click|nav_menu_open|outbound_click|calendar_add|share_open|share_method|share_complete|stream_mount|stream_play|section_view|scroll_depth|tracked_link_open)$`.
   (Add `recording_play` if the Krishna Utsavam page's event should go too.)
3. **Tag.** Google Analytics: GA4 Event, measurement ID `G-FTZY5GBWTR`, event name
   `{{Event}}`, and one event parameter per variable above, same name, value
   `{{DLV - name}}`. Undefined values are not sent. Fire on the trigger above.
4. **Preview** on the live URL with Tag Assistant, click through, then **Submit**.
5. **GA4 Admin.** Register the parameters you want in reports as event-scoped custom
   dimensions (at least `poster_id`, `method`, `link_type`, `location`, `label`,
   `section_id`, `phase`, `festival_day`, `session_title`). Mark **`share_method`** and
   **`calendar_add`** as key events (Admin, Key events, New key event, exact name).

GA4's enhanced measurement sends its own `scroll` (90%) and outbound `click` events;
the names here are different, so nothing collides.

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
6. **YouTube links.** Done: all five evenings are scheduled on SVMF and in `STREAMS`. The kit used is in `_source/youtube/`.
7. **Switchy link.** Point `https://live.svmf.in/chidagni` at the GitHub Pages URL above.
8. **Analytics.** GTM `GTM-5XK8XFPK` is installed; the GA4 event tags must be configured in the container (see Analytics).

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

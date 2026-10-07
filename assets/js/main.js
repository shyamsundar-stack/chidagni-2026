/* ============================================================
   Chidagni 2026, The Fire of Consciousness Festival

   The schedule lives in index.html only. Every session is an
   .event with data-start / data-end in IST (+05:30), and those
   two attributes drive the countdown, the live highlight, the
   player state and the calendar downloads.
   ============================================================ */
(function () {
  'use strict';

  /* ── 1. CONFIG ──────────────────────────────────────────────
     One scheduled YouTube broadcast per festival evening, from the
     technician sheet. The key is the festival day in IST, which is
     exactly the date part of every data-start in index.html; the
     value is that day's YouTube link (any form: watch?v=, youtu.be,
     /live/) or just the video id. The
     player mounts the right embed on its own, so once these are in
     nothing needs touching while Chidagni runs. Each id keeps working
     afterwards as the day's recording.

     Until an id is filled in, a live session shows the Zoom and
     YouTube buttons in the player instead of an empty frame.
  ------------------------------------------------------------ */
  var STREAMS = {
    '2026-10-06': 'https://www.youtube.com/watch?v=8ziHMWExnOc',
    '2026-10-07': 'https://www.youtube.com/watch?v=CHUnsvQ6pP4',
    '2026-10-08': 'https://www.youtube.com/watch?v=cYGFyqgfhUk',
    '2026-10-09': 'https://www.youtube.com/watch?v=G5C9AeGgbiE',
    '2026-10-10': 'https://www.youtube.com/watch?v=s1mDOsg0OzM'
  };

  /* Accept whatever YouTube gives you: a bare id, a watch?v= link, a
     youtu.be link or a /live/ link. Everything below works with the id. */
  function videoId(v) {
    v = String(v || '').trim();
    var m = v.match(/(?:[?&]v=|youtu\.be\/|\/live\/|\/embed\/|\/shorts\/)([\w-]{11})/);
    if (m) return m[1];
    return /^[\w-]{11}$/.test(v) ? v : '';
  }
  Object.keys(STREAMS).forEach(function (k) { STREAMS[k] = videoId(STREAMS[k]); });

  var ZOOM = 'https://us02web.zoom.us/j/87692135267?pwd=UmNlTGhVVkhBdHpMM05aWkNSUXRwZz09';
  var CHANNEL = 'https://www.youtube.com/@svmf5987/live';

  /* Mount the day's embed this many minutes before the first item,
     so early arrivals land in YouTube's waiting room, not a card. */
  var EARLY_MIN = 25;

  var VENUE = 'Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, ' +
              'East Mada Street, Mylapore, Chennai 600004';

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var hasIO = 'IntersectionObserver' in window;
  var reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* ── 1b. ANALYTICS ───────────────────────────────────────────
     Every measurement goes through track(), which pushes a GA4-style
     event onto the dataLayer for Google Tag Manager (GTM-5XK8XFPK, in
     index.html). It never throws: measurement must never be the reason
     the page breaks. Each push names every parameter below, unset ones as
     undefined, so a value from one event cannot leak into the next through
     GTM's persistent data model. README.md, "Analytics", lists the events
     and the container setup GA4 needs to see them. */
  window.dataLayer = window.dataLayer || [];
  var TRACK_KEYS = [
    'label', 'destination', 'location', 'link_type', 'link_url', 'link_domain',
    'section_id', 'percent_scrolled', 'poster_id', 'method', 'share_payload',
    'festival_day', 'day_label', 'session_title', 'session_kind', 'session_start',
    'mode', 'video_id', 'phase', 'days_to_start'
  ];
  function track(name, params) {
    try {
      var o = { event: name };
      params = params || {};
      TRACK_KEYS.forEach(function (k) {
        var v = params[k];
        o[k] = (v === '' || v === null) ? undefined : v;
      });
      window.dataLayer.push(o);
    } catch (e) { /* never let measurement break the page */ }
  }
  var sharePoster;        // poster id of the open share sheet, for share_method

  /* ── 2. SCHEDULE MODEL ───────────────────────────────────── */
  var events = $$('.event').map(function (el) {
    return {
      el: el,
      start: new Date(el.dataset.start),
      end: new Date(el.dataset.end),
      billed: el.classList.contains('event--star'),
      title: text($('.event__who', el)) || 'Chidagni',
      kind: text($('.event__kind', el)),
      day: text($('.day__n', el.closest('.day')))
    };
  }).filter(function (e) {
    return !isNaN(e.start) && !isNaN(e.end);
  }).sort(function (a, b) { return a.start - b.start; });

  function text(node) { return node ? node.textContent.trim() : ''; }

  if (!events.length) return;

  var FIRST = events[0].start;
  /* the latest END, not the end of the last item by start time: the two are
     the same today but diverge the moment a session is re-ordered */
  var LAST = events.reduce(function (max, e) { return e.end > max ? e.end : max; }, events[0].end);

  var IST = { timeZone: 'Asia/Kolkata' };
  function fmtDate(d) {
    return d.toLocaleDateString('en-GB', Object.assign({ weekday: 'long', day: 'numeric', month: 'long' }, IST));
  }
  function fmtTime(d) {
    return d.toLocaleTimeString('en-GB', Object.assign({ hour: 'numeric', minute: '2-digit', hour12: true }, IST))
      .replace(/\s*(am|pm)/i, function (m) { return ' ' + m.trim().toLowerCase(); });
  }

  /* ── 3. COUNTDOWN, LIVE STATE, PLAYER ────────────────────── */
  var countEl = $('#countdown'), labelEl = $('#countLabel'), nextEl = $('#countNext');
  var grid = $('#countGrid');
  var units = { d: $('[data-unit="d"]'), h: $('[data-unit="h"]'), m: $('[data-unit="m"]'), s: $('[data-unit="s"]') };
  var player = $('#player'), pBadge = $('#playerBadge'), pHead = $('#playerHead'), pSub = $('#playerSub');
  var watchCta = $('#watchCta');

  function pad(n) { return n < 10 ? '0' + n : String(n); }
  function set(node, prop, value) {           // never rewrite an unchanged live region
    if (node && node[prop] !== value) node[prop] = value;
  }

  function currentEvent(now) {
    for (var i = 0; i < events.length; i++) {
      if (now >= events[i].start && now < events[i].end) return events[i];
    }
    return null;
  }
  function nextEvent(now, billedOnly) {
    for (var i = 0; i < events.length; i++) {
      if (events[i].start > now && (!billedOnly || events[i].billed)) return events[i];
    }
    return null;
  }

  var mountedDay = null;
  /* the untouched "streaming opens soon" card, so a stale embed can be torn down */
  var frameInitial = player ? $('.player__frame', player).innerHTML : null;
  function dayKey(e) { return (e.el.dataset.start || '').slice(0, 10); }

  /* The festival day in IST, whatever timezone the viewer is in. en-CA renders
     as YYYY-MM-DD, which is exactly how STREAMS is keyed. */
  function istDateKey(d) {
    return d.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
  }

  /* Which day's broadcast is "the current one": today while Chidagni is on,
     otherwise the next day still to come, and the final day once it is over. */
  function streamDayFor(now) {
    var today = istDateKey(now);
    if (STREAMS[today]) return today;
    var days = Object.keys(STREAMS).filter(function (k) { return STREAMS[k]; }).sort();
    if (!days.length) return null;
    for (var i = 0; i < days.length; i++) {
      if (days[i] > today) return days[i];
    }
    return days[days.length - 1];
  }

  /* Keeps the "Open today's stream on YouTube" link pointing at the right
     broadcast every day, with no edit to this file while Chidagni runs. */
  var ytLink = $('#ytLink');
  function syncYouTubeLink(now) {
    if (!ytLink) return;
    var day = streamDayFor(now);
    var id = day && STREAMS[day];
    if (!id) return;
    var href = 'https://www.youtube.com/watch?v=' + encodeURIComponent(id);
    if (ytLink.getAttribute('href') !== href) ytLink.setAttribute('href', href);
  }

  /* Yesterday's embed must not sit in the player once its day is over: a tab
     left open overnight would otherwise offer the previous day's recording. */
  /* While a day's stream is mounted the player sits at the top of the page,
     under the wordmark; otherwise it lives in the Watch section. It is moved
     before the embed is created, because moving an iframe reloads it. */
  var heroLive = $('#heroLive');
  var playerHome = player ? { parent: player.parentNode, next: player.nextSibling } : null;
  function placePlayer(top) {
    if (!player || !heroLive) return;
    if (top && player.parentNode !== heroLive) {
      heroLive.appendChild(player);
      heroLive.hidden = false;
      player.classList.add('is-in');      // never wait for a scroll reveal up here
    } else if (!top && player.parentNode === heroLive) {
      playerHome.parent.insertBefore(player, playerHome.next);
      heroLive.hidden = true;
    }
    var to = top ? '#heroLive' : '#watch';
    if (watchCta) watchCta.setAttribute('href', to);
    $$('.count__next a[href="#watch"], .count__next a[href="#heroLive"]').forEach(function (a) { a.setAttribute('href', to); });
  }

  function unmountStream() {
    if (!player || mountedDay === null || frameInitial === null) return;
    var frame = $('.player__frame', player);
    if (!frame) return;
    frame.innerHTML = frameInitial;
    player.classList.remove('has-ways');
    mountedDay = null;
    placePlayer(false);
    /* the card was rebuilt, so these three nodes are new */
    pBadge = $('#playerBadge');
    pHead = $('#playerHead');
    pSub = $('#playerSub');
  }

  function mountStream(day) {
    if (!player || !day || mountedDay === day) return;
    var frame = $('.player__frame', player);
    var id = STREAMS[day];
    placePlayer(true);

    if (id) {
      var iframe = document.createElement('iframe');
      /* enablejsapi lets the player report play/pause over postMessage, which
         both stream_play below and GTM's built-in YouTube trigger rely on */
      iframe.src = 'https://www.youtube.com/embed/' + encodeURIComponent(id) +
        '?playsinline=1&rel=0&enablejsapi=1' +
        (/^https?:/.test(location.origin) ? '&origin=' + encodeURIComponent(location.origin) : '');
      iframe.title = 'Chidagni live stream';
      iframe.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture; fullscreen';
      iframe.allowFullscreen = true;
      frame.innerHTML = '';
      frame.appendChild(iframe);
      player.classList.remove('has-ways');
      mountedDay = day;
      listenForPlay(iframe, day, id);
      track('stream_mount', { festival_day: day, mode: 'embed', video_id: id });
      return;
    }

    /* No id for this day. Rather than show a dead player while a session is
       genuinely on stage, hand the viewer the rooms that always exist. */
    var box = $('.player__soon', frame);
    if (!box || $('.player__ways', box)) return;
    var ways = document.createElement('div');
    ways.className = 'player__ways';
    ways.innerHTML =
      '<a class="btn btn--flame" target="_blank" rel="noopener" data-track-label="player_zoom" href="' + ZOOM + '">Open the Zoom room</a>' +
      '<a class="btn btn--ghost" target="_blank" rel="noopener" data-track-label="player_youtube" href="' + CHANNEL + '">Watch on YouTube</a>';
    box.appendChild(ways);
    /* lets the CSS drop the fixed 16/9 box so the buttons cannot be clipped */
    player.classList.add('has-ways');
    /* remembered, so the next day puts the waiting card back */
    mountedDay = day;
    track('stream_mount', { festival_day: day, mode: 'fallback' });
  }

  /* stream_play, once per mounted embed. With enablejsapi=1 the YouTube
     player posts its state to this window once told someone is listening
     (the same handshake the IFrame API script does, without loading it).
     Playing is state 1: "onStateChange" carries it as info, "infoDelivery"
     as info.playerState. */
  var yt = { frame: null };
  function listenForPlay(iframe, day, id) {
    yt = { frame: iframe, day: day, id: id, heard: false, played: false };
    var tries = 0;
    function hello() {
      if (yt.frame !== iframe || yt.heard || tries++ > 20) return;
      try {
        var w = iframe.contentWindow;
        w.postMessage(JSON.stringify({ event: 'listening', id: 1, channel: 'widget' }), 'https://www.youtube.com');
        w.postMessage(JSON.stringify({ event: 'command', func: 'addEventListener',
          args: ['onStateChange'], id: 1, channel: 'widget' }), 'https://www.youtube.com');
      } catch (e) { /* frame gone */ }
      setTimeout(hello, 500);
    }
    iframe.addEventListener('load', hello);
  }
  window.addEventListener('message', function (e) {
    try {
      if (!yt.frame || e.source !== yt.frame.contentWindow) return;
      if (!/^https:\/\/www\.youtube(-nocookie)?\.com$/.test(e.origin)) return;
      yt.heard = true;
      var d = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
      if (!d) return;
      var state = d.event === 'onStateChange' ? d.info : (d.info && d.info.playerState);
      if (state === 1 && !yt.played) {
        yt.played = true;
        track('stream_play', { festival_day: yt.day, video_id: yt.id, mode: 'embed' });
      }
    } catch (err) { /* not a YouTube message */ }
  });

  var lastNow = null;
  function tick() {
    var now = new Date();
    var live = currentEvent(now);

    syncYouTubeLink(now);

    if (live !== lastNow) {
      events.forEach(function (e) { e.el.classList.toggle('is-now', e === live); });
      if (watchCta) watchCta.classList.toggle('is-live', !!live);
      /* if the on-stage item is inside the collapsed inauguration block, open it */
      if (live) {
        var box = live.el.closest('details');
        if (box) box.open = true;
      }
      lastNow = live;
    }

    /* ── a session is on stage ── */
    if (live) {
      countEl.classList.add('is-live');
      grid.hidden = true;
      set(labelEl, 'textContent', 'Live now, ' + live.day);
      set(nextEl, 'innerHTML', '<b>' + live.title + '</b> is on stage. <a href="' +
        (heroLive && !heroLive.hidden ? '#heroLive' : '#watch') + '">Watch the stream</a>');
      if (player) {
        player.dataset.state = 'live';
        set(pBadge, 'textContent', 'Live now');
        set(pHead, 'textContent', live.title);
        set(pSub, 'textContent', live.kind || fmtDate(live.start));
        mountStream(dayKey(live));
      }
      return;
    }

    /* ── the festival is over ── */
    if (now >= LAST) {
      countEl.classList.remove('is-live');
      grid.hidden = true;
      set(labelEl, 'textContent', 'Until we meet again');
      set(nextEl, 'innerHTML', 'The 16<sup>th</sup> Chidagni has concluded. ' +
        'Recordings will be shared on the SVMF channel.');
      if (player) {
        player.dataset.state = 'ended';
        set(pBadge, 'textContent', 'Stream ended');
        set(pHead, 'textContent', 'Thank you for joining us');
        set(pSub, 'textContent', 'Recordings will be posted on the SVMF YouTube channel.');
      }
      return;
    }

    /* ── counting down ── */
    var next = nextEvent(now, false);
    var diff = Math.max(0, (next ? next.start : FIRST) - now);
    var s = Math.floor(diff / 1000);

    countEl.classList.remove('is-live');
    grid.hidden = false;
    set(units.d, 'textContent', String(Math.floor(s / 86400)));
    set(units.h, 'textContent', pad(Math.floor(s / 3600) % 24));
    set(units.m, 'textContent', pad(Math.floor(s / 60) % 60));
    set(units.s, 'textContent', pad(s % 60));

    if (now < FIRST || !next) {
      set(labelEl, 'textContent', 'Chidagni begins in');
      set(nextEl, 'innerHTML', 'Opening on <b>' + fmtDate(FIRST) + '</b> at <b>' + fmtTime(FIRST) + ' IST</b>');
    } else {
      set(labelEl, 'textContent', 'Next session in');
      set(nextEl, 'innerHTML', '<b>' + next.title + '</b>, ' + fmtDate(next.start) + ' at ' + fmtTime(next.start) + ' IST');
    }

    if (player) {
      player.dataset.state = 'soon';
      var billed = nextEvent(now, true) || next;
      if (now < FIRST) {
        /* before opening night the stream starts with the inauguration at
           5:00 pm, not the first billed concert, so say that */
        set(pBadge, 'textContent', 'Streaming opens soon');
        set(pHead, 'textContent', 'The inauguration');
        set(pSub, 'textContent', fmtDate(FIRST) + ' at ' + fmtTime(FIRST) + ' IST');
      } else if (billed) {
        set(pBadge, 'textContent', 'Streaming opens soon');
        set(pHead, 'textContent', billed.title);
        set(pSub, 'textContent', billed.day + ', ' + fmtDate(billed.start) + ' at ' + fmtTime(billed.start) + ' IST');
      }
      /* the page promises the player "opens a few minutes before each
         performance": mount the day's embed a little ahead of the first
         item, so early arrivals see YouTube's waiting room, then the feed */
      if (next && next.start - now < EARLY_MIN * 60000) {
        mountStream(dayKey(next));
      } else if (mountedDay !== null && mountedDay !== (next ? dayKey(next) : null)) {
        /* a finished day's embed is still sitting there; put the waiting card
           back rather than leave yesterday's recording on offer */
        unmountStream();
      }
    }
  }

  /* live_state, once per page view: which phase of the festival this visit
     landed in, so traffic can be split into before / live / between / ended */
  (function () {
    var now = new Date(), live = currentEvent(now);
    var phase = live ? 'live' : now < FIRST ? 'before' : now >= LAST ? 'ended' : 'between';
    track('live_state', {
      phase: phase,
      festival_day: istDateKey(now),
      session_title: live ? live.title : undefined,
      days_to_start: phase === 'before' ? Math.ceil((FIRST - now) / 86400000) : undefined
    });
  })();

  tick();
  setInterval(tick, 1000);

  /* ── 4. ADD TO CALENDAR ──────────────────────────────────────
     Each button opens the phone's own calendar with the event filled in:
       Android      Google Calendar's "new event" screen (the app, if installed)
       iPhone, Mac  the .ics in assets/cal/, which Safari hands to Calendar
       elsewhere    a two-item menu: Google Calendar, or Apple / Outlook (.ics)
     The .ics files are written by _source/make_calendar.py from this page;
     re-run it after changing a time or name. Both carry the same text.

     The event's link is live.svmf.in/chidagni?go=calendar.<slug>.yt-<date>.
     Tapped from the reminder, the page records it and goes straight on to
     that evening's YouTube stream, looked up at that moment, so entries saved
     before the stream links existed still work (section 4b).            */
  var SITE = 'https://live.svmf.in/chidagni';
  var isAndroid = /Android/i.test(navigator.userAgent);
  var isApple = /iPhone|iPad|iPod/i.test(navigator.userAgent) ||
                (/Macintosh/i.test(navigator.userAgent) && 'ontouchend' in document) ||
                (/Macintosh/i.test(navigator.userAgent) && /Safari/i.test(navigator.userAgent) && !/Chrome|Firefox|Edg/i.test(navigator.userAgent));

  function stamp(d) { return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''); }

  /* one calendar entry per button: the enclosing session, or the whole
     inauguration block, which carries its own data-start / data-end */
  function calEntry(btn) {
    var box = btn.closest('[data-start]');
    if (!box) return null;
    var who = text($('.event__who', box));
    var kind = text($('.event__kind', box));
    var title = btn.dataset.calTitle || ('Chidagni: ' + who + (kind ? ', ' + kind : ''));
    var start = new Date(box.dataset.start), end = new Date(box.dataset.end);
    var day = box.dataset.start.slice(0, 10);
    var slug = btn.dataset.cal;
    var link = SITE + '?go=calendar.' + slug + '.yt-' + day;
    var desc = (btn.dataset.calKind || kind || '') + '\n\n' +
      'Watch live on YouTube: ' + link + '\n' +
      'Or join on Zoom: ' + ZOOM + ' (Meeting ID 876 9213 5267, password Krishna)\n\n' +
      'Chidagni 2026, the Fire of Consciousness Festival. ' + VENUE + '. All are welcome.';
    return { slug: slug, title: title, start: start, end: end, day: day, link: link, desc: desc,
             who: who || title, kind: btn.dataset.calKind ? 'Inauguration' : kind };
  }

  function googleUrl(c) {
    return 'https://calendar.google.com/calendar/render?action=TEMPLATE' +
      '&text=' + encodeURIComponent(c.title) +
      '&dates=' + stamp(c.start) + '/' + stamp(c.end) +
      '&details=' + encodeURIComponent(c.desc) +
      '&location=' + encodeURIComponent(VENUE) +
      '&ctz=Asia/Kolkata';
  }
  function icsUrl(c) { return 'assets/cal/' + c.slug + '.ics'; }

  var openMenu = null;
  function closeMenu() { if (openMenu) { openMenu.remove(); openMenu = null; } }
  document.addEventListener('click', function (e) {
    if (openMenu && !openMenu.contains(e.target) && !e.target.closest('[data-cal]')) closeMenu();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });

  function calTrack(c, method) {
    track('calendar_add', {
      session_title: c.who, session_kind: c.kind, festival_day: c.day,
      session_start: c.start.toISOString(), method: method, label: c.slug
    });
  }

  $$('[data-cal]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var c = calEntry(btn);
      if (!c) return;
      if (isAndroid) { calTrack(c, 'google'); window.open(googleUrl(c), '_blank', 'noopener'); return; }
      if (isApple) { calTrack(c, 'ics'); location.href = icsUrl(c); return; }

      /* desktop: let them pick */
      var again = openMenu && openMenu.previousElementSibling === btn;
      closeMenu();
      if (again) return;
      var menu = document.createElement('span');
      menu.className = 'calmenu';
      menu.setAttribute('role', 'menu');
      menu.innerHTML =
        '<a role="menuitem" target="_blank" rel="noopener" data-m="google">Google Calendar</a>' +
        '<a role="menuitem" data-m="ics">Apple, Outlook (.ics)</a>';
      $('[data-m="google"]', menu).href = googleUrl(c);
      $('[data-m="ics"]', menu).href = icsUrl(c);
      $('[data-m="ics"]', menu).setAttribute('download', 'chidagni-2026-' + c.slug + '.ics');
      $$('a', menu).forEach(function (a) {
        a.addEventListener('click', function () { calTrack(c, a.dataset.m); setTimeout(closeMenu, 50); });
      });
      btn.insertAdjacentElement('afterend', menu);
      openMenu = menu;
      $('a', menu).focus({ preventScroll: true });
    });
  });

  /* ── 4b. ARRIVING FROM A TRACKED LINK ─────────────────────────
     The head script has already turned #go=… into UTM tags. A calendar
     reminder (target yt-<date>) goes straight on to that evening's YouTube
     stream once GTM has sent the visit; with no stream link yet, the page
     simply stays on the player.                                        */
  (function () {
    var go = window.__go;
    if (!go) return;
    var yt = /^yt-(\d{4}-\d{2}-\d{2})$/.exec(go.target || '');
    var id = yt && STREAMS[yt[1]];
    var left = false;
    function leave() {
      if (left) return;
      left = true;
      location.replace('https://www.youtube.com/watch?v=' + encodeURIComponent(id));
    }
    try {
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        event: 'tracked_link_open', link_source: go.source, link_item: go.item,
        link_target: go.target || undefined, festival_day: yt ? yt[1] : undefined,
        redirect: id ? 'youtube' : 'page',
        eventCallback: id ? leave : undefined, eventTimeout: id ? 1500 : undefined
      });
    } catch (e) { /* tracking must never block the viewer */ }
    if (id) setTimeout(leave, 1800);     // GTM blocked or slow: go anyway
  })();

  /* ── 5. NAV ──────────────────────────────────────────────── */
  var nav = $('#nav'), toggle = $('#navToggle'), links = $('#navLinks');

  /* a sentinel at the top of the page rather than a scroll listener.
     Old Android WebViews have no IntersectionObserver, so fall back to
     leaving the nav in its solid state rather than throwing. */
  if (hasIO) {
    var sentinel = document.createElement('div');
    sentinel.setAttribute('aria-hidden', 'true');
    sentinel.style.cssText = 'position:absolute;top:0;left:0;width:1px;height:60px;pointer-events:none';
    document.body.insertBefore(sentinel, document.body.firstChild);
    new IntersectionObserver(function (entries) {
      nav.classList.toggle('is-stuck', !entries[0].isIntersecting);
    }, { threshold: 0 }).observe(sentinel);

    /* The nav wordmark only appears once the big one has scrolled away,
       so the logo is never on screen twice. */
    var heroMark = $('.hero__mark');
    if (heroMark) {
      new IntersectionObserver(function (entries) {
        nav.classList.toggle('has-brand', !entries[0].isIntersecting);
      }, { threshold: 0 }).observe(heroMark);
    } else {
      nav.classList.add('has-brand');
    }
  } else {
    nav.classList.add('is-stuck', 'has-brand');
  }

  if (toggle && links) {
    var setMenu = function (open) {
      links.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
    };
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') !== 'true';
      setMenu(open);
      if (open) track('nav_menu_open', { location: 'nav' });
    });
    $$('a', links).forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        toggle.focus();
      }
    });
  }

  /* ── 6. SHARE ────────────────────────────────────────────────
     Two kinds of button open the same sheet: the three printed pages in the
     "Send the invitation" strip (.poster, data-img), and the Share button on
     every session (data-card: that artist's card in assets/img/cards/). Each
     carries its own note in data-msg. Where the browser has a real share sheet (nearly all phones)
     we hand it the poster image itself, so WhatsApp sends the picture and
     not just a link. Everywhere else there are explicit buttons.        */
  var dlg = $('#shareDlg');

  if (dlg) {
    var picEl = $('#sharePic'), msgEl = $('#shareMsg'), noteEl = $('#shareNote');
    var btnNative = $('#shareNative'), aWa = $('#shareWa'), aMail = $('#shareMail');
    var btnCopy = $('#shareCopy'), aDl = $('#shareDl');
    var current = null;
    /* The link in every note is the Switchy link (SITE, section 4) with
       ?go=share.<card>.<day-N>: Switchy forwards the query, and the head script
       turns it into utm_source=share&utm_content=<card> and lands on that day. */

    /* The note has to end in an actual invitation, not just facts. */
    var TAIL = 'Mini Hall, 2nd Floor, Bharatiya Vidya Bhavan, Mylapore, Chennai. All are welcome.';
    var ASK = 'Do join us, or watch it live here:';

    function say(t) { noteEl.textContent = t || ''; }

    /* The poster is fetched when the sheet opens, not when Share is tapped.
       navigator.share needs transient user activation, and awaiting a fetch
       inside the click handler can spend it: Safari then rejects the call. */
    var readyFile = null;
    function prefetchPoster() {
      readyFile = null;
      if (!navigator.canShare || !current) return;
      var want = current.jpg;
      fetch(want)
        .then(function (r) { return r.ok ? r.blob() : Promise.reject(); })
        .then(function (blob) {
          if (!current || current.jpg !== want) return;      // sheet moved on
          var file = new File([blob], 'chidagni-2026-' + current.img + '.jpg',
                              { type: 'image/jpeg' });
          if (navigator.canShare({ files: [file] })) readyFile = file;
        })
        .catch(function () {
          /* only clear if this is still the poster on screen, or a failed
             fetch for an old poster wipes the file we just got for a new one */
          if (current && current.jpg === want) readyFile = null;
        });
    }

    /* One way out, so every path releases the scroll lock and returns focus,
       including on browsers with no <dialog> support where close() is absent. */
    var lastPoster = null;
    function closeShare() {
      if (typeof dlg.close === 'function' && dlg.open) dlg.close();
      else dlg.removeAttribute('open');
      say('');
      document.documentElement.style.overflow = '';
      if (lastPoster && lastPoster.isConnected) lastPoster.focus({ preventScroll: true });
    }

    function openShare(btn) {
      if (dlg.open) closeShare();         // never call showModal on an open dialog
      lastPoster = btn;
      var card = btn.dataset.card;
      var img = card || btn.dataset.img;
      var anchor = (btn.dataset.anchor || '').replace(/^#/, '');
      var url = SITE + '?go=share.' + img + (anchor ? '.' + anchor : '');
      current = {
        img: img,
        url: url,
        jpg: card ? 'assets/img/cards/' + card + '.jpg' : 'assets/img/posters/' + img + '.jpg'
      };

      picEl.src = card ? current.jpg : 'assets/img/posters/' + img + '.webp';
      picEl.alt = !card ? $('img', btn).alt : 'Invitation card: ' + (card === 'inauguration'
        ? 'Inauguration of Chidagni 2026' : text($('.event__who', btn.closest('[data-start]'))));
      picEl.classList.toggle('is-card', !!card);
      msgEl.value = btn.dataset.msg + '\n' + TAIL + '\n' + ASK + ' ' + url;
      aDl.href = current.jpg;
      aDl.setAttribute('download', 'chidagni-2026-' + img + '.jpg');
      say('');
      sync();
      prefetchPoster();

      if (typeof dlg.showModal === 'function') dlg.showModal();
      else dlg.setAttribute('open', '');
      document.documentElement.style.overflow = 'hidden';
      sharePoster = img;
      track('share_open', { poster_id: img });
      /* focus the heading, not the textarea: opening a phone keyboard over
         the sheet the moment it appears is hostile */
      $('.share__h', dlg).setAttribute('tabindex', '-1');
      $('.share__h', dlg).focus({ preventScroll: true });
    }

    /* keep the WhatsApp and mail links in step with any edit to the note */
    function sync() {
      var text = msgEl.value;
      aWa.href = 'https://wa.me/?text=' + encodeURIComponent(text);
      aMail.href = 'mailto:?subject=' +
        encodeURIComponent('Chidagni 2026, 6 to 10 October, Bharatiya Vidya Bhavan') +
        '&body=' + encodeURIComponent(text);
    }
    msgEl.addEventListener('input', sync);

    /* the OS sheet, with the poster attached when the browser allows files */
    if (navigator.share) {
      btnNative.hidden = false;
      btnNative.addEventListener('click', function () {
        var text = msgEl.value;
        /* called synchronously so the tap's user activation still counts */
        var payload = readyFile
          ? { files: [readyFile], text: text }
          : { text: text, url: current.url };

        var p;
        try { p = navigator.share(payload); } catch (e) { p = Promise.reject(e); }

        var sent = payload.files ? 'image' : 'link';
        p.then(function () {
          say('Thank you for passing it on.');
          track('share_complete', { method: 'native', poster_id: current && current.img, share_payload: sent });
        })
         .catch(function (err) {
           if (err && err.name === 'AbortError') { say(''); return; }
           say('Your browser could not open the share menu. Use WhatsApp or email instead.');
         });
      });
    }

    btnCopy.addEventListener('click', function () {
      var text = msgEl.value;
      var done = function () { say('Note copied. Paste it wherever you like.'); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { say('Copy did not work. Select the note and copy it by hand.'); });
      } else {
        msgEl.select();
        try { document.execCommand('copy'); done(); } catch (e) { say('Copy did not work. Select the note and copy it by hand.'); }
      }
    });

    $$('.poster, [data-card]').forEach(function (btn) {
      btn.addEventListener('click', function () { openShare(btn); });
    });

    $('#shareClose').addEventListener('click', closeShare);
    /* clicking the backdrop closes it, same as Esc */
    dlg.addEventListener('click', function (e) { if (e.target === dlg) closeShare(); });
    /* native dialogs handle Esc themselves; the fallback path does not */
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && dlg.hasAttribute('open')) closeShare();
    });
    /* covers Esc on the native dialog, which closes without touching us */
    dlg.addEventListener('close', function () {
      say('');
      document.documentElement.style.overflow = '';
    });
  }

  /* ── 7. ANALYTICS: CLICKS, SECTIONS, SCROLL ──────────────────
     One delegated listener for every link and tagged control:
     - "#..." links            cta_click      (label, destination, location)
     - off-site, tel:, mailto: outbound_click (link_type, link_url, ...)
     - [data-track="share"]    share_method   (method, poster_id)
     link_type comes from data-track when present, else from the host.
     label is data-track-label, else the link text. location is the
     nearest [data-track-section], else the enclosing section's id.     */
  function slug(t) {
    return String(t || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 60);
  }
  function labelOf(el) {
    return el.getAttribute('data-track-label') || slug(el.textContent) || slug(el.getAttribute('aria-label'));
  }
  function whereIs(el) {
    var tagged = el.closest('[data-track-section]');
    if (tagged) return tagged.getAttribute('data-track-section');
    var box = el.closest('section[id], dialog[id], header[id], footer');
    return box ? (box.id || box.tagName.toLowerCase()) : 'page';
  }
  function linkType(u) {
    var h = u.hostname.replace(/^www\./, '');
    if (u.protocol === 'tel:') return 'phone';
    if (u.protocol === 'mailto:') return 'email';
    if (/(^|\.)zoom\.us$/.test(h)) return 'zoom';
    if (/(^|\.)(youtube\.com|youtu\.be)$/.test(h)) return 'youtube';
    if (/^maps\.(google\.|app\.goo\.gl$)/.test(h) ||
        (/(^|\.)google\.[a-z.]+$/.test(h) && /^\/maps/.test(u.pathname))) return 'maps';
    if (/(^|\.)(wa\.me|whatsapp\.com)$/.test(h)) return 'whatsapp';
    return 'website';
  }

  document.addEventListener('click', function (e) {
    try {
      var el = e.target && e.target.closest && e.target.closest('a[href], [data-track]');
      if (!el) return;
      var kind = el.getAttribute('data-track');
      if (kind === 'none') return;
      if (kind === 'share') {
        track('share_method', { method: el.getAttribute('data-track-label'), poster_id: sharePoster });
        return;
      }
      if (el.closest('#shareDlg')) return;
      var href = el.getAttribute('href') || '';
      if (href.charAt(0) === '#') {
        if (href.length > 1) track('cta_click', { label: labelOf(el), destination: href, location: whereIs(el) });
        return;
      }
      var u = new URL(el.href, location.href);
      /* skips blob: (the calendar download clicks one), javascript:, data: */
      if (!/^(https?|tel|mailto):$/.test(u.protocol)) return;
      if (/^https?:$/.test(u.protocol) && u.host === location.host) return;
      track('outbound_click', {
        link_type: kind || linkType(u),
        link_url: u.href.slice(0, 100),        // GA4 truncates values at 100
        link_domain: u.hostname.replace(/^www\./, ''),
        label: labelOf(el),
        location: whereIs(el)
      });
    } catch (err) { /* never block the click */ }
  });

  /* section_view, once per section. "Seen" is half the section on screen,
     or, for a section taller than two screens (the schedule on a phone),
     the section filling half the viewport. */
  if (hasIO) {
    var seenSec = {};
    var steps = [];
    for (var st = 0; st <= 20; st++) steps.push(st / 20);
    var secIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var id = en.target.id;
        if (!en.isIntersecting || seenSec[id]) return;
        var vh = (en.rootBounds && en.rootBounds.height) || window.innerHeight;
        if (en.intersectionRatio >= 0.5 || en.intersectionRect.height >= vh * 0.5) {
          seenSec[id] = true;
          secIO.unobserve(en.target);
          track('section_view', { section_id: id });
        }
      });
    }, { threshold: steps });
    ['about', 'schedule', 'watch', 'visit', 'invite'].forEach(function (id) {
      var sec = document.getElementById(id);
      if (sec) secIO.observe(sec);
    });
  }

  /* scroll_depth at 25/50/75/100, each once. Measured at the bottom edge of
     the viewport, as GA4's own scroll event is. */
  var DEPTHS = [25, 50, 75, 100], depthHit = {}, depthQueued = false;
  function checkDepth() {
    depthQueued = false;
    try {
      var doc = document.documentElement;
      var bottom = (window.pageYOffset || doc.scrollTop) + window.innerHeight;
      var pct = bottom >= doc.scrollHeight - 4 ? 100 : bottom / doc.scrollHeight * 100;
      DEPTHS.forEach(function (d) {
        if (pct >= d && !depthHit[d]) {
          depthHit[d] = true;
          track('scroll_depth', { percent_scrolled: d });
        }
      });
      if (depthHit[100]) window.removeEventListener('scroll', onScrollDepth);
    } catch (e) { /* ignore */ }
  }
  function onScrollDepth() {
    if (depthQueued) return;
    depthQueued = true;
    (window.requestAnimationFrame || setTimeout)(checkDepth);
  }
  window.addEventListener('scroll', onScrollDepth, { passive: true });

  /* ── 8. REVEAL ON SCROLL ─────────────────────────────────── */
  if (hasIO && !reduceMotion) {
    var targets = $$('.about__text, .about__gurus, .day, .devis, .watch__copy, .player, .visit__card, .sec-head, .strip li');
    targets.forEach(function (el) { el.classList.add('reveal'); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: .05 });
    targets.forEach(function (el) { io.observe(el); });

    /* Failsafe. A reveal must never be the reason content is missing:
       observers do not fire in background tabs, in headless renderers, or
       in print. After a few seconds everything is shown regardless. */
    var reveal = function () {
      targets.forEach(function (el) { el.classList.add('is-in'); });
      io.disconnect();
    };
    setTimeout(reveal, 4000);
    window.addEventListener('beforeprint', reveal);
  }
})();

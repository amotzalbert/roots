/* פקדים גלובליים: מצב תצוגה, גודל גופן ובורר שפה — נשמרים בין ביקורים.
   ⚠ הערכה הראשונית של הערכה (theme) נעשית ב-<head> ע"י SNIPPET משובץ
   (ראו tools/inject-head.py). הקובץ הזה מטפל רק באינטראקציה. */
(function () {
  var root = document.documentElement, LS = window.localStorage;
  var ORDER = ['system', 'light', 'dark'];
  var LABEL = {
    he: { system: 'לפי המערכת', light: 'בהיר', dark: 'כהה' },
    en: { system: 'System', light: 'Light', dark: 'Dark' },
    pl: { system: 'Systemowy', light: 'Jasny', dark: 'Ciemny' }
  };
  var ICON = { system: '◑', light: '☀', dark: '☾' };

  function lang() {
    var l = (root.getAttribute('lang') || 'he').slice(0, 2);
    return LABEL[l] ? l : 'he';
  }
  function current() {
    var v = LS.getItem('roots-theme');
    if (v === 'light' || v === 'dark') return v;
    return 'system';           // null, '' (legacy) and anything else => system
  }
  function apply(pref) {
    if (pref === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', pref);
    try { LS.setItem('roots-theme', pref); } catch (e) {}
    paint(pref);
  }
  function paint(pref) {
    var b = document.getElementById('theme');
    if (!b) return;
    var L = LABEL[lang()];
    b.textContent = ICON[pref];
    b.title = L[pref];
    b.setAttribute('aria-label', L[pref]);
  }

  addEventListener('DOMContentLoaded', function () {
    paint(current());

    var t = document.getElementById('theme');
    if (t) t.addEventListener('click', function () {
      apply(ORDER[(ORDER.indexOf(current()) + 1) % ORDER.length]);
    });

    // בחירת שפה מפורשת נשמרת — וה-ROOTS-LANG-BOOT שבכל עמוד שומר על עקביות.
    // המעבר מעביר גם את הפרמטרים (?f= של דוח, ?p= באילן) ואת העוגן.
    Array.prototype.forEach.call(document.querySelectorAll('.langsw a'), function (a) {
      a.addEventListener('click', function () {
        try { LS.setItem('roots-lang', this.getAttribute('hreflang')); } catch (e) {}
        this.href = this.getAttribute('href') + location.search + location.hash;
      });
    });

    // גופן גדול
    if (LS.getItem('roots-bigfont') === '1') document.body.classList.add('font-lg');
    var f = document.getElementById('bigfont');
    if (f) f.addEventListener('click', function () {
      var on = document.body.classList.toggle('font-lg');
      try { LS.setItem('roots-bigfont', on ? '1' : '0'); } catch (e) {}
    });
  });

  // כשההעדפה היא "לפי המערכת" — להגיב לשינוי חי במערכת ההפעלה
  var mq = window.matchMedia && matchMedia('(prefers-color-scheme:dark)');
  if (mq && mq.addEventListener) mq.addEventListener('change', function () {
    if (current() === 'system') root.removeAttribute('data-theme');
  });
})();

/* ═══ «חדר הקריאה» — תנועת קריאה ═══════════════════════════════════
   1) חשיפת גלילה שקטה: בלוקים מבניים (לא פסקאות) עולים 10px בכניסה
      לחלון. ההסתרה חלה רק תחת html.js + prefers-reduced-motion:no-preference
      (ראו main.css §6) — בלי JS או עם צמצום תנועה הכל גלוי מהרגע הראשון.
   2) פס התקדמות קריאה בעמודי קריאה ארוכה (פרק/דו"ח).                  */
(function () {
  var root = document.documentElement;
  root.classList.add('js');

  // ── חשיפת גלילה ──
  var SEL = ['main>h2', 'main>section', '.plinths>*', '.chlist .ch', '.tools .tcard',
    '.dgrid .dcard', '.slist .sitem', '.rlist>*', '.index .index-row',
    '.artifact', '.genbox', '.pull', '.introcard', '.grade-key', '.whatsnew li'].join(',');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion:reduce)').matches;
  if (!reduce && 'IntersectionObserver' in window) {
    var els = document.querySelectorAll(SEL);
    if (els.length) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
      Array.prototype.forEach.call(els, function (el) {
        // מה שכבר על המסך בטעינה — לא מסתירים בכלל (רגע השער עושה את שלו)
        var r = el.getBoundingClientRect();
        if (r.top < innerHeight && r.bottom > 0) return;
        el.setAttribute('data-reveal', '');
        io.observe(el);
      });
    }
  }

  // ── פס התקדמות קריאה — רק בקריאה ארוכה ──
  if (document.querySelector('.chapter-meta, .md')) {
    var bar = document.createElement('div');
    bar.className = 'readbar';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    var ticking = false;
    function paintBar() {
      ticking = false;
      var h = document.documentElement;
      var max = h.scrollHeight - innerHeight;
      var f = max > 0 ? Math.min(1, h.scrollTop / max) : 0;
      bar.style.transform = 'scaleX(' + f + ')';
    }
    addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(paintBar); }
    }, { passive: true });
    paintBar();
  }
})();

/* ═══ ניווט נייד — «ארכיון שחור» ═══════════════════════════════════
   בטלפון הפס העליון נשבר לשלוש שורות וגזל שליש מסך. במקום זה:
   שורה אחת — מותג, מצב תצוגה, וכפתור תפריט שפותח את הניווט הקיים
   כמגירת עמודה עם יעדי מגע של 48px. שום קישור לא נוצר מחדש —
   ה-CSS פורס את ה-DOM הקיים, וכך שלוש השפות מקבלות זאת חינם.
   בלי JS: הפס המקופל הישן נשאר — הכל נגיש גם אז.                    */
(function () {
  var bar = document.querySelector('.topbar');
  var barIn = bar && bar.querySelector('.topbar-in');
  if (!bar || !barIn) return;
  var L = { he: { open: 'תפריט', close: 'סגירת התפריט' },
            en: { open: 'Menu', close: 'Close menu' },
            pl: { open: 'Menu', close: 'Zamknij menu' } };
  var lang = (document.documentElement.getAttribute('lang') || 'he').slice(0, 2);
  var T = L[lang] || L.he;

  var btn = document.createElement('button');
  btn.className = 'iconbtn menubtn';
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-label', T.open);
  btn.textContent = '☰';
  barIn.appendChild(btn);

  function setOpen(on, focusFirst) {
    bar.classList.toggle('open', on);
    document.documentElement.classList.toggle('nav-open', on);
    btn.setAttribute('aria-expanded', on ? 'true' : 'false');
    btn.setAttribute('aria-label', on ? T.close : T.open);
    btn.textContent = on ? '✕' : '☰';
    if (on && focusFirst) {
      var first = bar.querySelector('.tabs a, .navlinks a');
      if (first) first.focus();
    }
  }
  btn.addEventListener('click', function () {
    setOpen(!bar.classList.contains('open'), false);
  });
  btn.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(!bar.classList.contains('open'), true); }
  });
  bar.addEventListener('click', function (e) {
    if (e.target.closest('.tabs a, .navlinks a')) setOpen(false, false);
  });
  addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && bar.classList.contains('open')) { setOpen(false, false); btn.focus(); }
  });
  var mq = matchMedia('(min-width: 761px)');
  (mq.addEventListener ? mq.addEventListener.bind(mq, 'change') : mq.addListener.bind(mq))(function (ev) {
    if (ev.matches) setOpen(false, false);
  });
})();

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
      bar.style.width = (max > 0 ? Math.min(100, 100 * h.scrollTop / max) : 0) + '%';
    }
    addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(paintBar); }
    }, { passive: true });
    paintBar();
  }
})();

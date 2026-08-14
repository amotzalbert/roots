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

/* פקדים גלובליים: מצב תצוגה וגודל גופן — נשמרים בין ביקורים */
(function(){
  const root=document.documentElement, LS=window.localStorage;
  const saved=LS.getItem('roots-theme');
  root.setAttribute('data-theme', saved || 'light');
  if(LS.getItem('roots-bigfont')==='1') document.body.classList.add('font-lg');

  addEventListener('DOMContentLoaded',()=>{
    const t=document.getElementById('theme');
    t?.addEventListener('click',()=>{
      const now=root.getAttribute('data-theme');
      const next = now==='dark' ? 'light' : now==='light' ? '' : 'dark';
      if(next) root.setAttribute('data-theme',next); else root.removeAttribute('data-theme');
      LS.setItem('roots-theme',next);
    });
    const f=document.getElementById('bigfont');
    f?.addEventListener('click',()=>{
      const on=document.body.classList.toggle('font-lg');
      LS.setItem('roots-bigfont', on?'1':'0');
    });
  });
})();

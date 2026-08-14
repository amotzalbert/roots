/* ═══ אילן היוחסין האינטראקטיבי — «שורשים» ═══════════════════════════
   מימוש SVG עצמאי, בלי ספריות. ארבעה מודים.
   ⭐ הדרישה המרכזית: במוד «אילן מלא», בחירת אדם מדגישה את הקו הישיר שלו —
      כרטיסים גדולים וקווים עבים — ומקטינה ומעמעמת את כל השאר.            */

const S = {
  people: new Map(), unions: [], places: new Map(),
  mode: 'full', branch: 'all', focus: null,
  view: {x:0, y:0, k:1}, nodes: [], links: []
};

/* מידות כרטיס: [רגיל, קו־ישיר, מוקטן] */
const CARD = {
  direct: {w:186, h:62, fs:15, sub:11.5},
  normal: {w:150, h:50, fs:13, sub:10},
  faded:  {w:112, h:34, fs:11, sub:0}
};
const GAP_X = 26, GAP_Y = 120;

/* ── טעינה ───────────────────────────────────────────────────────── */
async function boot(){
  const [people, unions, places] = await Promise.all([
    fetch('data/people.json').then(r=>r.json()),
    fetch('data/unions.json').then(r=>r.json()),
    fetch('data/places.json').then(r=>r.json()),
  ]);
  people.forEach(p=>S.people.set(p.id,p));
  S.unions = unions;
  places.forEach(p=>S.places.set(p.id,p));
  assignGenerations();
  wireUI();
  const q = new URLSearchParams(location.search).get('p');
  S.focus = S.people.has(q) ? q : defaultFocus();
  render();
}

/** דור = 0 לצעירים ביותר, עולה כלפי האבות. מחושב מהקשרים בפועל.
    הרפיה איטרטיבית: הורה תמיד דור אחד מעל הילד הכי "עמוק" שלו, ובני זוג
    תמיד באותו דור — לשני הכיוונים, לא רק בהקצאה חד-פעמית. בלי זה, מי
    שנפגש עם דורו "האמיתי" (דרך הוריו/ילדיו) רק אחרי שכבר קיבל דור שגוי
    מבן/בת זוגו, נשאר תקוע שם לצמיתות — זו הייתה סיבת הערבוב בין דורות. */
function assignGenerations(){
  const P = S.people;
  P.forEach(p=>p._gen = null);
  const leaves = [...P.values()].filter(p=>p.children.length===0);
  const queue = leaves.map(p=>(p._gen=0, p));
  let guard = 0;
  while(queue.length && guard++ < 200000){
    const p = queue.shift();
    p.parents.forEach(id=>{
      const par = P.get(id); if(!par) return;
      const g = p._gen + 1;
      if(par._gen === null || par._gen < g){ par._gen = g; queue.push(par); }
    });
    // בני זוג חייבים להיות באותו דור — מרפים בשני הכיוונים ומפיצים הלאה
    p.spouses.forEach(id=>{
      const sp = P.get(id); if(!sp) return;
      if(sp._gen === null || sp._gen < p._gen){ sp._gen = p._gen; queue.push(sp); }
      else if(sp._gen > p._gen){ p._gen = sp._gen; queue.push(p); }
    });
    // אחים באותו דור — בלי זה, אח חסר־ילדים נשאר "עלה" בדור 0 ונופל
    // לשורת האחיינים (כך אמוץ הוצג דור מתחת לאחיו). מיישרים כל קבוצת
    // אחים כלפי מעלה אל הגבוה שבהם.
    p.parents.forEach(id=>{
      const par = P.get(id); if(!par) return;
      par.children.forEach(cid=>{
        const c = P.get(cid); if(!c || c === p) return;
        if(c._gen === null || c._gen < p._gen){ c._gen = p._gen; queue.push(c); }
      });
    });
  }
  P.forEach(p=>{ if(p._gen === null) p._gen = 0; });
}

function defaultFocus(){
  // ברירת מחדל: אמוץ — נקודת המפגש של שני הענפים. (היוריסטיקת "הצעיר
  // ביותר" הישנה נשענה על כך שהוא ישב בטעות בדור 0; אחרי תיקון יישור
  // האחים היא הייתה בוחרת אחיין.)
  if(S.people.has('p-amotz-albert')) return 'p-amotz-albert';
  return [...S.people.values()]
    .sort((a,b)=> a._gen - b._gen || (b.parents.length+b.children.length)-(a.parents.length+a.children.length))
    [0]?.id;
}

/* ── קו ישיר: כל האבות + כל הצאצאים + בני זוג בקו ─────────────────── */
function directLine(id){
  const set = new Set(), P = S.people;
  if(!id || !P.has(id)) return set;
  (function up(x){ if(!x||set.has(x)) return; set.add(x);
    P.get(x).parents.forEach(up); })(id);
  const down = new Set();
  (function dn(x){ if(!x||down.has(x)) return; down.add(x);
    P.get(x).children.forEach(dn); })(id);
  down.forEach(x=>set.add(x));
  // בני זוג של מי שבקו הישיר — הם ההורה השני, שייכים לסיפור
  [...set].forEach(x=>P.get(x).spouses.forEach(s=>set.add(s)));
  return set;
}

/* ── חישוב פריסה ─────────────────────────────────────────────────── */
function layout(){
  const P = S.people, direct = directLine(S.focus);
  let visible = [...P.values()];

  if(S.branch !== 'all')  visible = visible.filter(p=>p.branch===S.branch);
  if(S.mode === 'pedigree') visible = visible.filter(p=>isAncestorOrSelf(p.id, S.focus));
  if(S.mode === 'descend')  visible = visible.filter(p=>isDescendantOrSelf(p.id, S.focus));

  const vis = new Set(visible.map(p=>p.id));

  // קיבוץ לדורות
  const rows = new Map();
  visible.forEach(p=>{ (rows.get(p._gen) ?? rows.set(p._gen,[]).get(p._gen)).push(p); });

  // סידור בתוך דור: זוגות צמודים; ואז כמה מעברי מרכז־כובד כדי שילדים
  // ישבו מתחת להוריהם והקשתות לא יצטלבו לרוחב כל הדף.
  const ordered = new Map();
  const gensAsc = [...rows.keys()].sort((a,b)=>a-b);
  gensAsc.forEach(g=>{
    const list = rows.get(g), seen = new Set(), out = [];
    list.sort((a,b)=> (a.names.he||'').localeCompare(b.names.he||'','he'));
    list.forEach(p=>{
      if(seen.has(p.id)) return;
      out.push(p); seen.add(p.id);
      p.spouses.forEach(sid=>{                       // בן/בת הזוג צמודים תמיד
        if(!seen.has(sid) && vis.has(sid)){ out.push(P.get(sid)); seen.add(sid); }
      });
    });
    ordered.set(g, out);
  });

  // ── מעברי מרכז־כובד: פעם מלמטה למעלה ופעם מלמעלה למטה, שלוש סיבובים
  const posIn = g => {
    const m = new Map(); (ordered.get(g)||[]).forEach((p,i)=>m.set(p.id,i)); return m;
  };
  const coupleKey = p => {
    const mate = p.spouses.find(s=>vis.has(s));
    return mate ? [p.id, mate].sort().join('|') : p.id;
  };
  for(let pass=0; pass<3; pass++){
    const dirs = pass%2 ? [...gensAsc] : [...gensAsc].reverse();
    dirs.forEach(g=>{
      const list = ordered.get(g); if(!list || list.length<3) return;
      const below = posIn(g-1), above = posIn(g+1);
      const bary = new Map();
      list.forEach(p=>{
        const refs = [...p.children.map(c=>below.get(c)),
                      ...p.parents.map(x=>above.get(x))].filter(v=>v!==undefined);
        bary.set(p.id, refs.length ? refs.reduce((s,v)=>s+v,0)/refs.length : null);
      });
      // ממוצע לכל זוג, כדי שהזוג יזוז יחד
      const grp = new Map();
      list.forEach(p=>{
        const k = coupleKey(p);
        (grp.get(k) ?? grp.set(k,[]).get(k)).push(p);
      });
      const blocks = [...grp.values()].map(members=>{
        const vals = members.map(m=>bary.get(m.id)).filter(v=>v!==null);
        return {members, key: vals.length ? vals.reduce((s,v)=>s+v,0)/vals.length : Infinity};
      });
      blocks.sort((a,b)=> a.key - b.key);
      ordered.set(g, blocks.flatMap(b=>b.members));
    });
  }

  // מיקום
  const nodes = [], byId = new Map();
  const gens = [...ordered.keys()].sort((a,b)=>b-a);   // אבות למעלה
  gens.forEach((g, rowIdx)=>{
    const list = ordered.get(g);
    const sizes = list.map(p=>sizeOf(p, direct));
    const total = sizes.reduce((s,z)=>s+z.w,0) + GAP_X*(list.length-1);
    let x = -total/2;
    list.forEach((p,i)=>{
      const z = sizes[i];
      const n = {p, x: x + z.w/2, y: rowIdx*GAP_Y, ...z, direct: direct.has(p.id),
                 focus: p.id===S.focus};
      nodes.push(n); byId.set(p.id, n);
      x += z.w + GAP_X;
    });
  });

  // קשתות
  const links = [];
  S.unions.forEach(u=>{
    const sp = u.spouses.filter(id=>byId.has(id)).map(id=>byId.get(id));
    if(sp.length===2) links.push({type:'spouse', a:sp[0], b:sp[1],
      direct: sp.every(n=>n.direct), union:u});
    const kids = u.children.filter(id=>byId.has(id)).map(id=>byId.get(id));
    if(sp.length && kids.length){
      const px = sp.reduce((s,n)=>s+n.x,0)/sp.length;
      const py = Math.max(...sp.map(n=>n.y+n.h/2));
      kids.forEach(k=>links.push({type:'child', px, py, k,
        direct: k.direct && sp.some(n=>n.direct)}));
    }
  });

  S.nodes = nodes; S.links = links;
}

function sizeOf(p, direct){
  if(!S.focus) return CARD.normal;
  if(p.id===S.focus) return {...CARD.direct, w: CARD.direct.w+14, h: CARD.direct.h+6};
  if(direct.has(p.id)) return CARD.direct;
  return S.mode==='full' ? CARD.faded : CARD.normal;
}

function isAncestorOrSelf(id, root){
  if(id===root) return true;
  const seen=new Set(); const st=[root];
  while(st.length){ const x=st.pop(); if(seen.has(x))continue; seen.add(x);
    S.people.get(x)?.parents.forEach(p=>st.push(p)); }
  return seen.has(id);
}
function isDescendantOrSelf(id, root){
  if(id===root) return true;
  const seen=new Set(); const st=[root];
  while(st.length){ const x=st.pop(); if(seen.has(x))continue; seen.add(x);
    S.people.get(x)?.children.forEach(c=>st.push(c)); }
  return seen.has(id);
}

/* ── ציור ────────────────────────────────────────────────────────── */
const NS='http://www.w3.org/2000/svg';
const el=(t,a={})=>{const e=document.createElementNS(NS,t);
  for(const k in a) e.setAttribute(k,a[k]); return e;};

function render(){
  layout();
  const svg = document.getElementById('tree');
  svg.innerHTML='';
  const g = el('g',{id:'vp'});
  svg.appendChild(g);

  const gl = el('g',{class:'links'}), gn = el('g',{class:'nodes'});
  g.appendChild(gl); g.appendChild(gn);

  S.links.forEach(L=>{
    if(L.type==='spouse'){
      const [a,b] = L.a.x < L.b.x ? [L.a,L.b] : [L.b,L.a];
      gl.appendChild(el('path',{
        d:`M${a.x + a.w/2},${a.y} L${b.x - b.w/2},${b.y}`,
        class:'lnk spouse'+(L.direct?' d':'')}));
    } else {
      const {px,py,k}=L, my=(py + (k.y-k.h/2))/2;
      gl.appendChild(el('path',{
        d:`M${px},${py} C${px},${my} ${k.x},${my} ${k.x},${k.y - k.h/2}`,
        class:'lnk child'+(L.direct?' d':'')}));
    }
  });

  S.nodes.forEach(n=>{
    const p=n.p;
    const grp = el('g',{class:'node'+(n.direct?' d':'')+(n.focus?' f':'')+' b-'+p.branch,
                        transform:`translate(${n.x},${n.y})`, tabindex:0,
                        role:'button', 'aria-label':p.names.he||p.names.latin});
    grp.appendChild(el('rect',{x:-n.w/2, y:-n.h/2, width:n.w, height:n.h, rx:7, class:'box'}));
    grp.appendChild(el('rect',{x:n.w/2-4, y:-n.h/2, width:4, height:n.h, class:'edge'}));

    const t1 = el('text',{y: n.sub? -3 : 4, 'font-size':n.fs, class:'nm'});
    t1.textContent = clip(p.names.he || p.names.latin, n.w, n.fs);
    grp.appendChild(t1);

    if(n.sub){
      const t2 = el('text',{y:15, 'font-size':n.sub, class:'yr'});
      t2.textContent = years(p);
      grp.appendChild(t2);
      const gd = gradeChar(p.grade);
      if(gd){ const t3=el('text',{x:n.w/2-11, y:-n.h/2+14, 'font-size':10, class:'gr g-'+p.grade});
        t3.textContent=gd; grp.appendChild(t3); }
    }
    grp.addEventListener('click',()=>select(p.id));
    grp.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){e.preventDefault();select(p.id);} });
    gn.appendChild(grp);
  });

  fitView(svg,g);
  showCard(S.focus);
}

const clip=(s,w,fs)=>{const max=Math.floor((w-16)/(fs*0.52));
  return s.length>max ? s.slice(0,max-1)+'…' : s;};

function years(p){
  const b=(p.birth||{}).dateHe, d=(p.death||{}).dateHe;
  const y=s=>s? (String(s).match(/\d{4}/)||[''])[0] : '';
  const by=y(b), dy=y(d);
  if(by&&dy) return `${by}–${dy}`;
  if(by) return by;
  if(dy) return `נפ׳ ${dy}`;
  return '';
}
const gradeChar = g => ({documented:'●',probable:'◐',inference:'○'})[g] || '';

function select(id){
  S.focus=id; render();
  history.replaceState(null,'',`?p=${encodeURIComponent(id)}`);
}

/* ── מבט: התאמה, גרירה, זום ──────────────────────────────────────── */
function fitView(svg,g){
  const bb=g.getBBox(), r=svg.getBoundingClientRect(), pad=40;
  const kFit=Math.min((r.width-pad*2)/bb.width,(r.height-pad*2)/bb.height,1.15);
  // אם ההתאמה המלאה מקטינה מדי — לא לכווץ את כל העץ לנקודה, אלא
  // להתמקד בנבחר בקנה מידה קריא ולתת למשתמש לגרור.
  const MIN_READABLE = 0.62;
  if(kFit >= MIN_READABLE){
    S.view={k:kFit, x:r.width/2-(bb.x+bb.width/2)*kFit, y:pad-bb.y*kFit};
  } else {
    const f = S.nodes.find(n=>n.focus) || S.nodes.find(n=>n.direct) || S.nodes[0];
    const k = 0.92;
    S.view={k, x:r.width/2 - (f?f.x:0)*k, y:r.height*0.42 - (f?f.y:0)*k};
  }
  applyView();
}
function applyView(){
  const g=document.getElementById('vp');
  if(g) g.setAttribute('transform',`translate(${S.view.x},${S.view.y}) scale(${S.view.k})`);
}
function wirePanZoom(svg){
  let drag=null;
  svg.addEventListener('pointerdown',e=>{
    if(e.target.closest('.node')) return;
    drag={x:e.clientX,y:e.clientY,vx:S.view.x,vy:S.view.y};
    svg.setPointerCapture(e.pointerId); svg.style.cursor='grabbing';
  });
  svg.addEventListener('pointermove',e=>{
    if(!drag) return;
    S.view.x=drag.vx+(e.clientX-drag.x); S.view.y=drag.vy+(e.clientY-drag.y); applyView();
  });
  const end=()=>{drag=null; svg.style.cursor='grab';};
  svg.addEventListener('pointerup',end); svg.addEventListener('pointercancel',end);
  svg.addEventListener('wheel',e=>{
    e.preventDefault();
    const r=svg.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top;
    const f=e.deltaY<0?1.12:1/1.12, nk=Math.max(.25,Math.min(2.6,S.view.k*f));
    S.view.x=mx-(mx-S.view.x)*(nk/S.view.k);
    S.view.y=my-(my-S.view.y)*(nk/S.view.k);
    S.view.k=nk; applyView();
  },{passive:false});
}

/* ── כרטיס אדם ───────────────────────────────────────────────────── */
function showCard(id){
  const box=document.getElementById('person'); if(!box) return;
  const p=S.people.get(id);
  if(!p){ box.innerHTML=''; return; }
  const place=x=>{const q=S.places.get(x); return q? q.he : (x||'');};
  const ev=(e,label)=>{
    if(!e) return '';
    const bits=[e.dateHe, place(e.place)].filter(Boolean).join(' · ');
    if(!bits) return '';
    return `<div class="row"><dt>${label}</dt><dd>${bits} ${gr(e.grade)}</dd></div>`;
  };
  const gr=g=>g?`<span class="g g-${g}" title="${
      {documented:'מתועד — אקט או מסמך שנקרא',probable:'סביר — אינדקס או הצלבה',
       inference:'השערה — הסקה בלבד'}[g]}"></span>`:'';
  const link=arr=>arr.map(x=>{
      const q=S.people.get(x); return q?`<button class="chip" data-go="${x}">${q.names.he||q.names.latin}</button>`:'';
    }).join('') || '<span class="none">—</span>';

  box.innerHTML = `
    <div class="phead b-${p.branch}">
      <p class="kicker">${p.branch==='moskal'?'מוסקל–שאפיר':'אלברט–ריבנבייריך'}</p>
      <h2>${p.names.he||p.names.latin} ${gr(p.grade)}</h2>
      ${p.names.latin && p.names.latin!==p.names.he ? `<p class="lat">${p.names.latin}</p>`:''}
    </div>
    <dl>
      ${ev(p.birth,'לידה')}${ev(p.death,'פטירה')}
      ${p.occupation?`<div class="row"><dt>עיסוק</dt><dd>${p.occupation}</dd></div>`:''}
      <div class="row"><dt>הורים</dt><dd>${link(p.parents)}</dd></div>
      <div class="row"><dt>בני זוג</dt><dd>${link(p.spouses)}</dd></div>
      <div class="row"><dt>ילדים</dt><dd>${link(p.children)}</dd></div>
    </dl>
    ${p.conflict?`<p class="conflict">${p.conflict}</p>`:''}
    ${(p.names.variants||[]).length?`<p class="vars"><b>כתיבים במסמכים:</b> ${p.names.variants.join(' · ')}</p>`:''}
    ${p.notes && p.notes.length ? `<details><summary>הערות מחקר (${p.notes.length})</summary>
       ${p.notes.map(n=>`<p class="note">${esc(n)}</p>`).join('')}</details>`:''}
  `;
  box.querySelectorAll('[data-go]').forEach(b=>
    b.addEventListener('click',()=>select(b.dataset.go)));
}
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

/* ── פקדים ───────────────────────────────────────────────────────── */
function wireUI(){
  const svg=document.getElementById('tree');
  wirePanZoom(svg);

  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{
    S.mode=b.dataset.mode;
    document.querySelectorAll('[data-mode]').forEach(x=>x.setAttribute('aria-pressed', x===b));
    render();
  }));
  document.querySelectorAll('[data-branch]').forEach(b=>b.addEventListener('click',()=>{
    S.branch=b.dataset.branch;
    document.querySelectorAll('[data-branch]').forEach(x=>x.setAttribute('aria-pressed', x===b));
    render();
  }));

  const box=document.getElementById('find'), list=document.getElementById('findlist');
  box?.addEventListener('input',()=>{
    const q=box.value.trim().toLowerCase();
    list.innerHTML='';
    if(q.length<2) return;
    [...S.people.values()].filter(p=>
      (p.names.he+' '+p.names.latin+' '+(p.names.variants||[]).join(' ')).toLowerCase().includes(q))
      .slice(0,8).forEach(p=>{
        const b=document.createElement('button');
        b.textContent=p.names.he||p.names.latin;
        b.onclick=()=>{select(p.id); box.value=''; list.innerHTML='';};
        list.appendChild(b);
      });
  });
  addEventListener('resize',()=>{const g=document.getElementById('vp'); if(g) fitView(svg,g);});
}

boot();

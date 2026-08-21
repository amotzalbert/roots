/* ═══ «שורשים» — שלוש תצוגות אילן בסגנון MyHeritage ═══════════════════
   משפחה · מניפה · פדיגרי — בורר אחד, נתונים מהגדקום המאוחד.
   SVG טהור, בלי ספריות.                                              */

const S = { people:new Map(), unions:[], places:new Map(), byChild:new Map(),
            bySpouse:new Map(), view:'family', focus:null, branch:'all',
            gens:5, vt:{x:0,y:0,k:1}, drag:null };

const LANG = (document.documentElement.getAttribute('lang')||'he').slice(0,2);
const RTL  = LANG === 'he';
const T = {
  he:{family:'משפחה',fan:'מניפה',pedigree:'פדיגרי',gens:'דורות',
      born:'נולד/ה',died:'נפטר/ה',parents:'הורים',spouses:'בני זוג',children:'ילדים',
      find:'חיפוש אדם…',reset:'מרכוז',unknown:'לא ידוע',variants:'כתיבים במסמכים:',
      notes:n=>`הערות מחקר (${n})`,bio:'לפרק בספר →',
      documented:'מתועד',probable:'סביר',inference:'השערה',
      about:'בערך',before:'לפני',after:'אחרי',between:'בין',and:'ל־',
      hint:'גרירה להזזה · גלגלת לזום · לחיצה על כרטיס ממקדת',
      months:['ינו׳','פבר׳','מרץ','אפר׳','מאי','יוני','יולי','אוג׳','ספט׳','אוק׳','נוב׳','דצמ׳']},
  en:{family:'Family',fan:'Fan chart',pedigree:'Pedigree',gens:'Generations',
      born:'Born',died:'Died',parents:'Parents',spouses:'Spouse(s)',children:'Children',
      find:'Find a person…',reset:'Recentre',unknown:'unknown',variants:'Spellings in documents:',
      notes:n=>`Research notes (${n})`,bio:'Read the chapter →',
      documented:'Documented',probable:'Probable',inference:'Inference',
      about:'about',before:'before',after:'after',between:'between',and:'and',
      hint:'Drag to pan · scroll to zoom · click a card to focus',
      months:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']},
  pl:{family:'Rodzina',fan:'Wachlarz',pedigree:'Rodowód',gens:'Pokolenia',
      born:'Ur.',died:'Zm.',parents:'Rodzice',spouses:'Małżonkowie',children:'Dzieci',
      find:'Znajdź osobę…',reset:'Wyśrodkuj',unknown:'nieznane',variants:'Zapisy w dokumentach:',
      notes:n=>`Notatki badawcze (${n})`,bio:'Rozdział →',
      documented:'Udokumentowane',probable:'Prawdopodobne',inference:'Wnioskowanie',
      about:'ok.',before:'przed',after:'po',between:'między',and:'a',
      hint:'Przeciągnij · przewiń aby przybliżyć · kliknij kartę',
      months:['sty','lut','mar','kwi','maj','cze','lip','sie','wrz','paź','lis','gru']}
}[LANG] || {};

const DATA_BASE = /\/(en|pl)\//.test(location.pathname) ? '../' : '';
const $ = s => document.querySelector(s);
const el = (n,a={}) => { const e=document.createElementNS('http://www.w3.org/2000/svg',n);
  for(const k in a) if(a[k]!=null) e.setAttribute(k,a[k]); return e; };

/* ── תאריכים ─────────────────────────────────────────────────────── */
const MON={JAN:0,FEB:1,MAR:2,APR:3,MAY:4,JUN:5,JUL:6,AUG:7,SEP:8,OCT:9,NOV:10,DEC:11};
function year(d){ const m=/(\d{4})/.exec(d||''); return m?+m[1]:null; }
function fmtDate(d){
  if(!d) return '';
  let s=d.trim(), pre='';
  const q=/^(ABT|EST|CAL|BEF|AFT)\s+/i.exec(s);
  if(q){ pre={ABT:T.about,EST:T.about,CAL:T.about,BEF:T.before,AFT:T.after}[q[1].toUpperCase()]+' '; s=s.slice(q[0].length); }
  const bt=/^BET\s+(.+?)\s+AND\s+(.+)$/i.exec(s);
  if(bt) return `${T.between} ${fmtDate(bt[1])} ${T.and}${fmtDate(bt[2])}`;
  const m=/^(?:(\d{1,2})\s+)?([A-Z]{3})\s+(\d{4})$/i.exec(s);
  if(m){ const mo=T.months[MON[m[2].toUpperCase()]];
    return pre + (m[1] ? (RTL?`${+m[1]} ${mo} ${m[3]}`:`${+m[1]} ${mo} ${m[3]}`) : `${mo} ${m[3]}`); }
  return pre + s;
}
function lifespan(p){
  const b=year(p.birth&&p.birth.date), d=year(p.death&&p.death.date);
  if(!b&&!d) return p.living?'':'';
  return `${b||'?'}–${p.living&&!d?'':(d||'?')}`;
}
const nameOf = p => (LANG==='he' ? (p.names.he||p.names.latin) : (p.names.latin||p.names.he)) || '—';
const latinOf = p => p.names.latin || '';

/* ── ניווט במבנה ─────────────────────────────────────────────────── */
function parentsOf(id){ const out=[];
  for(const u of (S.byChild.get(id)||[])) for(const s of u.spouses) if(!out.includes(s)) out.push(s);
  return out; }
const unionsOf  = id => S.bySpouse.get(id) || [];
function childrenOf(id){ const out=[]; for(const u of unionsOf(id)) for(const c of u.children) if(!out.includes(c)) out.push(c); return out; }
function spousesOf(id){ const out=[]; for(const u of unionsOf(id)) for(const s of u.spouses) if(s!==id&&!out.includes(s)) out.push(s); return out; }

function ancestorLine(id,depth){                    /* מערך לפי דורות */
  const rows=[[id]];
  for(let g=1; g<depth; g++){
    const prev=rows[g-1], row=[];
    for(const pid of prev){
      const ps = pid ? parentsOf(pid) : [];
      const f = ps.find(x=>(S.people.get(x)||{}).sex==='M') ?? ps[0] ?? null;
      const m = ps.find(x=>x!==f) ?? null;
      row.push(f??null, m??null);
    }
    rows.push(row);
    if(row.every(x=>!x)) break;
  }
  return rows;
}


/* ── התאמת שם למקום הפנוי ────────────────────────────────────────
   במקום לקצוץ באמצע מילה («לייבה מו…»), מקצרים קודם את שם המשפחה
   לראשי תיבות («לייבה מ׳»). רק אם גם זה לא נכנס — קיצוץ.          */
const CHW = 0.55;                       /* רוחב תו ממוצע ביחס לגובה הגופן */
const textW = (s,fs) => s.length*fs*CHW;
const LETTER = /[\u0590-\u05FF A-Za-z\u00C0-\u024F]/;   /* עברית או לטינית */
const initial = w => { const m = [...w].find(ch => LETTER.test(ch)); return m ? m + '׳' : ''; };
function fitName(name, avail, fs){
  const fits = s => textW(s,fs) <= avail;
  if(fits(name)) return name;
  /* 1 · לוותר על השם שבסוגריים (שם נעורים / כתיב ארכיוני) */
  const noParen = name.replace(/\s*[({\[][^)}\]]*[)}\]]/g,'').trim();
  if(noParen && fits(noParen)) return noParen;
  /* 2 · לוותר על סעיף שם הנעורים. «לבית» אינה שם ואסור לקצר אותה
         לראשי תיבות — «רודלה אלפרט לבית בוטקובסקה» חייבת לרדת
         ל«רודלה אלפרט», לא ל«רודלה א׳ ל׳ ב׳».                     */
  const noNee = (noParen||name).replace(/\s+(?:לבית|z\s+domu|née|nee|de\s+soltera)\s+.*$/i,'').trim();
  if(noNee && fits(noNee)) return noNee;
  const base = noNee || noParen || name;
  const w = base.split(/\s+/).filter(Boolean);
  /* 3 · לקצר את שם המשפחה לראשי תיבות */
  if(w.length > 1){
    const abbr = (w[0] + ' ' + w.slice(1).map(initial).filter(Boolean).join(' ')).trim();
    if(fits(abbr)) return abbr;
    if(fits(w[0])) return w[0];
  }
  /* 4 · רק אז קיצוץ */
  const max = Math.max(2, Math.floor(avail/(fs*CHW)) - 1);
  return base.slice(0,max).trim() + '…';
}

/* ── צבע וסימון ──────────────────────────────────────────────────── */
const gcol = g => g==='documented'?'var(--ok)':g==='probable'?'var(--gold)':'var(--ink-3)';
/* הצבע מקודד ענף — איזו שושלת, לא איזה מין. */
const BR = p => p&&p.branch==='moskal' ? 'moskal'
              : p&&p.branch==='albert' ? 'albert' : 'both';
function tint(p){ return `var(--${BR(p)}-tint)`; }
function edge(p){ return `var(--${BR(p)})`; }
function line(p){ return `var(--${BR(p)}-line)`; }

/* ── כרטיס בסגנון MyHeritage ─────────────────────────────────────── */
const CW=206, CH=66;
function card(p,x,y,{focus=false,w=CW,h=CH}={}){
  const g=el('g',{class:'mh-card'+(focus?' is-focus':''),transform:`translate(${x},${y})`,
                  tabindex:0,role:'button','aria-label':nameOf(p)});
  g.appendChild(el('rect',{class:'bg',x:0,y:0,width:w,height:h,rx:9,fill:tint(p)}));
  g.appendChild(el('rect',{class:'spine',x:RTL?w-4:0,y:0,width:4,height:h,rx:2,fill:edge(p)}));
  /* עיגול תמונה/ראשי־תיבות */
  const cx = RTL ? w-24 : 24, r=17;
  g.appendChild(el('circle',{class:'av',cx,cy:h/2,r,fill:'var(--paper)',stroke:'var(--rule-2)'}));
  const ini=el('text',{class:'ini',x:cx,y:h/2+5,'text-anchor':'middle',fill:'var(--ink-3)'});
  ini.textContent=(nameOf(p).trim()[0]||'?'); g.appendChild(ini);
  const tx = RTL ? w-48 : 48, dirv = RTL ? 'rtl' : 'ltr';
  const nm=el('text',{class:'nm',x:tx,y:h/2-4,'text-anchor':'start',
                      direction:dirv,'unicode-bidi':'isolate',fill:'var(--ink)'});
  let s=nameOf(p); const cap=Math.max(10,Math.floor((w-58)/7.1));
  if(s.length>cap) s=s.slice(0,cap-1)+'…'; nm.textContent=s; g.appendChild(nm);
  const yr=el('text',{class:'yr',x:tx,y:h/2+14,'text-anchor':'start',
                      direction:dirv,'unicode-bidi':'isolate',fill:'var(--ink-3)'});
  yr.textContent=lifespan(p); g.appendChild(yr);
  if(p.grade) g.appendChild(el('circle',{cx:RTL?10:w-10,cy:10,r:3.4,fill:gcol(p.grade)}));
  g.addEventListener('click',()=>setFocus(p.id));
  g.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){e.preventDefault();setFocus(p.id);} });
  g.addEventListener('mouseenter',()=>showPerson(p.id,true));
  return g;
}
const orth = (x1,y1,x2,y2)=>{ const my=(y1+y2)/2;
  return `M${x1},${y1} V${my} H${x2} V${y2}`; };

/* ══ תצוגה 1 — משפחה ═════════════════════════════════════════════ */
function drawFamily(root){
  const f=S.people.get(S.focus); if(!f) return;
  const GX=26, GY=118;
  const put=(p,x,y,fc)=>{ const c=card(p,x,y,{focus:fc}); root.appendChild(c); return c; };
  const lines=el('g',{class:'lines'}); root.appendChild(lines);
  const line=(d,cls='')=>lines.appendChild(el('path',{class:'lnk '+cls,d}));

  /* שורת המוקד ובני זוג */
  const sp=spousesOf(f.id).map(id=>S.people.get(id)).filter(Boolean);
  const midRow=[f,...sp];
  const midW=midRow.length*CW+(midRow.length-1)*GX;
  let x=-midW/2;
  const midPos=new Map();
  for(const p of midRow){ put(p,x,0,p.id===f.id); midPos.set(p.id,x); x+=CW+GX; }
  for(let i=1;i<midRow.length;i++){
    const a=midPos.get(midRow[i-1].id)+CW, b=midPos.get(midRow[i].id);
    line(`M${a},${CH/2} H${b}`,'spouse');
  }

  /* הורים */
  const par=parentsOf(f.id).map(id=>S.people.get(id)).filter(Boolean);
  if(par.length){
    const w=par.length*CW+(par.length-1)*GX; let px=-w/2;
    const anchor=midPos.get(f.id)+CW/2;
    const jy=-GY+CH+((GY-CH)/2);
    for(const p of par){ put(p,px,-GY,false);
      line(`M${px+CW/2},${-GY+CH} V${jy}`); px+=CW+GX; }
    line(`M${-w/2+CW/2},${jy} H${w/2-CW/2}`);
    line(`M${anchor},${jy} V0`);
  }

  /* ילדים */
  const kids=childrenOf(f.id).map(id=>S.people.get(id)).filter(Boolean);
  if(kids.length){
    const w=kids.length*CW+(kids.length-1)*GX; let kx=-w/2;
    const jy=CH+((GY-CH)/2), anchor=midPos.get(f.id)+CW/2;
    line(`M${anchor},${CH} V${jy}`);
    if(kids.length>1) line(`M${-w/2+CW/2},${jy} H${w/2-CW/2}`);
    for(const p of kids){ put(p,kx,GY,false);
      line(`M${kx+CW/2},${jy} V${GY}`); kx+=CW+GX; }
  }

  /* סבים וסבתות — שורה דהויה */
  const gp=[];
  for(const p of par) for(const q of parentsOf(p.id)) gp.push(S.people.get(q));
  const gps=gp.filter(Boolean);
  if(gps.length){
    const w=gps.length*(CW*0.86)+(gps.length-1)*GX; let gx=-w/2;
    for(const p of gps){ const c=card(p,gx,-GY*2,{w:CW*0.86,h:CH*0.84});
      c.classList.add('faded'); root.appendChild(c); gx+=CW*0.86+GX; }
  }
}

/* ══ תצוגה 2 — מניפה ═════════════════════════════════════════════ */
function drawFan(root){
  const rows=ancestorLine(S.focus,S.gens);
  const R0=58, RING=74, SPAN=Math.PI*1.42, START=-Math.PI/2-SPAN/2;
  const arc=(r1,r2,a1,a2)=>{
    const P=(r,a)=>[r*Math.cos(a),r*Math.sin(a)];
    const [x1,y1]=P(r1,a1),[x2,y2]=P(r1,a2),[x3,y3]=P(r2,a2),[x4,y4]=P(r2,a1);
    const big=(a2-a1)>Math.PI?1:0;
    return `M${x1},${y1} A${r1},${r1} 0 ${big} 1 ${x2},${y2} L${x3},${y3} A${r2},${r2} 0 ${big} 0 ${x4},${y4} Z`;
  };
  /* מרכז */
  const f=S.people.get(S.focus);
  if(f){
    const g=el('g',{class:'fan-hub',tabindex:0});
    g.appendChild(el('circle',{r:R0,fill:tint(f),stroke:edge(f),'stroke-width':2.5}));
    const t1=el('text',{y:-4,'text-anchor':'middle',class:'nm',fill:'var(--ink)'});
    let s=nameOf(f); if(s.length>16) s=s.slice(0,15)+'…'; t1.textContent=s;
    const t2=el('text',{y:14,'text-anchor':'middle',class:'yr',fill:'var(--ink-3)'});
    t2.textContent=lifespan(f);
    g.append(t1,t2); root.appendChild(g);
  }
  for(let gi=1; gi<rows.length; gi++){
    const row=rows[gi], n=row.length, step=SPAN/n;
    const r1=R0+ (gi-1)*RING + 8, r2=r1+RING-8;
    for(let i=0;i<n;i++){
      const a1=START+i*step+0.006, a2=a1+step-0.012;
      const id=row[i], p=id?S.people.get(id):null;
      const seg=el('path',{class:'fan-seg'+(p?'':' empty'),d:arc(r1,r2,a1,a2),
        fill:p?tint(p):'var(--plinth-2)',stroke:p?line(p):'var(--rule)','stroke-width':1});
      if(p){
        seg.setAttribute('tabindex','0'); seg.setAttribute('role','button');
        seg.setAttribute('aria-label',nameOf(p));
        seg.addEventListener('click',()=>setFocus(p.id));
        seg.addEventListener('mouseenter',()=>showPerson(p.id,true));
        seg.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();setFocus(p.id);}});
      }
      root.appendChild(seg);
      if(!p) continue;
      /* רצועת הענף — קשת עבה בשפה הפנימית של הטבעת, כמו בשושלות המודפסות */
      root.appendChild(el('path',{class:'fan-band',d:arc(r1,r1+3.5,a1,a2),
        fill:edge(p),stroke:'none'}));
      /* ── תווית: לרוחב הקשת כברירת מחדל, לאורך הרדיוס כשאין מקום ──
         בדורות החיצוניים המשבצת צרה לרוחב אבל גבוהה לאורך הרדיוס,
         ולכן שם מסובבים את הכיתוב במקום לקצץ אותו.                 */
      const am=(a1+a2)/2, rm=(r1+r2)/2;
      const deg=am*180/Math.PI;
      const fs = gi<=2?12:gi===3?10.5:9;
      const tangential = step*rm - 8;      /* מקום לרוחב הקשת */
      const radial     = (r2-r1) - 14;     /* מקום לאורך הרדיוס */
      const full = nameOf(p);
      const needed = textW(full,fs);
      const radialMode = needed > tangential && radial > tangential;
      const avail = radialMode ? radial : tangential;

      let rot;
      if(radialMode){
        const d=((deg%360)+360)%360;       /* הפוך? מסובבים ב-180 כדי לא לקרוא הפוך */
        rot = (d>90 && d<270) ? deg+180 : deg;
      } else {
        rot = (deg>0 && deg<180) ? deg-90 : deg+90;
      }
      const tg=el('g',{transform:`translate(${rm*Math.cos(am)},${rm*Math.sin(am)}) rotate(${rot})`,
                       class:'fan-lbl'+(radialMode?' radial':'')});

      const s = fitName(full, avail, fs);
      /* שנים רק כשיש באמת מקום לשורה שנייה */
      const room2 = radialMode ? tangential >= fs*2.2 : gi<=3;
      const t=el('text',{'text-anchor':'middle',y:room2?-2:3,class:'nm',fill:'var(--ink)',
                         'font-size':fs});
      t.textContent=s; tg.appendChild(t);
      if(room2 && gi<=4){
        const y2=el('text',{'text-anchor':'middle',y:gi<=2?12:11,class:'yr',fill:'var(--ink-3)',
                      'font-size':gi<=2?9.5:8.5});
        y2.textContent=lifespan(p); tg.appendChild(y2);
      }
      if(s!==full){ const ttl=el('title'); ttl.textContent=full; tg.appendChild(ttl); }
      root.appendChild(tg);
    }
  }
}

/* ══ תצוגה 3 — פדיגרי ════════════════════════════════════════════ */
function drawPedigree(root){
  const rows=ancestorLine(S.focus,S.gens);
  const CWp=186, CHp=56, GAPY=14, COLG=54;
  const dir = RTL ? -1 : 1;
  const lines=el('g'); root.appendChild(lines);
  const lastGen=rows.length-1, leaf=CHp+GAPY;
  const posOf=new Map();
  /* מציבים מהדור האחרון אחורה */
  for(let gi=lastGen; gi>=0; gi--){
    const row=rows[gi], n=row.length;
    for(let i=0;i<n;i++){
      const key=gi+':'+i;
      if(gi===lastGen){ posOf.set(key, i*leaf); }
      else { const a=posOf.get((gi+1)+':'+(i*2)), b=posOf.get((gi+1)+':'+(i*2+1));
             posOf.set(key,(a+b)/2); }
    }
  }
  const totalH=(rows[lastGen].length-1)*leaf;
  for(let gi=0; gi<rows.length; gi++){
    const row=rows[gi];
    const x = dir*gi*(CWp+COLG) - (dir<0?CWp:0);
    for(let i=0;i<row.length;i++){
      const y=posOf.get(gi+':'+i)-totalH/2;
      const id=row[i];
      if(id){ const p=S.people.get(id);
        root.appendChild(card(p,x,y,{focus:gi===0,w:CWp,h:CHp})); }
      else { root.appendChild(el('rect',{class:'ped-empty',x,y,width:CWp,height:CHp,rx:8,
              fill:'none',stroke:'var(--rule)','stroke-dasharray':'3 4'})); }
      if(gi<rows.length-1){
        const kids=[posOf.get((gi+1)+':'+(i*2)),posOf.get((gi+1)+':'+(i*2+1))];
        if(kids[0]==null) continue;
        const xs = dir>0 ? x+CWp : x;
        const xe = dir>0 ? x+CWp+COLG/2 : x-COLG/2;
        const xt = dir>0 ? x+CWp+COLG : x-COLG;
        lines.appendChild(el('path',{class:'lnk',
          d:`M${xs},${y+CHp/2} H${xe} V${kids[0]-totalH/2+CHp/2} `}));
        lines.appendChild(el('path',{class:'lnk',
          d:`M${xe},${y+CHp/2} V${kids[1]-totalH/2+CHp/2} H${xt}`}));
        lines.appendChild(el('path',{class:'lnk',
          d:`M${xe},${kids[0]-totalH/2+CHp/2} H${xt}`}));
      }
    }
  }
}

/* ── ציור ראשי + זום/הזזה ────────────────────────────────────────── */
function render(){
  const svg=$('#tree'); svg.innerHTML='';
  const root=el('g',{id:'vp'}); svg.appendChild(root);
  if(!S.focus) return;
  ({family:drawFamily,fan:drawFan,pedigree:drawPedigree}[S.view])(root);
  fitSoon();
  showPerson(S.focus);
}
function applyVT(){ const g=$('#vp'); if(g)
  g.setAttribute('transform',`translate(${S.vt.x},${S.vt.y}) scale(${S.vt.k})`); }
function fit(){
  const svg=$('#tree'), g=$('#vp'); if(!g) return;
  g.removeAttribute('transform');
  let b; try{ b=g.getBBox(); }catch(e){ return; }
  const r=svg.getBoundingClientRect();
  if(!b.width||!b.height||!r.width||!r.height) return;
  const k=Math.max(.12, Math.min(r.width/(b.width+46), r.height/(b.height+46), 1.5));
  S.vt={k, x:r.width/2-(b.x+b.width/2)*k, y:r.height/2-(b.y+b.height/2)*k};
  applyVT();
}
function fitSoon(){ requestAnimationFrame(()=>requestAnimationFrame(fit));
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(fit); }
function wireCanvas(){
  const svg=$('#tree');
  svg.addEventListener('wheel',e=>{ e.preventDefault();
    const r=svg.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top;
    const f=Math.exp(-e.deltaY*0.0014), nk=Math.min(3,Math.max(.15,S.vt.k*f));
    S.vt.x=mx-(mx-S.vt.x)*(nk/S.vt.k); S.vt.y=my-(my-S.vt.y)*(nk/S.vt.k);
    S.vt.k=nk; applyVT(); },{passive:false});
  const down=e=>{ const t=e.touches?e.touches[0]:e;
    S.drag={x:t.clientX-S.vt.x,y:t.clientY-S.vt.y}; svg.style.cursor='grabbing'; };
  const move=e=>{ if(!S.drag) return; const t=e.touches?e.touches[0]:e;
    S.vt.x=t.clientX-S.drag.x; S.vt.y=t.clientY-S.drag.y; applyVT(); };
  const up=()=>{ S.drag=null; svg.style.cursor='grab'; };
  svg.addEventListener('mousedown',down); addEventListener('mousemove',move); addEventListener('mouseup',up);
  svg.addEventListener('touchstart',down,{passive:true});
  svg.addEventListener('touchmove',move,{passive:true}); addEventListener('touchend',up);
  addEventListener('resize',()=>fitSoon());
}

/* ── לוח האדם ────────────────────────────────────────────────────── */
function placeName(id){ const p=S.places.get(id);
  return p ? (LANG==='he'?(p.he||p.latin):(p.latin||p.he)) : id; }
function showPerson(id,peek){
  const p=S.people.get(id); const box=$('#person'); if(!p||!box) return;
  const ev=e=>{ if(!e) return `<span class="none">${T.unknown}</span>`;
    const d=fmtDate(e.date), pl=e.place?placeName(e.place):'';
    return [d,pl].filter(Boolean).join(' · ')||`<span class="none">${T.unknown}</span>`; };
  const chips=(ids)=>ids.length? ids.map(x=>{const q=S.people.get(x);
      return q?`<button class="chip" data-go="${x}">${nameOf(q)}</button>`:''}).join('')
    : `<span class="none">—</span>`;
  const lat=latinOf(p);
  box.innerHTML=`
   <div class="phead b-${p.branch}">
     <h2>${nameOf(p)}</h2>
     ${lat&&lat!==nameOf(p)?`<p class="lat">${lat}</p>`:''}
     ${p.grade?`<span class="gradepill" style="--c:${gcol(p.grade)}">${T[p.grade]||p.grade}</span>`:''}
     ${p.notInGedcom?'<span class="gradepill" style="--c:var(--ink-3)">≠GEDCOM</span>':''}
   </div>
   <dl>
     <div class="row"><dt>${T.born}</dt><dd>${ev(p.birth)}</dd></div>
     <div class="row"><dt>${T.died}</dt><dd>${p.living?'<span class="none">—</span>':ev(p.death)}</dd></div>
     ${p.occupation?`<div class="row"><dt>—</dt><dd>${p.occupation}</dd></div>`:''}
     <div class="row"><dt>${T.parents}</dt><dd>${chips(parentsOf(p.id))}</dd></div>
     <div class="row"><dt>${T.spouses}</dt><dd>${chips(spousesOf(p.id))}</dd></div>
     <div class="row"><dt>${T.children}</dt><dd>${chips(childrenOf(p.id))}</dd></div>
   </dl>
   ${p.names.variants&&p.names.variants.length?`<p class="vars"><b>${T.variants}</b>${p.names.variants.join(' · ')}</p>`:''}
   ${p.bioChapter?`<p style="margin:.8rem 0 0"><a class="biolink" href="${DATA_BASE}${p.bioChapter}">${T.bio}</a></p>`:''}
   ${p.notes&&p.notes.length?`<details><summary>${T.notes(p.notes.length)}</summary>
      ${p.notes.map(n=>`<p class="note">${String(n).replace(/</g,'&lt;')}</p>`).join('')}</details>`:''}`;
  box.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>setFocus(b.dataset.go));
}

/* ── מצב ─────────────────────────────────────────────────────────── */
function setFocus(id){ if(!S.people.has(id)) return;
  S.focus=id; history.replaceState(null,'','#'+id); render(); }
function setView(v){ S.view=v;
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===v)));
  $('#gensWrap').hidden = (v==='family');
  render(); }

/* ── חיפוש ───────────────────────────────────────────────────────── */
function wireFind(){
  const inp=$('#find'), list=$('#findlist'); if(!inp) return;
  inp.placeholder=T.find;
  const close=()=>{ list.innerHTML=''; list.style.display='none'; };
  close();
  inp.addEventListener('input',()=>{
    const q=inp.value.trim().toLowerCase(); if(q.length<2) return close();
    const hits=[...S.people.values()].filter(p=>
      (p.names.he||'').toLowerCase().includes(q)||(p.names.latin||'').toLowerCase().includes(q)
    ).slice(0,10);
    if(!hits.length) return close();
    list.innerHTML=hits.map(p=>`<button data-id="${p.id}">${nameOf(p)} <span style="opacity:.6">${lifespan(p)}</span></button>`).join('');
    list.style.display='flex';
    list.querySelectorAll('button').forEach(b=>b.onclick=()=>{ setFocus(b.dataset.id); inp.value=''; close(); });
  });
  document.addEventListener('click',e=>{ if(!e.target.closest('.findwrap')) close(); });
}

/* ── עלייה ───────────────────────────────────────────────────────── */
Promise.all([
  fetch(DATA_BASE+'data/people.unified.json').then(r=>r.ok?r.json():fetch(DATA_BASE+'data/people.json').then(r=>r.json())),
  fetch(DATA_BASE+'data/unions.unified.json').then(r=>r.ok?r.json():fetch(DATA_BASE+'data/unions.json').then(r=>r.json())),
  fetch(DATA_BASE+'data/places.json').then(r=>r.ok?r.json():[]).catch(()=>[]),
  fetch(DATA_BASE+'data/id-aliases.json').then(r=>r.ok?r.json():{}).catch(()=>({}))
]).then(([people,unions,places,aliases])=>{
  people.forEach(p=>S.people.set(p.id,p));
  S.unions=unions;
  (Array.isArray(places)?places:Object.values(places||{})).forEach(pl=>pl&&pl.id&&S.places.set(pl.id,pl));
  for(const u of unions){
    for(const c of u.children){ if(!S.byChild.has(c)) S.byChild.set(c,[]); S.byChild.get(c).push(u); }
    for(const s of u.spouses){ if(!S.bySpouse.has(s)) S.bySpouse.set(s,[]); S.bySpouse.get(s).push(u); }
  }
  let want=decodeURIComponent(location.hash.slice(1));
  if(aliases[want]) want=aliases[want];
  S.focus = S.people.has(want) ? want
    : (S.people.has('p-amotz-albert') ? 'p-amotz-albert' : people[0] && people[0].id);
  document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
  const gsel=$('#gens'); if(gsel) gsel.onchange=()=>{ S.gens=+gsel.value; render(); };
  const rb=$('#recentre'); if(rb) rb.onclick=fit;
  wireCanvas(); wireFind(); setView('family');
}).catch(e=>{ console.error(e);
  const b=$('#person'); if(b) b.textContent='שגיאה בטעינת הנתונים'; });

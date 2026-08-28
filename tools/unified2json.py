#!/usr/bin/env python3
"""unified2json.py — מייצר people.unified.json מהגדקום המאוחד,
ומעשיר אותו מהקבצים המתוחזקים ידנית (שמות עבריים, פרקי ספר, מקומות, דירוגים).

קלט : site/data/albert-moskal-UNIFIED.ged
       site/data/people.albert.json · people.moskal.json · he-names.albert.json  (להעשרה)
פלט  : site/data/people.unified.json · unions.unified.json
"""
import re, json, unicodedata
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
GED  = DATA / "albert-moskal-UNIFIED.ged"

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9]+', '', s.lower())

def given_key(given):
    g = norm(given)
    return ('G:' + g) if len(g) > 2 else None

def keys_for(latin, given, surname):
    """מפתחות התאמה — כולל צורת «née», שבה שם המשפחה בקובץ הידני הוא שם הנישואין."""
    ks = {norm(latin)}
    if given and surname:
        ks.add(norm(given + surname))
        pass
    m = re.match(r'^(.*?)\s+n[eé]e\s+(.*)$', latin or '', re.I)
    if m: ks.add(norm(m.group(1))); ks.add(norm(m.group(2)))
    return {k for k in ks if len(k) > 2}

def slug(latin, xid):
    s = unicodedata.normalize('NFKD', latin or '').encode('ascii','ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return 'p-' + (s or xid.strip('@').lower())

# ── קריאת הגדקום ────────────────────────────────────────────────────────
raw = GED.read_text(encoding='utf-8')
def records(tag):
    return re.finditer(r'^0 (@'+tag+r'\d+@) '+('INDI' if tag=='I' else 'FAM')+r'\n((?:[1-9] .*\n)*)', raw, re.M)

def unfold(body):
    out=[]
    for line in body.split('\n'):
        m=re.match(r'^(\d) (CONT|CONC) ?(.*)$', line)
        if m and out: out[-1] += ('\n' if m.group(2)=='CONT' else '') + m.group(3)
        elif line.strip(): out.append(line)
    return out

def sub(body, tag, lvl=1):
    m = re.search(r'^'+str(lvl)+r' '+tag+r'(?: (.*))?$', body, re.M)
    return (m.group(1) or '').strip() if m else None

def event(body, tag):
    m = re.search(r'^1 '+tag+r'\n((?:[2-9] .*\n)*)', body, re.M)
    if not m: return None
    blk = m.group(1)
    d = re.search(r'^2 DATE (.+)$', blk, re.M)
    p = re.search(r'^2 PLAC (.+)$', blk, re.M)
    if not d and not p: return None
    return {"date": d.group(1).strip() if d else None,
            "place": p.group(1).strip() if p else None}

GRADE = [(r'\(documented', 'documented'), (r'\(probable', 'probable'), (r'\(inference', 'inference')]

people, unions, idmap = {}, [], {}
for m in records('I'):
    xid, body = m.group(1), m.group(2)
    lines = unfold(body)
    joined = '\n'.join(lines)
    nm = re.search(r'^1 NAME (.+)$', joined, re.M)
    rawname = nm.group(1) if nm else ''
    given = (sub(joined,'GIVN',2) or rawname.split('/')[0]).strip()
    surname = (sub(joined,'SURN',2) or (rawname.split('/')[1] if '/' in rawname else '')).strip()
    latin = ' '.join(x for x in (given, surname) if x).strip()
    pid = slug(latin, xid)
    while pid in people: pid += '-' + xid.strip('@').lower()
    idmap[xid] = pid
    nicks = [n.strip() for n in re.findall(r'^2 NICK (.+)$', joined, re.M)]
    nicks = [re.split(r'\s*[(（]', n)[0].strip() for n in nicks]
    notes = [n.strip() for n in re.findall(r'^1 NOTE (.+?)(?=\n1 |\Z)', joined, re.M|re.S)]
    low = ' '.join(notes).lower()
    grade = next((g for pat,g in GRADE if re.search(pat, low)), None)
    birth, death = event(joined,'BIRT'), event(joined,'DEAT')
    # ציטוטי מקור מהגדקום עצמו — @S84@ ⇒ s-s84. עד 29.8.2026 לא נקראו כלל,
    # והמקורות הגיעו רק מהקבצים הידניים; מקור שנוסף לגדקום בלבד נעלם מהאתר.
    ged_sources = [f"s-{s.strip('@').lower()}" for s in
                   re.findall(r'^1 SOUR (@S[^@]+@)$', joined, re.M)]
    branch = 'albert'
    mb = re.search(r'_BRANCH\s+(albert|moskal|both)', joined)
    if mb: branch = mb.group(1)
    elif int(re.sub(r'\D','',xid)) >= 1000: branch = 'moskal'
    people[pid] = {"id":pid, "gedcomId":xid.strip('@'), "branch":branch,
        "names":{"he":"", "latin":latin, "given":given, "surname":surname, "variants":[x for x in nicks if x]},
        "sex": sub(joined,'SEX'), "living": death is None and not (birth or {}).get('date'),
        "birth":birth, "death":death, "occupation": sub(joined,'OCCU') or "",
        "notes":notes, "grade":grade, "sources":ged_sources, "photos":[], "docs":[], "bioChapter":None}

for m in records('F'):
    xid, body = m.group(1), m.group(2)
    j = '\n'.join(unfold(body))
    h, w = sub(j,'HUSB'), sub(j,'WIFE')
    kids = re.findall(r'^1 CHIL (@I\d+@)$', j, re.M)
    unions.append({"id":"u-"+xid.strip('@').lower(), "gedcomId":xid.strip('@'),
        "branch":"albert",
        "spouses":[idmap[x] for x in (h,w) if x and x in idmap],
        "children":[idmap[k] for k in kids if k in idmap],
        "marriage": event(j,'MARR'), "notes":[]})

# ── תיקון דגל living ────────────────────────────────────────────────────
# הכלל הגולמי ("אין תאריך לידה ואין פטירה ⇒ חי") סימן עשרות אבות-קדמונים כחיים
# והסתיר אותם מהאתר.  כאן מסיקים מוות מעוגן תאריכי לפני 1900 ומפיצים אותו
# ‏**כלפי מעלה בלבד** — הורה של מת מת, בן/בת זוג של מת מת.  לא כלפי ילדים:
# ילדו של אדם שנולד 1890 עשוי להיות בחיים.  מי שאין לו עוגן נשאר כפי שהיה,
# כדי שלא נפרסם פרטיו של אדם חי.
def _fix_living(people, unions):
    parents, spouses = {}, {}
    for u in unions:
        sp, ch = u.get('spouses') or [], u.get('children') or []
        for s in sp:
            spouses.setdefault(s, set()).update(x for x in sp if x != s)
        for c in ch:
            parents.setdefault(c, set()).update(sp)
    def _yr(p):
        ys = []
        for k in ('birth', 'death'):
            ys += [int(x) for x in re.findall(r'\b(1[5-9]\d\d)\b', (p.get(k) or {}).get('date') or '')]
        return min(ys) if ys else None
    dead = {pid for pid, p in people.items() if (_yr(p) or 9999) < 1900}
    for _ in range(8):
        grow = set()
        for pid in dead:
            grow |= parents.get(pid, set()) | spouses.get(pid, set())
        if grow <= dead: break
        dead |= grow
    n = 0
    for pid in dead:
        if pid in people and people[pid].get('living'):
            people[pid]['living'] = False; n += 1
    return n

_n = _fix_living(people, unions)
if _n: print(f"  living: {_n} אנשים סומנו כנפטרים לפי עוגן לפני 1900")

# ── העשרה מהקבצים המתוחזקים ─────────────────────────────────────────────
# כל מפתח נקלט רק אם הוא חד־ערכי בשני הצדדים — אחרת שני אנשים שונים היו ממוזגים.
curated_all = []
for fn in ("people.moskal.json", "people.albert.json"):
    fp = DATA/fn
    if fp.exists(): curated_all += json.loads(fp.read_text(encoding='utf-8'))

def all_keys(latin, given, surname):
    ks = keys_for(latin, given, surname)
    gk = given_key(given)
    if gk: ks.add(gk)
    return ks

def index_by_key(items, get):
    idx = {}
    for it in items:
        n = get(it)
        for k in all_keys(n.get('latin',''), n.get('given',''), n.get('surname','')):
            idx.setdefault(k, []).append(it)
    return idx


# ── שער בטיחות 28.8.2026: התאמה לפי שם פרטי בלבד (מפתח "G:") אינה מספיקה ──
# מקרה שחשף את הבאג: הוספת "Sara Rutkowska" (ענף אלברט, נפטרה 1823 ברודה סטראווצ׳ינסקה)
# גרמה למפתח G:sara להצביע עליה, והיא בלעה את הזהות של "Sara Soche Moskal" מהענף האימהי —
# שם עברי, כינויים, ענף, ואפילו חברות בזיווג u-f1007. מעכשיו מפתח G: נדחה אם שני
# הצדדים נושאים שם משפחה והם שונים, או אם הענפים שונים.
REJECTED_G = []
def g_match_ok(ged_names, cur_names):
    gs, cs = norm(ged_names.get('surname','')), norm((cur_names or {}).get('surname',''))
    return not (gs and cs and gs != cs)

MANUAL = {}
mp_ = DATA/"curated-to-gedcom.map.json"
if mp_.exists(): MANUAL = json.loads(mp_.read_text(encoding='utf-8'))
by_ged = {p_['gedcomId']: p_ for p_ in people.values()}

cur_idx = index_by_key(curated_all, lambda x: x.get('names') or {})
ged_idx = index_by_key(list(people.values()), lambda x: x['names'])
GOOD = {k for k in cur_idx if len(cur_idx[k]) == 1 and len(ged_idx.get(k, [])) == 1}
enrich = {k: cur_idx[k][0] for k in GOOD}
alias  = {k: ged_idx[k][0]['id'] for k in GOOD}
print(f"unambiguous match keys: {len(GOOD)}  (dropped ambiguous: {len(set(cur_idx) & set(ged_idx)) - len(GOOD)})")

henames = {}
hp = DATA/"he-names.albert.json"
if hp.exists():
    for gid, v in json.loads(hp.read_text(encoding='utf-8')).items():
        if isinstance(v, dict) and v.get('he'): henames[gid] = v['he']

matched = set()
hits = 0
for p in people.values():
    if p['gedcomId'] in henames: p['names']['he'] = henames[p['gedcomId']]
    src = None; via_manual = False
    for cid, ent in MANUAL.items():                    # ← זהות מוכחת גוברת על שם
        if ent['gedcomId'] == p['gedcomId']:
            src = next((c for c in curated_all if c['id'] == cid), None)
            if src: via_manual = True; break
    if not src:
        for k in all_keys(p['names']['latin'], p['names']['given'], p['names']['surname']):
            if k not in enrich: continue
            cand = enrich[k]
            if k.startswith('G:') and not g_match_ok(p['names'], cand.get('names')):
                REJECTED_G.append((p['gedcomId'], p['names']['latin'], cand['id'],
                                   ((cand.get('names') or {}).get('latin') or '')))
                continue
            src = cand; break
    if not src: continue
    hits += 1; matched.add(src['id'])
    sn = src.get('names') or {}
    if not p['names']['he'] and sn.get('he'): p['names']['he'] = sn['he']
    # שם פרטי חלופי מהקובץ הידני נשמר ככתיב, לא כזהות נפרדת
    if via_manual and sn.get('given') and norm(sn['given']) != norm(p['names']['given']):
        if sn['given'] not in p['names']['variants']: p['names']['variants'].append(sn['given'])
    if sn.get('variants'):                       # מיזוג, לא דריסה — כינויי הגדקום נשמרים
        seen_v = {v.lower() for v in p['names']['variants']}
        p['names']['variants'] += [v for v in sn['variants'] if v.lower() not in seen_v]
    for fld in ('bioChapter','photos','docs','gen'):
        if src.get(fld): p[fld] = src[fld]
    # מקורות — איחוד, לא דריסה: הקובץ הידני מוסיף לציטוטים שבגדקום ולא מוחק אותם
    if src.get('sources'):
        have = set(p['sources'])
        p['sources'] += [s for s in src['sources'] if s not in have]
    if src.get('grade') and not p['grade']: p['grade'] = src['grade']
    if src.get('branch') in ('moskal','both'): p['branch'] = src['branch']
    p['siteId'] = src['id']
    for ev in ('birth','death'):
        if src.get(ev) and p.get(ev):
            for kk in ('place','grade','dateHe','notes'):
                if src[ev].get(kk) and not p[ev].get(kk): p[ev][kk] = src[ev][kk]
        elif src.get(ev) and not p.get(ev):
            p[ev] = src[ev]

# ── מעבר שני: אנשים וזיווגים שקיימים רק בקבצים הידניים ──────────────────
curated, curated_unions = curated_all, []
for ufn in ("unions.moskal.json", "unions.albert.json"):
    up = DATA/ufn
    if up.exists(): curated_unions += json.loads(up.read_text(encoding='utf-8'))

idmap2, added = {}, 0
for c in curated:
    cn = c.get('names') or {}
    tgt = None
    if c['id'] in MANUAL:
        tgt = by_ged.get(MANUAL[c['id']]['gedcomId'], {}).get('id')
    if not tgt and c['id'] in matched:
        for k in all_keys(cn.get('latin',''), cn.get('given',''), cn.get('surname','')):
            if k not in alias: continue
            if k.startswith('G:') and not g_match_ok(people[alias[k]]['names'], cn): continue
            tgt = alias[k]; break
    if tgt:
        idmap2[c['id']] = tgt
        continue
    # לא קיים בגדקום — נשמר כמות שהוא, מסומן לרישום עתידי
    nid = c['id']
    while nid in people: nid += '-c'
    idmap2[c['id']] = nid
    rec = dict(c); rec['id'] = nid; rec['notInGedcom'] = True
    rec.setdefault('branch', 'moskal'); rec.setdefault('notes', [])
    people[nid] = rec; added += 1

seen_u = {tuple(sorted(u['spouses'])) for u in unions if u['spouses']}
for cu in curated_unions:
    sp = [idmap2.get(x, x) for x in cu.get('spouses', [])]
    ch = [idmap2.get(x, x) for x in cu.get('children', [])]
    sp = [x for x in sp if x in people]; ch = [x for x in ch if x in people]
    if not sp and not ch: continue
    key = tuple(sorted(sp))
    if key and key in seen_u:                      # הזיווג כבר מהגדקום — משלים ילדים חסרים
        tgt = next(u for u in unions if tuple(sorted(u['spouses'])) == key)
        for k in ch:
            if k not in tgt['children']: tgt['children'].append(k)
        if cu.get('marriage') and not tgt.get('marriage'): tgt['marriage'] = cu['marriage']
        continue
    nu = dict(cu); nu['spouses'] = sp; nu['children'] = ch
    nu['id'] = cu['id'] if not any(u['id'] == cu['id'] for u in unions) else cu['id'] + '-c'
    unions.append(nu); seen_u.add(key)

print(f"carried over from curated files: {added} people")

# ── ניקוי: זיווג שכל בני־הזוג והילדים שלו כלולים בזיווג אחר הוא שריד מיותר ──
def _sets(u): return set(u.get('spouses') or []), set(u.get('children') or [])
drop = set()
for i, a in enumerate(unions):
    sa, ca = _sets(a)
    if not (sa or ca): continue
    for j, b in enumerate(unions):
        if i == j or j in drop: continue
        sb, cb = _sets(b)
        if sa <= sb and ca <= cb and (len(sa) + len(ca) < len(sb) + len(cb)):
            drop.add(i); break
if drop:
    print(f"זיווגים שנבלעו והוסרו: {len(drop)}  ({', '.join(unions[i]['id'] for i in sorted(drop))})")
    unions[:] = [u for k, u in enumerate(unions) if k not in drop]

# ── שער בטיחות: אדם «חדש» שחולק שם־חלופה + אותו מקום משפחתי עם קיים = כפילות ──
def variants_of(x):
    n = x.get('names') or x['names']
    out = {norm(n.get('given',''))}
    for v in (n.get('variants') or []):
        if v: out.add(norm(v.split()[0]))
    return out - {''}
kin = {}
for u in unions:
    for sp in u['spouses']:
        kin.setdefault(sp, set()).update(x for x in u['spouses'] if x != sp)
    for ch in u['children']:
        kin.setdefault(ch, set()).update(u['spouses'])
suspects = []
for nid in [p_['id'] for p_ in people.values() if p_.get('notInGedcom')]:
    a = people[nid]; av, ak = variants_of(a), kin.get(nid, set())
    for other in people.values():
        if other['id'] == nid or other.get('notInGedcom'): continue
        if not (av & variants_of(other)): continue
        shared = ak & kin.get(other['id'], set())
        if shared:
            suspects.append((nid, other['id'], sorted(shared)[:2]))
            break
nick_hits = []
for nid in [p_['id'] for p_ in people.values() if p_.get('notInGedcom')]:
    g = norm(people[nid]['names'].get('given',''))
    if len(g) < 3: continue
    for other in people.values():
        if other['id'] == nid or other.get('notInGedcom'): continue
        if g in {norm(v.split()[0]) for v in (other['names'].get('variants') or []) if v}:
            nick_hits.append((nid, other['id'], other['names']['latin']))
            break
if nick_hits:
    print("\n*** עצור — שם של «חדש» תואם כינוי של אדם קיים: ***")
    for a, b, nm in nick_hits:
        print(f"    {a}  הוא ככל הנראה הכינוי של  {b} «{nm}»")
    raise SystemExit("הרצה נעצרה: התנגשות שם־כינוי.")

if suspects:
    print("\n*** עצור — מועמדים לכפילות, אל תוסיף לגדקום לפני בדיקה ידנית: ***")
    for a, b, sh in suspects:
        print(f"    {a}  ≟  {b}   (קרובים משותפים: {sh})")
    raise SystemExit("הרצה נעצרה: יש מועמדים לכפילות. הכריעו והוסיפו ל-curated-to-gedcom.map.json")
print("שער הכפילויות: נקי")
if REJECTED_G:
    print("שער G: נדחו %d התאמות שם-פרטי-בלבד עם שמות משפחה סותרים:" % len(REJECTED_G))
    for g,gl,cid,cl in REJECTED_G: print(f"    {g} «{gl}»  ≠  {cid} «{cl}»")

(DATA/"people.unified.json").write_text(json.dumps(list(people.values()), ensure_ascii=False, indent=1), encoding='utf-8')
(DATA/"unions.unified.json").write_text(json.dumps(unions, ensure_ascii=False, indent=1), encoding='utf-8')
print(f"people : {len(people)}  (enriched from curated files: {hits})")
print(f"unions : {len(unions)}")
from collections import Counter
print("branches:", dict(Counter(p['branch'] for p in people.values())))
print("with he :", sum(1 for p in people.values() if p['names']['he']))
print("with bio:", sum(1 for p in people.values() if p['bioChapter']))

import re, json, sys
from pathlib import Path
ROOT = Path('/Users/amotz/Projects/family-history')
A = ROOT/'albert/chart/albert-rywenbajrych.ged'
M = ROOT/'wojslawice/chart/moskal-schafir.ged'
OFF = 1000

def parse(path):
    recs, cur = [], None
    for ln in path.read_text(encoding='utf-8').split('\n'):
        if not ln.strip(): continue
        m = re.match(r'^0 (@[^@]+@) (\w+)', ln)
        if m:
            cur = {'xref':m.group(1),'tag':m.group(2),'lines':[ln]}; recs.append(cur); continue
        m0 = re.match(r'^0 (\w+)', ln)
        if m0:
            cur = {'xref':None,'tag':m0.group(1),'lines':[ln]}; recs.append(cur); continue
        if cur: cur['lines'].append(ln)
    return recs

ar, mr = parse(A), parse(M)

def name_of(rec):
    for l in rec['lines']:
        m = re.match(r'^1 NAME (.+)$', l)
        if m: return m.group(1).strip()
    return None

# the 11 living-generation people that exist in BOTH files
dupe_names = {'Amotz /Albert/','Boaz /Albert/','Aya /Albert/','Michal /Albert/',
              'Neta //','Maayan //','Moran //','Nitzan //','Rotem //','Aviv //','Tamar //'}
a_by_name = {name_of(r): r['xref'] for r in ar if r['tag']=='INDI'}
m_dupe = {}   # moskal xref -> albert xref
for r in mr:
    if r['tag']=='INDI' and name_of(r) in dupe_names:
        m_dupe[r['xref']] = a_by_name[name_of(r)]

# moskal families that duplicate albert ones
fam_dupe = {'@F10@':'@F75@', '@F54@':'@F76@', '@F55@':'@F77@', '@F56@':'@F78@'}

def shift(x):
    if x in m_dupe: return m_dupe[x]
    if x in fam_dupe: return fam_dupe[x]
    m = re.match(r'^@([IF])(\d+)@$', x)
    if m: return f'@{m.group(1)}{int(m.group(2))+OFF}@'
    m = re.match(r'^@S(\d+)@$', x)
    if m: return f'@S{int(m.group(1))+OFF}@'
    return x

out = []
for r in ar:
    if r['tag'] in ('HEAD','TRLR'): continue
    out.append(list(r['lines']))

skip = set(m_dupe) | set(fam_dupe)
for r in mr:
    if r['tag'] in ('HEAD','TRLR','SUBM'): continue
    if r['xref'] in skip: continue
    new = []
    for l in r['lines']:
        l = re.sub(r'(@[ISF]\d+@)', lambda mm: shift(mm.group(1)), l)
        new.append(l)
    out.append(new)

# merge Dvora into the David family (@F75@): add WIFE + keep the four children
dv = None
for r in mr:
    if r['tag']=='INDI' and name_of(r)=='Dvora /Albert/': dv = shift(r['xref'])
for rec in out:
    if rec[0].startswith('0 @F75@'):
        if not any(l.startswith('1 WIFE') for l in rec):
            i = next((k for k,l in enumerate(rec) if l.startswith('1 CHIL')), 1)
            rec.insert(i, f'1 WIFE {dv}')
    # Dvora's FAMS should point at F75
    if dv and rec[0].startswith(f'0 {dv} '):
        rec[:] = [re.sub(r'^1 FAMS @F1010@$', '1 FAMS @F75@', l) for l in rec]

head = ['0 HEAD','1 SOUR family-history-project','2 NAME Albert-Rywenbajrych + Moskal-Schafir, merged',
        '1 DATE 21 AUG 2026','1 CHAR UTF-8','1 GEDC','2 VERS 5.5.1','2 FORM LINEAGE-LINKED',
        '1 NOTE Merged export for MyHeritage, 21 Aug 2026. Paternal (Albert-Rywenbajrych) and',
        '2 CONT maternal (Moskal-Schafir) lines in one tree. The 11 people who appear in both',
        '2 CONT source files - Amotz, Boaz, Aya, Michal and the seven children of that',
        '2 CONT generation - were de-duplicated, and the two parent families were merged into',
        '2 CONT one (David Albert x Dvora nee Moskal).']
body = []
for rec in out: body.extend(rec + [''])
text = '\n'.join(head + [''] + body + ['0 TRLR',''])
dest = ROOT/'site/data/merged-for-myheritage-21aug2026.ged'
dest.write_text(text, encoding='utf-8')
print('written:', dest)
print('INDI:', text.count('\n0 @I'), ' FAM:', text.count('\n0 @F'), ' SOUR:', text.count('\n0 @S'))

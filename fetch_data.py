import csv, json, re, urllib.request
from datetime import datetime, timedelta

SHEET_ID = '1Y1QV6_hBlZJY9ktltCjiJsNCFqcBsGUmdrRuxwwBWn4'
SHEETS   = {'overall':'', 'web':'Web', 'ios':'iOS', 'android':'Android'}
MONTHS   = {m:i+1 for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}

def fetch(name=''):
    base = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
    url  = base + (f'&sheet={name}' if name else '')
    req  = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8')

def money(s):
    return int(re.sub(r'[^\d]', '', str(s)) or '0')

def iso(s):
    p = str(s).strip().split('-')
    if len(p) != 3: return None
    m = MONTHS.get(p[1].lower())
    if not m: return None
    return f'{2000+int(p[2]):04d}-{m:02d}-{int(p[0]):02d}'

def lbl(d, gran):
    dt = datetime.strptime(d, '%Y-%m-%d')
    if gran == 'daily':   return dt.strftime(f'{dt.day} %b')
    if gran == 'weekly':  return 'Wk ' + dt.strftime(f'{dt.day} %b')
    if gran == 'monthly': return dt.strftime("%b '%y")

def wk(d):
    dt = datetime.strptime(d, '%Y-%m-%d')
    return (dt - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')

def mo(d): return d[:7] + '-01'

def parse(text):
    rows = []
    for cols in csv.reader(text.splitlines()):
        if not cols or cols[0] in ('', 'Time'): continue
        d = iso(cols[0])
        if not d or len(cols) < 14: continue
        tp = int(float(cols[1] or 0))
        if not tp: continue
        rows.append({'date':d, 'tp':tp,
                     'np':int(float(cols[2] or 0)),
                     'rp':int(float(cols[3] or 0)),
                     'tr':money(cols[6]),
                     'nr':money(cols[7]),
                     'rr':money(cols[8])})
    return sorted(rows, key=lambda r: r['date'])

def agg(rows, keyfn, gran):
    g = {}; order = []
    for r in rows:
        k = keyfn(r['date'])
        if k not in g: g[k]=[]; order.append(k)
        g[k].append(r)
    out = []
    for k in order:
        rs = g[k]
        tp=sum(r['tp'] for r in rs); np=sum(r['np'] for r in rs); rp=sum(r['rp'] for r in rs)
        tr=sum(r['tr'] for r in rs); nr=sum(r['nr'] for r in rs); rr=sum(r['rr'] for r in rs)
        out.append({'date':k,'label':lbl(k,gran),'tp':tp,'np':np,'rp':rp,'tr':tr,'nr':nr,'rr':rr})
    return out

def section(raw):
    return {'daily':   agg(raw, lambda d:d, 'daily'),
            'weekly':  agg(raw, wk, 'weekly'),
            'monthly': agg(raw, mo, 'monthly')}

# Fetch raw
raw = {}
for key, name in SHEETS.items():
    print(f'Fetching {key}...')
    raw[key] = parse(fetch(name))
    print(f'  {len(raw[key])} rows')

# Per-platform sections
data = {k: section(raw[k]) for k in ['overall','web','ios','android']}

# Platform comparison section
all_dates = sorted(set(r['date'] for k in ['web','ios','android'] for r in raw[k]))
by = {k:{r['date']:r for r in raw[k]} for k in ['web','ios','android']}

def plat_agg(daily_rows, keyfn, gran):
    g = {}; order = []
    for r in daily_rows:
        k = keyfn(r['date'])
        if k not in g: g[k]=[]; order.append(k)
        g[k].append(r)
    out = []
    for k in order:
        rs = g[k]
        out.append({'date':k,'label':lbl(k,gran),
                    'web_tp':sum(r['web_tp'] for r in rs),
                    'ios_tp':sum(r['ios_tp'] for r in rs),
                    'android_tp':sum(r['android_tp'] for r in rs),
                    'web_tr':sum(r['web_tr'] for r in rs),
                    'ios_tr':sum(r['ios_tr'] for r in rs),
                    'android_tr':sum(r['android_tr'] for r in rs)})
    return out

daily_plat = []
for d in all_dates:
    w=by['web'].get(d,{}); i=by['ios'].get(d,{}); a=by['android'].get(d,{})
    daily_plat.append({'date':d,
                       'web_tp':w.get('tp',0),'ios_tp':i.get('tp',0),'android_tp':a.get('tp',0),
                       'web_tr':w.get('tr',0),'ios_tr':i.get('tr',0),'android_tr':a.get('tr',0)})

data['platform'] = {'daily':   plat_agg(daily_plat, lambda d:d, 'daily'),
                    'weekly':  plat_agg(daily_plat, wk, 'weekly'),
                    'monthly': plat_agg(daily_plat, mo, 'monthly')}

data['last_updated'] = datetime.now().strftime('%d %b %Y, %I:%M %p')

with open('data.json','w') as f:
    json.dump(data, f, separators=(',',':'))

print(f"\nDone — {data['last_updated']}")

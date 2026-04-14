import csv, json, re, urllib.request
from datetime import datetime

SHEET_ID = '1Y1QV6_hBlZJY9ktltCjiJsNCFqcBsGUmdrRuxwwBWn4'
SHEETS   = {'overall': '', 'web': 'Web', 'ios': 'iOS', 'android': 'Android'}
MONTHS   = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}

def fetch_sheet(name=''):
    base = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'
    url  = base + (f'&sheet={name}' if name else '')
    req  = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8')

def parse_money(s):
    try:
        return int(re.sub(r'[^\d]', '', str(s)))
    except:
        return 0

def parse_date(s):
    parts = str(s).strip().split('-')
    if len(parts) != 3:
        return None
    mon = MONTHS.get(parts[1].lower())
    if not mon:
        return None
    return f'{2000+int(parts[2]):04d}-{mon:02d}-{int(parts[0]):02d}'

def parse_sheet(text):
    rows = []
    reader = csv.reader(text.splitlines())
    next(reader, None)          # skip header
    for cols in reader:
        if len(cols) < 14:
            continue
        date = parse_date(cols[0])
        if not date:
            continue
        tp = int(float(cols[1] or 0))
        if tp == 0:
            continue
        rows.append({
            'date': date,
            'tp':   tp,
            'np':   int(float(cols[2] or 0)),
            'rp':   int(float(cols[3] or 0)),
            'tr':   parse_money(cols[6]),
            'nr':   parse_money(cols[7]),
            'rr':   parse_money(cols[8]),
            'oa':   parse_money(cols[11]),
            'na':   parse_money(cols[12]),
            'ra':   parse_money(cols[13]),
        })
    return sorted(rows, key=lambda r: r['date'])

data = {}
for key, name in SHEETS.items():
    print(f'Fetching {key}...')
    text = fetch_sheet(name)
    data[key] = parse_sheet(text)
    print(f'  {len(data[key])} rows')

data['last_updated'] = datetime.now().strftime('%d %b %Y, %I:%M %p')

with open('data.json', 'w') as f:
    json.dump(data, f, separators=(',', ':'))

total = sum(len(data[k]) for k in ['overall','web','ios','android'])
print(f'\nSaved data.json  ({total} total rows, last_updated: {data["last_updated"]})')

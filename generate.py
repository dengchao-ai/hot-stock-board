#!/usr/bin/env python3
"""生成热门前100页面 - 数据源: 同花顺"""
import json, re, os, sys
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

try:
    import requests
except:
    import urllib.request
    class R:
        def get(self, url, **kw):
            try:
                req = urllib.request.Request(url, headers=kw.get('headers', {}))
                resp = urllib.request.urlopen(req, timeout=15)
                return type('X', (), {'status_code': 200, 'text': resp.read().decode('utf-8','ignore'), 'ok': True})()
            except:
                return type('X', (), {'status_code': 0, 'text': '', 'ok': False})()
    requests = R()

HDR = {"User-Agent": "Mozilla/5.0","Referer":"https://stock.10jqka.com.cn/"}
BASE = os.path.dirname(os.path.abspath(__file__))

def jq(url):
    try:
        r = requests.get(url, headers=HDR, timeout=15)
        if hasattr(r, 'status_code') and r.status_code == 200 and len(r.text) > 50:
            return r.text
    except:
        pass
    return None

def main():
    print("Fetching 同花顺 hot stocks...", flush=True)

    # 同花顺热门股票API
    urls = [
        "https://data.10jqka.com.cn/financial/hot/stock/rank/v1/rank/?type=1&market=0&page=1",
        "https://data.10jqka.com.cn/financial/hot/stock/cx/proport/v1/hot_cx_stock/?page=1&type=0&tag=0&finance=0",
    ]

    raw = None
    for u in urls:
        print(f"  trying: {u[:60]}...", flush=True)
        raw = jq(u)
        if raw:
            print(f"  got data ({len(raw)} bytes)", flush=True)
            break

    if not raw:
        # Try scraping the 10jqka page
        print("  trying backup: scraping 10jqka page...", flush=True)
        raw = jq("https://stock.10jqka.com.cn/hotstock/")
        if raw:
            # Try to extract stock list from HTML
            import html as html_mod
            # Look for stock data in script tags
            ms = re.findall(r'"stock_code":"(\d+)","stock_name":"([^"]+)"', raw)
            if ms:
                stocks = []
                for i, (code, name) in enumerate(ms[:100]):
                    stocks.append({
                        'c': code, 'n': html_mod.unescape(name), 'o': i+1,
                        'q': 0, 'p': 0, 'cs': ['热门'], 'rc': [], 'tg': '',
                        'mcap': 0, 'turn': 0, 'vol': 0, 'kl': []
                    })
                if stocks:
                    save(stocks)
                    return

    if raw:
        # Try JSON parse
        import html as html_mod
        try:
            data = json.loads(raw)
        except:
            data = None

        if data:
            # Try different response formats
            stocks_data = None
            if 'data' in data:
                d = data['data']
                if isinstance(d, list):
                    stocks_data = d
                elif isinstance(d, dict):
                    for key in ['list', 'items', 'stock', 'rank', 'data']:
                        if key in d and isinstance(d[key], list):
                            stocks_data = d[key]
                            break

            if stocks_data:
                stocks = []
                for i, item in enumerate(stocks_data[:100]):
                    if not isinstance(item, dict):
                        continue
                    code = str(item.get('stock_code') or item.get('code') or item.get('c') or '')
                    name = item.get('stock_name') or item.get('name') or item.get('n') or ''
                    if not code or not name:
                        continue
                    price = item.get('price') or item.get('q') or item.get('f2') or 0
                    chg = item.get('change_pct') or item.get('p') or item.get('f3') or 0
                    stocks.append({
                        'c': code, 'n': html_mod.unescape(name) if '&' in str(name) else name,
                        'o': i+1,
                        'q': round(float(price), 2) if price else 0,
                        'p': round(float(chg), 2) if chg else 0,
                        'cs': ['热门'], 'rc': [], 'tg': '',
                        'mcap': 0, 'turn': 0, 'vol': 0, 'kl': []
                    })
                if stocks:
                    save(stocks)
                    return

    print("ERROR: All APIs failed")
    sys.exit(1)

def save(stocks):
    ts = datetime.now(tz).strftime('%H:%M:%S')
    dt = datetime.now(tz).strftime('%Y-%m-%d')

    # Get prices from Sina for accuracy
    print(f"  fetching prices for {len(stocks)} stocks...", flush=True)
    for i in range(0, len(stocks), 50):
        chunk = stocks[i:i+50]
        code_list = []
        for s in chunk:
            c = s['c']
            prefix = 'sh' if c.startswith('6') else 'sz'
            code_list.append(prefix + c)
        try:
            url = "https://hq.sinajs.cn/list=" + ",".join(code_list)
            r = requests.get(url, headers={**HDR, "Referer": "https://finance.sina.com.cn"}, timeout=10)
            if hasattr(r, 'text') and r.text:
                for line in r.text.strip().split('\n'):
                    if not line or '=' not in line:
                        continue
                    parts = line.split('=')[1].strip().strip('"').split(',')
                    if len(parts) >= 3:
                        code_in_line = line.split('=')[0].split('_')[-1]
                        now = float(parts[3]) if parts[3] else 0
                        yc = float(parts[2]) if parts[2] else 0
                        for s in chunk:
                            if s['c'] == code_in_line[2:] if code_in_line.startswith(('sh','sz')) else s['c'] == code_in_line:
                                s['q'] = now
                                if yc and now:
                                    s['p'] = round((now-yc)/yc*100, 2)
                                break
        except:
            pass

    data_json = json.dumps({'s': stocks, 'ut': ts, 'dt': dt}, ensure_ascii=False)

    html_path = os.path.join(BASE, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace DATA
    new_html = re.sub(
        r'var DATA = \{.*?"dt": "\d{4}-\d{2}-\d{2}"\};',
        f'var DATA = {data_json};',
        html, count=1, flags=re.DOTALL
    )

    if new_html == html:
        m = re.search(r'var DATA = \{', html)
        if m:
            start = m.start()
            end = html.index('};', start) + 2
            new_html = html[:start] + f'var DATA = {data_json};' + html[end:]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"OK - {len(stocks)} stocks @ {ts}")

if __name__ == '__main__':
    main()

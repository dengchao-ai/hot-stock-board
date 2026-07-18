#!/usr/bin/env python3
"""生成热门前100页面"""
import json, re, os, sys
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

try:
    import requests
except ImportError:
    import urllib.request, urllib.error
    class RequestsLike:
        def get(self, url, **kw):
            req = urllib.request.Request(url, headers=kw.get('headers', {}))
            try:
                resp = urllib.request.urlopen(req, timeout=15)
                return type('R', (), {'status_code': 200, 'text': resp.read().decode('utf-8', errors='replace')})()
            except Exception as e:
                return type('R', (), {'status_code': 0, 'text': '', 'ok': False})()
    requests = RequestsLike()

HDR = {"User-Agent": "Mozilla/5.0"}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_json(url):
    r = requests.get(url, headers=HDR, timeout=15) if hasattr(requests, 'get') and 'timeout' in __import__('inspect').signature(requests.get).parameters else requests.get(url, headers=HDR)
    if not hasattr(r, 'status_code') or r.status_code != 200:
        return None
    # EastMoney returns GBK sometimes
    try:
        return json.loads(r.text)
    except:
        try:
            import chardet
            enc = chardet.detect(r.content)['encoding'] or 'gbk'
            return json.loads(r.content.decode(enc, errors='replace'))
        except:
            return None

def main():
    print("Fetching hot stocks...", flush=True)

    # Step 1: Get hot stocks by turnover
    url = ("https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=150"
           "&po=1&np=1&fltt=2&invt=2&fid=f62"
           "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
           "&fields=f12,f14,f2,f3,f62,f20,f69,f8,f15")

    data = fetch_json(url)
    if not data or 'data' not in data:
        print("ERROR: Failed to fetch stock list")
        sys.exit(1)

    items = data.get('data', {}).get('diff', [])[:100]
    if not items:
        print("ERROR: Empty stock list")
        sys.exit(1)

    stocks = []
    for idx, item in enumerate(items):
        try:
            code = str(item.get('f12', ''))
            name = item.get('f14', '') or ''
            price = item.get('f2')
            chg = item.get('f3')
            vol_val = item.get('f62', 0) or 0  # turnover
            mcap_val = item.get('f20', 0) or 0
            turn_val = item.get('f69', 0) or 0

            if not code or not name or price is None:
                continue

            # Determine sector
            n = name
            if any(k in n for k in ['半导体','芯片','集成','微','科技','电子']):
                cs = ['半导体芯片']
            elif any(k in n for k in ['医药','医疗','药','生物','健康']):
                cs = ['医药医疗']
            elif any(k in n for k in ['新能源','光伏','锂电','电池','风电','能源']):
                cs = ['新能源']
            elif any(k in n for k in ['通信','光','5G','6G']):
                cs = ['通信']
            elif any(k in n for k in ['银行','证券','保险','金融']):
                cs = ['金融']
            elif any(k in n for k in ['汽车','车','电动']):
                cs = ['新能源汽车']
            elif any(k in n for k in ['电力','电网']):
                cs = ['电力']
            elif any(k in n for k in ['军工','航天','航空','国防']):
                cs = ['军工']
            elif any(k in n for k in ['消费','食品','饮料','酒']):
                cs = ['大消费']
            elif any(k in n for k in ['AI','智能','机器','数据','软件']):
                cs = ['人工智能']
            elif any(k in n for k in ['传媒','游戏','影视']):
                cs = ['传媒']
            elif any(k in n for k in ['化工','化纤']):
                cs = ['化工']
            elif any(k in n for k in ['地产','房产']):
                cs = ['房地产']
            else:
                cs = ['其他']

            stock = {
                'c': code, 'n': name, 'o': idx + 1,
                'q': round(float(price), 2) if price else 0,
                'p': round(float(chg), 2) if chg else 0,
                'cs': cs, 'rc': [], 'tg': '',
                'mcap': round(float(mcap_val)/1e8, 2) if mcap_val and mcap_val > 0 else 0,
                'turn': round(float(turn_val), 2) if turn_val else 0,
                'vol': round(float(vol_val)/1e4, 2) if vol_val else 0,
                'kl': []
            }

            # Fetch K-line (daily, ~168 bars)
            market = 1 if code.startswith('6') else 0
            try:
                kurl = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
                        f"secid={market}.{code}"
                        f"&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57"
                        f"&klt=101&fqt=1&end=20500101&lmt=168")
                kd = fetch_json(kurl)
                if kd and 'data' in kd and kd['data'] and 'klines' in kd['data']:
                    for line in kd['data']['klines'][-168:]:
                        p = line.split(',')
                        if len(p) >= 6:
                            stock['kl'].append([p[0], float(p[1]), float(p[2]),
                                                float(p[3]), float(p[4]), float(p[5])])
            except:
                pass

            stocks.append(stock)
        except:
            continue

    ts = datetime.now(tz).strftime('%H:%M:%S')
    dt = datetime.now(tz).strftime('%Y-%m-%d')
    data_json = json.dumps({'s': stocks, 'ut': ts, 'dt': dt}, ensure_ascii=False)

    # Read current index.html as template
    html_path = os.path.join(BASE_DIR, 'index.html')
    if not os.path.exists(html_path):
        print("ERROR: index.html not found")
        sys.exit(1)

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace DATA
    new_html = re.sub(
        r'var DATA = \{.*?"dt": "\d{4}-\d{2}-\d{2}"\};',
        f'var DATA = {data_json};',
        html, count=1, flags=re.DOTALL
    )

    if new_html == html:
        print("WARNING: DATA not replaced, trying fallback...")
        # Fallback: find the DATA line
        import re as re2
        m = re2.search(r'var DATA = \{', html)
        if m:
            start = m.start()
            end = html.index('};', start) + 2
            new_html = html[:start] + f'var DATA = {data_json};' + html[end:]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"OK - {len(stocks)} stocks @ {ts}")

if __name__ == '__main__':
    main()

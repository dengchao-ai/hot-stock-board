#!/usr/bin/env python3
"""热门前100生成器"""
import json, re, os, sys, urllib.request, ssl
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))
BASE = os.path.dirname(os.path.abspath(__file__))

def fetch(url, enc='utf-8', ref='https://stock.10jqka.com.cn'):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
            'Referer': ref
        })
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        return resp.read().decode(enc, 'ignore')
    except:
        return None

def main():
    print("Fetching...", flush=True)

    # 方案1: 同花顺移动端API
    raw = fetch("https://m.10jqka.com.cn/api/v1/hot/stock/?page=1&size=100&type=1")
    if raw:
        try:
            d = json.loads(raw)
            items = d.get('data',[])
            if isinstance(items, dict):
                for k in ['list','items','data']:
                    if isinstance(items.get(k), list):
                        items = items[k]
                        break
            if isinstance(items, list) and len(items) > 10:
                print(f"  同花顺mobi OK ({len(items)} stocks)")
                save(items)
                return
        except: pass

    # 方案2: 同花顺另一接口
    raw = fetch("https://data.10jqka.com.cn/financial/hot/stock/rank/v1/rank/")
    if raw:
        try:
            d = json.loads(raw)
            items = None
            if 'data' in d:
                if isinstance(d['data'], list): items = d['data']
                elif isinstance(d['data'], dict):
                    for k in ['list','items','data']:
                        if k in d['data'] and isinstance(d['data'][k], list):
                            items = d['data'][k]; break
            if items and len(items) > 10:
                print(f"  同花顺rank OK ({len(items)} stocks)")
                save(items)
                return
        except: pass

    # 方案3: 东方财富（按成交额）
    raw = fetch(
        "https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=100"
        "&po=1&np=1&fltt=2&invt=2&fid=f62"
        "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
        "&fields=f12,f14,f2,f3,f20,f69,f62",
        ref='https://finance.eastmoney.com')
    if raw:
        try:
            d = json.loads(raw)
            items = d.get('data',{}).get('diff',[])
            if items and len(items) > 10:
                print(f"  东方财富 OK ({len(items)} stocks)")
                save_em(items)
                return
        except: pass

    print("ERROR: All APIs failed")
    sys.exit(1)

def save_em(items):
    """东方财富格式保存"""
    stocks = []
    for i, s in enumerate(items[:100]):
        code = str(s.get('f12',''))
        name = s.get('f14','') or ''
        if not code or not name: continue
        trade = float(s.get('f2',0) or 0)
        chg = float(s.get('f3',0) or 0)
        mcap = float(s.get('f20',0) or 0) / 1e8
        vol = float(s.get('f62',0) or 0) / 1e4
        turn = float(s.get('f69',0) or 0)

        n = name
        if any(k in n for k in ['半导体','芯片','集成','微','电子','科技']): cs = ['半导体芯片']
        elif any(k in n for k in ['医药','医疗','药','生物','健康']): cs = ['医药医疗']
        elif any(k in n for k in ['新能源','光伏','锂电','电池','风电','能源','宁德']): cs = ['新能源']
        elif any(k in n for k in ['通信','光迅','中兴','5G','6G']): cs = ['通信']
        elif any(k in n for k in ['银行','证券','保险','金融','同花顺']): cs = ['金融']
        elif any(k in n for k in ['汽车','比亚迪','长城','赛力斯']): cs = ['新能源汽车']
        elif any(k in n for k in ['电力','电网','华能']): cs = ['电力']
        elif any(k in n for k in ['军工','航天','航空','国防','中航']): cs = ['军工']
        elif any(k in n for k in ['消费','食品','饮料','酒','茅台','五粮液']): cs = ['大消费']
        elif any(k in n for k in ['AI','智能','机器','数据','软件','浪潮']): cs = ['人工智能']
        elif any(k in n for k in ['有色','黄金','铜','铝','矿','钢铁']): cs = ['有色']
        elif any(k in n for k in ['传媒','游戏']): cs = ['传媒']
        else: cs = ['其他']

        stocks.append({
            'c':code,'n':name,'o':i+1,'q':round(trade,2),'p':round(chg,2),
            'cs':cs,'rc':[],'tg':'','mcap':round(mcap,2),
            'turn':round(turn,2),'vol':round(vol,2),'kl':[]
        })

    do_save(stocks)

def save(items):
    """同花顺格式保存"""
    stocks = []
    for i, s in enumerate(items[:100]):
        if not isinstance(s, dict): continue
        code = str(s.get('stock_code') or s.get('code') or '')
        name = s.get('stock_name') or s.get('name') or ''
        if not code or not name: continue
        trade = float(s.get('price') or s.get('q') or 0)
        chg = float(s.get('change_pct') or s.get('p') or 0)
        stocks.append({
            'c':code,'n':name,'o':i+1,'q':round(trade,2),'p':round(chg,2),
            'cs':['热门'],'rc':[],'tg':'','mcap':0,'turn':0,'vol':0,'kl':[]
        })

    # 补价格
    for i in range(0, len(stocks), 50):
        chunk = stocks[i:i+50]
        codes = [(('sh' if c['c'].startswith('6') else 'sz')+c['c']) for c in chunk]
        r = fetch("https://hq.sinajs.cn/list="+",".join(codes), ref="https://finance.sina.com.cn")
        if r:
            for line in r.strip().split('\n'):
                if '=' not in line: continue
                try:
                    p = line.split('=')[1].strip().strip('"').split(',')
                    key = line.split('=')[0].split('_')[-1]
                    now = float(p[3]) if p[3] else 0
                    yc = float(p[2]) if p[2] else 0
                    for s in chunk:
                        sc = s['c']
                        if key == sc or (len(key) > 2 and key[2:] == sc):
                            s['q'] = now
                            if yc and now: s['p'] = round((now-yc)/yc*100, 2)
                            break
                except: pass

    do_save(stocks)

def do_save(stocks):
    ts = datetime.now(tz).strftime('%H:%M:%S')
    dt = datetime.now(tz).strftime('%Y-%m-%d')
    data_json = json.dumps({'s':stocks,'ut':ts,'dt':dt}, ensure_ascii=False)

    html_path = os.path.join(BASE, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    new_html = re.sub(r'var DATA = \{.*?"dt": "\d{4}-\d{2}-\d{2}"\};',
                      f'var DATA = {data_json};', html, count=1, flags=re.DOTALL)
    if new_html == html:
        m = re.search(r'var DATA = \{', html)
        if m:
            s = m.start()
            e = html.index('};', s) + 2
            new_html = html[:s] + f'var DATA = {data_json};' + html[e:]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"OK - {len(stocks)} stocks @ {ts}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""生成热门前100页面 - 每30分钟自动更新"""
import json, urllib.request, time, os, ssl
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

# 获取全部A股列表（按成交额排序 = 热门）
url = ("https://push2.eastmoney.com/api/qt/clist/get?"
       "cb=&pn=1&pz=200&po=1&np=1&fltt=2&invt=2&fid=f62"
       "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
       "&fields=f12,f14,f2,f3,f62,f184,f66,f69,f100,f8")

ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, context=ctx)
data = json.loads(resp.read().decode("gbk"))
items = data.get("data", {}).get("diff", [])[:100]

stocks = []
for idx, item in enumerate(items):
    try:
        code = str(item.get("f12", ""))
        name = item.get("f14", "")
        price = item.get("f2")
        chg_pct = item.get("f3")
        vol = item.get("f62")  # 成交额
        turn = item.get("f69")  # 换手率
        mcap = item.get("f20")  # 总市值

        if not code or not name or price is None:
            continue

        stock = {
            "c": code,
            "n": name,
            "o": idx + 1,
            "q": round(float(price), 2) if price else 0,
            "p": round(float(chg_pct), 2) if chg_pct else 0,
            "cs": ["热门"],
            "rc": [],
            "tg": "",
            "mcap": round(float(mcap) / 1e8, 2) if mcap and mcap > 0 else 0,
            "turn": round(float(turn), 2) if turn else 0,
            "vol": round(float(vol) / 1e4, 2) if vol else 0,
            "kl": []
        }

        # 获取K线数据
        market = 1 if code.startswith("6") else 0
        try:
            kurl = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
                    f"secid={market}.{code}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57"
                    f"&klt=101&fqt=1&end=20500101&lmt=168")
            kr = urllib.request.Request(kurl, headers={"User-Agent": "Mozilla/5.0"})
            kd = json.loads(urllib.request.urlopen(kr, context=ctx).read())
            klines = kd.get("data", {}).get("klines", [])
            for line in klines[-168:]:
                parts = line.split(",")
                if len(parts) >= 6:
                    stock["kl"].append([parts[0], float(parts[1]), float(parts[2]),
                                        float(parts[3]), float(parts[4]), float(parts[5])])
        except:
            pass

        # 归类到概念板块（简单规则）
        name_lower = name
        if any(k in name_lower for k in ["半导体", "芯片", "集成", "微", "科技", "电子"]):
            stock["cs"] = ["半导体芯片"]
        elif any(k in name_lower for k in ["医药", "医疗", "药", "生物", "健康"]):
            stock["cs"] = ["医药医疗"]
        elif any(k in name_lower for k in ["新能源", "光伏", "锂电", "电池", "风电", "能源"]):
            stock["cs"] = ["新能源"]
        elif any(k in name_lower for k in ["通信", "光", "5G", "6G", "信息"]):
            stock["cs"] = ["通信"]
        elif any(k in name_lower for k in ["金融", "银行", "证券", "保险", "基金"]):
            stock["cs"] = ["金融"]
        elif any(k in name_lower for k in ["汽车", "车", "电动"]):
            stock["cs"] = ["新能源汽车"]
        elif any(k in name_lower for k in ["电力", "电网", "电"]):
            stock["cs"] = ["电力"]
        elif any(k in name_lower for k in ["地产", "房产", "物业"]):
            stock["cs"] = ["房地产"]
        elif any(k in name_lower for k in ["军工", "航天", "航空", "国防"]):
            stock["cs"] = ["军工"]
        elif any(k in name_lower for k in ["消费", "食品", "饮料", "酒", "乳"]):
            stock["cs"] = ["大消费"]
        elif any(k in name_lower for k in ["传媒", "游戏", "影视", "娱乐"]):
            stock["cs"] = ["传媒"]
        elif any(k in name_lower for k in ["化工", "化纤", "化学"]):
            stock["cs"] = ["化工"]
        elif any(k in name_lower for k in ["机械", "装备", "设备"]):
            stock["cs"] = ["机械设备"]
        elif any(k in name_lower for k in ["AI", "智能", "机器", "数据", "软件", "互联"]):
            stock["cs"] = ["人工智能"]
        else:
            stock["cs"] = ["其他"]

        stocks.append(stock)
    except:
        continue

ts = datetime.now(tz).strftime("%H:%M:%S")
dt = datetime.now(tz).strftime("%Y-%m-%d")

data_json = json.dumps({"s": stocks, "ut": ts, "dt": dt}, ensure_ascii=False)

# 读取HTML模板
html_path = os.path.join(os.path.dirname(__file__), "template.html")
if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
else:
    # 从当前 index.html 提取模板
    cur = os.path.join(os.path.dirname(__file__), "index.html")
    with open(cur, "r", encoding="utf-8") as f:
        html = f.read()

# 替换数据
import re
html = re.sub(
    r'var DATA = \{"s":.*?"dt": "\d{4}-\d{2}-\d{2}"\};',
    f'var DATA = {data_json};',
    html, flags=re.DOTALL
)

out = os.path.join(os.path.dirname(__file__), "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK - {len(stocks)} stocks, {ts}")

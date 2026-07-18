#!/usr/bin/env python3
"""生成带实时数据的 index.html"""
import urllib.request, json, ssl, os
from datetime import datetime

HTML_TEMPLATE = open('index.html', 'r', encoding='utf-8').read()

def fetch_data():
    ctx = ssl.create_default_context()
    
    # 同花顺热门排名
    url = 'https://eq.10jqka.com.cn/open/api/hot_list/v1/hot_stock/a/hour/data.txt'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://10jqka.com.cn'})
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    raw = json.loads(resp.read().decode('utf-8'))
    hot_list = raw['data']['stock_list'][:100]
    
    # 实时价格
    price_codes = []
    for s in hot_list:
        code = s['code']
        price_codes.append(('sh' if code.startswith('6') else 'sz') + code)
    
    prices = {}
    if price_codes:
        try:
            qurl = 'https://qt.gtimg.cn/q=' + ','.join(price_codes)
            qreq = urllib.request.Request(qurl, headers={'User-Agent': 'Mozilla/5.0'})
            qresp = urllib.request.urlopen(qreq, timeout=15, context=ctx)
            for line in qresp.read().decode('gbk', 'ignore').split(';'):
                line = line.strip()
                if '="' not in line: continue
                var_name = line.split('=')[0].strip()
                vals = line.split('="')[1].rstrip(';').split('~')
                if len(vals) < 33: continue
                try:
                    cur = float(vals[3]) if vals[3] else 0
                    chg = float(vals[32]) if vals[32] else 0
                    prices[var_name] = {'q': cur, 'p': chg}
                except: pass
        except: pass
    
    # 分类
    def classify(name, concepts):
        text = name + ' ' + ' '.join(concepts)
        rules = [
            ('通信', ['通信', 'CPO', '光纤', '光模块', 'F5G', '5G', '6G', '共封装光学']),
            ('半导体', ['半导体', '芯片', '存储芯片', '封装', '集成电路', 'PCB', '先进封装', '中芯', '晶圆', '汽车芯片', '功率半导体', 'MCU', 'FPGA']),
            ('电力', ['电力', '电网', '特高压', '绿色电力', '虚拟电厂', '超超临界', '抽水蓄能', '核电', '风电', '光热', '智能电网', '发电']),
            ('新能源', ['光伏', '储能', '碳交易', '页岩气', '氢能源', '太阳能', '新能源', '盐湖提锂', '钠离子', '固态电池', '锂电', '电池', '能源']),
            ('医药', ['医药', '医疗', '生物', 'CRO', '流感', '创新药', '仿制药', '血氧仪', '医疗器械']),
            ('人工智能', ['人工智能', '算力', '大模型', '机器人', 'AI', '东数西算']),
            ('消费电子', ['消费电子', '果指数', '无线耳机', '智能穿戴', '电子纸', 'MicroLED', '光学光电子', 'VR', 'AR', '面板']),
            ('新能源汽车', ['新能源汽车', '充电桩', '新能源车', '动力电池', '整车', '汽车零部件', '无人驾驶', '汽车']),
            ('地产', ['房地产', '物业', '房产', '城中村', '新型城镇化', '房屋检测']),
            ('化工', ['化工', '化肥', '煤化工', '氟化工', '磷化工', '新材料', '有机硅']),
            ('金融', ['金融', '银行', '证券', '保险', '券商']),
            ('消费', ['消费', '食品', '饮料', '白酒', '免税', '旅游', '农业', '猪肉', '种植', '纺织', '服装', '家电']),
            ('数字经济', ['数字经济', 'NFT', 'Web3', '区块链', '元宇宙', '数据确权', '数据要素', '数字货币']),
            ('军工', ['军工', '航天', '航空', '国防', '航母', '卫星', '导航', '国产航母']),
            ('传媒', ['传媒', '游戏', '电竞', '影视', '广告', '互联网', '云游戏']),
            ('基建', ['基建', '建筑', '工程', '装配式', '建筑节能', '水利', '路桥', '建材']),
            ('机械设备', ['机械', '设备', '高端装备', '工业母机', '机床', '工程机械']),
            ('有色/钢铁', ['有色', '钢铁', '黄金', '铜', '铝', '矿', '金属', '稀土', '小金属']),
            ('环保', ['环保', '碳中和', '净水', '污水处理']),
            ('物流运输', ['物流', '航运', '港口', '运输', '快递']),
            ('教育', ['教育', '培训']),
        ]
        for cat, kws in rules:
            for kw in kws:
                if kw in text:
                    return cat
        return ''
    
    stocks = []
    for i, s in enumerate(hot_list):
        code = s['code']
        name = s['name']
        tag_obj = s.get('tag', {}) or {}
        concepts = tag_obj.get('concept_tag', []) if isinstance(tag_obj, dict) else []
        pc = ('v_sh' if code.startswith('6') else 'v_sz') + code
        pinfo = prices.get(pc, {'q': 0, 'p': 0})
        stocks.append({
            'c': code, 'n': name, 'o': i + 1,
            'q': pinfo['q'], 'p': pinfo['p'],
            'cs': [classify(name, concepts)],
            'rc': concepts, 'kl': []
        })
    
    now = datetime.now()
    return {'s': stocks, 'ut': now.strftime('%H:%M:%S'), 'dt': now.strftime('%Y-%m-%d')}


# 生成 HTML
data = fetch_data()
data_json = json.dumps(data, ensure_ascii=False)

# 把 DATA 嵌入 HTML（替换 var DATA = 后面的内容）
import re
new_html = re.sub(
    r'var DATA = \{.*?\};',
    'var DATA = ' + data_json + ';',
    HTML_TEMPLATE,
    count=1,
    flags=re.DOTALL
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'✅ 生成成功！{len(data["s"])} 只股票 @ {data["ut"]}')

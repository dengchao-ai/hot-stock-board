"""Vercel Serverless 版 - 热门前100 API"""
import json, urllib.request, ssl
from datetime import datetime

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<title>热门前100 · 实时行情</title>
<style>
:root{--safe-t:env(safe-area-inset-top,0px);--safe-b:env(safe-area-inset-bottom,0px)}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Segoe UI',sans-serif;background:#f0f2f5;color:#1d1d1f;overflow-x:hidden}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:16px;padding-top:calc(16px + var(--safe-t));text-align:center;position:sticky;top:0;z-index:20}
.header h1{font-size:22px;font-weight:700;letter-spacing:1px}
.header .sub{font-size:13px;color:rgba(255,255,255,.6);margin-top:4px;display:flex;align-items:center;justify-content:center;gap:6px}
.container{max-width:100%;margin:0 auto;padding:10px 10px calc(10px + var(--safe-b))}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:10px}
.stat{background:#fff;border-radius:14px;padding:12px 4px;text-align:center;border:1px solid #eee;box-shadow:0 2px 6px rgba(0,0,0,.04)}
.stat .n{font-size:20px;font-weight:700;color:#1a1a2e}
.stat .n.up{color:#e53935}
.stat .n .dn{color:#27ae60}
.stat .l{font-size:11px;color:#999;margin-top:2px;font-weight:500}
.sector{background:#fff;border-radius:12px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.04);overflow:hidden}
.sector-hd{padding:12px 14px;font-size:15px;font-weight:700;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;gap:8px;background:#fafbfc}
.sector-hd .badge{background:#e53935;color:#fff;font-size:14px;padding:2px 10px;border-radius:12px;font-weight:700;min-width:26px;text-align:center}
.stock-list{list-style:none;display:grid;grid-template-columns:repeat(2,1fr);gap:8px;padding:10px}
.stock-row{display:flex;flex-direction:column;padding:10px 8px;cursor:pointer;background:#fff;border-radius:8px;border:1px solid #e8e8ed;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.stock-row:active{background:#f2f2f7}
.stock-top{display:flex;align-items:center;justify-content:space-between;width:100%}
.stock-rank{font-size:12px;font-weight:700;color:#e53935;flex-shrink:0;min-width:28px}
.stock-name{font-size:13px;font-weight:600;color:#1d1d1f;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;text-align:center;margin:0 4px}
.stock-chg{text-align:right;font-weight:700;font-size:12px;flex-shrink:0;min-width:52px}
.stock-chg.r{color:#e53935}
.stock-chg.g{color:#27ae60}
.stock-sub{font-size:9px;color:#999;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:2px}
.ft{color:#999;font-size:11px;text-align:center;padding:14px 16px;padding-bottom:calc(14px + var(--safe-b))}
@media(min-width:600px){.container{max-width:680px;padding:16px}.stats{grid-template-columns:repeat(5,1fr)}}
body{overscroll-behavior-y:contain}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.sector{animation:fadeUp .4s ease both}
</style>
</head>
<body>
<div class="header"><h1>热门前100</h1><div class="sub"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#4ade80"></span> 同花顺实时 · <span id="liveTime">--:--</span></div></div>
<div class="container" id="app"><div style="text-align:center;padding:40px;color:#999">加载中...</div></div>
<div class="ft">热门前100 · 同花顺实时数据</div>
<script>
var DATA = STOCK_DATA;
(function(s){
if(!s||!s.length){document.getElementById('app').innerHTML='<div style="text-align:center;padding:40px;color:#999">暂无数据</div>';return}
var n=new Date();document.getElementById('liveTime').textContent=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');
var up=s.filter(function(x){return x.p>0}).length,dn=s.filter(function(x){return x.p<0}).length,zt=s.filter(function(x){return x.p>=9.8}).length,av=(s.reduce(function(a,x){return a+x.p},0)/s.length).toFixed(2);
var g={};s.forEach(function(x){var cn=(x.cs||[''])[0]||'';if(!cn)return;if(!g[cn])g[cn]=[];g[cn].push(x)});
var e=Object.entries(g).sort(function(a,b){return b[1].length-a[1].length});
var h='<div class="stats"><div class="stat"><div class="n">'+s.length+'</div><div class="l">热门股票</div></div><div class="stat"><div class="n up">'+zt+'</div><div class="l">涨停</div></div><div class="stat"><div class="n up">'+up+'/<span class="dn">'+dn+'</span></div><div class="l">涨/跌</div></div><div class="stat"><div class="n">'+Object.keys(g).length+'</div><div class="l">行业大类</div></div><div class="stat"><div class="n '+(av>=0?'up':'dn')+'">'+av+'%</div><div class="l">平均涨幅</div></div></div>';
e.forEach(function(p){var cn=p[0],ss=p[1];h+='<div class="sector"><div class="sector-hd"><span>'+cn+'</span><span class="badge">'+ss.length+'只</span></div><ul class="stock-list">';ss.sort(function(a,b){return a.o-b.o}).forEach(function(x){var cp=x.p||0,cl=cp>0?'r':'g',sg=cp>0?'+':'';h+='<li class="stock-row" onclick="showDetail(\''+x.c+'\')"><div class="stock-top"><span class="stock-rank">#'+x.o+'</span><span class="stock-name">'+(x.n||'-')+'</span><span class="stock-chg '+cl+'">'+sg+cp.toFixed(2)+'%</span></div><span class="stock-sub">'+((x.rc||[]).filter(function(t){return ['同花顺指数','国家大基金持股','超级品牌','中国AI 50','同花顺漂亮100','证金持股','同花顺中特估100','同花顺果指数','国企改革','新股与次新股','高股息精选','注册制次新股','同花顺人工智能','含H股的H股','央企国企改革','MSCI概念','富时罗素概念股','标普道琼斯A股','2026一季报预增','同花顺出海50'].indexOf(t)<0})[0]||(x.cs||[])[0]||'')+'</span></li>'});h+='</ul></div>'});
document.getElementById('app').innerHTML=h;
})(DATA.s);
function showDetail(code){var s=DATA.s.find(function(x){return x.c===code});if(!s)return;var p=document.getElementById('detail');if(!p){p=document.createElement('div');p.id='detail';p.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;z-index:999;background:#fff;overflow-y:auto';document.body.appendChild(p)}p.style.display='block';var cc=s.p>=0?'#ff6b6b':'#27ae60',sg=s.p>=0?'+':'';p.innerHTML='<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:16px;padding-top:calc(16px + env(safe-area-inset-top,10px))"><div style="display:flex;align-items:center;gap:10px;margin-bottom:8px"><span style="font-size:20px;font-weight:700">'+(s.n||'-')+'</span><span style="font-size:13px;opacity:.6">'+(s.c||'')+'</span><div onclick="closeDetail()" style="margin-left:auto;width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,.15);display:flex;align-items:center;justify-content:center;font-size:18px;cursor:pointer">✕</div></div><div style="display:flex;align-items:baseline;gap:12px"><span style="font-size:32px;font-weight:700">'+(s.q||'--')+'</span><span style="font-size:18px;font-weight:600;color:'+cc+'">'+sg+(s.p||0).toFixed(2)+'%</span></div><div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap"><span style="background:rgba(255,255,255,.1);padding:4px 12px;border-radius:8px;font-size:12px">热度: <b>#'+s.o+'</b></span><span style="background:rgba(255,255,255,.1);padding:4px 12px;border-radius:8px;font-size:12px">概念: <b>'+((s.rc||[]).filter(function(t){return ['同花顺指数','国家大基金持股','超级品牌','中国AI 50','同花顺漂亮100','证金持股','同花顺中特估100','同花顺果指数','国企改革','新股与次新股','高股息精选','注册制次新股','同花顺人工智能','含H股的H股','央企国企改革','MSCI概念','富时罗素概念股','标普道琼斯A股','2026一季报预增','同花顺出海50'].indexOf(t)<0}).slice(0,3).join(' · ')||'--')+'</b></span></div></div><div style="padding:10px"><canvas id="k_chart" style="width:100%;display:block"></canvas></div>';drawChart(s.c)}
function closeDetail(){var el=document.getElementById('detail');if(el)el.style.display='none'}
function calcMACD(p,f,s){f=f||12;s=s||26;var sig=9;function ema(d,n){var r=[d[0]],k=2/(n+1);for(var i=1;i<d.length;i++)r.push(d[i]*k+r[i-1]*(1-k));return r}var eF=ema(p,f),eS=ema(p,s),dif=eF.map(function(v,i){return v-eS[i]}),dea=ema(dif,sig),hist=dif.map(function(v,i){return 2*(v-dea[i])});return{dif:dif,dea:dea,hist:hist}}
function drawChart(code){var c=document.getElementById('k_chart');if(!c)return;var pw=Math.min(c.offsetWidth||360,window.innerWidth-32),dpr=window.devicePixelRatio||1,W=Math.round(pw),H=Math.round(W*3/4);c.width=W*dpr;c.height=H*dpr;c.style.width=W+'px';c.style.height=H+'px';var ctx=c.getContext('2d');ctx.scale(dpr,dpr);ctx.fillStyle='#f8f9fa';ctx.fillRect(0,0,W,H);ctx.fillStyle='#999';ctx.font='14px sans-serif';ctx.textAlign='center';ctx.fillText('加载中...',W/2,H/2);fetch('/api/kline?code='+code).then(function(r){return r.json()}).then(function(kl){if(!kl||!kl.length){ctx.fillStyle='#f8f9fa';ctx.fillRect(0,0,W,H);ctx.fillStyle='#999';ctx.font='14px sans-serif';ctx.textAlign='center';ctx.fillText('暂无K线数据',W/2,H/2);return}
var bars=kl.map(function(d){var dt=d[0];if(dt&&dt.indexOf('-')<0&&dt.length===8)dt=dt.substring(0,4)+'-'+dt.substring(4,6)+'-'+dt.substring(6,8);return{d:dt,o:+d[1],c:+d[2],h:+d[3],l:+d[4],v:+d[5]}});bars.sort(function(a,b){return a.d.localeCompare(b.d)});if(bars.length>150)bars=bars.slice(bars.length-150);var n=bars.length,pad={t:22,b:28,l:48,r:14},totalH=H-pad.t-pad.b-4,kH=Math.floor(totalH*0.45),vH=Math.floor(totalH*0.15),mH=totalH-kH-vH,cw=W-pad.l-pad.r;var maxH=Math.max.apply(null,bars.map(function(b){return b.h})),minL=Math.min.apply(null,bars.map(function(b){return b.l}));if(maxH===minL||maxH-minL<0.01){maxH*=1.02;minL*=0.98};var maxV=Math.max.apply(null,bars.map(function(b){return b.v}))||1,prices=bars.map(function(b){return b.c}),macd=calcMACD(prices),maxM=Math.max.apply(null,macd.hist.map(Math.abs))||1;maxM*=1.2;function xP(i){return pad.l+(i+0.5)/n*cw}function yP(v){return pad.t+kH-(v-minL)/(maxH-minL)*kH}function yV(v){return pad.t+kH+vH-(v/maxV)*vH}function yM(v){return pad.t+kH+vH+mH/2-(v)/(2*maxM)*mH}ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);ctx.strokeStyle='#f0f0f0';ctx.lineWidth=0.5;for(var i=0;i<4;i++){var y=pad.t+kH/4*i;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(pad.l+cw,y);ctx.stroke()}ctx.beginPath();ctx.moveTo(pad.l,pad.t+kH);ctx.lineTo(pad.l+cw,pad.t+kH);ctx.stroke();var y0=yM(0);ctx.strokeStyle='#e0e0e0';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(pad.l,y0);ctx.lineTo(pad.l+cw,y0);ctx.stroke();var bw=Math.max(cw/n*0.6,1);for(var i=0;i<n;i++){var b=bars[i],up=b.c>=b.o,col=up?'#e53935':'#27ae60',cx=xP(i);ctx.strokeStyle=col;ctx.lineWidth=0.8;ctx.beginPath();ctx.moveTo(cx,yP(b.h));ctx.lineTo(cx,yP(b.l));ctx.stroke();var t=Math.min(yP(b.o),yP(b.c)),bt=Math.max(yP(b.o),yP(b.c));ctx.fillStyle=col;ctx.fillRect(cx-bw/2,t,Math.max(bw,1),Math.max(bt-t,1))}
for(var i=0;i<n;i++){var b=bars[i],up=b.c>=b.o,col=up?'rgba(229,57,53,0.3)':'rgba(39,174,96,0.3)',cx=xP(i);ctx.fillStyle=col;ctx.fillRect(cx-bw/2,yV(b.v),Math.max(bw,1),pad.t+kH+vH-yV(b.v))}
ctx.strokeStyle='#e0e0e0';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(pad.l,pad.t+kH+vH);ctx.lineTo(pad.l+cw,pad.t+kH+vH);ctx.stroke();for(var i=0;i<n;i++){var hv=macd.hist[i],col=hv>=0?'rgba(229,57,53,0.5)':'rgba(39,174,96,0.5)',cx=xP(i),yh=yM(hv);ctx.fillStyle=col;ctx.fillRect(cx-bw/2,Math.min(y0,yh),Math.max(bw,1),Math.abs(yh-y0))}
ctx.fillStyle='#999';ctx.font='10px sans-serif';ctx.textAlign='right';ctx.fillText(maxH.toFixed(2),pad.l-4,pad.t+12);ctx.fillText(minL.toFixed(2),pad.l-4,pad.t+kH+4);ctx.textAlign='center';ctx.fillStyle='#999';ctx.font='9px sans-serif';var step=Math.max(1,Math.floor(n/6));for(var i=0;i<n;i+=step)ctx.fillText(bars[i].d,pad.l+(i+0.5)/n*cw,H-6)})}
</script>
</body>
</html>"""

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


def fetch_data():
    ctx = ssl.create_default_context()
    url = 'https://eq.10jqka.com.cn/open/api/hot_list/v1/hot_stock/a/hour/data.txt'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://10jqka.com.cn'})
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    raw = json.loads(resp.read().decode('utf-8'))
    hot_list = raw['data']['stock_list'][:100]
    
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
            'rc': concepts, 'tg': '',
            'kl': []
        })
    now = datetime.now()
    return {'s': stocks, 'ut': now.strftime('%H:%M:%S'), 'dt': now.strftime('%Y-%m-%d')}


def fetch_kline(code):
    ctx = ssl.create_default_context()
    market = 'sh' if code.startswith('6') else 'sz'
    try:
        url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=' + market + code + ',day,,,168'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        raw = json.loads(resp.read().decode('utf-8', 'ignore'))
        data = raw.get('data', {})
        kdata = data.get(market + code, {})
        lines = kdata.get('day') or kdata.get('qfqday') or []
        if lines and len(lines) > 0:
            result = []
            for line in lines:
                if isinstance(line, str):
                    parts = line.split(' ')
                    if len(parts) == 2:
                        d = parts[0]
                        vals = parts[1].split(',')
                        if len(vals) >= 6:
                            result.append([d, float(vals[0]), float(vals[2]), float(vals[1]), float(vals[3]), float(vals[5])])
                elif isinstance(line, list) and len(line) >= 6:
                    result.append(line)
            if result: return result
    except: pass
    try:
        url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=' + market + code + '&scale=240&datalen=168'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        raw = json.loads(resp.read().decode('gbk', 'ignore'))
        if isinstance(raw, list) and len(raw) > 0:
            return [[item['day'], float(item['open']), float(item['close']), float(item['high']), float(item['low']), float(item['volume'])] for item in raw]
    except: pass
    return []


def handler(request):
    path = request.get('path', '/')
    if path == '/api/kline':
        from urllib.parse import parse_qs
        qs = parse_qs(request.get('queryString', ''))
        code = qs.get('code', [''])[0]
        if not code: return {'statusCode': 400, 'body': '[]'}
        kdata = fetch_kline(code)
        return {'statusCode': 200, 'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(kdata)}
    
    try:
        data = fetch_data()
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Content-Type': 'text/plain'}, 'body': str(e)}
    
    html = HTML.replace('var DATA = STOCK_DATA;', 'var DATA = ' + json.dumps(data, ensure_ascii=False) + ';')
    return {'statusCode': 200, 'headers': {'Content-Type': 'text/html; charset=utf-8'}, 'body': html}

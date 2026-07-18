#!/usr/bin/env python3
"""生成 热门前100.html 静态页面（双击运行，无需服务器）"""
import json, urllib.request, urllib.error, re, time, gzip, os

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

def fetch(url,ref=None):
    h={"User-Agent":UA,"Accept":"*/*","Accept-Encoding":"gzip, deflate","Accept-Language":"zh-CN,zh;q=0.9"}
    if ref: h["Referer"]=ref
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=12)
        raw=r.read()
        if raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
        return raw
    except Exception as e:
        print(f"  ⚠ {e.__class__.__name__}")
        return None

print("="*50)
print("  同花顺热门前100 · 生成静态页面")
print("="*50)

# 获取热榜
print("[1/4] 获取1小时热榜...")
raw=fetch("https://eq.10jqka.com.cn/open/api/hot_list/v1/hot_stock/a/hour/data.txt",
          "https://eq.10jqka.com.cn/webpage/ths-hot-list/index.html")
stocks=None
if raw:
    try:
        d=json.loads(raw)
        if d.get("status_code")==0:
            stocks=d["data"]["stock_list"]
    except: pass

if not stocks:
    print("  ❌ 获取热榜失败"); exit(1)
print(f"  ✓ {len(stocks)} 只")

# 获取行情
print("[2/4] 获取实时行情...")
codes=[s["code"] for s in stocks]
quotes={}
for i in range(0,len(codes),50):
    b=codes[i:i+50]
    p=[f"sh{c}" if c.startswith(("6","9")) else f"sz{c}" for c in b]
    raw=fetch(f"https://qt.gtimg.cn/q={','.join(p)}","https://qt.gtimg.cn/")
    if not raw: continue
    t=raw.decode("gbk","replace")
    for line in t.strip().split("\n"):
        m=re.match(r'v_[^=]+="(.+)"\s*;?\s*$',line.strip())
        if not m: continue
        f=m.group(1).split("~")
        if len(f)<40: continue
        try: quotes[f[2]]={"p":float(f[3]) if f[3] else 0,"cp":float(f[32]) if f[32] else 0}
        except: continue
    time.sleep(0.1)
print(f"  ✓ {sum(1 for c in codes if c in quotes)}/{len(codes)}")

# 归类
print("[3/4] 归类合并...")
BROAD_RULES = [
    (["绿色电力","超超临界","虚拟电厂","碳交易","电力","电网","发电","能源","风电","光伏","核电","水电","火电","氢能","储能"],"电力能源"),
    (["芯片","半导体","封装","大基金","光刻","晶圆","中芯国际","集成电路","PCB","存储器","闪存","DRAM"],"半导体芯片"),
    (["CPO","共封装光学","光纤","F5G","5G","6G","WiFi","光通信","通信","光模块","光缆"],"通信光通信"),
    (["AI","人工智能","算力","东数西算","大模型","AIGC","ChatGPT","深度学习","大数据","云计算","数据要素"],"人工智能算力"),
    (["医药","医疗","药","CRO","CDMO","创新药","生物","疫苗","流感","血氧","医美","中药","医疗器械"],"医药医疗"),
    (["军工","航天","航空","船舶","军民融合","国防","卫星","无人机"],"军工航天"),
    (["白酒","超级品牌","消费","食品","饮料","家电","零售","免税","旅游","酒店","餐饮","乳业"],"大消费"),
    (["金融","银行","证券","保险","券商","信托","数字货币","支付"],"金融"),
    (["汽车","新能源车","特斯拉","锂电","充电","无人驾驶","整车","汽配","锂电池","钠离子"],"新能源汽车"),
    (["房地产","物业","园区","基建","建筑","建材","新型城镇化","水泥","钢铁","工程机械"],"房地产基建"),
    (["化工","化肥","农药","化纤","煤化工","石油","石化","天然气","稀土","有色","有机硅"],"化工材料"),
    (["电子","MicroLED","LED","OLED","面板","显示","消费电子","果指数","传感器"],"电子制造"),
    (["数字","NFT","Web3","区块链","元宇宙","信创","软件","信息安全"],"数字经济"),
    (["中特估","国企改革","央企","国资","中字头","一带一路"],"国企中特估"),
    (["传媒","游戏","影视","出版","广告","短视频","直播"],"传媒游戏"),
    (["环保","节能","减排","碳中和","污水处理","固废","生态"],"环保"),
]

def map_concept(name):
    for kw,broad in BROAD_RULES:
        for k in kw:
            if k in name: return broad
    return name

items=[]
for s in stocks:
    q=quotes.get(s["code"],{})
    raw_c=s.get("tag",{}).get("concept_tag",[])
    broad_c=list(dict.fromkeys(map_concept(c) for c in raw_c)) or ["其他"]
    items.append({"c":s["code"],"n":s.get("name",""),"o":s.get("order",0),
                   "q":q.get("p",0),"p":q.get("cp",0),
                   "cs":broad_c,"rc":raw_c,
                   "tg":s.get("tag",{}).get("popularity_tag","")})

# 统计
cats={}
for x in items:
    for c in x["cs"]: cats[c]=cats.get(c,0)+1
print(f"  ✓ {len(cats)} 个行业大类")
zt=sum(1 for x in items if x["p"]>=9.8)
print(f"  ✓ 涨停 {zt} 只")

# 生成HTML
print("[4/4] 生成页面...")
data_json=json.dumps({"s":items,"ut":time.strftime("%H:%M:%S"),"dt":time.strftime("%Y-%m-%d")},ensure_ascii=True)

HTML=f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>同花顺热门前100 · 广义板块分类</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333}}
.header{{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;padding:24px 32px;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(0,0,0,.15)}}
.header h1{{font-size:24px}}
.header .sub{{font-size:14px;opacity:.8;margin-top:4px}}
.header .bar{{display:flex;align-items:center;gap:20px;margin-top:10px;flex-wrap:wrap;font-size:13px;opacity:.85}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.stats{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
.stat{{background:#fff;border-radius:8px;padding:14px 20px;flex:1;min-width:100px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.stat .n{{font-size:28px;font-weight:700;color:#1a1a2e}}
.stat .l{{font-size:12px;color:#888;margin-top:2px}}
.sector{{background:#fff;border-radius:10px;margin-bottom:16px;box-shadow:0 1px 6px rgba(0,0,0,.06);overflow:hidden}}
.sector-hd{{padding:14px 20px;font-size:16px;font-weight:600;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;gap:10px;background:#fafbfc}}
.sector-hd .badge{{background:#e8ecf1;color:#666;font-size:12px;padding:2px 10px;border-radius:10px}}
.sector-hd .sub-tags{{font-size:11px;color:#aaa;font-weight:400;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:300px}}
table{{width:100%;border-collapse:collapse}}
th{{padding:10px 16px;font-size:12px;color:#888;font-weight:500;text-align:left;border-bottom:1px solid #f0f0f0;background:#fafbfc}}
td{{padding:10px 16px;font-size:14px;border-bottom:1px solid #f5f5f5}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#f8f9fb}}
.ca{{color:#999;font-family:monospace;font-size:13px}}
.cm{{font-weight:500}}
.r{{color:#d63031;font-weight:600}}
.g{{color:#00b894;font-weight:600}}
.ztg{{display:inline-block;padding:2px 8px;border-radius:3px;font-size:12px;font-weight:600}}
.ztg.zt{{background:#fde8e8;color:#d63031}}
.ztg.jzt{{background:#fff3e0;color:#e67e22}}
.pop{{display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;background:#e8f4fd;color:#2980b9;margin-left:6px}}
.ft{{color:#999;font-size:12px;text-align:center;padding:20px}}
</style></head><body>
<div class="header">
<h1>🔥 同花顺热门前100 · 广义板块分类</h1>
<div class="sub">{time.strftime("%Y-%m-%d %H:%M")} · 1小时热门 · 合并细分题材为行业大类</div>
</div>
<div class="container" id="app"></div>
<div class="ft">数据来源: 同花顺热榜API · 生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
<script>
var DATA = {data_json};
(function(s){{
if(!s||!s.length){{document.getElementById('app').innerHTML='<div class="stat"><div class="n">暂无数据</div></div>';return}}
var up=s.filter(function(x){{return x.p>0}}).length,dn=s.filter(function(x){{return x.p<0}}).length,zt=s.filter(function(x){{return x.p>=9.8}}).length,av=(s.reduce(function(a,x){{return a+x.p}},0)/s.length).toFixed(2);
var g={{}};
s.forEach(function(x){{(x.cs||['其他']).forEach(function(cn){{if(!g[cn])g[cn]=[];g[cn].push(x)}})}});
var e=Object.entries(g).sort(function(a,b){{return b[1].length-a[1].length}});
var h='<div class="stats"><div class="stat"><div class="n">'+s.length+'</div><div class="l">热门股票</div></div><div class="stat"><div class="n" style="color:#d63031">'+zt+'</div><div class="l">涨停</div></div><div class="stat"><div class="n" style="color:#d63031">'+up+'/<span style="color:#00b894">'+dn+'</span></div><div class="l">涨/跌</div></div><div class="stat"><div class="n">'+Object.keys(g).length+'</div><div class="l">行业大类</div></div><div class="stat"><div class="n">'+av+'%</div><div class="l">平均涨幅</div></div></div>';
e.forEach(function(p){{var cn=p[0],ss=p[1];var at={{}};ss.forEach(function(x){{(x.rc||[]).forEach(function(t){{at[t]=1}})}});var tags=Object.keys(at).sort().slice(0,5).join(' · ');
h+='<div class="sector"><div class="sector-hd">📌 '+cn+' <span class="badge">'+ss.length+'只</span><span class="sub-tags">'+tags+'</span></div><table><thead><tr><th>排名</th><th>名称</th><th>代码</th><th>最新价</th><th>涨幅</th><th>备注</th></tr></thead><tbody>';
ss.sort(function(a,b){{return parseInt(a.o)-parseInt(b.o)}}).forEach(function(x){{var cp=x.p||0,cl=cp>0?'r':cp<0?'g':'',sg=cp>0?'+':'';
var bg='';if(cp>=9.8)bg='<span class="ztg zt">涨停</span>';else if(cp>=7)bg='<span class="ztg jzt">近涨停</span>';
var pop=x.tg?'<span class="pop">'+x.tg+'</span>':'';
h+='<tr><td style="font-weight:600;color:#d63031">#'+x.o+'</td><td class="cm"><a href="https://stockpage.10jqka.com.cn/'+(x.c||'')+'/" target="_blank" style="color:inherit;text-decoration:none">'+(x.n||"-")+'</a>'+pop+'</td><td class="ca">'+(x.c||"-")+'</td><td>'+(x.q||0).toFixed(2)+'</td><td class="'+cl+'">'+sg+cp.toFixed(2)+'%</td><td>'+bg+'</td></tr>'}});
h+='</tbody></table></div>'}});
document.getElementById('app').innerHTML=h;
}})(DATA.s);
</script></body></html>"""

with open(os.path.join(os.path.dirname(__file__),"热门前100.html"),"w",encoding="utf-8") as f:
    f.write(HTML)
print(f"\n  ✅ 已生成: 热门前100.html")
print(f"  📊 {len(items)} 只股票, {len(cats)} 个行业大类, 涨停 {zt}")
print(f"  📁 双击打开即可查看")
print("="*50)

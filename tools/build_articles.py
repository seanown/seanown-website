# -*- coding: utf-8 -*-
"""
從 data/posts.json 生成每篇文章的獨立內頁：article/<slug>/index.html
每頁含：獨立 URL、單獨 TDK、Berkeley 藍金排版、作者簡介、延伸閱讀、洽談合作 CTA、JSON-LD Article。
"""
import io, os, re, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')

# 文章英文 slug（SEO 友善，關鍵詞命名）
SLUGS = {
    '34': 'macau-budget-2020-2024-analysis',
    '33': 'hdi-2025-human-development-report',
    '32': 'thinking-fast-and-slow-reading-notes',
    '31': 'macau-five-year-plan-diversification',
    '01': 'three-choices-define-your-life',
    '02': 'rent-hike-still-profitable-yet-closed',
    '03': 'sun-yat-sen-party-and-country',
    '04': 'qixi-festival-original-meaning',
    '05': 'richard-koo-balance-sheet-recession',
    '06': 'just-set-out-is-the-answer',
    '07': 'august-eighth-fathers-day-origin',
    '08': 'liqiu-start-of-autumn',
    '09': 'ring-finger-longer-than-index',
    '10': 'global-chinese-influencer-award-extended',
    '11': 'fuhang-a-fathers-wisdom',
    '12': 'jianlai-sword-immortals-oath',
    '13': 'jinggangshan-first-mountain',
    '14': 'wulong-waterfall-pools',
    '15': 'wugongshan-young-hikers',
    '16': 'one-promise-a-lifetime',
    '17': 'ninghong-tea-xiushui',
    '18': 'tengwang-pavilion-night-tour',
    '19': 'yimen-chen-clan-dean',
    '20': 'kaipu-group-reunion',
    '21': 'nanjing-firms-eyeing-shantou',
    '22': 'jieyang-shantou-overseas-letters',
    '23': 'all-meat-pizza-shantou',
    '24': 'kangfu-founder-huang-huaqun',
    '25': 'macau-ai-cross-border-services',
    '26': 'ai-content-marketing-ctr-jump',
    '27': 'macau-1-plus-4-digital-hub',
    '28': 'chinese-cultural-ip-globalization',
    '29': 'young-entrepreneur-cross-boundary-thinking',
    '30': 'choices-over-effort-three-turning-points',
}

SITE = 'https://seanown.org'


def esc(t):
    return html.escape(t or '', quote=False)


def inline(t):
    """行內格式：粗體、行內 HTML 保留、相對路徑修正；外部連結一律新標籤"""
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'href="(https?://[^"]+)"(?! target=)',
               r'href="\1" target="_blank" rel="noopener"', t)
    # 行內連結補上相對路徑
    t = re.sub(r'href="(?!https?:|#|/|\.\./)([^"]+)"', r'href="../../\1"', t)
    t = re.sub(r'href="/([^"]+)"', r'href="' + SITE + r'/\1"', t)
    return t


def fix_asset(p):
    if p.startswith(('http', '//', '/', '../')):
        return p
    return '../../' + p


def md_to_html(body, title=''):
    """極簡 Markdown → HTML：## / ### / 列表 / 引用 / 表格 / 粗體 / 分隔線"""
    if not body or not body.strip():
        return ''
    b = body.replace('\r\n', '\n')
    b = re.sub(r'<br\s*/?>', '\n', b, flags=re.I)
    lines = b.split('\n')
    # 去掉與標題重複的首行
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and title and lines[0].strip().rstrip('✨📊⌚🔥 ').strip() == title.strip().rstrip('✨📊⌚🔥 ').strip():
        lines.pop(0)
    out, buf, i = [], [], 0

    def flush():
        if buf:
            para = '<br>'.join(x.strip() for x in buf if x.strip())
            if para:
                out.append('<p>%s</p>' % inline(para))
            buf.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if re.match(r'^-{3,}$', s):
            flush(); out.append('<hr>'); i += 1; continue
        m = re.match(r'^(#{2,4})\s+(.*)$', s)
        if m:
            flush()
            lv = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lv, inline(m.group(2).strip()), lv))
            i += 1; continue
        if s.startswith('|'):  # 表格
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            if len(rows) >= 2:
                sep = re.match(r'^[\s:\-|]+$', '|'.join(rows[1])) if len(rows) > 1 else None
                head, rest = rows[0], (rows[2:] if sep else rows[1:])
                h = '<div class="tbl-wrap"><table><thead><tr>' + ''.join('<th>%s</th>' % inline(c) for c in head) + '</tr></thead><tbody>'
                for r in rest:
                    h += '<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>'
                out.append(h + '</tbody></table></div>')
            continue
        if s.startswith('>'):  # 引用
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                q.append(lines[i].strip().lstrip('>').strip())
                i += 1
            out.append('<blockquote>%s</blockquote>' % inline('<br>'.join(x for x in q if x)))
            continue
        if re.match(r'^[-*]\s+', s):  # 無序列表
            flush()
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i].strip()):
                items.append(re.sub(r'^[-*]\s+', '', lines[i].strip()))
                i += 1
            out.append('<ul>' + ''.join('<li>%s</li>' % inline(x) for x in items) + '</ul>')
            continue
        if re.match(r'^\d+\.\s+', s):  # 有序列表
            flush()
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                items.append(re.sub(r'^\d+\.\s+', '', lines[i].strip()))
                i += 1
            out.append('<ol>' + ''.join('<li>%s</li>' % inline(x) for x in items) + '</ol>')
            continue
        buf.append(ln); i += 1
    flush()
    return '\n'.join(out)


def plain(t, n=110):
    t = re.sub(r'<[^>]+>', '', t or '')
    t = re.sub(r'[#*>\-`|\n]', '', t).strip()
    return (t[:n] + '…') if len(t) > n else t


CSS = """
:root{--blue:#002676;--blue-dark:#010133;--gold:#FDB515;--gold-dark:#FC9313;--bg:#F8F9FB;--white:#fff;--text:#1A1A1A;--gray:#667085;--line:#E4E8EF}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;color:var(--text);background:var(--white);line-height:1.75;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
.topbar{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.82);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.topbar-in{max-width:1080px;margin:0 auto;padding:0 24px;height:58px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.brand{font-weight:800;color:var(--blue);font-size:16px;letter-spacing:.5px}
.brand span{color:var(--gold)}
.topbar .minimal-hint{font-size:13px;color:var(--gray);text-decoration:none}
.topbar .minimal-hint:hover{color:var(--blue)}
.wrap{max-width:780px;margin:0 auto;padding:36px 24px 0}
.crumb{font-size:13px;color:var(--gray);margin-bottom:22px}
.crumb a:hover{color:var(--blue)}
.meta{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.tag{background:var(--blue);color:#fff;font-size:13px;font-weight:600;padding:5px 14px;border-radius:4px;letter-spacing:1px}
.date{color:var(--gray);font-size:14px}
h1{font-size:34px;line-height:1.4;color:var(--blue);font-weight:800;margin-bottom:18px;letter-spacing:.5px}
.lead{font-size:17px;line-height:1.8;color:var(--gray);margin:0 0 26px;padding:2px 0 0;border-left:3px solid var(--gold);padding-left:16px}
.rule{width:56px;height:4px;background:var(--gold);border-radius:2px;margin:0 0 26px}
.cover{margin:0 0 26px;border-radius:12px;overflow:hidden;box-shadow:0 8px 28px rgba(1,1,51,.10)}
.cover img{width:100%;display:block}
.article p{margin:0 0 20px;font-size:17px;text-align:justify}
.article h2{font-size:23px;line-height:1.5;color:var(--blue);font-weight:800;margin:40px 0 16px;padding-left:14px;border-left:5px solid var(--gold)}
.article h3{font-size:19px;color:var(--blue);font-weight:700;margin:28px 0 12px}
.article strong{color:var(--blue);font-weight:700}
.article ul,.article ol{margin:0 0 20px;padding-left:24px}
.article li{margin-bottom:9px;font-size:17px}
.article blockquote{margin:0 0 22px;padding:16px 20px;background:var(--bg);border-left:4px solid var(--gold);border-radius:0 8px 8px 0;color:#3A3A3A;font-size:16px}
.article hr{border:none;border-top:1px solid var(--line);margin:38px 0}
.tbl-wrap{overflow-x:auto;margin:0 0 22px}
.article table{width:100%;border-collapse:collapse;font-size:15px}
.article th{background:var(--blue);color:#fff;padding:11px 14px;text-align:left;font-weight:600}
.article td{border-bottom:1px solid var(--line);padding:11px 14px}
.gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:30px 0 6px}
.gallery img{width:100%;height:170px;object-fit:cover;border-radius:10px;cursor:zoom-in;transition:transform .2s}
.gallery img:hover{transform:scale(1.02)}
.author{margin-top:46px;background:var(--bg);border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:12px;padding:26px 26px 22px;display:flex;gap:20px;align-items:flex-start}
.author .a-img{width:76px;height:76px;border-radius:50%;object-fit:cover;border:3px solid var(--gold);flex:0 0 auto}
.author .a-body{flex:1}
.author h2{font-size:17px;color:var(--blue);margin:0 0 8px;border:none;padding:0}
.author p{font-size:15px;color:#4A4A4A;margin-bottom:10px}
.author .who{font-weight:700;color:var(--blue);font-size:16px;margin-bottom:6px}
.author .a-btn{display:inline-block;background:var(--blue);color:#fff;font-size:13px;font-weight:700;padding:8px 18px;border-radius:999px;text-decoration:none}
.author .a-btn:hover{background:var(--blue-dark)}
.related{margin-top:42px;padding-top:30px;border-top:1px solid var(--line)}
.related h2{font-size:19px;color:var(--blue);margin:0 0 18px;padding-left:12px;border-left:4px solid var(--gold)}
.rel-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.rel-card{display:block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 20px;transition:all .2s}
.rel-card:hover{border-color:var(--gold);box-shadow:0 10px 26px rgba(1,1,51,.09);transform:translateY(-3px)}
.rel-card .rc-tag{font-size:12px;color:var(--blue);background:#FFF3D0;padding:2px 9px;border-radius:10px;font-weight:600}
.rel-card h3{font-size:16px;color:var(--blue);margin:9px 0 6px;line-height:1.45;font-weight:700}
.rel-card p{font-size:13px;color:var(--gray);margin:0}
.cta{margin:40px 0 0;background:linear-gradient(135deg,#002676 0%,#010133 100%);border-radius:14px;padding:32px 28px;text-align:center;color:#fff}
.cta h2{color:#fff;font-size:21px;margin:0 0 8px;border:none;padding:0}
.cta p{color:rgba(255,255,255,.82);font-size:15px;margin-bottom:20px}
.btn{display:inline-block;background:var(--gold);color:var(--blue-dark);font-weight:800;padding:13px 34px;border-radius:999px;font-size:15px;transition:all .2s}
.btn:hover{background:var(--gold-dark);transform:translateY(-2px)}
.btn.ghost{background:transparent;color:#fff;border:2px solid rgba(255,255,255,.5);margin-left:10px}
.btn.ghost:hover{background:rgba(255,255,255,.12)}
.foot{margin-top:46px;padding:26px 0 46px;border-top:1px solid var(--line);font-size:13px;color:var(--gray);line-height:1.9}
.foot a{color:var(--blue)}
.lb{position:fixed;inset:0;background:rgba(1,1,51,.92);display:none;align-items:center;justify-content:center;z-index:999;cursor:zoom-out;padding:24px}
.lb img{max-width:100%;max-height:100%;border-radius:8px}
.float-cta{position:fixed;right:22px;bottom:22px;z-index:1500;background:var(--gold);color:var(--blue-dark);font-weight:800;padding:13px 22px;border-radius:999px;box-shadow:0 10px 26px rgba(2,8,32,.35);text-decoration:none;font-size:14px;transition:transform .2s,box-shadow .2s}
.float-cta:hover{transform:translateY(-3px);box-shadow:0 16px 34px rgba(2,8,32,.4)}
@media(max-width:720px){h1{font-size:25px}.article h2{font-size:20px}.article p,.article li{font-size:16px}.rel-grid{grid-template-columns:1fr}.gallery{grid-template-columns:repeat(2,1fr)}.wrap{padding:26px 18px 0}.author{flex-direction:column;gap:14px}.lead{font-size:15.5px}}
"""

# ---------- 附件：雜誌翻頁閱讀器（研究報告類文章） ----------
ATTACHMENTS = {
    'macau-budget-2020-2024-analysis': {
        'kicker': '附件 · 研究報告',
        'title': '澳門政府五年賬本（2020–2024 決算）',
        'sub': '像翻雜誌一樣讀這份報告：左頁圖表、右頁解讀，共 4 頁。亦可下載 PDF 或開啟可查可篩的互動版。',
        'pdf': '../../assets/reports/macau-budget-ledger-report.pdf',
        'pdf_label': '下載完整報告 PDF（4 頁 / 1.3 MB）',
        'link': '../../macau-budget-ledger.html',
        'pages': [
            {
                'img': '../../assets/images/ledger-shot-dashboard.webp',
                'alt': '五年總支出看板與民生佔比圓環',
                'h': '財政大盤一覽',
                'body': ('<p>2020–2024 五年，澳門一般綜合預算<strong>累計總支出 4,759.5 億元</strong>，年均 951.9 億元；'
                         '2024 年度總支出 979.5 億元，對比 2023 年 <strong>+8.1%</strong>，回歸常態增長軌道。</p>'
                         '<p>按約 68 萬人口粗略估算，人均年財政支出<strong>約 14 萬元</strong>——公庫的每一筆錢，都對應著城市運作的真實脈動。</p>'),
            },
            {
                'img': '../../assets/images/ledger-shot-wheel.webp',
                'alt': '支出結構輪盤：九大功能分類五年決算額',
                'h': '錢都花在哪：九大分類',
                'body': ('<p>輪盤把九大功能分類攤開：「其他功能」（現金分享、醫療補貼、稅項返還等惠民措施）五年合計 1,129.1 億元；'
                         '<strong>經濟服務 805.0 億元</strong>居實質政策分類之首；教育 619.5 億、衛生 559.6 億緊隨其後。</p>'
                         '<p>教育、衛生、社會保障、房屋、社會及社區服務五大民生類別，合計佔總支出<strong> 40.1%</strong>，是公共財政的壓艙石。</p>'),
            },
            {
                'img': '../../assets/images/ledger-shot-trend.webp',
                'alt': '年度總支出趨勢：2020–2024',
                'h': '五年走勢：逆週期調節',
                'body': ('<p>走勢呈完整周期：<strong>2021 年 891.5 億</strong>為五年低點（疫情緊縮）；2022 年兩度《預算修改法》增撥投資，'
                         '衝上<strong> 1,021.5 億</strong>的唯一千億高點；2023 年特別措施退出回落至 905.7 億；2024 年復甦回升至 979.5 億。</p>'
                         '<p>「應急收縮 — 擴張托底 — 常態回歸」，正是澳門財政逆週期調節的完整軌跡。</p>'),
            },
            {
                'img': '../../assets/images/ledger-shot-donut.webp',
                'alt': '支出分類佔比甜甜圈圖',
                'h': '結構啟示：讀懂賬本找機會',
                'body': ('<p><strong>房屋支出五年增長近四倍</strong>，2024 年按年大增 49.2%、增幅居九大分類之首——公屋興建與都市更新，'
                         '將持續帶動建築、建材、物業上下游。</p>'
                         '<p>經濟服務重點從疫情救助轉向產業培育，配合「1+4」多元策略，中小企支援、旅遊推廣與數位經濟投入，'
                         '就是產業界的切入點。</p>'),
            },
        ],
    },
}

RDR_CSS = """
/* ---------- 附件：雜誌翻頁閱讀器 ---------- */
.rdr{margin:34px 0 40px;background:#F7F1E3;border:1px solid #E7DCC2;border-radius:18px;padding:26px 26px 22px;box-shadow:0 14px 40px rgba(1,1,51,.08)}
.rdr-badge{display:inline-block;background:#1F6B4A;color:#F2EFE3;font-size:12px;font-weight:700;letter-spacing:2px;padding:4px 14px;border-radius:999px;margin-bottom:12px}
.rdr-title{font-family:Georgia,"Songti TC",serif;font-size:23px;color:#14503A;line-height:1.35;margin:0 0 6px}
.rdr-sub{font-size:14px;color:#8A8266;margin:0 0 18px}
.rdr-stage{position:relative;background:#FFFDF6;border:1px solid #E7DCC2;border-radius:14px;overflow:hidden}
.rdr-spread{display:none;grid-template-columns:1.05fr 1fr;min-height:520px}
.rdr-spread.is-on{display:grid;animation:rdrIn .45s ease}
@keyframes rdrIn{from{opacity:0;transform:translateX(14px)}to{opacity:1;transform:none}}
.rdr-left{position:relative;background:#F7F1E3;border-right:1px dashed #E7DCC2;overflow:hidden}
.rdr-left img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center top}
.rdr-left::after{content:'';position:absolute;top:0;bottom:0;right:-14px;width:14px;background:linear-gradient(90deg,rgba(80,60,20,.14),rgba(80,60,20,0))}
.rdr-right{padding:30px 30px 26px;display:flex;flex-direction:column}
.rdr-pageno{font-size:12px;letter-spacing:2px;color:#B8912E;font-weight:700;margin-bottom:10px}
.rdr-right h3{font-family:Georgia,"Songti TC",serif;font-size:21px;color:#14503A;margin:0 0 14px;line-height:1.4}
.rdr-right p{font-size:15px;line-height:1.85;color:#3D4A55;margin:0 0 13px;text-align:justify}
.rdr-right strong{color:#14503A}
.rdr-hint{margin-top:auto;padding-top:14px;font-size:12.5px;color:#8A8266;border-top:1px dashed #E7DCC2}
.rdr-nav{display:flex;align-items:center;justify-content:center;gap:18px;margin-top:16px}
.rdr-btn2{background:#1F6B4A;color:#fff;border:none;border-radius:999px;padding:9px 24px;font-size:14px;cursor:pointer;font-family:inherit;transition:background .2s}
.rdr-btn2:hover{background:#14503A}
.rdr-btn2:disabled{opacity:.4;cursor:default}
.rdr-dots{display:flex;gap:8px}
.rdr-dot{width:9px;height:9px;border-radius:50%;background:#D8CBA8;border:none;padding:0;cursor:pointer;transition:all .2s}
.rdr-dot.on{background:#B8912E;transform:scale(1.25)}
.rdr-actions{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:18px}
.rdr-dl{display:inline-block;background:#B8912E;color:#fff;font-weight:700;font-size:14.5px;padding:12px 28px;border-radius:999px;text-decoration:none;transition:all .2s}
.rdr-dl:hover{background:#9A7822;transform:translateY(-2px)}
.rdr-open{display:inline-block;background:transparent;color:#14503A;border:1.5px solid #1F6B4A;font-weight:700;font-size:14.5px;padding:11px 26px;border-radius:999px;text-decoration:none;transition:all .2s}
.rdr-open:hover{background:rgba(31,107,74,.08)}
@media(max-width:820px){
.rdr{padding:18px 14px 16px}
.rdr-spread{grid-template-columns:1fr;min-height:0}
.rdr-spread.is-on{display:block}
.rdr-left{height:230px;border-right:none;border-bottom:1px dashed #E7DCC2}
.rdr-left img{position:absolute}
.rdr-right{padding:20px 18px 18px}
.rdr-title{font-size:19px}
}
"""


def build_reader(att):
    spreads = []
    n = len(att['pages'])
    for i, p in enumerate(att['pages']):
        spreads.append(
            ('<div class="rdr-spread%s">'
             '<div class="rdr-left"><img src="%s" alt="%s" loading="lazy"></div>'
             '<div class="rdr-right"><span class="rdr-pageno">第 %d 頁 · 共 %d 頁</span>'
             '<h3>%s</h3>%s'
             '<p class="rdr-hint">想查每一筆明細？下方可下載 PDF，或開啟可篩選的互動賬本。</p></div></div>'
             ) % (' is-on' if i == 0 else '', p['img'], esc(p['alt']), i + 1, n,
                  esc(p['h']), p['body']))
    dots = ''.join('<button class="rdr-dot%s" data-rp="%d" aria-label="第 %d 頁"></button>'
                   % (' on' if i == 0 else '', i, i + 1) for i in range(n))
    rdr = (
        '<section class="rdr" id="report-reader">'
        '<span class="rdr-badge">%s</span>'
        '<h2 class="rdr-title">%s</h2>'
        '<p class="rdr-sub">%s</p>'
        '<div class="rdr-stage" id="rdrStage">%s</div>'
        '<div class="rdr-nav">'
        '<button class="rdr-btn2" id="rdrPrev" type="button">← 上一頁</button>'
        '<div class="rdr-dots">%s</div>'
        '<button class="rdr-btn2" id="rdrNext" type="button">下一頁 →</button>'
        '</div>'
        '<div class="rdr-actions">'
        '<a class="rdr-dl" href="%s" download>⬇ %s</a>'
        '<a class="rdr-open" href="%s" target="_blank" rel="noopener">互動賬本（可轉 · 可查 · 可篩選）↗</a>'
        '</div>'
        '<script>(function(){var sp=document.querySelectorAll("#rdrStage .rdr-spread");if(!sp.length)return;'
        'var cur=0,dots=document.querySelectorAll(".rdr-dot"),pv=document.getElementById("rdrPrev"),nx=document.getElementById("rdrNext");'
        'function go(k){if(k<0||k>=sp.length)return;sp[cur].classList.remove("is-on");dots[cur].classList.remove("on");'
        'cur=k;sp[cur].classList.add("is-on");dots[cur].classList.add("on");'
        'pv.disabled=cur===0;nx.disabled=cur===sp.length-1}'
        'pv.addEventListener("click",function(){go(cur-1)});nx.addEventListener("click",function(){go(cur+1)});'
        'dots.forEach(function(d,i){d.addEventListener("click",function(){go(i)})});'
        'document.addEventListener("keydown",function(e){if(!document.getElementById("report-reader"))return;'
        'if(e.key==="ArrowLeft")go(cur-1);if(e.key==="ArrowRight")go(cur+1)});'
        'pv.disabled=true;nx.disabled=sp.length===1})();</script>'
        '</section>'
    ) % (esc(att['kicker']), esc(att['title']), esc(att['sub']),
         ''.join(spreads), dots,
         att['pdf'], esc(att['pdf_label']), att['link'])
    return rdr


def build(post, allposts):
    num = str(post.get('num', '')).strip()
    slug = SLUGS.get(num) or ('post-' + (num or 'x'))
    title = (post.get('title') or '').strip()
    cat = (post.get('category') or '').strip()
    date = (post.get('date') or '').strip()
    loc = (post.get('location') or '').strip()
    imgs = [fix_asset(x) for x in (post.get('images') or [])]
    body_html = md_to_html(post.get('body') or '', title)
    desc = plain(post.get('body') or title, 105) or title
    url = '%s/article/%s/' % (SITE, slug)

    rel = [p for p in allposts if p.get('category') == cat and str(p.get('num')) != num]
    rel += [p for p in allposts if p.get('category') != cat and str(p.get('num')) != num]
    rel = [p for p in rel if (p.get('body') or '').strip()][:2]
    rel_html = ''
    for p in rel:
        pn = str(p.get('num', '')).strip()
        ps = SLUGS.get(pn) or ('post-' + pn)
        rel_html += (
            '<a class="rel-card" href="%s/article/%s/">'
            '<span class="rc-tag">%s</span><h3>%s</h3><p>%s</p></a>'
        ) % (SITE, ps, esc(p.get('category')), esc(p.get('title')), esc(plain(p.get('body'), 46)))

    cover = ''
    gallery = ''
    if imgs:
        cover = ('<figure class="cover"><img src="%s" alt="%s — %s 配圖" loading="lazy"></figure>'
                 % (imgs[0], esc(title), esc(cat)))
    if len(imgs) > 1:
        gallery = '<div class="gallery">' + ''.join(
            '<img src="%s" alt="%s 實拍圖 %d" loading="lazy" onclick="document.getElementById(\'lbimg\').src=this.src;document.getElementById(\'lb\').style.display=\'flex\'">'
            % (x, esc(title), n + 1) for n, x in enumerate(imgs[1:])) + '</div>'

    att = ATTACHMENTS.get(slug)
    reader = build_reader(att) if att else ''
    page_css = CSS + (RDR_CSS if att else '')

    ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "datePublished": date,
        "dateModified": date,
        "articleSection": cat,
        "inLanguage": "zh-Hant",
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "author": {"@type": "Person", "name": "翁振軒 Sean Own", "url": SITE + "/"},
        "publisher": {"@type": "Person", "name": "翁振軒 Sean Own", "url": SITE + "/"},
        "url": url,
    }
    if imgs:
        ld["image"] = SITE + '/' + imgs[0].replace('../../', '')
    else:
        ld["image"] = '%s/assets/og/%s.jpg' % (SITE, slug)

    kw = '，'.join([x for x in ['翁振軒', 'Sean Own', cat, '澳門', '產業觀察'] if x])

    page = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜翁振軒專欄</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{kw}">
<meta name="author" content="翁振軒 Sean Own">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="../../assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="翁振軒 Sean Own 專欄">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="{og_img}">
<script type="application/ld+json">{ld}</script>
<style>{css}</style>
</head>
<body>
<div class="topbar"><div class="topbar-in">
<a class="brand" href="{site}/">翁振軒 <span>SEAN OWN</span></a>
<a class="minimal-hint" href="{site}/articles/">專欄文章</a>
</div></div>

<div class="wrap">
<div class="crumb"><a href="{site}/">首頁</a> › <a href="{site}/articles/">專欄文章</a> › 本文</div>
<article class="article">
<div class="meta"><span class="tag">{cat}</span><span class="date">{date_fmt}{loc_fmt}</span></div>
<h1>{title}</h1>
<div class="rule"></div>
<p class="lead">{lead}</p>
{reader}
{cover}
{body}
{gallery}
</article>

<div class="author">
<img class="a-img" src="../../assets/images/avatar-1x1.jpg" alt="翁振軒 Sean Own 大頭照" loading="lazy">
<div class="a-body">
<div class="who">翁振軒 Sean Own</div>
<p>粵港澳大灣區電子商會會長、龍遊集團創辦人。以澳門為基地，深耕文化產業，推動中國數位服務出海與中華文創 IP 落地。</p>
<a class="a-btn" href="{site}/#sec-author">瞭解更多關於作者</a>
</div>
</div>

<div class="related">
<h2>延伸閱讀</h2>
<div class="rel-grid">{rel}</div>
</div>

<div class="cta">
<h2>想進一步交流？</h2>
<p>無論是數位出海、文化 IP 合作，或青年跨界連結，都歡迎與我聊聊。</p>
<a class="btn" href="{site}/#sec-contact">洽談合作</a>
<a class="btn ghost" href="{site}/articles/">更多文章</a>
</div>

<div class="foot">
© 2026 翁振軒 Sean Own · <a href="{site}/">返回首頁</a><br>
本文為作者個人觀點，轉載請註明出處。
</div>
</div>
<a class="float-cta" href="{site}/#sec-contact">洽談合作</a>
<div class="lb" id="lb" onclick="this.style.display='none'"><img id="lbimg" src="" alt=""></div>
</body>
</html>
""".format(
        title=esc(title), cat=esc(cat), desc=esc(desc), kw=esc(kw), url=url,
        og_title=esc(title[:30]), og_desc=esc(desc[:80]),
        og_img='%s/assets/og/%s.jpg' % (SITE, slug),
        ld=json.dumps(ld, ensure_ascii=False), css=page_css, site=SITE,
        lead=esc(plain(post.get('body') or title, 110)),
        reader=reader,
        date_fmt=date.replace('-', ' 年 ', 1).replace('-', ' 月 ') + ' 日' if date else '',
        loc_fmt=(' · ' + esc(loc)) if loc else '',
        cover=cover, body=body_html, gallery=gallery, rel=rel_html,
    )

    d = os.path.join(ROOT, 'article', slug)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    return slug, title


CATS = ['澳門觀察', '產業評論', '商道隨筆', '行走見聞', '文化雅述', '研究報告']


def build_list(posts):
    """雜誌目錄式專欄列表頁：articles/index.html（靜態卡片 + JS 分類過濾）"""
    items = sorted(posts, key=lambda p: str(p.get('date', '')), reverse=True)
    cards = ''
    for p in items:
        num = str(p.get('num', '')).strip()
        slug = SLUGS.get(num) or ('post-' + num)
        title = (p.get('title') or '').strip()
        cat = (p.get('category') or '').strip()
        date = (p.get('date') or '').strip()
        lead = plain(p.get('body') or title, 62)
        cover = '../assets/og/%s.jpg' % slug
        cards += (
            '<a class="lc-card" href="%s/article/%s/" data-cat="%s">'
            '<div class="lc-img"><img src="%s" alt="%s — %s 封面" loading="lazy"></div>'
            '<div class="lc-body"><div class="lc-top"><span class="lc-tag">%s</span><span class="lc-date">%s</span></div>'
            '<h2>%s</h2><p>%s</p></div></a>'
        ) % (SITE, slug, esc(cat), cover, esc(title), esc(cat), esc(cat),
             date.replace('-', '.'), esc(title), esc(lead))

    cat_btns = '<button class="lc-cat on" data-c="全部">全部<span>%d</span></button>' % len(items)
    for c in CATS:
        n = sum(1 for p in items if p.get('category') == c)
        if n:
            cat_btns += '<button class="lc-cat" data-c="%s">%s<span>%d</span></button>' % (esc(c), esc(c), n)

    url = SITE + '/articles/'
    desc = '翁振軒專欄，聚焦澳門產業觀察、數位經濟趨勢、商業戰略思考。'
    ld = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "專欄文章｜翁振軒 Sean Own", "url": url,
        "description": desc, "inLanguage": "zh-Hant",
        "author": {"@type": "Person", "name": "翁振軒 Sean Own", "url": SITE + "/"},
    }
    page = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>專欄文章｜翁振軒 Sean Own</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="翁振軒,專欄,澳門觀察,產業評論,商道隨筆,數位經濟,Sean Own">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="專欄文章｜翁振軒 Sean Own">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld}</script>
<style>
:root{{--blue:#002676;--blue-dark:#010133;--gold:#FDB515;--gold-dark:#FC9313;--gold-light:#FFF3D0;--bg:#F8F9FB;--text:#1A1A1A;--gray:#667085;--line:#E4E8EF}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;color:var(--text);background:var(--white);line-height:1.75;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue);text-decoration:none}}
html{{scroll-behavior:smooth}}
.topbar{{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.82);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}}
.topbar-in{{max-width:1180px;margin:0 auto;padding:0 24px;height:62px;display:flex;align-items:center;justify-content:space-between}}
.brand{{font-weight:800;color:var(--blue);font-size:17px;letter-spacing:.5px}}
.brand span{{color:var(--gold)}}
.mini-cta{{background:var(--blue);color:#fff;font-size:14px;font-weight:700;padding:9px 20px;border-radius:999px}}
.mini-cta:hover{{background:var(--blue-dark)}}
.masthead{{background:linear-gradient(135deg,#002676 0%,#010133 100%);color:#fff;padding:64px 24px 58px;text-align:center}}
.masthead .kicker{{font-size:14px;letter-spacing:6px;color:var(--gold);font-weight:700;margin-bottom:14px}}
.masthead h1{{font-size:44px;font-weight:800;letter-spacing:2px;margin-bottom:12px}}
.masthead p{{color:rgba(255,255,255,.75);font-size:16px}}
.filter-bar{{position:sticky;top:62px;z-index:40;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);padding:14px 24px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}}
.lc-cat{{border:1.5px solid var(--line);background:#fff;border-radius:999px;padding:8px 18px;font-size:14px;font-weight:600;color:var(--text);cursor:pointer;transition:all .2s}}
.lc-cat span{{font-size:12px;color:var(--gray);margin-left:5px}}
.lc-cat:hover{{border-color:var(--gold)}}
.lc-cat.on{{background:var(--blue);border-color:var(--blue);color:#fff}}
.lc-cat.on span{{color:var(--gold)}}
.grid{{max-width:1180px;margin:0 auto;padding:44px 24px 60px;display:grid;grid-template-columns:repeat(3,1fr);gap:26px}}
.lc-card{{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;transition:transform .2s,box-shadow .2s;color:inherit}}
.lc-card:hover{{transform:translateY(-5px);box-shadow:0 18px 44px rgba(0,38,118,.13)}}
.lc-card.hide{{display:none}}
.lc-img{{aspect-ratio:16/9;overflow:hidden}}
.lc-img img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s}}
.lc-card:hover .lc-img img{{transform:scale(1.04)}}
.lc-body{{padding:20px 22px 22px;flex:1;display:flex;flex-direction:column}}
.lc-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
.lc-tag{{font-size:12px;font-weight:700;color:var(--blue);background:var(--gold-light);padding:3px 11px;border-radius:10px}}
.lc-date{{font-size:12px;color:var(--gray)}}
.lc-card h2{{font-size:17.5px;line-height:1.5;color:var(--blue);margin-bottom:8px;font-weight:800}}
.lc-card p{{font-size:13.5px;color:var(--gray);line-height:1.7;flex:1}}
.foot{{border-top:1px solid var(--line);padding:30px 24px 44px;text-align:center;font-size:13px;color:var(--gray);line-height:1.9}}
.foot a{{color:var(--blue)}}
.float-cta{{position:fixed;right:22px;bottom:22px;z-index:1500;background:var(--gold);color:var(--blue-dark);font-weight:800;padding:13px 22px;border-radius:999px;box-shadow:0 10px 26px rgba(2,8,32,.35);font-size:14px;transition:transform .2s,box-shadow .2s}}
.float-cta:hover{{transform:translateY(-3px);box-shadow:0 16px 34px rgba(2,8,32,.4)}}
@media(max-width:960px){{.grid{{grid-template-columns:repeat(2,1fr)}}.masthead h1{{font-size:34px}}}}
@media(max-width:620px){{.grid{{grid-template-columns:1fr;padding:30px 16px 50px}}.filter-bar{{top:62px;padding:12px 14px}}.masthead{{padding:46px 18px 40px}}.masthead h1{{font-size:28px}}}}
</style>
</head>
<body>
<div class="topbar"><div class="topbar-in">
<a class="brand" href="{site}/">翁振軒 <span>SEAN OWN</span></a>
<a class="mini-cta" href="{site}/#sec-contact">洽談合作</a>
</div></div>

<header class="masthead">
<div class="kicker">SEAN OWN COLUMNS</div>
<h1>專欄文章</h1>
<p>澳門產業觀察 · 數位經濟趨勢 · 商道與文化隨筆 — 共 {n} 篇</p>
</header>

<div class="filter-bar" id="cats">{cats}</div>

<main class="grid" id="grid">{cards}</main>

<footer class="foot">
© 2026 翁振軒 Sean Own · <a href="{site}/">返回首頁</a> · <a href="{site}/#sec-contact">洽談合作</a><br>
觀點僅代表作者個人立場，轉載請註明出處。
</footer>

<a class="float-cta" href="{site}/#sec-contact">洽談合作</a>
<script>
(function(){{
var btns=document.querySelectorAll('.lc-cat');
btns.forEach(function(b){{b.addEventListener('click',function(){{
btns.forEach(function(x){{x.classList.remove('on')}});
b.classList.add('on');
var c=b.getAttribute('data-c');
document.querySelectorAll('.lc-card').forEach(function(card){{
card.classList.toggle('hide',c!=='全部'&&card.getAttribute('data-cat')!==c);
}});
}})}});
}})();
</script>
</body>
</html>
""".format(desc=esc(desc), url=url, og='%s/assets/og/articles.jpg' % SITE,
           ld=json.dumps(ld, ensure_ascii=False), site=SITE,
           n=len(items), cats=cat_btns, cards=cards)
    d = os.path.join(ROOT, 'articles')
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    print('generated /articles/ list page (%d cards)' % len(items))


def main():
    data = json.load(io.open(POSTS, encoding='utf-8'))
    posts = data['posts']
    published = [p for p in posts if p.get('status') != '整理中']
    for p in posts:
        p['slug'] = SLUGS.get(str(p.get('num', '')).strip(), '')
    made = []
    for p in published:
        made.append(build(p, published))
    build_list(published)
    io.open(POSTS, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('generated %d article pages' % len(made))
    for s, t in made:
        print('  /article/%s/  %s' % (s, t[:34]))


if __name__ == '__main__':
    main()

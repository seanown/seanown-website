# -*- coding: utf-8 -*-
"""
從 data/posts.json 生成每篇文章的獨立內頁：article/<slug>/index.html
每頁含：獨立 URL、單獨 TDK、Berkeley 藍金排版、作者簡介、延伸閱讀、洽談合作 CTA、JSON-LD Article。
"""
import io, os, re, json, html, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SERIES_JSON = os.path.join(ROOT, 'data', 'series.json')

# 輯（Series）定義：由 data/series.json 驅動，posts.json 用 series 欄位掛載
SERIES = {'collections': [], 'series': []}
SERIES_BY_ID = {}


def load_series():
    """載入輯定義。檔案不存在時退化為空，不阻斷原有 build。"""
    global SERIES, SERIES_BY_ID
    SERIES = {'collections': [], 'series': []}
    if os.path.exists(SERIES_JSON):
        SERIES = json.load(io.open(SERIES_JSON, encoding='utf-8'))
    SERIES.setdefault('collections', [])
    SERIES.setdefault('series', [])
    SERIES_BY_ID = {s['id']: s for s in SERIES['series']}
    return SERIES


def sorted_series():
    """輯的顯示順序：order 小的在前，同值再按輯名。"""
    return sorted(SERIES['series'],
                  key=lambda s: (int(s.get('order', 99) or 99), s.get('name', '')))


def series_members(posts, sid):
    """取回某輯的成員文章。

    order_dir='desc' → 新的在前（主線／隨筆類，讓最新觀點當門面）
    order_dir='asc'（預設）→ 日期升序（行記類，按實際行程順序讀）
    同日再按篇號。
    """
    ms = [p for p in posts
          if (p.get('series') or '').strip() == sid and p.get('status') != '整理中']
    desc = str(SERIES_BY_ID.get(sid, {}).get('order_dir') or 'asc').lower() == 'desc'
    return sorted(ms, key=lambda p: (str(p.get('date', '')), str(p.get('num', ''))),
                  reverse=desc)

# 文章英文 slug（SEO 友善，關鍵詞命名）
SLUGS = {
    '37': 'naval-three-steps-find-your-calling',
    '36': 'wealth-leverage-macau',
    '35': 'recent-reflections-twelve-quotes-sketch',
    '34': 'macau-budget-2020-2024-analysis',
    '33': 'hdi-2025-human-development-report',
    '32': 'thinking-fast-and-slow-reading-notes',
    '31': 'macau-five-year-plan-diversification',
    '01': 'three-choices-define-your-life',
    '02': 'rent-hike-still-profitable-yet-closed',
    '04': 'qixi-festival-original-meaning',
    '05': 'richard-koo-balance-sheet-recession',
    '06': 'two-thoughts-set-out-and-palm',
    '07': 'august-eighth-fathers-day-origin',
    '08': 'liqiu-start-of-autumn',
    '11': 'fuhang-a-fathers-wisdom',
    '13': 'jiangxi-seven-days',
    '20': 'kaipu-group-reunion',
    '21': 'chaoshan-journey-letters-home',
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
.wrap{max-width:1120px;margin:0 auto;padding:36px 24px 0}
/* PC：雜誌跨頁雙欄——左右兩頁並排、圖文交織；手機自動回單欄 */
@media(min-width:900px){
.abody{column-count:2;column-gap:56px;column-rule:1px solid var(--line)}
.abody h2{column-span:all;margin-top:34px}
.abody h3{break-after:avoid-column}
.abody .tbl-wrap{column-span:all;break-inside:avoid}
.abody blockquote{break-inside:avoid;margin-bottom:20px}
.abody ul,.abody ol{break-inside:avoid}
.abody hr{column-span:all}
}
@media(min-width:900px) and (max-width:1279px){.wrap{max-width:960px}}
.crumb{font-size:13px;color:var(--gray);margin-bottom:22px}
.crumb a:hover{color:var(--blue)}
.meta{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.tag{background:var(--blue);color:#fff;font-size:13px;font-weight:600;padding:5px 14px;border-radius:4px;letter-spacing:1px}
.date{color:var(--gray);font-size:14px}
h1{font-size:30px;line-height:1.45;color:var(--blue);font-weight:800;margin-bottom:18px;letter-spacing:.5px;max-width:960px}
.lead{font-size:17px;line-height:1.8;color:var(--gray);margin:0 0 26px;padding:2px 0 0;border-left:3px solid var(--gold);padding-left:16px;max-width:940px}
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

# ---------- 輯（Series）導覽 ----------
SERIES_NAV_CSS = """
.series-nav{margin-top:34px;background:linear-gradient(135deg,#F5F7FC 0%,#EEF2FA 100%);border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:12px;padding:22px 24px}
.sn-kicker{display:inline-block;font-size:12px;font-weight:700;letter-spacing:2px;color:var(--blue);background:#fff;border:1px solid var(--line);border-radius:999px;padding:3px 12px;margin-bottom:10px}
.sn-title{display:block;font-size:22px;font-weight:800;color:var(--blue);margin-bottom:4px}
.sn-title:hover{color:var(--gold-dark)}
.sn-meta{font-size:13px;color:var(--gray);margin-bottom:16px}
.sn-links{display:flex;gap:10px;flex-wrap:wrap}
.sn-links a{flex:1 1 180px;min-width:0;background:#fff;border:1px solid var(--line);border-radius:9px;padding:11px 14px;font-size:13.5px;line-height:1.5;color:var(--text);transition:all .2s}
.sn-links a:hover{border-color:var(--gold);transform:translateY(-2px)}
.sn-links .sn-lab{display:block;font-size:11px;letter-spacing:1.5px;color:var(--gray);font-weight:700;margin-bottom:3px}
.sn-links .sn-all{flex:0 0 auto;text-align:center;color:var(--blue);font-weight:700;background:var(--blue);color:#fff;border-color:var(--blue)}
.sn-links .sn-all:hover{background:var(--blue-dark);color:#fff}
.sn-empty{opacity:.45;pointer-events:none}
@media(max-width:720px){.series-nav{padding:18px}.sn-title{font-size:19px}.sn-links a{flex:1 1 100%}}
"""

# ---------- 輯頁（series/<id>/index.html）獨立版型 ----------
SERIES_PAGE_CSS = """
:root{--blue:#002676;--blue-dark:#010133;--gold:#FDB515;--gold-dark:#FC9313;--bg:#F8F9FB;--text:#1A1A1A;--gray:#667085;--line:#E4E8EF}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;color:var(--text);background:var(--bg);line-height:1.8;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
.topbar{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.85);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.topbar-in{max-width:1080px;margin:0 auto;padding:0 24px;height:62px;display:flex;align-items:center;justify-content:space-between}
.brand{font-weight:800;color:var(--blue);font-size:17px;letter-spacing:.5px}
.brand span{color:var(--gold)}
.mini-cta{background:var(--blue);color:#fff;font-size:14px;font-weight:700;padding:9px 20px;border-radius:999px}
.mini-cta:hover{background:var(--blue-dark)}
.masthead{background:linear-gradient(135deg,#002676 0%,#010133 100%);color:#fff;padding:60px 24px 54px}
.masthead-in{max-width:1080px;margin:0 auto}
.kicker{font-size:13px;letter-spacing:5px;color:var(--gold);font-weight:700;margin-bottom:12px}
.masthead h1{font-size:42px;font-weight:800;letter-spacing:2px;margin-bottom:10px}
.masthead .sub{color:rgba(255,255,255,.8);font-size:16px;margin-bottom:6px}
.masthead .period{color:var(--gold);font-size:14px;font-weight:700;letter-spacing:1px}
.wrap{max-width:1080px;margin:0 auto;padding:36px 24px 0}
.intro{background:#fff;border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:12px;padding:26px 28px;margin-bottom:34px}
.intro .i-lab{font-size:12px;letter-spacing:3px;color:var(--gray);font-weight:700;margin-bottom:12px}
.intro p{font-size:15.5px;color:#2B2B2B;margin-bottom:12px;white-space:pre-line}
.intro p:last-child{margin-bottom:0}
.sec-lab{font-size:13px;letter-spacing:3px;color:var(--gray);font-weight:700;margin-bottom:16px}
.timeline{list-style:none;position:relative;padding-left:26px}
.timeline:before{content:"";position:absolute;left:6px;top:6px;bottom:6px;width:2px;background:var(--line)}
.tl-item{position:relative;margin-bottom:18px}
.tl-item:before{content:"";position:absolute;left:-25px;top:16px;width:11px;height:11px;border-radius:50%;background:var(--gold);border:2px solid #fff;box-shadow:0 0 0 2px var(--line)}
.tl-card{display:flex;gap:18px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;align-items:center;transition:all .22s}
.tl-card:hover{border-color:var(--gold);transform:translateY(-3px);box-shadow:0 10px 26px rgba(2,8,32,.09)}
.tl-img{flex:0 0 132px;height:88px;border-radius:8px;overflow:hidden;background:var(--bg)}
.tl-img img{width:100%;height:100%;object-fit:cover;display:block}
.tl-body{flex:1;min-width:0}
.tl-top{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:5px}
.tl-no{font-size:11px;font-weight:800;color:var(--blue);background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:1px 8px;letter-spacing:1px}
.tl-date{font-size:12.5px;color:var(--gray)}
.tl-loc{font-size:12.5px;color:var(--gray)}
.tl-body h2{font-size:18px;font-weight:800;line-height:1.5;margin-bottom:5px}
.tl-body h2 a{color:var(--text)}
.tl-card:hover h2 a{color:var(--blue)}
.tl-body p{font-size:14px;color:var(--gray)}
.tl-arr{flex:0 0 auto;font-size:20px;color:var(--gold)}
.other-ser{max-width:1080px;margin:0 auto;padding:8px 24px 0;display:flex;gap:12px;flex-wrap:wrap}
.os-card{flex:1 1 240px;background:#fff;border:1px solid var(--line);border-radius:11px;padding:16px 18px;transition:all .2s}
.os-card:hover{border-color:var(--gold);transform:translateY(-2px)}
.os-card .os-n{font-size:17px;font-weight:800;color:var(--blue);margin-bottom:3px}
.os-card .os-d{font-size:13px;color:var(--gray)}
.os-card .os-grp{display:inline-block;font-size:11px;font-weight:700;letter-spacing:2px;color:var(--blue);background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:1px 8px;margin-bottom:7px}
.foot{margin-top:46px;padding:26px 24px 46px;border-top:1px solid var(--line);font-size:13px;color:var(--gray);text-align:center}
.foot a{color:var(--blue)}
@media(max-width:720px){.masthead h1{font-size:28px}.tl-card{flex-direction:column;align-items:flex-start}.tl-img{flex:0 0 auto;width:100%;height:170px}.wrap{padding:26px 18px 0}}
"""


def build_series_page(s, posts, all_series):
    """產生單一輯頁 series/<id>/index.html"""
    sid = s['id']
    members = series_members(posts, sid)
    if not members:
        return None
    desc_order = str(s.get('order_dir') or 'asc').lower() == 'desc'
    cover_num = str(s.get('cover_num') or members[0].get('num', '')).strip()
    cover_slug = SLUGS.get(cover_num) or ('post-' + cover_num)

    items = ''
    for i, p in enumerate(members):
        pn = str(p.get('num', '')).strip()
        pslug = SLUGS.get(pn) or ('post-' + pn)
        loc = (p.get('location') or '').strip()
        ptitle = (p.get('title') or '').strip()
        plead = plain(p.get('body') or '', 58)
        if ptitle and plead.startswith(ptitle):  # 正文開頭常重複一次標題，去掉
            plead = plead[len(ptitle):].lstrip('。：: ·|｜—-,，')
        items += (
            '<li class="tl-item"><a class="tl-card" href="%s/article/%s/">'
            '<div class="tl-img"><img src="../../assets/og/%s.jpg" alt="%s 封面" loading="lazy"></div>'
            '<div class="tl-body"><div class="tl-top">'
            '<span class="tl-no">%02d / %02d</span>'
            '<span class="tl-date">%s</span>'
            '%s'
            '</div><h2>%s</h2><p>%s</p></div>'
            '<div class="tl-arr">›</div></a></li>'
        ) % (SITE, pslug, pslug, esc(p.get('title')), i + 1, len(members),
             (p.get('date') or '').replace('-', '.'),
             ('<span class="tl-loc">· %s</span>' % esc(loc)) if loc else '',
             esc(ptitle), esc(plead))

    others = ''
    for o in sorted_series():
        if o['id'] == sid:
            continue
        om = series_members(posts, o['id'])
        if not om:
            continue
        others += ('<a class="os-card" href="%s/series/%s/"><div class="os-n">%s</div>'
                   '<div class="os-d">%d 篇 · %s</div></a>'
                   % (SITE, esc(o['id']), esc(o['name']), len(om), esc(o.get('period') or '')))
    if others:
        others = ('<div class="sec-lab" style="max-width:1080px;margin:0 auto;padding:34px 24px 0">'
                  '其他輯</div><div class="other-ser">%s</div>' % others)

    coll_name = ''
    for c in SERIES.get('collections', []):
        if c['id'] == s.get('collection'):
            coll_name = c['name']
            break

    name = s.get('name') or sid
    url = '%s/series/%s/' % (SITE, sid)
    desc = plain(s.get('intro') or s.get('subtitle') or name, 100)
    ld = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "%s｜翁振軒 Sean Own" % name, "url": url, "description": desc,
        "inLanguage": "zh-Hant",
        "author": {"@type": "Person", "name": "翁振軒 Sean Own", "url": SITE + "/"},
    }
    page = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}｜輯｜翁振軒 Sean Own</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{kw}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="../../assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{name}｜輯｜翁振軒 Sean Own">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld}</script>
<style>{css}</style>
</head>
<body>
<div class="topbar"><div class="topbar-in">
<a class="brand" href="{site}/">翁振軒 <span>SEAN OWN</span></a>
<a class="mini-cta" href="{site}/articles/">專欄文章</a>
</div></div>

<div class="masthead"><div class="masthead-in">
<div class="kicker">{kicker}</div>
<h1>{name}</h1>
<div class="sub">{sub}</div>
<div class="period">{period} · 共 {n} 篇</div>
</div></div>

<div class="wrap">
<div class="intro"><div class="i-lab">輯 序</div>{intro}</div>
<div class="sec-lab">{sec_lab}</div>
<ul class="timeline">{items}</ul>
</div>

{others}

<div class="foot">© 2026 翁振軒 Sean Own · <a href="{site}/">返回首頁</a> · <a href="{site}/articles/">全部文章</a></div>
</body>
</html>
""".format(
        name=esc(name), desc=esc(desc), kw=esc('%s,%s,翁振軒,Sean Own,專欄' % (name, coll_name)),
        url=url, og='%s/assets/og/%s.jpg' % (SITE, cover_slug),
        ld=json.dumps(ld, ensure_ascii=False), css=SERIES_PAGE_CSS, site=SITE,
        kicker=esc(('%s · 輯' % coll_name) if coll_name else '輯'),
        sub=esc(s.get('subtitle') or ''), period=esc(s.get('period') or ''),
        n=len(members), items=items, others=others,
        sec_lab='按時間倒序 · 最新在前' if desc_order else '按時間順序',
        intro=''.join('<p>%s</p>' % esc(x.strip())
                      for x in (s.get('intro') or '（輯序待補）').split('\n\n') if x.strip()),
    )
    d = os.path.join(ROOT, 'series', sid)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    return sid, name, len(members)


def build_series_index(posts):
    """產生輯總覽頁 series/index.html

    全部輯按 order 一次排到底（主線輯在最前）。分組名（如「行記」）改為
    顯示在卡片上的小標籤，不再切分區塊——否則分組邏輯會壓過 order，
    讓行記排到主線前面。
    """
    coll_name = {c['id']: c['name'] for c in SERIES.get('collections', [])}
    cards = ''
    any_series = False
    for s in sorted_series():
        m = series_members(posts, s['id'])
        if not m:
            continue
        any_series = True
        grp = coll_name.get(s.get('collection'), '')
        cards += (
            '<a class="os-card" href="%s/series/%s/" style="flex:1 1 300px">'
            '%s'
            '<div class="os-n">%s</div>'
            '<div class="os-d" style="margin-bottom:6px">%s</div>'
            '<div class="os-d">%d 篇 · %s</div></a>'
        ) % (SITE, esc(s['id']),
             ('<div class="os-grp">%s</div>' % esc(grp)) if grp else '',
             esc(s['name']), esc(s.get('subtitle') or ''),
             len(m), esc(s.get('period') or ''))
    rows = ''
    if cards:
        rows = '<div class="other-ser" style="padding-top:30px">%s</div>' % cards
    if not any_series:
        return

    url = SITE + '/series/'
    desc = '翁振軒專欄分輯總覽：同一主題的文章收成一輯，按順序讀。'
    ld = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "輯總覽｜翁振軒 Sean Own", "url": url, "description": desc,
        "inLanguage": "zh-Hant",
        "author": {"@type": "Person", "name": "翁振軒 Sean Own", "url": SITE + "/"},
    }
    page = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>輯總覽｜翁振軒 Sean Own</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="輯總覽｜翁振軒 Sean Own">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld}</script>
<style>{css}</style>
</head>
<body>
<div class="topbar"><div class="topbar-in">
<a class="brand" href="{site}/">翁振軒 <span>SEAN OWN</span></a>
<a class="mini-cta" href="{site}/articles/">專欄文章</a>
</div></div>

<div class="masthead"><div class="masthead-in">
<div class="kicker">SERIES</div>
<h1>輯</h1>
<div class="sub">同一主題的文章收成一輯，按順序讀。</div>
</div></div>

{rows}

<div class="foot">© 2026 翁振軒 Sean Own · <a href="{site}/">返回首頁</a> · <a href="{site}/articles/">全部文章</a></div>
</body>
</html>
""".format(desc=esc(desc), url=url, ld=json.dumps(ld, ensure_ascii=False),
           css=SERIES_PAGE_CSS, site=SITE, rows=rows)
    d = os.path.join(ROOT, 'series')
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)


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
    'hdi-2025-human-development-report': {
        'kicker': '附件 · 原版報告',
        'title': 'GDP 之外：用 HDI 重新丈量發展（原版全 11 頁）',
        'sub': '像翻雜誌一樣讀原版報告：左右兩頁、可翻頁。亦可下載完整 PDF，或開啟互動星海版。',
        'pdf': '../../assets/reports/hdi-report-2025.pdf',
        'pdf_label': '下載完整報告 PDF（11 頁 / 2.0 MB）',
        'link': '../../hdi-starfield/index.html',
        'open_label': '互動星海版（可滑動 · 星空動畫）↗',
        'hint': '想看星空動畫與完整數據？下方可下載 PDF，或開啟互動星海版。',
        'pages': [
            {'img': '../../assets/images/hdi-pages/p01.webp', 'img2': '../../assets/images/hdi-pages/p02.webp',
             'alt': '報告封面：GDP 之外，用 HDI 重新丈量發展', 'alt2': '01 夜燈不等於燭光',
             'pn1': 'PDF 第 1 頁', 'pn2': 'PDF 第 2 頁'},
            {'img': '../../assets/images/hdi-pages/p03.webp', 'img2': '../../assets/images/hdi-pages/p04.webp',
             'alt': '02 HDI 是什麼：三把尺，一把指數', 'alt2': '三把尺細節：收入封頂等設計',
             'pn1': 'PDF 第 3 頁', 'pn2': 'PDF 第 4 頁'},
            {'img': '../../assets/images/hdi-pages/p05.webp', 'img2': '../../assets/images/hdi-pages/p06.webp',
             'alt': '03 核心一圖：人均 GDP × HDI 星圖', 'alt2': '04 HDI 排行榜：誰在頂端，中國在哪',
             'pn1': 'PDF 第 5 頁', 'pn2': 'PDF 第 6 頁'},
            {'img': '../../assets/images/hdi-pages/p07.webp', 'img2': '../../assets/images/hdi-pages/p08.webp',
             'alt': '澳門 0.934 折算約第 21 位（附註）', 'alt2': '05 四個反差：GDP 看不見的東西',
             'pn1': 'PDF 第 7 頁', 'pn2': 'PDF 第 8 頁'},
            {'img': '../../assets/images/hdi-pages/p09.webp', 'img2': '../../assets/images/hdi-pages/p10.webp',
             'alt': '中國 33 年 HDI +62% 與澳門比較', 'alt2': '數據來源 Data Sources',
             'pn1': 'PDF 第 9 頁', 'pn2': 'PDF 第 10 頁'},
            {'img': '../../assets/images/hdi-pages/p11.webp',
             'alt': '封底：SEAN OWN 數據研究特輯',
             'h': '讀完這份報告',
             'body': ('<p>封底的三個數字，就是全篇的座標系：<strong>冰島 0.972</strong> 說明小經濟體也能登頂；'
                      '<strong>中國 0.797</strong> 是 33 年 +62% 的進行式；<strong>中國澳門 0.934</strong> 提醒我們——'
                      '賭收蓋得起醫院，大學與科研卻要時間生長。</p>'
                      '<p>GDP 回答「有多大」，HDI 回答「活得如何」。兩把尺都拿在手裡，才量得出一個真實的世界。</p>'),
             'pn1': 'PDF 第 11 頁 · 封底'},
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
.rdr-spread.is-dual{grid-template-columns:1fr 1fr}
.rdr-spread.is-dual .rdr-left{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:18px 14px 14px;overflow:auto}
.rdr-spread.is-dual .rdr-left img{position:static;width:auto;max-width:100%;max-height:600px;object-fit:contain;border-radius:3px;box-shadow:0 8px 26px rgba(80,60,20,.2)}
.rdr-right-page{padding:18px 14px 14px;align-items:center;justify-content:flex-start;overflow:auto}
.rdr-right-page img{width:auto;max-width:100%;max-height:600px;border-radius:3px;box-shadow:0 8px 26px rgba(80,60,20,.2)}
.rdr-pgnum{display:block;font-size:11.5px;letter-spacing:2px;color:#B8912E;font-weight:700;margin-top:12px}
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
.rdr-spread.is-dual .rdr-left{height:auto;padding:14px 10px 10px}
.rdr-spread.is-dual .rdr-left img{max-height:none;width:100%}
.rdr-right-page{padding:14px 10px 10px}
.rdr-right-page img{max-height:none;width:100%}
.rdr-right{padding:20px 18px 18px}
.rdr-title{font-size:19px}
}
"""


def build_reader(att):
    spreads = []
    n = len(att['pages'])
    for i, p in enumerate(att['pages']):
        cls = ' is-dual' if p.get('img2') else ''
        if p.get('img2'):
            html = ('<div class="rdr-spread is-dual%s">'
                    '<div class="rdr-left"><img src="%s" alt="%s" loading="lazy"><span class="rdr-pgnum">%s</span></div>'
                    '<div class="rdr-right rdr-right-page"><img src="%s" alt="%s" loading="lazy"><span class="rdr-pgnum">%s</span></div>'
                    '</div>') % (' is-on' if i == 0 else '', p['img'], esc(p['alt']),
                                 esc(p.get('pn1', '')), p['img2'], esc(p.get('alt2', '')),
                                 esc(p.get('pn2', '')))
        else:
            html = ('<div class="rdr-spread%s">'
                    '<div class="rdr-left"><img src="%s" alt="%s" loading="lazy"></div>'
                    '<div class="rdr-right"><span class="rdr-pageno">第 %d 頁 · 共 %d 頁</span>'
                    '<h3>%s</h3>%s'
                    '<p class="rdr-hint">%s</p></div></div>'
                    ) % (' is-on' if i == 0 else '', p['img'], esc(p['alt']), i + 1, n,
                         esc(p['h']), p['body'], esc(att.get('hint', '想查每一筆明細？下方可下載 PDF，或開啟可篩選的互動賬本。')))
        spreads.append(html)
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
        '<a class="rdr-open" href="%s" target="_blank" rel="noopener">%s</a>'
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
         att['pdf'], esc(att['pdf_label']), att['link'],
         esc(att.get('open_label', '互動賬本（可轉 · 可查 · 可篩選）↗')))
    return rdr


QK_CSS = """
/* ---------- 金句手繪卡片組（自訂 HTML 片段用） ---------- */
.qk{column-span:all;margin:4px 0 0}
.qk-grid{display:grid;grid-template-columns:1fr;gap:30px}
@media(min-width:900px){.qk-grid{grid-template-columns:1fr 1fr;gap:34px 52px}}
.article .qk-card{display:block;background:#fff;border:1px solid #E9ECF2;border-radius:14px;padding:22px 22px 24px;margin:0;box-shadow:0 12px 28px -24px rgba(1,1,51,.4);break-inside:avoid}
.qk-inner{display:flex;gap:20px;align-items:flex-start}
.qk-badge{flex:0 0 106px;margin:0}
.qk-img{width:100%;height:auto;display:block}
.qk-scribble{margin:5px 0 0;text-align:center;font-size:11px;color:#9AA2B1;letter-spacing:.05em}
.qk-text{flex:1 1 auto;min-width:0}
.article .qk-num{font-size:11px;letter-spacing:.28em;color:#9AA2B1;margin:0 0 8px;font-weight:400}
.article .qk-tag{display:inline-block;background:#FFF3D0;color:#002676;font-size:11.5px;font-weight:700;letter-spacing:.14em;padding:3px 11px;border-radius:999px;margin:0 0 12px;border:none}
.article h2.qk-quote{font-size:20px;line-height:1.62;color:#1A1A1A;font-weight:800;margin:0 0 12px;padding:0 0 0 14px;border:none;border-left:3px solid var(--gold)}
.article p.qk-bg{margin:0 0 10px;font-size:13.5px;line-height:1.85;color:#667085;text-align:left}
.article p.qk-bg .qk-lbl{display:inline;margin-right:8px;font-size:10px;letter-spacing:.2em;color:#9AA2B1}
.article p.qk-insight{margin:0;font-size:13.5px;line-height:1.85;color:#1A1A1A;background:#F8F9FB;border-radius:10px;padding:11px 14px;text-align:left}
.article p.qk-insight .qk-lbl{display:block;margin-bottom:3px;font-size:10px;letter-spacing:.2em;color:#9AA2B1}
.qk-more{display:inline-block;margin-top:11px;font-size:12.5px;color:var(--blue);font-weight:700}
.qk-more:hover{color:var(--gold-dark)}
@media(max-width:640px){.article .qk-card{padding:18px 16px 20px}.qk-badge{flex:0 0 84px}.qk-inner{gap:14px}.article h2.qk-quote{font-size:18.5px}}
/* 長標題自適應（不影響站上其他文章） */
@media(max-width:720px){.article h1{font-size:clamp(17px,5vw,22px);letter-spacing:.02em;line-height:1.42;word-break:break-word}}
/* 手繪線稿筆觸 */
.qk .ln{fill:none;stroke:#1f1d1a;stroke-width:2.1;stroke-linecap:round;stroke-linejoin:round}
.qk .thin{stroke-width:1.3}
.qk .gray{fill:none;stroke:#9b958a;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.qk .dash{fill:none;stroke:#aaa49a;stroke-width:1.3;stroke-dasharray:5 5;stroke-linecap:round}
.qk .wash{fill:#ecebe6;stroke:none}
.qk .wash2{fill:#f4f3ef;stroke:none}
.qk .inkfill{fill:#1f1d1a;stroke:none}
.qk .ring{fill:none;stroke:#1f1d1a;stroke-width:1.8;opacity:.85}
.qk .ring2{fill:none;stroke:#1f1d1a;stroke-width:.9;opacity:.22}
"""

def build(post, allposts):
    num = str(post.get('num', '')).strip()
    slug = SLUGS.get(num) or ('post-' + (num or 'x'))
    title = (post.get('title') or '').strip()
    cat = (post.get('category') or '').strip()
    date = (post.get('date') or '').strip()
    loc = (post.get('location') or '').strip()
    imgs = [fix_asset(x) for x in (post.get('images') or [])]
    raw_rel = (post.get('raw_html') or '').strip()
    if raw_rel:  # 自訂 HTML 片段（跳過 Markdown 解析，原樣嵌入）
        body_html = io.open(os.path.join(ROOT, raw_rel), encoding='utf-8').read()
    else:
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

    # ---- 輯導覽：本篇所屬輯 + 輯內上一篇／下一篇 ----
    series_nav = ''
    sid = (post.get('series') or '').strip()
    if sid and sid in SERIES_BY_ID:
        s = SERIES_BY_ID[sid]
        ms = series_members(allposts, sid)
        idx = next((i for i, p in enumerate(ms)
                    if str(p.get('num', '')).strip() == num), -1)
        coll_name = next((c['name'] for c in SERIES.get('collections', [])
                          if c['id'] == s.get('collection')), '輯')
        if idx > 0:
            pp = ms[idx - 1]
            prev_a = ('<a href="%s/article/%s/"><span class="sn-lab">上一篇</span>%s</a>'
                      % (SITE, SLUGS.get(str(pp.get('num', '')).strip()), esc(pp.get('title'))))
        else:
            prev_a = '<a class="sn-empty"><span class="sn-lab">上一篇</span>（已是第一篇）</a>'
        if 0 <= idx < len(ms) - 1:
            nx = ms[idx + 1]
            next_a = ('<a href="%s/article/%s/"><span class="sn-lab">下一篇</span>%s</a>'
                      % (SITE, SLUGS.get(str(nx.get('num', '')).strip()), esc(nx.get('title'))))
        else:
            next_a = '<a class="sn-empty"><span class="sn-lab">下一篇</span>（已是最後一篇）</a>'
        series_nav = (
            '\n\n<div class="series-nav">'
            '<span class="sn-kicker">%s · 輯</span>'
            '<a class="sn-title" href="%s/series/%s/">《%s》</a>'
            '<div class="sn-meta">第 %d / %d 篇 · %s</div>'
            '<div class="sn-links">%s<a class="sn-all" href="%s/series/%s/">查看全輯</a>%s</div>'
            '</div>'
        ) % (esc(coll_name), SITE, sid, esc(s.get('name') or sid),
             idx + 1, len(ms), esc(s.get('period') or ''),
             prev_a, SITE, sid, next_a)

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
    page_css = CSS + (QK_CSS if raw_rel else '') + (RDR_CSS if att else '') + (SERIES_NAV_CSS if series_nav.strip() else '')

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
<div class="abody">{body}</div>
{gallery}
</article>{series_nav}

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
        series_nav=series_nav,
    )

    d = os.path.join(ROOT, 'article', slug)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    return slug, title


CATS = ['澳門觀察', '行走見聞', '閱讀筆記', '文化隨筆', '生活隨筆']


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

    # 輯資料：全部輯清單 + 欄目 → 輯（以該輯成員最多的分類歸屬）
    all_ser = []
    ser_of_cat = {}
    for s in sorted_series():
        m = series_members(items, s['id'])
        if not m:
            continue
        all_ser.append({'id': s['id'], 'name': s['name'], 'n': len(m)})
        cnt = {}
        for p in m:
            k = (p.get('category') or '').strip()
            cnt[k] = cnt.get(k, 0) + 1
        top = max(cnt.items(), key=lambda kv: kv[1])[0] if cnt else ''
        ser_of_cat.setdefault(top, []).append(
            {'id': s['id'], 'name': s['name'], 'n': len(m)})

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
<meta name="keywords" content="翁振軒,專欄,澳門觀察,行走見聞,閱讀筆記,文化隨筆,生活隨筆,數位經濟,Sean Own">
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
.ser-panel{{max-width:1180px;margin:0 auto;padding:0 24px;gap:10px;flex-wrap:wrap;align-items:center;display:none}}
.ser-panel.on{{display:flex;margin-top:16px}}
.ser-panel .sp-lab{{font-size:12px;letter-spacing:3px;color:var(--gray);font-weight:700}}
.ser-panel a{{border:1.5px solid var(--gold);background:#fff;border-radius:999px;padding:7px 16px;font-size:13.5px;font-weight:700;color:var(--blue);transition:all .2s}}
.ser-panel a:hover{{background:var(--blue);border-color:var(--blue);color:#fff}}
.ser-panel a span{{font-size:11.5px;color:var(--gray);margin-left:5px;font-weight:600}}
.ser-panel a:hover span{{color:var(--gold)}}
.ser-panel .sp-all{{border-color:var(--line);color:var(--gray);font-weight:600}}
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

<div class="ser-panel" id="serPanel"></div>

<main class="grid" id="grid">{cards}</main>

<footer class="foot">
© 2026 翁振軒 Sean Own · <a href="{site}/">返回首頁</a> · <a href="{site}/#sec-contact">洽談合作</a><br>
觀點僅代表作者個人立場，轉載請註明出處。
</footer>

<a class="float-cta" href="{site}/#sec-contact">洽談合作</a>
<script>
(function(){{
var ALL_SER={all_ser},SER_OF_CAT={ser_of_cat},SITE='{site}';
var panel=document.getElementById('serPanel');
function renderPanel(c){{
var list=(c==='全部')?ALL_SER:(SER_OF_CAT[c]||[]);
if(!list.length){{panel.innerHTML='';panel.classList.remove('on');return;}}
var h='<span class="sp-lab">輯</span>';
list.forEach(function(s){{h+='<a href="'+SITE+'/series/'+s.id+'/">'+s.name+'<span>'+s.n+' 篇</span></a>';}});
h+='<a class="sp-all" href="'+SITE+'/series/">全部輯 ›</a>';
panel.innerHTML=h;panel.classList.add('on');
}}
var btns=document.querySelectorAll('.lc-cat');
btns.forEach(function(b){{b.addEventListener('click',function(){{
btns.forEach(function(x){{x.classList.remove('on')}});
b.classList.add('on');
var c=b.getAttribute('data-c');
document.querySelectorAll('.lc-card').forEach(function(card){{
card.classList.toggle('hide',c!=='全部'&&card.getAttribute('data-cat')!==c);
}});
renderPanel(c);
}})}});
renderPanel('全部');
}})();
</script>
</body>
</html>
""".format(desc=esc(desc), url=url, og='%s/assets/og/articles.jpg' % SITE,
           ld=json.dumps(ld, ensure_ascii=False), site=SITE,
           n=len(items), cats=cat_btns, cards=cards,
           all_ser=json.dumps(all_ser, ensure_ascii=False),
           ser_of_cat=json.dumps(ser_of_cat, ensure_ascii=False))
    d = os.path.join(ROOT, 'articles')
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    print('generated /articles/ list page (%d cards)' % len(items))


PAGE_NODE_RE = re.compile(r'\s+data-page-node-id="[A-Za-z0-9_-]+"')


def sanitize_outputs():
    """清掉預覽工具注入的 data-page-node-id 屬性。

    WorkBuddy 的 HTML 預覽面板在開啟本機 HTML 時，會往標籤注入
    data-page-node-id="..."，讓檔案變大（10KB → 19KB）、<h1> 被吃掉。
    每次 build 收尾統一清一次，讓「重跑 build 就恢復」這條永遠成立。
    """
    targets = []
    targets += glob.glob(os.path.join(ROOT, 'article', '*', 'index.html'))
    targets += glob.glob(os.path.join(ROOT, 'series', '*', 'index.html'))
    targets += [os.path.join(ROOT, 'series', 'index.html'),
                os.path.join(ROOT, 'articles', 'index.html')]
    total = 0
    for f in targets:
        if not os.path.exists(f):
            continue
        s = io.open(f, encoding='utf-8').read()
        n = len(PAGE_NODE_RE.findall(s))
        if n:
            io.open(f, 'w', encoding='utf-8', newline='\n').write(
                PAGE_NODE_RE.sub('', s))
            total += n
    if total:
        print('sanitized data-page-node-id: %d' % total)
    return total


def main():
    data = json.load(io.open(POSTS, encoding='utf-8'))
    posts = data['posts']
    published = [p for p in posts if p.get('status') != '整理中']
    for p in posts:
        p['slug'] = SLUGS.get(str(p.get('num', '')).strip(), '')
    load_series()
    made = []
    for p in published:
        made.append(build(p, published))
    build_list(published)
    nser = 0
    for s in sorted_series():
        r = build_series_page(s, published, SERIES['series'])
        if r:
            nser += 1
            print('  /series/%s/  %s（%d 篇）' % r)
    build_series_index(published)
    sanitize_outputs()
    io.open(POSTS, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('generated %d article pages, %d series pages' % (len(made), nser))
    for sl, t in made:
        print('  /article/%s/  %s' % (sl, t[:34]))


if __name__ == '__main__':
    main()

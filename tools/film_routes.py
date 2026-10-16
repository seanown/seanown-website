# -*- coding: utf-8 -*-
"""跟著電影遊澳門 · 數字路線頁（hub + N 條路線；路線數由 routes.json 決定，勿硬編碼）。

與 film_collections.py 的分工：
  - collection/ 按「電影」聚合（一部片裡有哪些地標）——橫向看城；
  - route/      按「走法」串聯（一條線裡有哪些站）——縱向走路。
兩者互鏈，讓 83 篇觀後感從孤島變成網，再從網變成可走的路線。

資料來源 data/routes.json（由 tools/_export_routes.py 一次性橋接生成）：
  書的 63 站 × 網站的 GPS／文章 slug／同地電影。本模組只負責渲染，
  不做匹配；書更新後重跑 _export_routes.py 即可。

設計要點：
  - 每站一張卡：站名、電影（海報縮圖＋深鏈）、金句框、站位描寫、拍攝提示、
    實用資訊（地址／交通／開放／費用）、GPS＋Google 地圖連結、同地其他電影。
  - 無座標的站如實呈現原因（全城型場景／網站未收錄），用地址兜底，不造假座標。
  - 不嵌瓦片地圖（國外地圖瓦片有合规風險），只用座標文字＋Google 連結。
"""
import io, os, re, json, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def esc(t):
    return html.escape(t or '', quote=False)


def _maps_url(gps):
    """GPS 字串（'22.1943, 113.5377'）→ Google Maps search URL。"""
    q = (gps or '').replace('約 ', '').replace(' ', '')
    return 'https://www.google.com/maps/search/?api=1&query=' + q


# ── CSS（沿用 collection/ 的藍金＋米色體系，前綴 rp-/st-）────────────
PAGE_CSS = """
.rpage{--blue:#002676;--gold:#FDB515;--ink:#1c1a17;--muted:#8a8277;--line:#e7e0d4;--soft:#f6f3ec}
.rpage body,.rpage{font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;background:#faf8f3}
.rp-top{background:#002676;color:#fff}
.rp-top .in{max-width:1080px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:18px}
.rp-top a.brand{color:#fff;font-weight:700;letter-spacing:.04em;text-decoration:none;font-family:"Noto Serif TC",serif}
.rp-top a.brand span{color:#FDB515}
.rp-top a.lnk{color:#c9d6ee;text-decoration:none;font-size:14px}
.rp-top a.lnk:hover{color:#fff}
.rp-hero{background:linear-gradient(180deg,#002676,#001a4d);color:#fff;padding:52px 24px 46px;text-align:center}
.rp-hero .kick{letter-spacing:.4em;font-size:12px;color:#FDB515;margin-bottom:16px}
.rp-hero h1{font-family:"Noto Serif TC",serif;font-size:clamp(28px,4.6vw,44px);font-weight:900;margin:0 0 12px}
.rp-hero .sub{color:#c9d6ee;font-size:15px;max-width:680px;margin:0 auto;line-height:1.9}
.rp-hero .stat{margin-top:20px;display:flex;justify-content:center;gap:10px;flex-wrap:wrap}
.rp-hero .stat span{background:rgba(253,181,21,.14);border:1px solid rgba(253,181,21,.4);color:#FDB515;
  border-radius:20px;padding:5px 16px;font-size:13px;font-weight:700}
.rp-wrap{max-width:1080px;margin:0 auto;padding:36px 24px 70px}
.rp-sec{margin:0 0 40px}
.rp-sec h2{font-family:"Noto Serif TC",serif;font-size:22px;font-weight:900;color:#002676;
  border-left:5px solid #FDB515;padding-left:12px;margin:0 0 6px}
.rp-sec .d{color:#8a8277;font-size:13.5px;margin:0 0 18px;line-height:1.8}
/* hub 路線卡 */
.rp-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
@media(max-width:720px){.rp-grid{grid-template-columns:1fr}}
.rp-card{display:block;background:#fff;border:1px solid #e7e0d4;border-radius:14px;padding:22px 22px 18px;
  text-decoration:none;color:#1c1a17;transition:border-color .25s,box-shadow .25s}
.rp-card:hover{border-color:#002676;box-shadow:0 6px 22px rgba(0,20,70,.10)}
.rp-card .no{font-family:"Noto Serif TC",serif;font-size:13px;font-weight:900;color:#FDB515;letter-spacing:.18em}
.rp-card .t{font-family:"Noto Serif TC",serif;font-weight:900;font-size:19px;color:#002676;margin:6px 0 2px;line-height:1.4}
.rp-card .tag{display:inline-block;background:#002676;color:#FDB515;font-size:12px;font-weight:700;
  border-radius:12px;padding:2px 10px;margin:4px 0 8px}
.rp-card .c{font-size:13px;color:#6b6459;line-height:1.85;margin:0}
.rp-card .n{margin-top:12px;font-size:12.5px;font-weight:700;color:#002676}
.rp-card .n b{color:#B8860B}
/* 互鏈卡 */
.rp-x{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:720px){.rp-x{grid-template-columns:1fr}}
.rp-x a{display:block;background:#fff;border:1px dashed #d8cfbe;border-radius:12px;padding:16px 18px;
  text-decoration:none;color:#1c1a17}
.rp-x a:hover{border-color:#002676;border-style:solid}
.rp-x .t{font-family:"Noto Serif TC",serif;font-weight:900;font-size:15px;color:#002676}
.rp-x .c{font-size:12.5px;color:#8a8277;margin-top:4px;line-height:1.7}
/* 路線頁站點跳轉 */
.rp-jump{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 26px}
.rp-jump a{background:#fff;border:1px solid #e7e0d4;border-radius:18px;padding:5px 14px;text-decoration:none;
  font-size:13px;color:#002676;font-weight:700}
.rp-jump a:hover{background:#002676;color:#fff;border-color:#002676}
.rp-jump a b{color:#B8860B;margin-right:5px}
.rp-jump a:hover b{color:#FDB515}
.rp-jump .m{color:#8a8277;font-weight:400;font-size:12px;margin-left:5px}
/* 站點卡 */
.st{display:grid;grid-template-columns:58px 1fr;column-gap:18px;row-gap:0;padding:28px 0;border-top:1px dashed #e0d9cc}
.st:first-of-type{border-top:none}
/* 🔴 修版面塌縮：.st 是兩列網格，但只有 .no 與 .st-h 該並排——
   其餘子元素（金句框／正文／提示／資訊格）若不強制進第 2 列，
   會被 grid 自動換行輪流塞進 58px 窄列，造成「一字一行」（2026-10-16 軒哥抓到） */
.st>*:not(.no){grid-column:2}
.st .no{align-self:start}
@media(max-width:720px){.st{grid-template-columns:1fr;gap:10px}.st>*:not(.no){grid-column:1}}
.st .no{width:52px;height:52px;border-radius:50%;background:#002676;color:#FDB515;
  font-family:"Noto Serif TC",serif;font-weight:900;font-size:22px;
  display:flex;align-items:center;justify-content:center}
@media(max-width:720px){.st .no{width:44px;height:44px;font-size:19px}}
.st-h{display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap}
.st-h .thumb{flex:0 0 auto;width:52px;height:78px;object-fit:cover;border-radius:6px;
  box-shadow:0 2px 8px rgba(0,20,70,.16);background:#eee}
.st-h .nm{font-family:"Noto Serif TC",serif;font-size:20px;font-weight:900;color:#002676;line-height:1.4}
.st-h .mv{margin-top:6px;font-size:13.5px;color:#5a534a}
.st-h .mv a{color:#002676;font-weight:700;text-decoration:none;border-bottom:1px solid #FDB515}
.st-h .mv a:hover{background:#FDB515;color:#002676}
.st-h .mv .yr{color:#8a8277;font-size:12.5px;margin-left:4px}
.st-h .mv .nolink{color:#5a534a}
.st-h .txt{padding-top:2px}
.st-q{margin:14px 0 4px;padding:13px 18px;background:#f6f3ec;border-left:4px solid #FDB515;border-radius:0 10px 10px 0}
.st-q .q{font-family:"Noto Serif TC",serif;font-size:16px;font-weight:700;color:#1c1a17;line-height:1.75}
.st-q .a{font-size:12.5px;color:#8a8277;margin-top:6px;text-align:right}
.st-b p{font-size:15px;line-height:2.0;color:#3a352e;margin:12px 0 0}
.st-sub{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}
.st-sub .lab{font-size:12.5px;font-weight:700;color:#002676;background:#f0ebdf;
  border-radius:6px;padding:2px 8px;white-space:nowrap;height:fit-content}
.st-photo{flex:1;min-width:240px;display:flex;flex-wrap:wrap;gap:6px}
.st-photo span{font-size:12.5px;color:#5a534a;background:#fff;border:1px solid #e7e0d4;
  border-radius:14px;padding:3px 12px;line-height:1.6}
.st-info{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:16px 0 0}
@media(max-width:720px){.st-info{grid-template-columns:1fr}}
.st-info div{background:#fff;border:1px solid #e7e0d4;border-radius:10px;padding:9px 14px;font-size:13px;color:#3a352e;line-height:1.7}
.st-info b{color:#002676;font-weight:700;margin-right:6px}
.st-gps{margin:14px 0 0;font-size:13px;color:#5a534a;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.st-gps code{background:#fff;border:1px solid #e7e0d4;border-radius:6px;padding:2px 8px;
  font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12.5px;color:#002676}
.st-gps a{color:#002676;font-weight:700;text-decoration:none;border-bottom:1px solid #FDB515;white-space:nowrap}
.st-gps a:hover{background:#FDB515}
.st-gps .nogps{color:#8a8277}
.st-fact{margin:14px 0 0;font-size:13.5px;color:#5a534a;line-height:1.9;background:#fdf6e3;
  border:1px solid #f0e2b6;border-radius:10px;padding:11px 16px}
.st-fact b{color:#8a6d1a}
.st-also{margin:14px 0 0;font-size:13px;color:#8a8277;line-height:2.2}
.st-also a{color:#002676;text-decoration:none;background:#fff;border:1px solid #e2dbcf;
  border-radius:16px;padding:3px 12px;margin-right:6px;white-space:nowrap}
.st-also a:hover{border-color:#002676}
.st-also .yr{color:#8a8277;font-size:12px;margin-left:3px}
/* 同址快照（並站後的多片列） */
.st-extra{margin:14px 0 0;background:#fff;border:1px dashed #d8cfbe;border-radius:12px;padding:12px 16px}
.st-extra .lab{font-size:12.5px;font-weight:700;color:#002676}
.st-extra .ef{display:flex;gap:10px;align-items:flex-start;padding:9px 0 0;margin-top:9px;border-top:1px dashed #efe9dd}
.st-extra .ef:first-of-type{border-top:none;padding-top:6px;margin-top:6px}
.st-extra .thumb.xs{width:34px;height:51px;box-shadow:0 1px 5px rgba(0,20,70,.14)}
.st-extra .ef-t{font-size:13.5px;color:#5a534a;line-height:1.7;padding-top:2px}
.st-extra .ef-t a{color:#002676;font-weight:700;text-decoration:none;border-bottom:1px solid #FDB515}
.st-extra .ef-t a:hover{background:#FDB515;color:#002676}
.st-extra .eq{font-size:12.5px;color:#8a8277;margin-top:3px;line-height:1.7}
/* 上下線導航 */
.rp-nav{display:flex;justify-content:space-between;gap:12px;margin:44px 0 0;flex-wrap:wrap}
.rp-nav a{flex:1;min-width:200px;background:#fff;border:1px solid #e7e0d4;border-radius:12px;
  padding:14px 18px;text-decoration:none;color:#1c1a17}
.rp-nav a:hover{border-color:#002676}
.rp-nav .k{font-size:12px;color:#8a8277}
.rp-nav .t{font-family:"Noto Serif TC",serif;font-weight:900;font-size:15px;color:#002676;margin-top:3px}
.rp-nav .r{text-align:right}
.rp-foot{border-top:1px solid #e7e0d4;margin-top:44px;padding-top:18px;font-size:12.5px;color:#8a8277;line-height:1.9}
.rp-foot a{color:#002676}
/* 路線概览（2026-10-16：步行导览） */
.rp-overview{background:linear-gradient(180deg,#fbf8f1,#f4eee2);border:1px solid #e7dcc6;
  border-radius:14px;padding:18px 22px;margin:0 0 18px}
.rp-overview .ov-h{font-family:"Noto Serif TC",serif;font-weight:900;font-size:16px;color:#002676}
.rp-overview .ov-guide{font-size:14.5px;line-height:1.95;color:#3a352e;margin:8px 0 0}
.rp-overview .ov-stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.rp-overview .ov-stats div{background:#fff;border:1px solid #e7e0d4;border-radius:10px;
  padding:8px 14px;text-align:center;min-width:78px}
.rp-overview .ov-stats b{display:block;font-family:"Noto Serif TC",serif;font-weight:900;
  font-size:20px;color:#002676;line-height:1.2}
.rp-overview .ov-stats span{font-size:11.5px;color:#8a8277}
/* 跨區線警示（r9：電影主題線，非旅遊路線）2026-10-17 */
.rp-overview .ov-warn{background:#fff8e8;border:1px solid #e8c98a;border-left:4px solid #b07a1a;
  border-radius:10px;padding:12px 16px;margin:12px 0 0}
.rp-overview .ov-warn b{display:block;font-family:"Noto Serif TC",serif;font-weight:900;
  font-size:14px;color:#8a5a10;line-height:1.6}
.rp-overview .ov-warn span{display:block;font-size:13px;color:#5c5346;line-height:1.85;margin-top:4px}
/* 每站「距上一站步行」 */
.walk-from{font-size:12.5px;color:#002676;background:#eef3fb;border:1px solid #cdddf2;
  border-radius:14px;padding:3px 12px;margin:10px 0 0;display:inline-block;line-height:1.7}
.walk-from .rep{color:#b07a1a;font-weight:700}
.walk-from .cross{color:#b07a1a;font-weight:700}
"""


def _shell(title, kicker, h1, sub, body, site='', og_img='', stat=''):
    # 頂欄連結一律用絕對路徑：route/ 有 hub（深一層）與子頁（深兩層）兩種深度，
    # 相對連結必然有一邊寫錯（2026-10-15 上線當日被軒哥抓到：
    # '../macau-film/' 在 hub 解析成 /macau-film/、在子頁解析成 /route/macau-film/，全 404）。
    og = (og_img or (site + '/assets/og/seanown-home.jpg')) if site else ''
    og_tag = ('<meta property="og:image" content="%s">' % esc(og)) if og else ''
    home = (site + '/') if site else '../../'
    favicon = (site + '/assets/favicon.svg') if site else '../../assets/favicon.svg'
    album = (site + '/series/macau-film/') if site else '../../series/macau-film/'
    coll = (site + '/collection/') if site else '../collection/'
    stat_html = ('<div class="stat">%s</div>' % stat) if stat else ''
    return """<!DOCTYPE html>
<html lang="zh-Hant" class="rpage">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s｜翁振軒 Sean Own</title>
<meta name="description" content="%s">
<link rel="icon" type="image/svg+xml" href="%s">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="website">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
%s
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@700;900&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>%s</style>
</head>
<body>
<div class="rp-top"><div class="in">
<a class="brand" href="%s">翁振軒 <span>SEAN OWN</span></a>
<a class="lnk" href="%s">← 澳門電影專輯</a>
<a class="lnk" href="%s">主題合輯</a>
</div></div>
<div class="rp-hero"><div class="kick">%s</div><h1>%s</h1><div class="sub">%s</div>%s</div>
<div class="rp-wrap">%s</div>
</body>
</html>""" % (esc(title), esc(sub[:110]), esc(favicon), esc(title), esc(sub[:110]), og_tag, PAGE_CSS,
               esc(home), esc(album), esc(coll), esc(kicker), esc(h1), esc(sub), stat_html, body)


def _write(relpath, html_str):
    """relpath 可以是目錄（自動補 index.html）或完整 .html 檔案路徑，兩種都收。"""
    if relpath.replace('\\', '/').endswith('index.html'):
        fpath = os.path.join(ROOT, relpath)
        d = os.path.dirname(fpath)
    else:
        d = os.path.join(ROOT, relpath)
        fpath = os.path.join(d, 'index.html')
    os.makedirs(d, exist_ok=True)
    with io.open(fpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html_str)


def _film_link(st, site, ov):
    """站點的電影列：海報縮圖＋片名＋年份；有文章深鏈才可點。"""
    mv = (st.get('movie') or '').strip()
    yr = (st.get('year') or '').strip()
    slug = st.get('article_slug') or ''
    yr_html = ('<span class="yr">%s</span>' % esc(yr)) if yr else ''
    if slug:
        thumb = ov('../../assets/og/%s-poster.jpg' % slug)
        line = ('<a href="%s/article/%s/">《%s》</a>%s'
                % (site, slug, esc(mv), yr_html))
    else:
        thumb = ''
        line = '<span class="nolink">《%s》</span>%s' % (esc(mv), yr_html)
    img = ('<img class="thumb" src="%s" alt="%s" loading="lazy">' % (thumb, esc(mv))) if thumb else ''
    return img, line


def _station_html(st, idx, site, ov):
    """一站一張卡。idx 為路線內序（1 起）。"""
    img, film_line = _film_link(st, site, ov)
    parts = []
    parts.append('<div class="st" id="st-%d">' % idx)
    parts.append('<div class="no">%d</div><div class="st-h">%s<div class="txt">'
                 '<div class="nm">%s</div><div class="mv">%s</div></div></div>'
                 % (idx, img, esc(st.get('scene') or ''), film_line))
    # 距上一站步行（2026-10-16 步行導覽）；跨區段標「建議搭車」、全城代表點標 △、無座標斷鏈標「實地站」
    wf = st.get('walk_from_prev')
    if wf and idx > 1:
        if wf.get('cross'):
            parts.append('<div class="walk-from">距上一站約 %d 公里<span class="cross">（跨區・建議搭車）</span></div>'
                         % (wf['m'] // 1000))
        else:
            rep = ' <span class="rep">△ 含全城代表點</span>' if wf.get('rep') else ''
            if wf.get('gap'):
                parts.append('<div class="walk-from">距上一實地站步行約 <b>%d</b> 分鐘 · %d 公尺'
                             '<span class="rep">（中間含無座標站）</span>%s</div>'
                             % (wf['min'], wf['m'], rep))
            else:
                parts.append('<div class="walk-from">距上一站步行約 <b>%d</b> 分鐘 · %d 公尺%s</div>'
                             % (wf['min'], wf['m'], rep))
    # 金句框（兩行式：金句一行、署名一行）
    q = (st.get('quote') or '').strip()
    if q:
        a = (st.get('quote_author') or '').strip()
        parts.append('<div class="st-q"><div class="q">%s</div>%s</div>'
                     % (esc(q), ('<div class="a">—— %s</div>' % esc(a)) if a else ''))
    # 站位描寫
    for b in (st.get('body') or []):
        parts.append('<div class="st-b"><p>%s</p></div>' % esc(b))
    # 拍攝提示
    pn = [x.strip() for x in (st.get('photo_notes') or []) if x and x.strip()]
    if pn:
        parts.append('<div class="st-sub"><span class="lab">📷 拍攝提示</span>'
                     '<div class="st-photo">%s</div></div>'
                     % ''.join('<span>%s</span>' % esc(x) for x in pn))
    # 實用資訊
    info = st.get('info') or {}
    labels = (('📍 地址', 'address'), ('🚌 交通', 'transport'),
              ('🕐 開放', 'open_time'), ('💰 費用', 'fee'))
    cells = ''.join('<div><b>%s</b>%s</div>' % (lab, esc(info.get(k) or ''))
                    for lab, k in labels if (info.get(k) or '').strip())
    if cells:
        parts.append('<div class="st-info">%s</div>' % cells)
    # GPS／無座標如實呈現
    gps = (st.get('gps') or '').strip()
    if gps:
        parts.append('<div class="st-gps">📍 座標 <code>%s</code>'
                     '<a href="%s" target="_blank" rel="noopener">在 Google 地圖打開 →</a></div>'
                     % (esc(gps), esc(_maps_url(gps))))
    else:
        note = (st.get('match') or '').strip() or '網站未收錄此地點'
        addr = (info.get('address') or '').strip()
        parts.append('<div class="st-gps"><span class="nogps">這個場景沒有單一座標（%s）%s</span></div>'
                     % (esc(note), ('；地址參考：%s' % esc(addr)) if addr else ''))
    # 冷知識
    fact = (st.get('fact') or '').strip()
    if fact:
        parts.append('<div class="st-fact"><b>💡 冷知識</b>　%s</div>' % esc(fact))
    # 同址快照（2026-10-16 並站：同座標多片站，主站講第一部，其餘片列此）
    extras = st.get('extra_films') or []
    if extras:
        rows = []
        for f in extras:
            fslug = f.get('article_slug') or ''
            fyr = str(f.get('year') or '')
            fthumb = ('<img class="thumb xs" src="%s" alt="%s" loading="lazy">'
                      % (ov('../../assets/og/%s-poster.jpg' % fslug), esc(f.get('movie') or ''))) if fslug else ''
            ftitle = ('<a href="%s/article/%s/">《%s》</a><span class="yr">%s</span>'
                      % (site, fslug, esc(f.get('movie') or ''), esc(fyr))) if fslug \
                     else ('<span class="nolink">《%s》</span><span class="yr">%s</span>'
                           % (esc(f.get('movie') or ''), esc(fyr)))
            fq = (f.get('quote') or '').strip()
            fql = ('<div class="eq">「%s」%s</div>' % (esc(fq), ('—— %s' % esc(f.get('quote_author')))
                  if (f.get('quote_author') or '').strip() else '')) if fq else ''
            rows.append('<div class="ef">%s<div class="ef-t">%s%s</div></div>' % (fthumb, ftitle, fql))
        parts.append('<div class="st-extra"><div class="lab">🎬 同址快照・這個地點還有這些電影</div>%s</div>'
                     % ''.join(rows))
    # 同地其他電影
    also = st.get('also') or []
    if also:
        chips = ''.join('<a href="%s/article/%s/">《%s》<span class="yr">%s</span></a>'
                        % (site, f['slug'], esc(f.get('name') or ''), esc(str(f.get('year') or '')))
                        for f in also[:8])
        more = ('<span style="color:#8a8277">等 %d 部</span>' % len(also)) if len(also) > 8 else ''
        parts.append('<div class="st-also">🎬 同地還有這些電影來過：%s%s</div>' % (chips, more))
    parts.append('</div>')
    return ''.join(parts)


# ── 每條線的「宣歌」導覽句（2026-10-16 軒哥拍板：頂部用導覽口吻講這條線）──
# 風格對齊旅遊書《跟著電影遊澳門》的敘事語氣；步行總距／總時間由 routes.json 動態接在句尾。
ROUTE_GUIDE = {
    # ── 2026-10-17 拆分（整條線步行 ≤90min）：原 r1/r2/r3 拆成七條，各配一段導覽文案 ──
    'r1a-central-lower': '福隆新街的燈籠、新馬路的舊夢、戀愛巷的擦肩而過，一路走到大三巴——把王家衛的宿命街區走成一條黃昏路線。',
    'r1b-mong-hau': '崗頂劇院、龍嵩正街，這一段遊人不多，節奏很慢，適合想避開人潮單純走一圈的人。',
    'r2a-inner-harbour': '亞婆井、下環街、光復圍——澳門最市井的老城。港片拍過深夜與失落，游客走過卻常常只是匆匆一瞥。',
    'r2b-sendomou': '司打口是苦力登岸的舊碼頭，往上走經聖若瑟修院、舊廣州大酒店、蠔里、白鴿巢公園，最真實的街區紋理。',
    'r3a-outer-harbour': '漁人碼頭、澳門科學館、澳門美高梅——外港海濱這一片，步行十幾分鐘就串成一線，走完剛好一個下午。',
    'r3b-sao-lazaro': '望德堂的葡式斜巷，轉個彎就是葡京與新葡京的霓虹——古老與浮華在這裡只隔幾分鐘。',
    'r3c-maca-tao': '媽閣的香火、西望洋的斜坡、澳門塔的海景，這一線最有呼吸感；走到半山回頭，整個海就在腳下。',
    'r4-cotai': '跨過橋來到路氹金光大道，入夜後霓虹全開，是這座城最「亮」的一塊賭城舞台。',
    'r5-taipa': '氹仔舊城還留著生活氣——官也街的餅家、嘉模斜巷的舊宅、龍環葡韻的荷花，電影拍的是日子。',
    'r6-coloane': '路環是澳門的盡頭，沒有賭場，有海、有聖方濟各聖堂、有安德魯餅店——電影走到這裡都慢下來。',
    'r7-local-eyes': '這一線收澳門人自己拍的澳門：本地短片、獨立製作、紀錄片，鏡頭裡的家。',
    'r9-world-eyes': '從《奪寶奇兵》到 007，好萊塢與亞洲名導透過澳門想像東方，這一線看被選中的角度。',
}


def build_routes(site, ov, data_path=None):
    """產生 route/ 全部頁面，回傳 [(url, lastmod)] 供 sitemap。"""
    data_path = data_path or os.path.join(ROOT, 'data', 'routes.json')
    if not os.path.exists(data_path):
        print('  [WARN] data/routes.json 不存在，跳過路線頁（先跑 tools/_export_routes.py）')
        return []
    data = json.load(io.open(data_path, encoding='utf-8'))
    routes = data.get('routes') or []
    if not routes:
        return []
    sitemap = []
    today = date.today().isoformat()
    hub = site + '/route/'
    coll_hub = site + '/collection/'
    album_url = site + '/series/macau-film/'

    # ── Hub 總覽 ──
    cards = ''
    for r in routes:
        n = len(r['stations'])
        g = sum(1 for s in r['stations'] if s.get('gps'))
        a = sum(1 for s in r['stations'] if s.get('article_slug'))
        cards += ('<a class="rp-card" href="%s">'
                  '<div class="no">%s</div>'
                  '<div class="t">%s</div>'
                  '<div class="tag">%s</div>'
                  '<p class="c">%s</p>'
                  '<div class="n">%d 站 · %d 個實地座標 · %d 篇觀後感深鏈 <b>→</b></div></a>'
                  % (esc(hub + r['slug'] + '/'), esc(r['key']), esc(r['region']),
                     esc(r['tag']), esc(r['desc']), n, g, a))
    n_st = sum(len(r['stations']) for r in routes)
    n_gps = sum(1 for r in routes for s in r['stations'] if s.get('gps'))
    n_art = sum(1 for r in routes for s in r['stations'] if s.get('article_slug'))
    # 路線數動態（2026-10-17 拆線後 8→12；再增減也不會與統計數字不一致）
    n_route = len(routes)
    n_walk = sum(1 for r in routes if not r.get('walk_cross'))
    hub_body = (
        '<div class="rp-sec"><h2>🚶 %d 條路線，把 83 篇觀後感走成一條線</h2>'
        '<p class="d">澳門電影專輯的 83 篇觀後感裡，藏著 %d 個可實地重訪的場景。'
        '我們把它編成 %d 條路線：每一站都有電影、座標、現場站位描寫與拍攝提示，'
        '並深鏈回對應的觀後感——從「看一篇」變成「走一條線」。'
        '其中 %d 條是可以真正走完的步行路線，每條步行總量控制在 90 分鐘以內；'
        '沒有的座標場景（全城型／網站未收錄）如實標注，不造假。</p>'
        '<div class="rp-grid">%s</div></div>'
        '<div class="rp-sec"><h2>🧭 兩種逛法，自由切換</h2>'
        '<p class="d">想按電影查，去主題合輯；想按路線走，留在這裡。</p>'
        '<div class="rp-x">'
        '<a href="%s"><div class="t">🗺 澳門電影地圖</div><div class="c">按取景地聚合——同一個地標，反覆出現在哪些電影裡。</div></a>'
        '<a href="%s"><div class="t">🕰 時光機</div><div class="c">按年代逛——三個時代、十個十年代的澳門銀幕。</div></a>'
        '<a href="%s"><div class="t">🎬 澳門電影專輯</div><div class="c">83 篇觀後感全文，路線每一站都深鏈回這裡。</div></a>'
        '</div></div>'
        '<div class="rp-sec"><h2>📖 關於這批路線</h2>'
        '<p class="d">路線與場景內容取自《跟著電影遊澳門》（63 場景）；'
        '座標、機位提示與文章深鏈，由本站澳門電影專輯的觀後感逐站比對生成。'
        '部分場景網站未收錄對應座標，頁面如實標注原因並給地址參考。'
        '地圖僅提供座標與 Google 地圖連結，步行顺序以現場為準。</p></div>'
    ) % (n_route, n_gps, n_route, n_walk, cards, coll_hub, coll_hub, album_url)
    _write('route/index.html',
           _shell('跟著電影遊澳門 · 主題路線', '跟著電影遊澳門 · FOLLOW THE FILMS',
                  '%d 條路線，走一遍澳門的銀幕' % n_route,
                  '把 83 篇電影觀後感編成 %d 條可實地走的路線：每站有電影、座標、站位描寫與拍攝提示。' % n_route,
                  hub_body, site, stat='<span>%d 條路線</span><span>%d 站</span><span>%d 個座標</span><span>%d 篇深鏈</span>'
                  % (n_route, n_st, n_gps, n_art)))
    sitemap.append((hub, today))

    # ── 每條路線頁 ──
    for i, r in enumerate(routes):
        sts = r['stations']
        n = len(sts)
        g = sum(1 for s in sts if s.get('gps'))
        a = sum(1 for s in sts if s.get('article_slug'))
        # ── 路線概览卡（2026-10-16：步行導覽）──
        tot_km = r.get('total_walk_km') or 0
        tot_min = r.get('total_walk_min') or 0
        rep = r.get('walk_rep')
        cross = r.get('walk_cross')
        guide = ROUTE_GUIDE.get(r['slug'], '')
        note = '（含全城型代表點估算）' if rep else ('（含跨區段・另計）' if cross else '')
        # ── 跨區線警示（2026-10-17 軒哥拍板：r9 不做真正的旅遊路線）──
        # r9「世界眼中的澳門」本質是電影主題線（與書裡「建議去哪」同一層的資訊層），
        # 按外國片取景地串站，半島／路氹／路環跳跨數公里，無法步行走完。
        # 明確標示避免讀者誤當成可步行的旅遊路線。
        cross_banner = ''
        if cross:
            cross_banner = (
                '<div class="ov-warn">'
                '<b>📍 本線是跨區看景清單，不是步行旅遊路線</b>'
                '<span>這一線按外國電影的取景地串起來的，點與點之間跨著半島、路氹、路環，'
                '動輒數公里，需要搭公交、巴士或的士前往，無法全程步行走完。'
                '它比較像一份「看過這些片、可以順路去的地點」清單；'
                '要真正能走完的旅行路線，請看同頁其他分區線。'
                '下方各站標的「步行分鐘」只計算區內那一段。</span>'
                '</div>'
            )
        # 跨區線：標題與統計改為跨區語意，不寫「步行」，避免讀者誤以為能走完
        ov_title = '📍 這條線怎麼看' if cross else '🚶 這條線怎麼走'
        lbl_km = '公里（區內步行）' if cross else '公里（步行）'
        lbl_min = '分鐘（區內步行）' if cross else '分鐘（步行）'
        overview = (
            '<div class="rp-overview">'
            '<div class="ov-h">%s</div>' % ov_title
            + cross_banner +
            '<p class="ov-guide">%s 全程約 %.1f 公里，慢走約 %d 分鐘%s。</p>'
            '<div class="ov-stats">'
            '<div><b>%d</b><span>站</span></div>'
            '<div><b>%.1f</b><span>%s</span></div>'
            '<div><b>%d</b><span>%s</span></div>'
            '<div><b>%d</b><span>篇深鏈</span></div>'
            '</div></div>'
        ) % (esc(guide), tot_km, tot_min, note, n, tot_km, lbl_km, tot_min, lbl_min, a)
        jump = ''.join('<a href="#st-%d"><b>%02d</b>%s<span class="m">%s</span></a>'
                       % (j + 1, j + 1, esc(s.get('scene') or ''), esc(s.get('movie') or ''))
                       for j, s in enumerate(sts))
        stations_html = ''.join(_station_html(s, j + 1, site, ov) for j, s in enumerate(sts))
        prev_r = routes[i - 1] if i > 0 else None
        next_r = routes[i + 1] if i < len(routes) - 1 else None
        nav = ''
        if prev_r:
            nav += ('<a href="%s"><div class="k">← 上一條</div><div class="t">%s・%s</div></a>'
                    % (esc(hub + prev_r['slug'] + '/'), esc(prev_r['key']), esc(prev_r['region'])))
        else:
            nav += ('<a href="%s"><div class="k">← 返回</div><div class="t">全部路線</div></a>'
                    % esc(hub))
        if next_r:
            nav += ('<a class="r" href="%s"><div class="k">下一條 →</div><div class="t">%s・%s</div></a>'
                    % (esc(hub + next_r['slug'] + '/'), esc(next_r['key']), esc(next_r['region'])))
        body = (
            '%s'
            '<div class="rp-jump">%s</div>'
            '%s'
            '<div class="rp-nav">%s</div>'
            '<div class="rp-foot">路線內容取自《跟著電影遊澳門》；座標與深鏈由澳門電影專輯比對生成，'
            '未收錄座標的站如實標注。　<a href="%s">← 全部路線</a>｜'
            '<a href="%s">澳門電影地圖</a>｜<a href="%s">澳門電影專輯</a></div>'
        ) % (overview, jump, stations_html, nav, esc(hub), esc(coll_hub), esc(album_url))
        _write('route/%s/index.html' % r['slug'],
               _shell('跟著電影遊澳門・%s' % r['key'], 'ROUTE · 跟著電影遊澳門',
                      r['key'], r['desc'], body, site,
                      stat='<span>%s</span><span>%d 站</span><span>%d 個座標</span><span>%d 篇深鏈</span>'
                      % (esc(r['tag']), n, g, a)))
        sitemap.append(('%s/route/%s/' % (site, r['slug']), today))

    return sitemap

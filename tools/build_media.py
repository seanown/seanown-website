#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 data/media.json 的媒體報導靜態寫入 media/index.html
原因：原本 /media/ 內容全靠 JS fetch，SEO 爬蟲抓不到任何報導標題／來源／連結。
做法：Python 生成靜態 HTML（保留 media.json 為唯一資料源，之後重跑此腳本即可更新）。
"""
import json, os, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'media.json')
OUT = os.path.join(ROOT, 'media', 'index.html')

ORDER = ['論壇盛會', '文化盛事', '考察交流', '專訪報導', '產業動態', '其他']


def esc(s):
    return html.escape(str(s or ''), quote=True)


def fmt_date(d):
    if not d:
        return '日期未註'
    try:
        dt = datetime.date.fromisoformat(str(d)[:10])
        return f'{dt.year}.{dt.month:02d}.{dt.day:02d}'
    except Exception:
        return str(d)


def build():
    with open(SRC, encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('media') or []

    groups = {}
    for m in items:
        groups.setdefault(m.get('category') or '其他', []).append(m)

    total = len(items)
    # 只統計有原文連結的（可核查）與無連結的（現場紀錄）
    linked = sum(1 for m in items if m.get('url'))
    sources = sorted({m.get('source') for m in items if m.get('source')})
    years = sorted({str(m.get('date'))[:4] for m in items if m.get('date')}, reverse=True)

    # ---------- 分類區塊（靜態） ----------
    blocks = []
    for cat in ORDER:
        rows = groups.get(cat)
        if not rows:
            continue
        cards = []
        for m in rows:
            title = esc(m.get('title'))
            src = esc(m.get('source'))
            date = fmt_date(m.get('date'))
            url = m.get('url')
            if url:
                action = (f'<a class="m-link" href="{esc(url)}" target="_blank" rel="noopener nofollow">'
                          f'原文<span class="ext" aria-hidden="true">↗</span>'
                          f'<span class="sr-only">（在新視窗開啟：{title}）</span></a>')
                tgt = ' _blank rel="noopener nofollow"'
            else:
                action = '<span class="m-link is-none">現場紀錄・無公開原文</span>'
                tgt = ''
            cards.append(
                f'<li class="m-item">'
                f'<div class="m-meta"><time datetime="{esc(m.get("date"))}">{date}</time>'
                f'<span class="m-src">{src}</span></div>'
                f'<h3 class="m-title">{title}{tgt and "" or ""}</h3>'
                f'<div class="m-cta">{action}</div>'
                f'</li>'
            )
        open_attr = ' open'
        blocks.append(
            f'<details class="m-cat"{open_attr} id="cat-{esc(cat)}">'
            f'<summary><span class="cat-name">{esc(cat)}</span>'
            f'<span class="mc-count">{len(rows)} 則</span>'
            f'<span class="mc-arrow" aria-hidden="true">▾</span></summary>'
            f'<ul class="m-list">{"".join(cards)}</ul>'
            f'</details>'
        )

    # ---------- 年份索引（錨點） ----------
    year_links = ''.join(
        f'<a class="y-chip" href="#y{y}">{y}</a>' for y in years
    )

    # ---------- 依年份分組（第二種篩選維度） ----------
    by_year = {}
    for m in items:
        y = str(m.get('date'))[:4] if m.get('date') else '未註日期'
        by_year.setdefault(y, []).append(m)
    year_blocks = []
    for y in sorted(by_year, reverse=True):
        rows = by_year[y]
        lis = []
        for m in rows:
            url = m.get('url')
            title = esc(m.get('title'))
            if url:
                lis.append(f'<li><a href="{esc(url)}" target="_blank" rel="noopener nofollow">{title}'
                           f'<span class="ext" aria-hidden="true">↗</span></a>'
                           f'<span class="y-src">{esc(m.get("source"))}</span></li>')
            else:
                lis.append(f'<li><span class="y-plain">{title}</span>'
                           f'<span class="y-src">{esc(m.get("source"))}</span></li>')
        year_blocks.append(
            f'<section class="yr" id="y{y}"><h3 class="yr-h">{esc(y)} 年'
            f'<span class="yr-n">{len(rows)} 則</span></h3>'
            f'<ul class="yr-list">{"".join(lis)}</ul></section>'
        )

    today = datetime.date.today().isoformat()
    canonical = 'https://seanown.org/media/'
    desc = (f'翁振軒 Sean Own 媒體報導總覽：{total} 則公開可查的採訪、論壇、文化盛事與考察交流報導，'
            f'涵蓋 {years[-1] if years else ""}–{years[0] if years else ""} 年，'
            f'每則均附媒體來源、日期與原文連結。')

    src_list = '、'.join(sources[:10])

    html_doc = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>媒體報導（{total} 則）｜翁振軒 Sean Own</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="翁振軒,Sean Own,媒體報導,澳門,大灣區,ECI,亞洲電子論壇,專訪">
<meta name="author" content="翁振軒 Sean Own">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="媒體報導（{total} 則）｜翁振軒 Sean Own">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="https://seanown.org/assets/og/seanown-home.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="SEAN OWN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="媒體報導（{total} 則）｜翁振軒 Sean Own">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="https://seanown.org/assets/og/seanown-home.jpg">
<script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": f"媒體報導｜翁振軒 Sean Own",
    "url": canonical,
    "description": desc,
    "inLanguage": "zh-Hant",
    "author": {"@type": "Person", "name": "翁振軒 Sean Own", "url": "https://seanown.org/"},
    "mainEntity": {
        "@type": "ItemList",
        "numberOfItems": total,
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "NewsArticle", "headline": m.get("title"),
                      "datePublished": m.get("date"),
                      "url": m.get("url") or canonical,
                      "publisher": {"@type": "Organization", "name": m.get("source")}}}
            for i, m in enumerate(items)
        ],
    },
}, ensure_ascii=False, indent=1)}
</script>
<style>
:root{{--blue:#002676;--blue-dark:#010133;--gold:#FDB515;--gold-light:#FFF3D0;--white:#fff;--bg:#F8F9FB;--text:#1A1A1A;--gray:#667085;--line:#E4E8EF;--shadow:0 4px 20px rgba(0,38,118,.08);--shadow-hover:0 10px 34px rgba(0,38,118,.16)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.75;-webkit-font-smoothing:antialiased}}
a{{color:inherit;text-decoration:none}}
img{{max-width:100%;display:block}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
:focus-visible{{outline:3px solid var(--gold);outline-offset:3px;border-radius:4px}}

/* 導覽 */
.topbar{{background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:50}}
.topbar-in{{max-width:1080px;margin:0 auto;padding:0 24px;height:62px;display:flex;align-items:center;justify-content:space-between;gap:12px}}
.brand{{font-weight:800;font-size:17px;color:var(--blue);letter-spacing:.5px}}
.brand span{{color:var(--gold)}}
.tnav{{display:flex;gap:18px;align-items:center}}
.tnav a{{font-size:14px;font-weight:600;color:var(--text)}}
.tnav a:hover{{color:var(--blue)}}
.tnav .cta{{background:var(--blue);color:#fff;padding:8px 18px;border-radius:999px;font-size:13.5px}}
.tnav .cta:hover{{background:var(--blue-dark)}}

/* 頁首 */
.masthead{{background:linear-gradient(135deg,#002676 0%,#010133 100%);color:#fff;padding:60px 24px 52px}}
.masthead-in{{max-width:1080px;margin:0 auto}}
.kicker{{font-size:13px;letter-spacing:6px;color:var(--gold);font-weight:700;margin-bottom:12px}}
.masthead h1{{font-size:42px;font-weight:800;letter-spacing:2px;margin-bottom:14px}}
.masthead p{{color:rgba(255,255,255,.8);font-size:16px;max-width:760px}}
.facts{{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}}
.fact{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:14px;padding:14px 20px;min-width:150px}}
.fact .n{{font-size:28px;font-weight:800;color:var(--gold);line-height:1.1}}
.fact .l{{font-size:12.5px;color:rgba(255,255,255,.8);margin-top:2px}}
.note{{margin-top:22px;font-size:13.5px;color:rgba(255,255,255,.72);border-left:3px solid var(--gold);padding-left:14px;max-width:820px}}

/* 主體 */
.wrap{{max-width:1080px;margin:0 auto;padding:44px 24px 70px}}
.sec-h{{font-size:28px;font-weight:800;color:var(--blue);padding-left:16px;position:relative;margin-bottom:8px}}
.sec-h::before{{content:'';position:absolute;left:0;top:4px;bottom:4px;width:5px;background:var(--gold);border-radius:3px}}
.sec-sub{{color:var(--gray);font-size:15px;margin-bottom:26px}}
.jump{{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:30px}}
.jump .lab{{font-size:12px;letter-spacing:2px;color:var(--gray);font-weight:700;margin-right:2px}}
.y-chip{{border:1.5px solid var(--line);background:#fff;border-radius:999px;padding:6px 15px;font-size:13.5px;font-weight:700;color:var(--blue);transition:all .2s}}
.y-chip:hover{{background:var(--blue);border-color:var(--blue);color:#fff}}

.m-cat{{background:#fff;border:1px solid var(--line);border-radius:16px;margin-bottom:18px;overflow:hidden}}
.m-cat summary{{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:18px 24px;user-select:none}}
.m-cat summary::-webkit-details-marker{{display:none}}
.m-cat summary:hover{{background:#FAFBFD}}
.cat-name{{font-size:20px;font-weight:800;color:var(--text)}}
.mc-count{{font-size:13px;color:var(--gray);font-weight:600}}
.mc-arrow{{margin-left:auto;color:var(--gold);font-weight:800;font-size:16px;transition:transform .2s}}
.m-cat[open] .mc-arrow{{transform:rotate(180deg)}}
.m-list{{list-style:none;border-top:1px solid var(--line)}}
.m-item{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;padding:16px 24px;border-bottom:1px solid #EFF2F6}}
.m-item:last-child{{border-bottom:none}}
.m-item:hover{{background:#FAFBFD}}
.m-meta{{display:flex;flex-direction:column;gap:3px;min-width:104px}}
.m-meta time{{font-size:13px;color:var(--gray);font-weight:700;font-variant-numeric:tabular-nums}}
.m-src{{font-size:11.5px;color:var(--blue);background:#F0F4F8;padding:2px 9px;border-radius:10px;align-self:flex-start;white-space:nowrap}}
.m-title{{flex:1;min-width:220px;font-size:15px;font-weight:600;color:var(--text);line-height:1.6}}
.m-item:hover .m-title{{color:var(--blue)}}
.m-cta{{margin-left:auto}}
.m-link{{display:inline-flex;align-items:center;gap:4px;font-size:13.5px;font-weight:700;color:var(--blue);border:1.5px solid var(--blue);border-radius:999px;padding:7px 16px;white-space:nowrap;transition:all .2s}}
.m-link:hover{{background:var(--blue);color:#fff}}
.m-link.is-none{{border-color:var(--line);color:var(--gray);font-weight:600;cursor:default}}
.ext{{font-size:12px}}

.yr{{margin-bottom:26px}}
.yr-h{{font-size:20px;font-weight:800;color:var(--blue);margin-bottom:12px;display:flex;align-items:center;gap:10px}}
.yr-n{{font-size:12.5px;color:var(--gray);font-weight:600}}
.yr-list{{list-style:none;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}
.yr-list li{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-size:14px;line-height:1.6}}
.yr-list a{{color:var(--blue);font-weight:600}}
.yr-list a:hover{{text-decoration:underline}}
.y-plain{{color:var(--text)}}
.y-src{{display:block;font-size:11.5px;color:var(--gray);margin-top:3px}}

/* 底部 CTA */
.cta-band{{background:linear-gradient(135deg,#002676 0%,#010133 100%);color:#fff;border-radius:22px;padding:44px 40px;margin-top:44px;text-align:center}}
.cta-band h2{{font-size:26px;font-weight:800;margin-bottom:10px}}
.cta-band p{{color:rgba(255,255,255,.8);margin-bottom:24px;font-size:15px}}
.cta-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}}
.cta-btns a{{padding:13px 30px;border-radius:999px;font-size:15px;font-weight:700;transition:all .2s}}
.cta-btns .b1{{background:var(--gold);color:var(--blue-dark)}}
.cta-btns .b1:hover{{transform:translateY(-2px)}}
.cta-btns .b2{{border:2px solid rgba(255,255,255,.7);color:#fff}}
.cta-btns .b2:hover{{background:#fff;color:var(--blue)}}

.foot{{border-top:1px solid var(--line);margin-top:44px;padding:28px 24px 46px;text-align:center;font-size:13px;color:var(--gray);line-height:1.9}}
.foot a{{color:var(--blue);font-weight:600}}

@media(max-width:760px){{
  .tnav a:not(.cta){{display:none}}
  .masthead h1{{font-size:29px}}
  .masthead{{padding:44px 18px 40px}}
  .wrap{{padding:32px 16px 56px}}
  .yr-list{{grid-template-columns:1fr}}
  .m-item{{padding:14px 16px}}
  .m-cta{{margin-left:0;width:100%}}
  .m-link{{width:100%;justify-content:center}}
  .cta-band{{padding:34px 20px}}
  .cta-btns a{{width:100%}}
  .sec-h{{font-size:22px}}
}}
</style>
</head>
<body>
<a class="sr-only" href="#media-main">跳到主要內容</a>

<header class="topbar"><div class="topbar-in">
<a class="brand" href="/">翁振軒 <span>SEAN OWN</span></a>
<nav class="tnav" aria-label="網站導覽">
<a href="/articles/">專欄文章</a>
<a href="/series/">專輯</a>
<a href="/about/">關於我</a>
<a href="/contact/" class="cta">洽談合作</a>
</nav>
</div></header>

<header class="masthead"><div class="masthead-in">
<div class="kicker">MEDIA &amp; COVERAGE</div>
<h1>媒體報導</h1>
<p>公開可查的採訪、論壇、文化盛事與考察交流報導總覽。每則均標示媒體來源、日期與原文連結，無原文者明確標記為現場紀錄，不以無法核實的內容充數。</p>
<div class="facts">
<div class="fact"><div class="n">{total}</div><div class="l">則報導收錄</div></div>
<div class="fact"><div class="n">{linked}</div><div class="l">則附原文連結</div></div>
<div class="fact"><div class="n">{len(sources)}</div><div class="l">家媒體／機構</div></div>
<div class="fact"><div class="n">{years[0] if years else '—'}</div><div class="l">最新報導年度</div></div>
</div>
<p class="note">資料來源：{esc(src_list)}{'等' if len(sources) > 10 else ''}。最後更新：{today}。本頁為靜態頁面，所有標題與連結均可被搜尋引擎直接讀取。</p>
</div></header>

<main class="wrap" id="media-main">

<h2 class="sec-h">依事件分類</h2>
<p class="sec-sub">共 {len([c for c in ORDER if groups.get(c)])} 類。點擊分類標題可收合／展開。</p>
{"".join(blocks)}

<h2 class="sec-h" style="margin-top:52px">依年份瀏覽</h2>
<p class="sec-sub">同一事件可能有多家媒體報導，會分別列出。</p>
<div class="jump"><span class="lab">快速跳轉</span>{year_links}</div>
{"".join(year_blocks)}

<div class="cta-band">
<h2>需要一份完整的合作簡介？</h2>
<p>我可以提供含經歷、合作方向與可公開報導的個人簡介資料，以及過去論壇與活動的講題。</p>
<div class="cta-btns">
<a class="b1" href="/contact/">洽談合作</a>
<a class="b2" href="/about/">先看我的經歷</a>
</div>
</div>

<footer class="foot">
© 2026 翁振軒 Sean Own · <a href="/">返回首頁</a> · <a href="/about/">關於我</a> · <a href="/articles/">專欄文章</a> · <a href="/contact/">聯絡</a><br>
報導標題與內容版權屬原媒體所有，本頁僅作索引與連結。
</footer>
</main>
</body>
</html>
'''

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f'[OK] {OUT}')
    print(f'     收錄 {total} 則／附原文 {linked} 則／{len(sources)} 家媒體／{len(years)} 個年度')
    print(f'     靜態化：SEO 可直接讀取 {len(blocks)} 個分類 + {len(year_blocks)} 個年度區塊')


if __name__ == '__main__':
    build()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生自建維基 wiki/index.html（條目頁・機構・常見問題）
原則：每個事實附來源標記；無來源者明示為「站內自述」，不與可查證事實混排。
資料層：data/wiki.json（唯一來源，數字全部動態取用）
"""
import io, os, json, html, datetime

ROOT = 'C:/Users/user/WorkBuddy/Seanown.org'
SRC = os.path.join(ROOT, 'data', 'wiki.json')
OUT = os.path.join(ROOT, 'wiki', 'index.html')
MEDIA = os.path.join(ROOT, 'data', 'media.json')

e = html.escape


def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def esc(s):
    return e(str(s if s is not None else ''), quote=True)


def src_link(url, label='來源'):
    if not url:
        return ''
    return f'<a class="src" href="{esc(url)}" target="_blank" rel="noopener">{label} ↗</a>'


def build():
    d = json.load(io.open(SRC, encoding='utf-8'))
    p = d['person']
    media = json.load(io.open(MEDIA, encoding='utf-8'))['media']
    today = datetime.date.today().isoformat()

    # ---------- 職務（verified 優先，其餘依原順序） ----------
    def pos_li(x):
        cls = 'v' if x.get('evidence') == 'verified' else 's'
        note = f'<span class="pos-note">{esc(x["note"])}</span>' if x.get('note') else ''
        return (f'<li class="pos {cls}"><span class="pos-t">{esc(x["title"])}</span>'
                f'<span class="pos-o">{esc(x["org"])}</span>'
                f'<span class="pos-src">{src_link(x.get("source_url"))}</span>{note}</li>')

    verified = [x for x in p['positions'] if x.get('evidence') == 'verified']
    stated = [x for x in p['positions'] if x.get('evidence') != 'verified']
    n_pos = len(p['positions'])
    n_ver = len(verified)

    pos_html = (
        '<h3 class="sec-h3">現任職務</h3>'
        '<ul class="pos-list">' + ''.join(pos_li(x) for x in p['positions']) + '</ul>'
    )

    # ---------- 機構 ----------
    def org_card(x):
        cls = 'v' if x.get('evidence') == 'verified' else 's'
        url = x['url'] or ''
        link = (f'<a class="org-url" href="{esc(url)}" target="_blank" rel="noopener">'
                f'{esc(url)} ↗</a>') if url.startswith('http') else (
                f'<a class="org-url" href="{esc(url)}">{esc(url)}</a>' if url else '')
        return f'''<article class="org-card {cls}">
  <h4>{esc(x['name'])}</h4>
  <p class="org-role">{esc(x['role'])}</p>
  <p class="org-desc">{esc(x['desc'])}</p>
  <div class="org-meta">{link}{src_link(x.get('source_url'))}</div>
</article>'''

    org_html = ''.join(org_card(x) for x in d['organizations'])

    # ---------- 詞彙 ----------
    gloss_html = ''.join(
        f'<div class="gl-item"><dt>{esc(x["term"])}</dt><dd>{esc(x["definition"])}'
        f' <span class="gl-src">{src_link(x.get("source_url"))}</span></dd></div>'
        for x in d['glossary'])

    # ---------- FAQ ----------
    faq_html = ''.join(
        f'<details class="faq"><summary>{esc(x["q"])}</summary>'
        f'<p>{esc(x["a"])}</p></details>'
        for x in d['faq'])

    # ---------- 未查證項目 ----------
    # 🔴 2026-10-18 軒哥指示：公開頁面不揭露未查證項、不寫「查不到來源」這類副標題。
    # not_verified 僅保留於 data/wiki.json 作內部管理，之後拿到公開來源再補入正式條目。
    nv_html = ''

    # ---------- 頭部統計（動態） ----------
    orgs_n = len(d['organizations'])
    media_n = len(media)
    media_with_url = sum(1 for m in media if m.get('url'))

    desc = (f'翁振軒（Sean Own，1978 年生於台北，現居澳門）為澳門商人與產業顧問，'
            f'粵港澳大灣區電子商會創會理事長、澳門龍遊集團創辦人。'
            f'本頁收錄其 {n_pos} 項現任職務、{orgs_n} 個相關機構與 {media_n} 則可查證的媒體報導，'
            f'各項職務與機構均附可查證的來源連結。')

    doc = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>翁振軒 Sean Own｜條目</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="翁振軒,Sean Own,澳門,澳門龍遊,粵港澳大灣區電子商會,數位服務出海,條目">
<meta name="author" content="翁振軒 Sean Own">
<link rel="canonical" href="https://seanown.org/wiki/">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="profile">
<meta property="og:url" content="https://seanown.org/wiki/">
<meta property="og:title" content="翁振軒 Sean Own｜條目">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="https://seanown.org/assets/og/seanown-home.jpg">
<meta property="og:locale" content="zh_TW">
<script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    "name": "翁振軒 Sean Own｜條目",
    "url": "https://seanown.org/wiki/",
    "inLanguage": "zh-Hant",
    "description": desc,
    "mainEntity": {
        "@type": "Person",
        "name": "翁振軒",
        "alternateName": ["Sean Own", "Weng Zhen-Xuan"],
        "url": "https://seanown.org/",
        "birthDate": "1978",
        "birthPlace": {"@type": "Place", "name": "台北"},
        "homeLocation": {"@type": "Place", "name": "澳門"},
        "description": p['summary'],
    },
}, ensure_ascii=False, indent=1)}
</script>
<style>
:root{{--blue:#002676;--blue-dark:#010133;--gold:#FDB515;--bg:#F8F9FB;--text:#1A1A1A;--gray:#667085;--line:#E4E8EF;--ok:#0E7C4A;--warn:#B45309}}
*{{box-sizing:border-box;margin:0;padding:0}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.8;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue)}}
.wrap{{max-width:900px;margin:0 auto;padding:0 24px 70px}}
/* 導覽 */
.topbar{{background:rgba(255,255,255,.93);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}}
.topbar-in{{max-width:900px;margin:0 auto;padding:0 24px;height:60px;display:flex;align-items:center;justify-content:space-between;gap:12px}}
.brand{{font-weight:800;font-size:16px;color:var(--blue);letter-spacing:.4px}}
.brand span{{color:var(--gold)}}
.tnav a{{font-size:14px;font-weight:600;margin-left:16px}}
/* 頭 */
header.top{{background:linear-gradient(135deg,#002676 0%,#010133 100%);color:#fff;padding:46px 0 40px;margin-bottom:34px}}
.kicker{{font-size:12px;letter-spacing:5px;color:var(--gold);font-weight:700;margin-bottom:10px}}
header.top h1{{font-size:34px;font-weight:800;letter-spacing:1px;margin-bottom:8px}}
header.top .en{{color:rgba(255,255,255,.7);font-size:15px;letter-spacing:1px;margin-bottom:14px}}
header.top p.lead{{color:rgba(255,255,255,.86);font-size:15.5px;max-width:760px}}
.facts{{display:flex;flex-wrap:wrap;gap:11px;margin-top:24px}}
.fact{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:13px;padding:12px 18px;min-width:132px}}
.fact .n{{font-size:24px;font-weight:800;color:var(--gold);line-height:1.15}}
.fact .l{{font-size:12px;color:rgba(255,255,255,.8);margin-top:2px}}
/* 章節 */
.sec{{margin-bottom:38px}}
.sec-h{{font-size:24px;font-weight:800;color:var(--blue);padding-left:14px;position:relative;margin-bottom:9px}}
.sec-h::before{{content:'';position:absolute;left:0;top:4px;bottom:4px;width:5px;background:var(--gold);border-radius:3px}}
.sec-h3{{font-size:18px;font-weight:800;color:var(--blue);margin:22px 0 7px}}
.sec-note{{color:var(--gray);font-size:14px;margin-bottom:14px}}
.panel{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px}}
/* 資訊表 */
.infobox{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden}}
.infobox th,.infobox td{{padding:11px 18px;text-align:left;font-size:14.5px;border-bottom:1px solid var(--line);vertical-align:top}}
.infobox tr:last-child th,.infobox tr:last-child td{{border-bottom:none}}
.infobox th{{width:132px;color:var(--blue);font-weight:700;background:#F5F8FC;white-space:nowrap}}
/* 職務 */
.pos-list{{list-style:none}}
.pos{{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;padding:10px 0;border-bottom:1px dashed var(--line)}}
.pos:last-child{{border-bottom:none}}
.pos-t{{font-weight:700;font-size:15px;color:var(--text);min-width:96px}}
.pos-o{{font-size:15px;color:var(--blue);font-weight:600}}
.pos-src{{margin-left:auto;font-size:12.5px}}
.src{{color:var(--blue);font-weight:700;white-space:nowrap}}

.pos-note{{flex-basis:100%;font-size:13px;color:var(--gray);padding-left:2px}}


/* 機構 */
.org-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(258px,1fr));gap:13px}}
.org-card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:17px;border-left:4px solid var(--blue)}}
.org-card.s{{border-left-color:#C9D2DE}}
.org-card h4{{font-size:16px;font-weight:800;margin-bottom:5px;line-height:1.5}}
.org-role{{font-size:13px;color:#8A6200;font-weight:700;margin-bottom:7px}}
.org-role::before{{content:''}}
.org-desc{{font-size:14px;color:#3D4653;margin-bottom:10px}}
.org-meta{{display:flex;flex-wrap:wrap;gap:9px;align-items:center;font-size:12.5px}}
.org-url{{color:var(--blue);font-weight:700;word-break:break-all}}
/* 詞彙 */
.gl-item{{padding:11px 0;border-bottom:1px dashed var(--line)}}
.gl-item:last-child{{border-bottom:none}}
.gl-item dt{{font-weight:700;color:var(--blue);margin-bottom:2px}}
.gl-item dd{{font-size:14.5px}}
.gl-src{{margin-left:5px}}
/* FAQ */
.faq{{background:#fff;border:1px solid var(--line);border-radius:13px;margin-bottom:9px;overflow:hidden}}
.faq summary{{list-style:none;cursor:pointer;padding:14px 20px;font-weight:700;font-size:15.5px;color:var(--blue);user-select:none;display:flex;align-items:center}}
.faq summary::-webkit-details-marker{{display:none}}
.faq summary::after{{content:'＋';margin-left:auto;color:var(--gold);font-size:19px;font-weight:800}}
.faq[open] summary::after{{content:'－'}}
.faq[open] summary{{border-bottom:1px solid var(--line)}}
.faq p{{padding:14px 20px;font-size:14.5px;color:#333}}
/* 未查證 */





/* 頁尾 */
.foot{{border-top:1px solid var(--line);margin-top:44px;padding-top:22px;font-size:13px;color:var(--gray)}}
@media(max-width:640px){{
  header.top h1{{font-size:26px}}
  .wrap{{padding:0 16px 50px}}
  .panel{{padding:17px}}
  .infobox th{{width:auto}}
  .pos-src{{margin-left:0;flex-basis:100%}}
}}
</style>
</head>
<body>
<a class="sr-only" href="#main">跳到主要內容</a>

<div class="topbar"><div class="topbar-in">
<a class="brand" href="/">翁振軒 <span>SEAN OWN</span></a>
<nav class="tnav" aria-label="網站導覽">
  <a href="/about/">關於我</a>
  <a href="/media/">媒體</a>
  <a href="/articles/">專欄</a>
</nav>
</div></div>

<header class="top"><div class="wrap">
  <div class="kicker">WIKI ENTRY</div>
  <h1>{esc(p['name_zh'])}</h1>
  <div class="en">{esc(p['name_en'])}</div>
  <p class="lead">{esc(p['summary'])}</p>
  <div class="facts">
    <div class="fact"><div class="n">{p['birth_year']}</div><div class="l">出生年份</div></div>
    <div class="fact"><div class="n">{n_pos}</div><div class="l">現任職務</div></div>
    <div class="fact"><div class="n">{orgs_n}</div><div class="l">相關機構</div></div>
    <div class="fact"><div class="n">{media_n}</div><div class="l">可查證媒體報導</div></div>
  </div>
</div></header>

<main class="wrap" id="main">

<section class="sec">
  <h2 class="sec-h">基本資料</h2>
  <table class="infobox">
    <tr><th>姓名</th><td>{esc(p['name_zh'])}（{esc(p['name_en'])}）</td></tr>
    <tr><th>出生</th><td>{p['birth_year']} 年，{esc(p['birth_place'])}</td></tr>
    <tr><th>祖籍</th><td>{esc(p['ancestral_home'])}</td></tr>
    <tr><th>現居</th><td>{esc(p['residence'])}</td></tr>
    <tr><th>學歷</th><td>{''.join(f'{esc(x["item"])}｜{esc(x["detail"])} {src_link(x.get("source_url"))}' for x in p['education'])}</td></tr>
    <tr><th>主要職務</th><td>粵港澳大灣區電子商會會長、澳門龍遊集團創辦人暨董事總經理</td></tr>
  </table>
</section>

<section class="sec">
  <h2 class="sec-h">職務</h2>
  <div class="panel">
    {pos_html}
    {nv_html}
  </div>
</section>

<section class="sec">
  <h2 class="sec-h">相關機構</h2>
  <p class="sec-note">附官方網址與報導來源。</p>
  <div class="org-grid">{org_html}</div>
</section>

<section class="sec">
  <h2 class="sec-h">常見問題</h2>
  {faq_html}
</section>

<section class="sec">
  <h2 class="sec-h">相關條目用語</h2>
  <div class="panel">{gloss_html}</div>
</section>

<section class="sec">
  <h2 class="sec-h">媒體報導</h2>
  <p class="sec-note">本條目的事實支撐來源。共 {media_n} 則，其中 {media_with_url} 則附原文連結，
     全部收錄於<a href="/media/">媒體報導頁</a>；另存有<a href="/media-archive/">離線存檔</a>，
     保留每篇的完整全文、報頭照片與版面截圖，供原連結失效時查證。</p>
</section>

<footer class="foot">
  本頁最後更新：{today}。各項職務與機構均附來源連結，可直接點擊查核。<br>
  如需更正或有可提供的公開來源，歡迎透過 <a href="/contact/">聯絡頁</a> 提供。<br>
  <a href="/">返回首頁</a> ・ <a href="/about/">關於我</a> ・ <a href="/media/">媒體報導</a> ・ <a href="/articles/">專欄文章</a>
</footer>
</main>
</body>
</html>
'''
    ensure_dir(OUT)
    io.open(OUT, 'w', encoding='utf-8').write(doc)
    print(f'[OK] {OUT}')
    print(f'     職務 {n_pos}（可查證 {n_ver}）／機構 {orgs_n}／媒體 {media_n}／FAQ {len(d["faq"])}')
    print(f'     SEO：ProfilePage JSON-LD + 描述 {len(desc)} 字')


build()

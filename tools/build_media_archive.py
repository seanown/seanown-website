#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生媒體報導離線存檔索引頁 media-archive/index.html
用途：原連結若日後失效，站內仍留有全文與版面截圖；此頁亦作為 IMA 知識庫匯入來源。
"""
import io, os, json, glob, html

ROOT = 'C:/Users/user/WorkBuddy/Seanown.org'
OUT = os.path.join(ROOT, 'media-archive', 'index.html')

# 依 data/media.json 補齊媒體來源與標題，避免兩處資訊不一致
MEDIA = json.load(io.open(os.path.join(ROOT, 'data', 'media.json'), encoding='utf-8'))['media']
BY_URL = {m.get('url'): m for m in MEDIA}

# 對應關係：存檔資料夾 → media.json 的原文連結
MAP = [
    ('2025-12-04-huaxiawa', 'http://www.hqxwtoutiao.com/?p=63881'),
    ('2025-12-05-asiaeconomy', 'https://www.asiaeconomynews.com/page193.html?article_id=852'),
    ('2025-12-07-macaudaily', 'https://www.modaily.cn/app/szb/pc/content/202512/07/content_450225.html'),
    ('2025-12-08-houkongdaily', 'https://www.houkongdailynews.com/sectionNews/141028'),
]

e = html.escape


def esc(s):
    return e(str(s or ''), quote=True)


def build():
    cards = []
    total_files = 0
    for folder, url in MAP:
        d = os.path.join(ROOT, 'media-archive', folder)
        if not os.path.isdir(d):
            continue
        m = BY_URL.get(url, {})
        files = sorted(os.listdir(d))
        total_files += len(files)
        md = f'{folder}.md'
        txt = 'content.txt'
        # 圖片類附件
        pics = [f for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
        # 辨識截圖與報頭照
        shot = next((f for f in pics if 'screenshot' in f.lower()), None)
        photo = next((f for f in pics if f.lower().startswith('photo')), None)

        body = io.open(os.path.join(d, txt), encoding='utf-8').read().strip() \
            if os.path.exists(os.path.join(d, txt)) else ''
        chars = len(body)

        thumbs = []
        if photo:
            thumbs.append(f'<img src="{esc(folder)}/{esc(photo)}" alt="{esc(m.get("title"))} 報頭照片" loading="lazy">')
        if shot:
            thumbs.append(f'<img src="{esc(folder)}/{esc(shot)}" alt="{esc(m.get("title"))} 版面截圖" loading="lazy">')

        dl = []
        for f in files:
            kb = os.path.getsize(os.path.join(d, f)) / 1024
            dl.append(f'<li><a href="{esc(folder)}/{esc(f)}" download>{esc(f)}</a>'
                      f'<span class="kb">{kb:.0f} KB</span></li>')

        cards.append(f'''
<article class="arc">
  <header class="arc-h">
    <span class="arc-src">{esc(m.get('source'))}</span>
    <time datetime="{esc(m.get('date'))}">{esc(m.get('date'))}</time>
  </header>
  <h2>{esc(m.get('title'))}</h2>
  <p class="arc-meta">全文存檔 {chars} 字・附件 {len(files)} 個
    ・<a href="{esc(url)}" target="_blank" rel="noopener">原文連結 ↗</a></p>
  <div class="arc-shots">{''.join(thumbs)}</div>
  <details class="arc-body">
    <summary>展開全文</summary>
    <div class="arc-text">{e(body).replace(chr(10), '<br>')}</div>
  </details>
  <details class="arc-dl">
    <summary>下載附件（{len(files)}）</summary>
    <ul>{''.join(dl)}</ul>
  </details>
</article>''')

    today = '2026-10-17'
    doc = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>媒體報導存檔（{len(cards)} 篇）｜翁振軒 Sean Own</title>
<meta name="description" content="seanown.org 媒體報導的離線存檔：完整全文、報頭照片與版面截圖，供原連結失效時查證之用。">
<meta name="robots" content="noindex,follow">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<style>
:root{{--blue:#002676;--gold:#FDB515;--bg:#F8F9FB;--line:#E4E8EF;--text:#1A1A1A;--gray:#667085}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.8;-webkit-font-smoothing:antialiased}}
a{{color:var(--blue)}}
.wrap{{max-width:900px;margin:0 auto;padding:0 24px 70px}}
header.top{{background:linear-gradient(135deg,#002676,#010133);color:#fff;padding:48px 0 40px;margin-bottom:40px}}
header.top .wrap{{padding-bottom:0}}
.kicker{{font-size:12px;letter-spacing:5px;color:var(--gold);font-weight:700;margin-bottom:10px}}
header.top h1{{font-size:34px;font-weight:800;letter-spacing:1px;margin-bottom:12px}}
header.top p{{color:rgba(255,255,255,.82);font-size:15px;max-width:720px}}
.warn{{margin-top:20px;border-left:3px solid var(--gold);padding-left:13px;font-size:13.5px;color:rgba(255,255,255,.72);max-width:760px}}
.arc{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;margin-bottom:22px}}
.arc-h{{display:flex;align-items:center;gap:12px;margin-bottom:9px}}
.arc-src{{font-size:12px;font-weight:700;color:var(--blue);background:#F0F4F8;padding:3px 11px;border-radius:10px}}
.arc-h time{{font-size:13px;color:var(--gray);font-variant-numeric:tabular-nums;font-weight:600}}
.arc h2{{font-size:20px;font-weight:800;line-height:1.5;margin-bottom:7px}}
.arc-meta{{font-size:13.5px;color:var(--gray);margin-bottom:16px}}
.arc-meta a{{font-weight:600}}
.arc-shots{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-bottom:16px}}
.arc-shots img{{width:100%;border-radius:10px;border:1px solid var(--line);display:block}}
details{{border-top:1px solid var(--line);padding-top:12px;margin-top:4px}}
summary{{cursor:pointer;font-size:14px;font-weight:700;color:var(--blue);list-style:none;user-select:none}}
summary::-webkit-details-marker{{display:none}}
summary::after{{content:' ▾';color:var(--gold)}}
details[open] summary::after{{content:' ▴'}}
.arc-text{{margin-top:13px;font-size:14.5px;line-height:1.95;color:#333}}
.arc-dl ul{{list-style:none;margin-top:11px;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:7px}}
.arc-dl li{{display:flex;justify-content:space-between;gap:10px;font-size:13.5px;background:#F8F9FB;border:1px solid var(--line);border-radius:8px;padding:7px 12px}}
.kb{{color:var(--gray);font-size:12px;white-space:nowrap}}
footer{{border-top:1px solid var(--line);margin-top:36px;padding-top:22px;font-size:13px;color:var(--gray)}}
@media(max-width:640px){{
  header.top h1{{font-size:25px}}
  .wrap{{padding:0 16px 50px}}
  .arc{{padding:18px}}
}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="kicker">MEDIA ARCHIVE</div>
  <h1>媒體報導存檔</h1>
  <p>本站「媒體報導」頁（/media/）所收錄報導的離線存檔。每篇保留完整原文、報頭照片與版面截圖，
     供原連結日後失效時仍可查證之用。存檔日期：{today}。</p>
  <p class="warn">本頁所載全文與圖片版權屬原媒體所有，僅作存檔與查證用途，不對外轉載。
     <a href="/media/" style="color:#FDB515;font-weight:700">← 返回媒體報導總覽</a></p>
</div></header>
<div class="wrap">
{''.join(cards)}
<footer>
  收錄 {len(cards)} 篇・附件 {total_files} 個<br>
  來源為各原媒體公開頁面，擷取時間 {today}。存檔目錄 <code>media-archive/</code>。
</footer>
</div>
</body>
</html>
'''
    io.open(OUT, 'w', encoding='utf-8').write(doc)
    print(f'[OK] {OUT}')
    print(f'     {len(cards)} 篇・附件 {total_files} 個')


build()

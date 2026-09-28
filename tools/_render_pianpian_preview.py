# -*- coding: utf-8 -*-
"""渲染 #44《「騙騙」喜歡你》為獨立可開啟的 HTML 預覽（與網站 build 同源 md_to_html）。"""
import io, os, json, re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_articles import md_to_html  # 網站同款渲染

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
OUT = os.path.join(ROOT, '_pianpian_44_preview.html')

data = json.load(io.open(POSTS, encoding='utf-8'))
post = next((p for p in data['posts'] if str(p.get('num')) == '44'), None)
assert post, 'posts.json 找不到 num=44'

title = post['title']
subtitle = post.get('subtitle', '')
slug = post['slug']
body_html = md_to_html(post['body'], title)
# 讓本地 file:// 開啟時圖片路徑正確（預覽檔放專案根，assets 在根下）
body_html = body_html.replace('../../assets/', 'assets/')

CSS = """
:root{--blue:#002676;--blue-dark:#010133;--gold:#FDB515;--gold-dark:#FC9313;--bg:#F8F9FB;--white:#fff;--text:#1A1A1A;--gray:#667085;--line:#E4E8EF}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;color:var(--text);background:var(--white);line-height:1.75;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:36px 24px 80px}
.crumb{font-size:13px;color:var(--gray);margin-bottom:22px}
.meta{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.tag{background:var(--blue);color:#fff;font-size:13px;font-weight:600;padding:5px 14px;border-radius:4px;letter-spacing:1px}
.date{color:var(--gray);font-size:14px}
h1{font-size:30px;line-height:1.45;color:var(--blue);font-weight:800;margin-bottom:10px;letter-spacing:.5px}
.subtitle{font-size:19px;line-height:1.5;color:var(--blue);font-weight:600;margin:6px 0 18px;letter-spacing:.3px}
.rule{width:56px;height:4px;background:var(--gold);border-radius:2px;margin:0 0 26px}
.cover{margin:0 0 26px;border-radius:12px;overflow:hidden;box-shadow:0 8px 28px rgba(1,1,51,.10)}
.cover img{width:100%;display:block}
.abody p{margin:0 0 20px;font-size:17px;text-align:justify}
.abody h2{font-size:23px;line-height:1.5;color:var(--blue);font-weight:800;margin:40px 0 16px;padding-left:14px;border-left:5px solid var(--gold)}
.abody h3{font-size:19px;color:var(--blue);font-weight:700;margin:28px 0 12px}
.abody strong{color:var(--blue);font-weight:700}
.abody ul,.abody ol{margin:0 0 20px;padding-left:24px}
.abody li{margin-bottom:9px;font-size:17px}
.abody blockquote{margin:0 0 22px;padding:16px 20px;background:var(--bg);border-left:4px solid var(--gold);border-radius:0 8px 8px 0;color:#3A3A3A;font-size:16px}
.abody hr{border:none;border-top:1px solid var(--line);margin:38px 0}
.abody img{column-span:all;width:min(100%,520px);display:block;margin:8px auto 28px;border-radius:10px}
.note{margin:14px 0 0;font-size:13px;color:var(--gray);background:#FFF7E6;border:1px solid var(--gold);padding:10px 14px;border-radius:8px}
@media(min-width:900px){.abody{column-count:2;column-gap:56px;column-rule:1px solid var(--line)}.abody h2{column-span:all}.abody blockquote,.abody ul,.abody ol,.abody img{break-inside:avoid}.abody hr{column-span:all}}
"""

html_doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}｜預覽（status={post.get('status','')}）</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="crumb">預覽・未上線草稿（status={post.get('status','')}）｜澳門電影輯 macau-film</div>
  <div class="meta"><span class="tag">澳門電影</span><span class="date">{post.get('date','')}</span></div>
  <h1>{title}</h1>
  <div class="subtitle">{subtitle}</div>
  <div class="rule"></div>
  <div class="cover"><img src="assets/og/{slug}-cover.jpg" alt="封面"></div>
  <div class="abody">
{body_html}
  </div>
  <p class="note">本頁為本地預覽，與網站 build 同源渲染（md_to_html）。確認無誤、軒哥說「可以上線」後，才 flip status→已上線、git push、補 sitemap、IndexNow。</p>
</div>
</body>
</html>
"""

io.open(OUT, 'w', encoding='utf-8').write(html_doc)
print('written:', OUT, 'bytes=', len(html_doc))
print('body_paragraphs≈', body_html.count('<p>'), '| blockquotes=', body_html.count('<blockquote>'), '| h3=', body_html.count('<h3>'))

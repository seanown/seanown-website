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
    """行內格式：粗體、行內 HTML 保留、相對路徑修正"""
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'^>\s*', '', t) if False else t
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
.topbar{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.topbar-in{max-width:1080px;margin:0 auto;padding:0 24px;height:62px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.brand{font-weight:800;color:var(--blue);font-size:17px;letter-spacing:.5px}
.brand span{color:var(--gold)}
.topbar nav{display:flex;gap:20px;font-size:14px;color:var(--gray);flex-wrap:wrap}
.topbar nav a:hover{color:var(--blue)}
.wrap{max-width:780px;margin:0 auto;padding:36px 24px 0}
.crumb{font-size:13px;color:var(--gray);margin-bottom:22px}
.crumb a:hover{color:var(--blue)}
.meta{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.tag{background:var(--blue);color:#fff;font-size:13px;font-weight:600;padding:5px 14px;border-radius:4px;letter-spacing:1px}
.date{color:var(--gray);font-size:14px}
h1{font-size:32px;line-height:1.4;color:var(--blue);font-weight:800;margin-bottom:14px;letter-spacing:.5px}
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
.author{margin-top:46px;background:var(--bg);border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:12px;padding:26px 26px 22px}
.author h2{font-size:17px;color:var(--blue);margin:0 0 10px;border:none;padding:0}
.author p{font-size:15px;color:#4A4A4A;margin-bottom:8px}
.author .who{font-weight:700;color:var(--blue);font-size:16px;margin-bottom:6px}
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
@media(max-width:720px){h1{font-size:25px}.article h2{font-size:20px}.article p,.article li{font-size:16px}.rel-grid{grid-template-columns:1fr}.gallery{grid-template-columns:repeat(2,1fr)}.wrap{padding:26px 18px 0}.topbar nav{display:none}}
"""


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

    kw = '，'.join([x for x in ['翁振軒', 'Sean Own', cat, '澳門', '產業觀察'] if x])

    page = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜{cat}｜翁振軒 Sean Own 專欄</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{kw}">
<meta name="author" content="翁振軒 Sean Own">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="../../assets/favicon.svg">
<meta name="theme-color" content="#002676">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="SEAN OWN 翁振軒">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script type="application/ld+json">{ld}</script>
<style>{css}</style>
</head>
<body>
<div class="topbar"><div class="topbar-in">
<a class="brand" href="../../">翁振軒 <span>SEAN OWN</span></a>
<nav>
<a href="../../#sec-services">核心業務</a><a href="../../#sec-projects">代表項目</a>
<a href="../../#sec-media">媒體報導</a><a href="../../#sec-articles">最新文章</a>
<a href="../../#sec-about">關於我</a><a href="../../#sec-contact">合作與聯絡</a>
</nav></div></div>

<div class="wrap">
<div class="crumb"><a href="../../">首頁</a> › <a href="../../#sec-articles">{cat}</a> › 本文</div>
<article class="article">
<div class="meta"><span class="tag">{cat}</span><span class="date">{date_fmt}{loc_fmt}</span></div>
<h1>{title}</h1>
<div class="rule"></div>
{cover}
{body}
{gallery}
</article>

<div class="author">
<h2>關於作者</h2>
<div class="who">翁振軒 Sean Own</div>
<p>龍遊集團創辦人暨董事總經理、粵港澳大灣區電子商會會長、澳門台商聯誼會監事長、澳門龍遊絲綢文化藝術中心館長。以澳門為基地，深耕文化產業，推動中國數位服務出海與中華文創 IP 落地。</p>
<p><a href="../../#sec-about">查看完整經歷 →</a></p>
</div>

<div class="related">
<h2>延伸閱讀</h2>
<div class="rel-grid">{rel}</div>
</div>

<div class="cta">
<h2>想進一步交流？</h2>
<p>無論是數位出海、文化 IP 合作，或青年跨界連結，都歡迎與我聊聊。</p>
<a class="btn" href="../../#sec-contact">洽談合作</a>
<a class="btn ghost" href="../../#sec-articles">更多文章</a>
</div>

<div class="foot">
© 2026 翁振軒 Sean Own · <a href="../../">返回首頁</a><br>
本文為作者個人觀點，轉載請註明出處。
</div>
</div>
<div class="lb" id="lb" onclick="this.style.display='none'"><img id="lbimg" src="" alt=""></div>
</body>
</html>
""".format(
        title=esc(title), cat=esc(cat), desc=esc(desc), kw=esc(kw), url=url,
        ld=json.dumps(ld, ensure_ascii=False), css=CSS,
        date_fmt=date.replace('-', ' 年 ', 1).replace('-', ' 月 ') + ' 日' if date else '',
        loc_fmt=(' · ' + esc(loc)) if loc else '',
        cover=cover, body=body_html, gallery=gallery, rel=rel_html,
    )

    d = os.path.join(ROOT, 'article', slug)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    return slug, title


def main():
    data = json.load(io.open(POSTS, encoding='utf-8'))
    posts = data['posts']
    published = [p for p in posts if p.get('status') != '整理中']
    for p in posts:
        p['slug'] = SLUGS.get(str(p.get('num', '')).strip(), '')
    made = []
    for p in published:
        made.append(build(p, published))
    io.open(POSTS, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('generated %d article pages' % len(made))
    for s, t in made:
        print('  /article/%s/  %s' % (s, t[:34]))


if __name__ == '__main__':
    main()

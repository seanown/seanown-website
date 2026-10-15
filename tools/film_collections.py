# -*- coding: utf-8 -*-
"""澳門電影專輯 · 三軸合輯 + 篇末互導（年代／取景地／影人）。

設計原則：
  - 不動 posts.json —— 年代(filmYear)、導演、演員、取景地都已在 movieInfo 裡結構化，
    由 build_articles 在 build 時派生，避免改動資料層（posts.json 有嚴格的入庫／提交鐵律）。
  - 地名正規化 —— macauScenes 的 places[].name 有大量變體（「議事亭前地」三種寫法），
    先去中英文括號、再去尾隨拉丁，套用小數別名對照，才能真正跨片聚合。
  - 產出兩部分：
      1) collection/ 落地頁（hub + 時代/十年代/地標/影人），供導覽與 SEO；
      2) 每篇電影文章末尾的「順手再看」三軸互導 HTML，讓 83 篇互相咬合成網。

本模組自包含 esc / CSS，不 import build_articles（避免循環依賴）；
og 快取版號 ov() 由 build_articles 傳入，SLUGS 亦外部傳入。
"""
import io, os, re, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 时代／十年代 ───────────────────────────────────────────────
ERA_META = {
    'early':  ('早期 · 1969 年前',  '黑白與粵語片年代，澳門最早出現在銀幕上的樣子'),
    'golden': ('港產黃金 · 1970–1999', '港片全盛期，澳門是江湖、是江湖兒女的退路'),
    'milli':  ('千禧之後 · 2000 起',  '澳門主權移交後再度成為主角，從背景板走進故事'),
}
ERA_ORDER = ['early', 'golden', 'milli']


def era_of(year):
    if not year:
        return 'milli'
    if year <= 1969:
        return 'early'
    if year <= 1999:
        return 'golden'
    return 'milli'


def decade_of(year):
    if not year:
        return '年份待考'
    return '%d 年代' % ((year // 10) * 10)


def decade_slug(year):
    if not year:
        return 'decade-unknown'
    return 'decade-%d' % ((year // 10) * 10)


def era_slug(era):
    return 'era-' + era


def esc(t):
    return html.escape(t or '', quote=False)


# ── 地名正規化 ─────────────────────────────────────────────────
_PAREN = re.compile(r'[（(][^）)]*[）)]')          # 中英文括號及其內容
_TRAIL_LATIN = re.compile(r'[\s]*[A-Za-z][A-Za-z\s\'’\.·\-]*$')  # 尾隨拉丁（英文／葡文名）
# 少數「去括號後仍不同名」的等價地名（保守，只收確定同指）
PLACE_ALIAS = {
    '大三巴': '大三巴牌坊',
    '大三八': '大三巴牌坊',
    '議事亭廣場': '議事亭前地',
    '議事亭前地廣場': '議事亭前地',
    '新馬路': '新馬路',
    '亞美打利庇盧大馬路': '新馬路',
    '葡京': '葡京酒店',
    '大三巴牌坊': '大三巴牌坊',
}


def norm_place(name):
    if not name:
        return ''
    s = str(name).strip()
    s = _PAREN.sub('', s)                 # 去（Senado Square）/（Ruins of St. Paul's）等
    s = _TRAIL_LATIN.sub('', s)           # 去「議事亭前地 Largo do Senado」尾隨葡文
    s = re.sub(r'\s+', ' ', s).strip(' ，,、·.')
    return PLACE_ALIAS.get(s, s)


def get_scenes(macau_scenes):
    """macauScenes 結構不一：dict{intro,scenes,foot} 或直接 list；取 scenes 陣列。"""
    if isinstance(macau_scenes, dict):
        return macau_scenes.get('scenes') or []
    if isinstance(macau_scenes, list):
        return macau_scenes
    return []


def film_places(mi):
    """一部片的正規化取景地集合（含 GPS，取首次出現者）。"""
    out = {}
    for sec in get_scenes(mi.get('macauScenes')):
        if not isinstance(sec, dict):
            continue
        for pl in (sec.get('places') or []):
            nm = norm_place(pl.get('name'))
            if nm and nm not in out:
                out[nm] = pl.get('gps') or ''
    return out  # {name: gps}


def film_people(mi):
    """一部片的影人 [(name, role)]，role ∈ {導演, 演員}；導演在前、演員依序。"""
    out = []
    d = (mi.get('director') or '').strip()
    if d:
        out.append((d, '導演'))
    for a in (mi.get('actors') or []):
        nm = (a.get('name') if isinstance(a, dict) else a) or ''
        nm = str(nm).strip()
        if nm and all(nm != x for x, _ in out):
            out.append((nm, '演員'))
    return out


def film_name(post):
    t = ((post.get('movieInfo') or {}).get('title') or post.get('title') or '').strip()
    t = re.sub(r'^《', '', t)
    t = re.sub(r'》觀後感$', '', t)
    t = t.rstrip('》').strip()  # movieInfo.title 自帶《…》時補剝尾括號，避免《XX》》
    return t or (post.get('title') or '')


# ── 建立三軸索引（一次計算，文章頁互導與合輯頁共用）──────────────
def build_index(posts, slugs):
    films = [p for p in posts if p.get('series') == 'macau-film' and p.get('movieInfo')]

    def slug_of(p):
        n = str(p.get('num', '')).strip()
        return slugs.get(n) or p.get('slug') or ('post-' + n)

    # 以 num（字串）為鍵
    meta = {}
    order = []
    for p in films:
        mi = p.get('movieInfo') or {}
        try:
            year = int(p.get('filmYear') or mi.get('year') or 0)
        except (TypeError, ValueError):
            year = 0
        key = str(p.get('num', '')).strip()
        meta[key] = {
            'num': key, 'slug': slug_of(p), 'name': film_name(p),
            'year': year, 'decade': decade_of(year), 'era': era_of(year),
            'places': film_places(mi), 'people': film_people(mi),
            'post': p,
        }
        order.append(key)

    # 聚合
    by_decade = {}   # 'decade-1980' -> [keys]
    by_era = {}      # 'early' -> [keys]
    by_place = {}    # norm_name -> [keys]
    place_gps = {}   # norm_name -> gps
    by_person = {}   # name -> {'導演':[keys], '演員':[keys]}
    for k in order:
        m = meta[k]
        by_decade.setdefault(decade_slug(m['year']), []).append(k)
        by_era.setdefault(m['era'], []).append(k)
        for nm, gps in m['places'].items():
            by_place.setdefault(nm, []).append(k)
            place_gps.setdefault(nm, gps)
        for nm, role in m['people']:
            by_person.setdefault(nm, {}).setdefault(role, [])
            if k not in by_person[nm][role]:
                by_person[nm][role].append(k)

    # 排序：十年代／時代內依年份升序
    for d in by_decade:
        by_decade[d].sort(key=lambda k: (meta[k]['year'], meta[k]['num']))
    for e in by_era:
        by_era[e].sort(key=lambda k: (meta[k]['year'], meta[k]['num']))

    # 地標／影人：依片數降序，取名次门槛以上者開獨立頁
    place_rank = sorted(by_place.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    person_rank = sorted(by_person.items(), key=lambda kv: (-sum(len(v) for v in kv[1].values()), kv[0]))

    PLACE_MIN = 3
    PERSON_MIN = 3

    def pslug(prefix, name, rank, i):
        return '%s-%02d' % (prefix, i)

    place_pages = {}   # name -> slug（只收 >=PLACE_MIN）
    for i, (nm, keys) in enumerate([kv for kv in place_rank if len(kv[1]) >= PLACE_MIN]):
        place_pages[nm] = 'place-%02d' % (i + 1)
    person_pages = {}  # name -> slug（只收 >=PERSON_MIN）
    for i, (nm, roles) in enumerate([kv for kv in person_rank if sum(len(v) for v in kv[1].values()) >= PERSON_MIN]):
        person_pages[nm] = 'person-%02d' % (i + 1)

    return {
        'meta': meta, 'order': order,
        'by_decade': by_decade, 'by_era': by_era,
        'by_place': by_place, 'place_gps': place_gps, 'place_rank': place_rank,
        'by_person': by_person, 'person_rank': person_rank,
        'place_pages': place_pages, 'person_pages': person_pages,
        'PLACE_MIN': PLACE_MIN, 'PERSON_MIN': PERSON_MIN,
        'decade_label': {decade_slug(m['year']): m['decade'] for m in meta.values()},
    }


# ── 影片小卡（合輯頁與互導共用）────────────────────────────────
def film_chip(meta, slugs, site, ov, show_year=True):
    m = meta
    poster = '../../assets/og/%s-poster.jpg' % m['slug']
    yr = ('<span class="fc-yr">%d</span>' % m['year']) if (show_year and m['year']) else ''
    return (
        '<a class="fc" href="%s/article/%s/">'
        '<img class="fc-img" src="%s" alt="%s" loading="lazy">'
        '<span class="fc-n">《%s》</span>%s</a>'
    ) % (site, m['slug'], ov(poster), esc(m['name']), esc(m['name']), yr)


def rel_chip(meta, site):
    yr = (' <span class="rc-yr">%d</span>' % meta['year']) if meta['year'] else ''
    return ('<a class="rc" href="%s/article/%s/">《%s》%s</a>'
            % (site, meta['slug'], esc(meta['name']), yr))


# ── CSS ────────────────────────────────────────────────────────
PAGE_CSS = """
.cpage{--blue:#002676;--gold:#FDB515;--ink:#1c1a17;--muted:#8a8277;--line:#e7e0d4;--soft:#f4f0e8}
.cpage body,.cpage{font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif}
.cp-top{background:#002676;color:#fff}
.cp-top .in{max-width:1080px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:18px}
.cp-top a.brand{color:#fff;font-weight:700;letter-spacing:.04em;text-decoration:none;font-family:"Noto Serif TC",serif}
.cp-top a.brand span{color:#FDB515}
.cp-top a.lnk{color:#c9d6ee;text-decoration:none;font-size:14px}
.cp-top a.lnk:hover{color:#fff}
.cp-hero{background:linear-gradient(180deg,#002676,#001a4d);color:#fff;padding:52px 24px 46px;text-align:center}
.cp-hero .kick{letter-spacing:.4em;font-size:12px;color:#FDB515;margin-bottom:16px}
.cp-hero h1{font-family:"Noto Serif TC",serif;font-size:clamp(30px,5vw,46px);font-weight:900;margin:0 0 12px}
.cp-hero .sub{color:#c9d6ee;font-size:15px;max-width:640px;margin:0 auto}
.cp-wrap{max-width:1080px;margin:0 auto;padding:36px 24px 70px}
.cp-sec{margin:0 0 40px}
.cp-sec h2{font-family:"Noto Serif TC",serif;font-size:22px;font-weight:900;color:#002676;
  border-left:5px solid #FDB515;padding-left:12px;margin:0 0 6px}
.cp-sec .d{color:#8a8277;font-size:13.5px;margin:0 0 18px}
.cp-grid{display:flex;flex-wrap:wrap;gap:14px}
.fc{display:flex;flex-direction:column;width:132px;text-decoration:none;color:#1c1a17}
.fc-img{width:132px;height:198px;object-fit:cover;border-radius:8px;box-shadow:0 2px 10px rgba(0,20,70,.14);background:#eee}
.fc-n{font-size:13.5px;font-weight:700;margin-top:8px;line-height:1.35;font-family:"Noto Serif TC",serif}
.fc-yr{display:inline-block;font-size:12px;color:#002676;font-weight:700;margin-top:2px}
.cp-era{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:8px}
@media(max-width:720px){.cp-era{grid-template-columns:1fr}}
.cp-era a{display:block;background:#fff;border:1px solid #e7e0d4;border-radius:14px;padding:20px;text-decoration:none;color:#1c1a17}
.cp-era a:hover{border-color:#002676}
.cp-era .t{font-family:"Noto Serif TC",serif;font-weight:900;font-size:17px;color:#002676}
.cp-era .c{font-size:13px;color:#8a8277;margin-top:6px}
.cp-era .n{font-size:26px;font-weight:900;color:#FDB515;font-family:"Noto Serif TC",serif}
.cp-chips{display:flex;flex-wrap:wrap;gap:10px}
.cp-chips a{background:#fff;border:1px solid #e7e0d4;border-radius:22px;padding:8px 16px;text-decoration:none;
  color:#002676;font-weight:700;font-size:14px}
.cp-chips a:hover{background:#002676;color:#fff;border-color:#002676}
.cp-chips a b{color:#FDB515;font-weight:700;margin-left:6px}
.cp-chips a:hover b{color:#fff}
.cp-foot{border-top:1px solid #e7e0d4;margin-top:40px;padding-top:18px;font-size:12.5px;color:#8a8277;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.cp-foot a{color:#002676}
.cp-gps{font-size:12.5px;color:#8a8277;margin-top:4px}
.cp-gps a{color:#002676}
.cp-route{display:block;background:linear-gradient(150deg,#002676,#001a4d);border:1px solid #FDB515;
  border-radius:14px;padding:22px 24px;text-decoration:none;color:#fff}
.cp-route:hover{box-shadow:0 8px 26px rgba(0,20,70,.22)}
.cp-route .t{font-family:"Noto Serif TC",serif;font-weight:900;font-size:19px;color:#FDB515}
.cp-route .c{font-size:13.5px;color:#c9d6ee;margin-top:8px;line-height:1.9}
.cp-route .go{margin-top:12px;font-size:13px;font-weight:700;color:#fff}
"""

REL_CSS = """
.frel{margin:34px 0 8px;padding:22px 22px 20px;background:#f6f3ec;border:1px solid #e7e0d4;border-radius:14px}
.frel .fr-h{font-family:"Noto Serif TC",serif;font-weight:900;font-size:16px;color:#002676;margin:0 0 4px}
.frel .fr-s{font-size:12.5px;color:#8a8277;margin:0 0 16px}
.frel .fr-row{display:flex;align-items:baseline;gap:10px;padding:9px 0;border-top:1px dashed #e0d9cc;flex-wrap:wrap}
.frel .fr-row:first-of-type{border-top:none}
.frel .fr-lab{flex:0 0 auto;font-size:13px;font-weight:700;color:#002676;min-width:96px}
.frel .fr-lab .em{margin-right:4px}
.frel .fr-list{display:flex;flex-wrap:wrap;gap:8px;flex:1}
.frel a.rc{font-size:13.5px;color:#1c1a17;text-decoration:none;background:#fff;border:1px solid #e2dbcf;
  border-radius:16px;padding:4px 12px;line-height:1.5}
.frel a.rc:hover{border-color:#002676;color:#002676}
.frel a.rc .rc-yr{color:#8a8277;font-size:12px;margin-left:2px}
.frel a.fr-all{font-size:12.5px;color:#B8860B;text-decoration:none;font-weight:700;white-space:nowrap}
.frel a.fr-all:hover{text-decoration:underline}
"""


# ── 合輯落地頁 ─────────────────────────────────────────────────
def _shell(title, kicker, h1, sub, body, site='', og_img=''):
    # 頂欄連結一律用絕對路徑：collection/ 有 hub（深一層）與子頁（深兩層）兩種深度，
    # 相對連結必然有一邊寫錯（2026-10-15 上線當日被軒哥抓到：
    # '../macau-film/' 在 hub 解析成 /macau-film/、在子頁解析成 /collection/macau-film/，全 404）。
    og = (og_img or (site + '/assets/og/seanown-home.jpg')) if site else ''
    og_tag = ('<meta property="og:image" content="%s">' % esc(og)) if og else ''
    home = (site + '/') if site else '../../'
    favicon = (site + '/assets/favicon.svg') if site else '../../assets/favicon.svg'
    album = (site + '/series/macau-film/') if site else '../../series/macau-film/'
    return """<!DOCTYPE html>
<html lang="zh-Hant" class="cpage">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s｜澳門電影專輯｜翁振軒 Sean Own</title>
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
<div class="cp-top"><div class="in">
<a class="brand" href="%s">翁振軒 <span>SEAN OWN</span></a>
<a class="lnk" href="%s">← 澳門電影專輯</a>
</div></div>
<div class="cp-hero"><div class="kick">%s</div><h1>%s</h1><div class="sub">%s</div></div>
<div class="cp-wrap">%s</div>
</body>
</html>""" % (esc(title), esc(sub[:110]), esc(favicon), esc(title), esc(sub[:110]), og_tag, PAGE_CSS,
               esc(home), esc(album), esc(kicker), esc(h1), esc(sub), body)


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


def _film_grid(keys, index, slugs, site, ov):
    return '<div class="cp-grid">' + ''.join(
        film_chip(index['meta'][k], slugs, site, ov) for k in keys) + '</div>'


def build_collections(index, slugs, site, ov, og_img=''):
    """產生 collection/ 全部頁面，回傳 [(url, lastmod)] 供 sitemap。"""
    meta = index['meta']
    sitemap = []
    today = date.today().isoformat()

    # ── Hub 總覽 ──
    era_cards = ''
    for e in ERA_ORDER:
        keys = index['by_era'].get(e, [])
        if not keys:
            continue
        lab, desc = ERA_META[e]
        era_cards += ('<a href="%s/">'
                      '<div class="t">%s</div>'
                      '<div class="n">%d 部</div>'
                      '<div class="c">%s</div></a>') % (era_slug(e), esc(lab), len(keys), esc(desc))

    dec_decades = sorted(index['by_decade'].items(),
                         key=lambda kv: -int(re.sub(r'\D', '', kv[0]) or 0))
    decade_chips = ''
    for dslug, keys in dec_decades:
        label = index['decade_label'].get(dslug, dslug)
        decade_chips += ('<a href="%s/">%s<b>%d</b></a>'
                         % (dslug + '/', esc(label), len(keys)))

    place_items = ''
    for nm, slug in list(index['place_pages'].items())[:24]:
        n = len(index['by_place'][nm])
        place_items += ('<a href="%s/">%s<b>%d 部</b></a>' % (slug + '/', esc(nm), n))
    person_items = ''
    for nm, slug in list(index['person_pages'].items())[:24]:
        roles = index['by_person'][nm]
        n = sum(len(v) for v in roles.values())
        tag = '導演' if '導演' in roles else '演員'
        person_items += ('<a href="%s/">%s · %s<b>%d 部</b></a>' % (slug + '/', esc(nm), tag, n))

    hub_body = (
        '<div class="cp-sec" id="by-route"><h2>🚶 跟著電影遊澳門</h2>'
        '<p class="d">不想一部部逛？八條路線把 63 個場景按走法串起來——每站有座標、站位描寫與拍攝提示。</p>'
        '<a class="cp-route" href="%s/route/">'
        '<div class="t">🚶 跟著電影遊澳門 · 8 條主題路線</div>'
        '<div class="c">半島中、內港、新口岸、路氹金光大道、氹仔舊城、路環、本地創作、世界眼中的澳門——'
        '從「看一篇」變成「走一條線」，每站深鏈回對應的觀後感。</div>'
        '<div class="go">進入路線總覽 →</div></a></div>'
        '<div class="cp-sec" id="by-era"><h2>🕰 時光機 · 按年代</h2>'
        '<p class="d">三個時代、十個十年代——從 1923 年的澳門看到 2025 年。</p>'
        '<div class="cp-era">%s</div></div>'
        '<div class="cp-sec" id="by-decade"><h2>📅 十年代</h2><div class="cp-chips">%s</div></div>'
        '<div class="cp-sec" id="by-place"><h2>🗺 澳門電影地圖 · 按取景地</h2>'
        '<p class="d">同一個澳門地標，反覆出現在不同電影裡。點進去，看這座城如何被一遍遍重拍。</p>'
        '<div class="cp-chips">%s</div></div>'
        '<div class="cp-sec" id="by-person"><h2>🎭 誰在澳門 · 按影人</h2>'
        '<p class="d">同一位導演或演員，一再回到澳門。出現 3 部以上者獨立成頁。</p>'
        '<div class="cp-chips">%s</div></div>'
    ) % (site, era_cards, decade_chips, place_items, person_items)
    _write('collection/index.html',
           _shell('澳門電影 · 主題合輯', '澳門電影專輯 · MACAU FILM',
                  '四種逛法，一座城的銀幕', '按年代、按取景地、按影人、按路線——把 83 篇觀後感編成一張網。',
                  hub_body, site, og_img))
    sitemap.append((site + '/collection/', today))

    # ── 時代頁 ──
    for e in ERA_ORDER:
        keys = index['by_era'].get(e, [])
        if not keys:
            continue
        lab, desc = ERA_META[e]
        # 內含十年代分組
        groups = {}
        for k in keys:
            groups.setdefault(meta[k]['decade'], []).append(k)
        inner = ''
        for dec in sorted(groups, key=lambda x: -int(re.sub(r'\D', '', x) or 0)):
            inner += ('<div class="cp-sec"><h2>%s</h2><div class="cp-gps">%d 部</div>%s</div>'
                      % (esc(dec), len(groups[dec]), _film_grid(groups[dec], index, slugs, site, ov)))
        body = ('<p class="d" style="font-size:15px;color:#5a534a;margin-bottom:24px">%s　共 %d 部。</p>%s'
                % (esc(desc), len(keys), inner))
        _write('collection/%s/index.html' % era_slug(e),
               _shell('澳門電影 · %s' % lab, '按年代', lab, '%s（%d 部）' % (desc, len(keys)), body, site, og_img))
        sitemap.append(('%s/collection/%s/' % (site, era_slug(e)), today))

    # ── 十年代頁 ──
    for dslug, keys in index['by_decade'].items():
        label = index['decade_label'].get(dslug, dslug)
        era = meta[keys[0]]['era'] if keys else ''
        body = ('<p class="d" style="font-size:15px;color:#5a534a;margin-bottom:24px">'
                '屬於「%s」，共 %d 部。</p>%s'
                % (esc(ERA_META.get(era, ('', ''))[0]), len(keys),
                   _film_grid(keys, index, slugs, site, ov)))
        _write('collection/%s/index.html' % dslug,
               _shell('澳門電影 · %s' % label, '按年代', label, '%s在澳門取景的電影，共 %d 部。' % (label, len(keys)), body, site, og_img))
        sitemap.append(('%s/collection/%s/' % (site, dslug), today))

    # ── 取景地頁 ──
    for nm, slug in index['place_pages'].items():
        keys = index['by_place'][nm]
        gps = index['place_gps'].get(nm, '')
        gps_html = ''
        if gps:
            gps_html = ('<div class="cp-gps">📍 座標約 %s　'
                        '<a href="https://www.google.com/maps/search/?api=1&query=%s" target="_blank" rel="noopener">在 Google 地圖打開 →</a></div>'
                        % (esc(gps), esc(gps.replace('約 ', '').replace(' ', ''))))
        body = ('<p class="d" style="font-size:15px;color:#5a534a;margin-bottom:8px">'
                '「%s」這個澳門地標，出現在專輯裡 %d 部電影的取景中。</p>%s%s'
                % (esc(nm), len(keys), gps_html, _film_grid(keys, index, slugs, site, ov)))
        _write('collection/%s/index.html' % slug,
               _shell('澳門電影地圖 · %s' % nm, '按取景地', nm, '在「%s」取景的澳門電影，共 %d 部。' % (nm, len(keys)), body, site, og_img))
        sitemap.append(('%s/collection/%s/' % (site, slug), today))

    # ── 影人頁 ──
    for nm, slug in index['person_pages'].items():
        roles = index['by_person'][nm]
        keys = []
        seen = set()
        for role in ('導演', '演員'):
            for k in roles.get(role, []):
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        keys.sort(key=lambda k: (meta[k]['year'], meta[k]['num']))
        role_txt = '、'.join('%s %d 部' % (r, len(roles[r])) for r in ('導演', '演員') if roles.get(r))
        body = ('<p class="d" style="font-size:15px;color:#5a534a;margin-bottom:24px">'
                '%s在澳門電影專輯裡：%s。</p>%s'
                % (esc(nm), esc(role_txt), _film_grid(keys, index, slugs, site, ov)))
        _write('collection/%s/index.html' % slug,
               _shell('誰在澳門 · %s' % nm, '按影人', nm, '%s與澳門電影（%s）。' % (nm, role_txt), body, site, og_img))
        sitemap.append(('%s/collection/%s/' % (site, slug), today))

    return sitemap


# ── 篇末三軸互導 ───────────────────────────────────────────────
def related_html(post, index, slugs, site, ov):
    """一篇電影文章的「順手再看」三軸互導塊；非電影文章或無鄰居回空字串。"""
    if post.get('series') != 'macau-film' or not post.get('movieInfo'):
        return ''
    num = str(post.get('num', '')).strip()
    me = index['meta'].get(num)
    if not me:
        return ''

    def row(em, label, count_txt, chips, all_url, all_txt):
        if not chips:
            return ''
        allh = ('<a class="fr-all" href="%s">%s →</a>' % (all_url, esc(all_txt))) if all_url else ''
        return ('<div class="fr-row"><span class="fr-lab"><span class="em">%s</span>%s</span>'
                '<span class="fr-list">%s</span>%s</div>'
                % (em, esc(label + (('（%s）' % count_txt) if count_txt else '')), ''.join(chips), allh))

    rows = ''

    # 同十年代
    dslug = decade_slug(me['year'])
    decade_keys = [k for k in index['by_decade'].get(dslug, []) if k != num]
    if decade_keys:
        chips = [rel_chip(index['meta'][k], site) for k in decade_keys[:4]]
        rows += row('🕰', '同年代', '%d 部' % len(decade_keys), chips,
                    '%s/collection/%s/' % (site, dslug), '看全部')

    # 同取景地（取本片全球片數最高的地標）
    best_place, best_n = '', 0
    for nm in me['places']:
        n = len(index['by_place'].get(nm, []))
        if n > best_n:
            best_place, best_n = nm, n
    if best_place and best_n >= 2:
        others = [k for k in index['by_place'][best_place] if k != num]
        chips = [rel_chip(index['meta'][k], site) for k in others[:4]]
        all_url = ''
        if best_place in index['place_pages']:
            all_url = '%s/collection/%s/' % (site, index['place_pages'][best_place])
        rows += row('🗺', '同取景地 · %s' % best_place, '%d 部' % best_n, chips,
                    all_url, '這座地標')

    # 同影人（取本片全球片數最高的影人）
    best_person, best_pn, best_role = '', 0, ''
    for nm, role in me['people']:
        n = sum(len(v) for v in index['by_person'].get(nm, {}).values())
        if n > best_pn:
            best_person, best_pn, best_role = nm, n, role
    if best_person and best_pn >= 2:
        prole = index['by_person'][best_person]
        others, seen = [], set()
        for r in ('導演', '演員'):
            for k in prole.get(r, []):
                if k != num and k not in seen:
                    seen.add(k)
                    others.append(k)
        chips = [rel_chip(index['meta'][k], site) for k in others[:4]]
        all_url = ''
        if best_person in index['person_pages']:
            all_url = '%s/collection/%s/' % (site, index['person_pages'][best_person])
        rows += row('🎭', '同影人 · %s' % best_person, '%d 部' % best_pn, chips,
                    all_url, '全部作品')

    if not rows:
        return ''
    return ('<div class="frel"><div class="fr-h">順手再看 · 這部片在專輯裡的鄰居</div>'
            '<div class="fr-s">83 篇觀後感，按年代、取景地、影人互相串聯——不必一座座孤島地讀。</div>'
            '%s</div>' % rows)


# ── 專輯頁（/series/macau-film/）三軸入口帶 ─────────────────────
AXES_CSS = """
.axes{background:linear-gradient(160deg,#002676,#001a4d);border-radius:16px;padding:20px 22px 18px;
  margin:0 0 26px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.axes .ax-h{grid-column:1/-1;color:#FDB515;font-size:12px;letter-spacing:.32em;font-weight:700;margin-bottom:2px}
.axes a{display:block;background:rgba(255,255,255,.06);border:1px solid rgba(253,181,21,.32);
  border-radius:12px;padding:13px 15px;text-decoration:none;color:#fff;transition:background .25s,border-color .25s}
.axes a:hover{background:rgba(253,181,21,.13);border-color:#FDB515}
.axes .t{font-family:"Noto Serif TC",serif;font-weight:900;font-size:16.5px;line-height:1.3}
.axes .c{font-size:12.5px;color:#c9d6ee;margin-top:5px}
@media(max-width:960px){.axes{grid-template-columns:repeat(2,1fr)}}
@media(max-width:720px){.axes{grid-template-columns:1fr}}
"""


def axes_html(index, site):
    """澳門電影專輯頁頂部的三軸入口帶：深鏈到 /collection/ 各分節。

    第四張卡深鏈到 /route/（跟著電影遊澳門）——同一個專輯的第四種逛法：
    按路線走。回傳值自带前導換行（貼在 sort_bar 之後）；非電影輯不呼叫本函式，
    頁面上不會留下多餘空行。
    """
    n_era = len([e for e in ERA_ORDER if index['by_era'].get(e)])
    n_dec = len(index['by_decade'])
    n_place = len(index['place_pages'])
    n_person = len(index['person_pages'])
    hub = site + '/collection/'
    cards = [
        ('🕰', '按年代', '%d 個時代 · %d 個十年代' % (n_era, n_dec), hub + '#by-era'),
        ('🗺', '按取景地', '%d 個澳門地標獨立成頁' % n_place, hub + '#by-place'),
        ('🎭', '按影人', '%d 位導演演員獨立成頁' % n_person, hub + '#by-person'),
        ('🚶', '跟著電影遊澳門', '8 條路線 · 63 站可實地走', site + '/route/'),
    ]
    out = '\n<div class="axes"><div class="ax-h">%d 篇觀後感 · 換個逛法</div>' % len(index['meta'])
    for em, t, c, href in cards:
        out += ('<a href="%s"><div class="t">%s %s</div><div class="c">%s</div></a>'
                % (esc(href), em, esc(t), esc(c)))
    return out + '</div>'

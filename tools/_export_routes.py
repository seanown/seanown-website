# -*- coding: utf-8 -*-
"""一次性匯出：旅遊書 63 場景 × 網站 83 篇（GPS／文章 slug／同地電影）→ data/routes.json。

為什麼需要這個橋：
  《跟著電影遊澳門》的內容生產線在另一個 repo（澳門旅遊攻略/content63.json），
  網站 build 不跨 repo 依賴。此腳本把書的 63 站與網站的座標／文章資產對接一次，
  落地成 data/routes.json；日後書更新，重跑本腳本即可。

匹配規則（按序）：
  1. STATION_ALIAS 人工校正表（逐站核對過，只收確定同指；站名先正規化再查一次）
  2. norm_place 正規化後直接命中網站地名索引
  3. movie 名匹配文章（MOVIE_ALIAS＋異體字＋多片拆分）→ 在該篇 places 內匹配站名
  4. 網站地名索引模糊匹配（去「酒店」尾綴／雙向包含／前綴，≥3 字）
  5. 仍無 → 無 GPS（頁面用 info.address 兜底，不造假座標）

NO_GPS_NOTE 的站（全城型／書比網站全）直接短路：不配座標，如實呈現。

article_slug 只看 movie 名是否匹配成功（含別名）——讀者點進去
必須是該站講的那部片的文章，不是同地其他片的文章；與地點是否匹配無關。

用法：python tools/_export_routes.py
"""
import io, os, re, json, time, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_JSON = r'C:\Users\user\WorkBuddy\澳門旅遊攻略\content63.json'
OUT = os.path.join(ROOT, 'data', 'routes.json')

# ── 地名正規化（與 tools/film_collections.py 同步；此處多剝證據等級符號與｜後分店描述）──
_PAREN = re.compile(r'[（(][^）)]*[）)]')
# 尾隨拉丁（英文／葡文名）——含拉丁擴展字符（á õ ç é í…），否則「嘉模斜巷 Calç」剝不掉
_TRAIL_LATIN = re.compile(r'[\s]*[A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F\s\'’\.·\-]*$')
_MARK = re.compile(r'[\s]*[⚠️✅]+[\s]*$')
PLACE_ALIAS = {
    '大三巴': '大三巴牌坊', '大三八': '大三巴牌坊',
    '議事亭廣場': '議事亭前地', '議事亭前地廣場': '議事亭前地',
    '亞美打利庇盧大馬路': '新馬路', '葡京': '葡京酒店',
}


def norm_place(name):
    if not name:
        return ''
    s = str(name).strip()
    s = _MARK.sub('', s)                     # 去尾隨 ⚠️／✅ 證據等級
    s = _PAREN.sub('', s)                    # 去（Senado Square）/（Ruins of St. Paul's）等
    s = re.sub(r'｜[^｜]*$', '', s)           # 去｜後的分店／地址描述
    s = _TRAIL_LATIN.sub('', s)              # 去尾隨拉丁（含 á õ ç é）
    s = re.sub(r'\s+', ' ', s).strip(' ，,、·.')
    return PLACE_ALIAS.get(s, s)


def norm_movie(name):
    s = re.sub(r'[\s《》・·，,。.（）()\-—:：]', '', str(name or ''))
    return s.replace('游', '遊')             # 游龍戲鳳＝遊龍戲鳳（異體字統一）


# ── 人工校正表（2026-10-15 逐站核對）────────────────────────────
# 書站名 → 網站地名。只收確定同指；書比網站全的站（倫敦人／路氹連貫公路…）
# 與全城型站（澳門（全城）…）故意不收，如實呈現為無座標。
STATION_ALIAS = {
    '福隆新街騎樓': '福隆新街',        # 《伊莎貝拉》福隆新街・新華大旅店一帶
    '亞婆井斜巷': '亞婆井前地',        # 《江湖龍虎門》網站無此片；座標用亞婆井前地
    '西望洋聖堂': '西望洋山',          # 主教山小堂在西望洋山上
    '舊廣州大酒店': '舊廣州大酒店',     # norm 去｜後即得（《群龍戲鳳》pedicab-driver-1989）
    '東望洋山': '東望洋山燈塔',         # 《伊莎貝拉》松山燈塔
    '新葡京酒店': '新葡京',            # 《撲克王》篇「新葡京 Grand Lisboa」
    '澳門塔': '澳門旅遊塔',            # 同地異名
    '婆仔屋': '仁慈堂婆仔屋',          # 婆仔屋＝仁慈堂婆仔屋
    '威尼斯人酒店': '澳門威尼斯人',      # 《遊龍戲鳳》篇內無；全局配《驚天魔盜團2》
    '倫敦人酒店': '澳門倫敦人酒店',      # 《驚天魔盜團2》篇內無；全局配《騙騙喜歡你》
    '魔術店': '翁氏魔術專門店',         # Iong's Magic Shop＝翁氏魔術專門店（馬忌士街36號）
    'MGM金殿': '澳門美高梅',           # 《遊龍戲鳳》篇「澳門美高梅・天幕廣場」
    '嘉模聖堂': '嘉模聖母堂',          # 同樓異名（Igreja de Nossa Senhora do Carmo）
    '路環漁村': '路環舊城區',          # 路環市區一帶
    '路環市': '路環舊城區',            # 路環市＝路環舊城區
    '澳門皇宮浮動賭場': '澳門皇宮畫舫',  # 浮動賭場故址＝畫舫原泊位（內港火船頭街）
    '聖方濟各聖堂': '路環聖方濟各堂',    # 韓劇《宮》網站無此片；座標配路環聖方濟各堂
}
MOVIE_ALIAS = {
    '007之金槍人': 'man-with-the-golden-gun',        # The Man with the Golden Gun 台譯＝鐵金剛大戰金槍客
    '奪寶奇兵：魔域奇兵': 'indiana-jones-temple-of-doom',  # 台譯；網站用《奪寶奇兵之魔宮傳奇》
    '憨豆特工': 'johnny-english-reborn-2011',        # 台譯；網站用《憨豆先生大戰特工》
}
# 書有、網站刻意不配座標的站（全城型／書比網站全）：站名 → 留空原因（寫入 routes.json 備註）
NO_GPS_NOTE = {
    '澳門（全城）': '全城型場景，無單一地點',
    '澳門（短片合集）': '短片合集，無單一地點',
    '澳門（70年代賭場）': '全城型場景，無單一地點',
    '澳門（60年代）': '全城型場景，無單一地點',
    '路環咀': '路環最南端；網站未收錄此精確地點',
    '北安碼頭': '網站未收錄此地點',
    '路氹連貫公路': '網站未收錄此道路場景',
    '聖若望修院': '網站未收錄此地點',
}

# ── 事實修正表（2026-10-16 軒哥核可）：源書錯字／偽台詞，導出層修正，不動書源 ──
FACT_FIXES = {
    # 原片名「花樣年華》《2046」畸形（漏了片名號配對）
    '新華大旅店': {'movie': '花樣年華・2046'},
    # 原片名「江湖龍虎門」錯字，應為《江湖龍虎鬥》(1987, Flaming Brothers)；
    # 「出來混的，遲早要還」查無出處（《無間道II》名句變體），且周潤發角色是
    # Cheung Ho-tin 並非「阿勇」→ 偽台詞清空（WebSearch 核實 2026-10-16）
    '亞婆井斜巷': {'movie': '江湖龍虎鬥', 'quote': '', 'quote_author': ''},
    # 「賭俠的傳說，從澳門開始。」係宣傳語非台詞；高進＝賭神＝周潤發飾，
    # 《賭俠》裡周星馳演刀仔 → 張冠李戴，偽台詞清空
    '葡京酒店': {'quote': '', 'quote_author': ''},
    # 「我們出來跑江湖的，遲早要還。」＝《無間道II》「出嚟行，預咗要還」變體（雙源確認），
    # 非《放・逐》台詞 → 換成 Subzin 字幕核實的真對白（01:18:25 "How much is a ton of dreams?"）
    '亞婆井前地': {'quote': '一噸夢想，值多少錢？',
                   'quote_author': '《放・逐》對白（英文字幕回譯）'},
}

# ── 全城型／年代型虛擬站的代表座標（2026-10-16 軒哥拍板「補代表座標」）──
# 這些站無單一實拍地點，給一個中心區代表點，讓步行段可算、未來地圖可釘中心。
# 注意：代表點「只」用於算步行（_eff_gps），不寫入 station 的 gps 字段，
# 因此 n_gps（實地座標統計）不被污染；渲染時標「代表點」以示區別。
REP_GPS = {
    '澳門（全城）': '22.1938,113.5429',       # 議事亭前地
    '澳門（短片合集）': '22.1880,113.5460',   # 南灣
    '澳門（70年代賭場）': '22.1885,113.5500', # 葡京一帶
    '澳門（60年代）': '22.1925,113.5435',     # 崗頂前地
}


def _eff_gps(st):
    """有效座標：實拍 gps 優先（剝「約」等中文與空白，與 merge_and_order._gps_of 一致）；
    無則取代表點；皆無則 (None, False)。回傳 (gps, is_rep)。"""
    g = (st.get('gps') or '').strip()
    if g:
        g = re.sub(r'[^0-9.,\-]', '', g)  # 去「約」等中文／空白，僅留數字與分隔符
        if g:
            return g, False
    rep = REP_GPS.get((st.get('scene') or '').strip())
    if rep:
        return rep, True
    return None, False


def _haversine_m(a, b):
    """a,b = 'lat,lon'（與 routes.json 座標格式一致）；回傳球面距離（公尺）。OSRM 離線備援用。"""
    try:
        alat, alon = [float(x) for x in a.split(',')]
        blat, blon = [float(x) for x in b.split(',')]
    except (ValueError, AttributeError):
        return None
    R = 6371000.0
    p1, p2 = math.radians(alat), math.radians(blat)
    dp = math.radians(blat - alat)
    dl = math.radians(blon - alon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(min(1, math.sqrt(h)))


def _osrm_foot(a, b):
    """a,b = 'lat,lon'（與 routes.json 座標格式一致）；回傳 (dist_m, dur_min) 或 None。
    優先真實路網（OSRM 需 'lon,lat'，內部互換），失敗回 haversine×1.4。"""
    import json as _json, urllib.request as _ur
    time.sleep(0.12)  # 節流，避免觸發 OSRM 公共服務限額
    try:
        alat, alon = [float(x) for x in a.split(',')]
        blat, blon = [float(x) for x in b.split(',')]
    except (ValueError, AttributeError):
        return None
    url = ('https://router.project-osrm.org/route/v1/foot/%s,%s;%s,%s?overview=false'
           % (alon, alat, blon, blat))
    try:
        with _ur.urlopen(url, timeout=12) as r:
            d = _json.load(r)
        if d.get('code') == 'Ok' and d.get('routes'):
            rt = d['routes'][0]
            # 距離用真實路網（可靠）；時間按步行速度推算——OSRM 公共服 duration 偏車速不可靠
            return rt['distance'], rt['distance'] / 59.5  # 5km/h ×1.4 坡道彎道係數 → 約 59.5 m/min
    except Exception:
        pass
    h = _haversine_m(a, b)
    if h is None:
        return None
    return h, h / 59.5  # 5km/h ×1.4 坡道彎道係數 → 約 59.5 m/min


def compute_walks(routes):
    """為每條線算「距上一站步行」並累加總距離／總時間；寫入 station.walk_from_prev 與 route.total_*。
    虛擬全城站經 _eff_gps 取代表點參與計算；跨區（>5km，如路環↔半島）標 cross，不計入可步行總距。
    無座標站本身不標步行；其「下一站」向前回溯到最近的有座標站計算，並標 gap（中間含無座標站）。"""
    CROSS_M = 5000  # 跨區閾值：超過視為不可步行，標「建議搭車」並不計入可步行總距
    for r in routes:
        sts = r['stations']
        tot_m, tot_min, rep_touch, cross = 0.0, 0.0, False, False
        last_gps = None  # 最近一個有有效座標的站序（向前回溯用）
        for j in range(len(sts)):
            st = sts[j]
            ga, ra = _eff_gps(st)
            if not ga:
                st['walk_from_prev'] = None  # 無座標站本身不標步行
                continue
            if last_gps is not None:
                gb, rb = _eff_gps(sts[last_gps])
                res = _osrm_foot(gb, ga)
                if res:
                    dm, dmin = res
                    is_rep = bool(ra or rb)
                    gap = (last_gps != j - 1)  # 中間隔了無座標站
                    if dm > CROSS_M:
                        st['walk_from_prev'] = {'m': int(round(dm)), 'min': int(round(dmin)),
                                                'rep': is_rep, 'cross': True, 'gap': gap}
                        cross = True
                    else:
                        st['walk_from_prev'] = {'m': int(round(dm)), 'min': int(round(dmin)),
                                                'rep': is_rep, 'cross': False, 'gap': gap}
                        tot_m += dm
                        tot_min += dmin
                        if is_rep:
                            rep_touch = True
                else:
                    st['walk_from_prev'] = None
            else:
                st['walk_from_prev'] = None  # 本線第一個有座標的站，無「上一站」
            last_gps = j
        r['total_walk_km'] = round(tot_m / 1000.0, 1)
        r['total_walk_min'] = int(round(tot_min))
        r['walk_rep'] = rep_touch
        r['walk_cross'] = cross


def build_place_index(films):
    """網站地名索引：norm_place -> {gps, films: [{slug, name, year}]}"""
    idx = {}
    for p in films:
        mi = p.get('movieInfo') or {}
        name = re.sub(r'^《|》觀後感$|》$', '', (mi.get('title') or p.get('title') or '')).strip()
        try:
            year = int(p.get('filmYear') or mi.get('year') or 0)
        except (TypeError, ValueError):
            year = 0
        ms = mi.get('macauScenes')
        if isinstance(ms, dict):
            scenes = ms.get('scenes') or []
        elif isinstance(ms, list):
            scenes = ms
        else:
            scenes = []
        for sec in scenes:
            if not isinstance(sec, dict):
                continue
            for pl in (sec.get('places') or []):
                nm = norm_place(pl.get('name'))
                if not nm:
                    continue
                e = idx.setdefault(nm, {'gps': (pl.get('gps') or '').strip(), 'films': []})
                if not e['gps'] and (pl.get('gps') or '').strip():
                    e['gps'] = pl['gps'].strip()
                if all(f['slug'] != p['slug'] for f in e['films']):
                    e['films'].append({'slug': p['slug'], 'name': name, 'year': year})
    return idx


def film_places_of(p):
    """一篇電影的正規化地名清單（保序）。"""
    mi = p.get('movieInfo') or {}
    ms = mi.get('macauScenes')
    if isinstance(ms, dict):
        scenes = ms.get('scenes') or []
    elif isinstance(ms, list):
        scenes = ms
    else:
        scenes = []
    out = []
    for sec in scenes:
        if not isinstance(sec, dict):
            continue
        for pl in (sec.get('places') or []):
            nm = norm_place(pl.get('name'))
            if nm and nm not in out:
                out.append(nm)
    return out


def match_in(keys, scene_norm):
    """在一組地名 key 內匹配站名：相等 > 去『酒店』相等 > 雙向包含 > 前綴（≥3 字）。"""
    if not keys or not scene_norm:
        return ''
    if scene_norm in keys:
        return scene_norm
    bare = re.sub(r'酒店$', '', scene_norm)
    if bare and bare in keys:
        return bare
    cands = [k for k in keys if len(k) >= 3 and (bare in k or k in bare or scene_norm in k)]
    if cands:
        return max(cands, key=len)          # 取最具体的（最长）候选
    pre = [k for k in keys if len(bare) >= 3 and (k.startswith(bare) or bare.startswith(k))]
    if pre:
        return max(pre, key=len)
    return ''


def main():
    book = json.load(io.open(BOOK_JSON, encoding='utf-8'))
    posts = json.load(io.open(os.path.join(ROOT, 'data', 'posts.json'), encoding='utf-8'))['posts']
    films = [p for p in posts if p.get('series') == 'macau-film' and p.get('movieInfo')]

    place_idx = build_place_index(films)
    # movie 名 → 文章（含異體字正規化）
    movie_idx = {}
    for p in films:
        mi = p.get('movieInfo') or {}
        for raw in (mi.get('title'), p.get('title')):
            k = norm_movie(raw)
            if k and k not in movie_idx:
                movie_idx[k] = p

    stations = []
    n_gps = n_art = n_alias = 0
    for i, s in enumerate(book):
        s = dict(s)  # 拷貝，不污染書源
        _fix = FACT_FIXES.get((s.get('scene') or '').strip())
        if _fix:
            s.update(_fix)
        scene = (s.get('scene') or '').strip()
        sn = norm_place(scene)
        gps, article_slug, also, match, cand = '', [], [], '', ''
        # movie 名匹配（含別名／異體字；「花樣年華》《2046」多片站逐部試，取首個命中）
        post = None
        mv_raw = (s.get('movie') or '').strip()
        mv_parts = [x.strip() for x in mv_raw.split('》《')] if '》《' in mv_raw else [mv_raw]
        for part in mv_parts:
            post = movie_idx.get(norm_movie(part))
            if post is None:
                al = MOVIE_ALIAS.get(part)
                if al:
                    post = next((p for p in films if p.get('slug') == al), None)
            if post:
                break
        # 全城型／網站刻意不配座標的站：直接短路，仍保留 movie 深链
        note = NO_GPS_NOTE.get(scene) or NO_GPS_NOTE.get(sn)
        if note:
            match = note
        else:
            in_film_keys = film_places_of(post) if post else []
            # 1) 人工校正表（站名帶括號的先用正規化名再查一次）
            alias = STATION_ALIAS.get(scene) or STATION_ALIAS.get(sn)
            if alias:
                n_alias += 1
                cand = alias if alias in place_idx else ''
                if not cand:
                    cand = match_in(list(place_idx), alias)
                if cand:
                    match = 'alias'
            # 2) 正規化後直接命中（全站或本篇內）
            if not match:
                if sn in place_idx:
                    cand, match = sn, 'exact'
                elif in_film_keys and sn in in_film_keys:
                    cand, match = sn, 'exact'
            # 3) 本篇內模糊
            if not match and in_film_keys:
                cand = match_in(in_film_keys, sn)
                if cand:
                    match = 'in-film'
            # 4) 全站模糊
            if not match:
                cand = match_in(list(place_idx), sn)
                if cand:
                    match = 'fuzzy'
        if cand:
            e = place_idx[cand]
            gps = e['gps']
            if post:
                also = [f for f in e['films'] if f['slug'] != post['slug']]
            else:
                also = list(e['films'])
        # 文章深鏈只認 movie 匹配，與地點匹配與否無關（讀者點進去必須是該站講的那部片）
        if post:
            article_slug = post['slug']
        if gps:
            n_gps += 1
        if article_slug:
            n_art += 1
        body = s.get('body') or []
        if isinstance(body, str):
            body = [body]
        pn = s.get('photo_notes') or []
        if isinstance(pn, str):
            pn = [pn]
        stations.append({
            'no': i + 1,
            'scene': scene,
            'movie': (s.get('movie') or '').strip(),
            'year': s.get('year'),
            'quote': (s.get('quote') or '').strip(),
            'quote_author': (s.get('quote_author') or '').strip(),
            'body': [x.strip() for x in body if x and x.strip()],
            'photo_notes': [x.strip() for x in pn if x and x.strip()],
            'fact': (s.get('fact') or '').strip(),
            'info': s.get('info') or {},
            'route': (s.get('route_final') or s.get('route') or '').strip(),
            'gps': gps,
            'match': match or (NO_GPS_NOTE.get(scene) if not gps else '') or ('網站未收錄此地點' if not gps else ''),
            'article_slug': article_slug,
            'also': also,
        })

    # 路線 = route_final 分組（保留書內順序）
    order, groups = [], {}
    for st in stations:
        groups.setdefault(st['route'], [])
        if st['route'] not in order:
            order.append(st['route'])
        groups[st['route']].append(st)

    ROUTE_META = {
        '路線一・半島中': ('r1-peninsula-central', '半島中區', '王家衛的宿命街區',
                        '半島中區是澳門被拍得最密的舊城心臟。一條福隆新街承載了《花樣年華》的錯過，亞婆井前地被《胭脂扣》與《暗花》借走了舊夢與宿命。從新馬路的街頭宿命，走到亞婆井的黃昏長窗。'),
        '路線二・半島西': ('r2-peninsula-west', '半島西區', '內港漁火與舊城巷戰',
                        '內港一帶是澳門最老的漁人碼頭記憶，也是港片江湖的後巷。《十月初五的月光》的碼頭、《放・逐》的巷戰、媽閣的廟前階——這一線沿著海，走的全是被城市留住的舊時光。'),
        '路線三・半島東': ('r3-peninsula-east', '半島東區', '新口岸的霓虹與身份',
                        '新口岸與外港是澳門「新」的那張臉。賭場飯店的玻璃幕牆、東望洋的燈塔與賽道、深夜的街——霓虹燈下的身份與慾望，都在這一帶取景。'),
        '路線四・路氹金光大道': ('r4-cotai', '路氹金光大道', '賭城動作片的舞台',
                        '跨過橋來到路氹，這裡是澳門最「亮」的一塊。韓國盜寶片、香港懸疑、Netflix、好萊塢都在金光大道留過腳印。入夜後霓虹全開，是拍「賭城動作片」最好的舞台。'),
        '路線五・氹仔舊城': ('r5-taipa', '氹仔舊城', '被電影留下來的生活感',
                        '氹仔舊城是澳門為數不多還留著生活氣的地方。官也街的餅家、嘉模斜巷的舊宅、龍環葡韻的荷花——電影來這裡，拍的不是賭場，是日子。'),
        '路線六・路環': ('r6-coloane', '路環', '澳門的盡頭與慢',
                        '路環是澳門的盡頭。沒有賭場，有海、有聖方濟各聖堂、有安德魯餅店的總店。電影走到這裡都慢下來——《伊莎貝拉》的摩托車、《放・逐》的碼頭，都在這條慢線上。'),
        '路線七・澳門人自己的澳門': ('r7-local-eyes', '澳門人自己的澳門', '本地創作者鏡頭裡的家',
                        '這一線不收外地劇組的眼睛，收澳門人自己拍的澳門：本地短片、獨立製作、紀錄片。他們拍的不再是異域風情，是家。'),
        '路線九・世界眼中的澳門': ('r9-world-eyes', '世界眼中的澳門', '好萊塢與亞洲名導的取景框',
                        '從《奪寶奇兵》到 007，從韓國到好萊塢——世界透過澳門想像東方。這一線看好萊塢與國際名導選中了哪些角度。'),
    }

    # ── 2026-10-16 方案A（軒哥拍板）：同座標並站（一站多片）＋ GPS 最近鄰重排（消折返）──
    import math

    def _gps_of(st):
        return (st.get('gps') or '').replace('約', '').replace(' ', '')

    def _near(a, b):
        """並站近鄰判定：經緯各差 ≤0.00015（≈17m）視為同址。
        兩次獨立查證的座標常有末位微差（如聖方濟各堂 113.5514/113.5515）；
        閾值同時保證相距 ≈33m 的不同景點（大三巴牌坊 vs 戀愛巷）不會誤併。"""
        try:
            ax, ay = [float(x) for x in a.split(',')]
            bx, by = [float(x) for x in b.split(',')]
        except (ValueError, AttributeError):
            return False
        return abs(ax - bx) <= 0.00015 and abs(ay - by) <= 0.00015

    def _dist(a, b):
        try:
            ax, ay = [float(x) for x in a.split(',')]
            bx, by = [float(x) for x in b.split(',')]
        except (ValueError, AttributeError):
            return 9e9
        return math.hypot(ax - bx, (ay - by) * 0.93)  # 澳門緯度經度加權，僅用於比大小

    def merge_and_order(sts):
        # 1) 同 GPS 並站：主站＝組內首個有深鏈者（無則取首個）；其餘片收進 extra_films
        #    （保留片名／年份／深鏈／金句；body 不重複堆疊，書源仍在）
        gps_buckets = []  # [{'rep': gps, 'idx': […]}] 近鄰聚類
        for j, st in enumerate(sts):
            g = _gps_of(st)
            if not g:
                continue
            for b in gps_buckets:
                if _near(b['rep'], g):
                    b['idx'].append(j)
                    break
            else:
                gps_buckets.append({'rep': g, 'idx': [j]})
        skip, merged = set(), []
        for j, st in enumerate(sts):
            if j in skip:
                continue
            g = _gps_of(st)
            grp_idx = next((b['idx'] for b in gps_buckets if g and j in b['idx']), [])
            if len(grp_idx) > 1:
                grp = [sts[x] for x in grp_idx]
                host_src = next((x for x in grp if x.get('article_slug')), grp[0])
                host = dict(host_src)
                host['extra_films'] = [
                    {'scene': x['scene'], 'movie': x['movie'], 'year': x.get('year'),
                     'quote': (x.get('quote') or '').strip(),
                     'quote_author': (x.get('quote_author') or '').strip(),
                     'article_slug': x.get('article_slug', '')}
                    for x in grp if x is not host_src and (x.get('movie') or '').strip()]
                seen = {host.get('article_slug', '')} | {
                    f.get('article_slug', '') for f in host['extra_films'] if f.get('article_slug')}
                also = []
                for x in grp:
                    for f in (x.get('also') or []):
                        if f['slug'] not in seen:
                            also.append(f)
                            seen.add(f['slug'])
                host['also'] = also
                merged.append(host)
                skip.update(grp_idx)
            else:
                merged.append(st)
        # 2) GPS 最近鄰重排：無 GPS 站保持原槽位，有 GPS 站從原首站貪心最近鄰回填
        slots = [j for j, s in enumerate(merged) if _gps_of(s)]
        if len(slots) > 2:
            seq = [slots[0]]
            while len(seq) < len(slots):
                cur = _gps_of(merged[seq[-1]])
                nxt = min((x for x in slots if x not in seq),
                          key=lambda x: _dist(cur, _gps_of(merged[x])))
                seq.append(nxt)
            out = list(merged)
            for slot, src in zip(slots, seq):
                out[slot] = merged[src]
            merged = out
        # 3) 路線內重編站號
        for j, s in enumerate(merged):
            s['no'] = j + 1
        return merged

    for k in groups:
        groups[k] = merge_and_order(groups[k])

    routes = []
    for key in order:
        sts = groups[key]
        slug, region, tag, desc = ROUTE_META.get(key, (re.sub(r'\W', '', key)[:20], key, '', ''))
        routes.append({'key': key, 'slug': slug, 'region': region, 'tag': tag,
                       'desc': desc, 'stations': sts})

    # 步行數據：真實路網（OSRM）算每站「距上一站」＋ 線路總步行（虛擬站取代表點）
    compute_walks(routes)

    data = {
        'meta': {
            'source': '澳門旅遊攻略/content63.json × Seanown.org/data/posts.json',
            'exported': '2026-10-15（2026-10-16 並站重排＋步行導覽）',
            'stations': len(stations),
            'merged_stations': sum(len(r['stations']) for r in routes),
            'with_gps': n_gps,
            'with_article': n_art,
            'alias_used': n_alias,
            'routes': len(routes),
            'total_walk_min': sum(r.get('total_walk_min', 0) for r in routes),
            'total_walk_km': round(sum(r.get('total_walk_km', 0.0) for r in routes), 1),
        },
        'routes': routes,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=1) + '\n')

    print('routes.json 已輸出：%d 條路線 / 書原 %d 站 → 並站後 %d 站'
          % (len(routes), len(stations), sum(len(r['stations']) for r in routes)))
    print('  有 GPS：%d（%.0f%%）｜有文章深链：%d｜人工校正表用上：%d'
          % (n_gps, 100.0 * n_gps / max(len(stations), 1), n_art, n_alias))
    print()
    for r in routes:
        miss = ['%s（%s）' % (s['scene'], s['match']) for s in r['stations'] if not s['gps']]
        print('  %s：%d 站%s' % (r['key'], len(r['stations']),
                                  ('；無座標：%s' % '、'.join(miss)) if miss else ''))
    print()
    for r in routes:
        flag = '（含全城代表點）' if r.get('walk_rep') else ''
        if r.get('walk_cross'):
            flag = '（含跨區段・另計）'
        print('  %s 步行：約 %d 分鐘 / %.1f 公里%s'
              % (r['key'], r.get('total_walk_min', 0), r.get('total_walk_km', 0.0), flag))


if __name__ == '__main__':
    main()

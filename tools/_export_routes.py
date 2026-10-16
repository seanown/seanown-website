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
    # ══ 2026-10-17 路線「一個區塊一條線」全淨化 r4（軒哥拍板全淨化）══
    # r4「路氹金光大道」原混入 4 個「半島」站（全在新口岸/外港/望德堂一帶），
    # 與路氹三度假村形成跨區死跳。全數移回「路線三・半島東」，r4 只剩純路氹 4 站
    #（威尼斯人/倫敦人/新濠天地/路氹連貫公路），成為一條短而順的純路氹線。
    # ① 澳門科學館 GPS(22.1862,113.5571) 外港東海岸 → 半島東
    # ② MGM金殿/澳門美高梅 GPS(22.1856,113.5483) 外港新口岸 → 半島東
    # ③ 嘉樂庇總督大橋 GPS(22.1870,113.5439) 半島橋頭 → 半島東（大橋本就是半島↔路氹分界）
    # ④ 魔術店/翁氏魔術專門店（馬忌士街36號）→ 半島東。
    #    ⚠️ 地理訂正：馬忌士街(Rua de Eduardo Marques)在「望德堂區」，北起西墳馬路、
    #    南至瘋堂斜巷/聖美基街，與仁慈堂婆仔屋隔街相對（近社保基金）——瘋堂斜巷本就屬
    #    路線三・半島東，故魔術店歸半島東，非早先誤判的「半島中（近新馬路）」。
    #    🔴 另查出既有 700m GPS 錯誤：站內座標 22.1912,113.5432 指向新葡京一帶，
    #    真實位置在馬忌士街（約 22.197,113.544，近瘋堂斜巷）。此為《驚天魔盜團2》
    #    文章地點座標錯，於此一併覆寫（見下一條 gps 覆寫）。
    '澳門科學館': {'route': '路線三・外港海濱'},
    'MGM金殿（澳門美高梅）': {'route': '路線三・外港海濱'},
    '嘉樂庇總督大橋': {'route': '路線三・外港海濱'},
    "魔術店（Iong's Magic Shop）": {'gps': '22.1976484,113.5448780',
                                  'route': '路線三・望德堂葡京'},
    '葡京酒店': {'route': '路線三・望德堂葡京'},
    '新葡京酒店': {'route': '路線三・望德堂葡京'},
    '瘋堂斜巷': {'route': '路線三・望德堂葡京'},
    '東望洋燈塔': {'route': '路線三・望德堂葡京'},
    '澳門塔': {'route': '路線三・媽閣西望洋'},
    # ══ 2026-10-17 路線拆分（軒哥拍板：整條線步行總量 ≤90min）══
    # 原「路線三・半島東」10 站 193min 遠超 90min 上限（末端「東望洋→澳門塔」一段就吃 63min），
    # 拆為三條：外港海濱線(60min)／望德堂葡京線(59min)／媽閣西望洋線(39min)。
    # 原「路線一・半島中」8 站 150min 拆為：中區下段(84min)／崗頂龍嵩線(8min)。
    # 原「路線二・半島西」9 站 152min 拆為：內港下環線(29min)／媽閣西望洋線(共用)／司打口上段線(52min)。
    # 聖若望修院→聖若瑟修院：原站名「聖若望」與實際「聖若瑟」（Igreja e Seminário de São José）
    # 名稱不符而抓不到 GPS；Nominatim 實查其位於司打口 22.1917568,113.5373845，屬西區，
    # 併入「路線二B・司打口上段」（距司打口 9min）。
    '福隆新街': {'route': '路線一A・中區下段'},
    '新馬路': {'route': '路線一A・中區下段'},
    '新華大旅店': {'route': '路線一A・中區下段'},
    '戀愛巷': {'route': '路線一A・中區下段'},
    '大三巴牌坊': {'route': '路線一A・中區下段'},
    '崗頂劇院': {'route': '路線一B・崗頂龍嵩'},
    '龍嵩正街': {'route': '路線一B・崗頂龍嵩'},
    '亞婆井前地': {'route': '路線二A・內港下環'},
    '下環街': {'route': '路線二A・內港下環'},
    '光復圍': {'route': '路線二A・內港下環'},
    '媽閣廟': {'route': '路線三・媽閣西望洋'},
    '西望洋聖堂': {'route': '路線三・媽閣西望洋'},
    '司打口': {'route': '路線二B・司打口上段'},
    '舊廣州大酒店': {'route': '路線二B・司打口上段'},
    '蠔里': {'route': '路線二B・司打口上段'},
    '白鴿巢公園': {'route': '路線二B・司打口上段'},
    '聖若望修院': {'gps': '22.1917568,113.5373845',
                'scene': '聖若瑟修院（St. Joseph Seminary）',
                'route': '路線二B・司打口上段'},
    # ── 同地異名站補派（書源用不同寫法，座標與已處理站相同，2026-10-17 拆線時漏掉）──
    '福隆新街騎樓': {'route': '路線一A・中區下段'},
    '亞婆井斜巷': {'route': '路線二A・內港下環'},
    '東望洋山': {'route': '路線三・望德堂葡京'},
    '婆仔屋': {'route': '路線三・望德堂葡京'},
}

# ── 本地補站表（2026-10-17 軒哥拍板「漁人碼頭加入路線」）──
# 書源《跟著電影遊澳門》63 站未收漁人碼頭，但《激戰》(ji-zhan) 篇已有完整場景資料與 GPS，
# 且它與澳門科學館、MGM 美高梅同屬外港／新口岸一片、步行可達（814m+1518m，實測 OSRM），
# 符合「一個區塊一條線」。故在此本地補站（不動書源），欄位格式對齊 content63.json 的站。
LOCAL_STATIONS = [
    {
        'scene': '漁人碼頭・羅馬競技場',
        'movie': '激戰',
        'year': '2013',
        'quote': '',
        'quote_author': '',
        'body': [
            '仿古羅馬圓形競技場，環形石階層層環繞中央擂台。《激戰》把全片最高潮的綜合格鬥放在這裡，燈光聚焦擂台，台下萬眾矚目。',
            '它就在外港海邊，與澳門科學館、MGM 美高梅同一片海濱綠帶，走路十分鐘內可串成一線——白天石造結構光影分明，最宜拍照。',
            '一部電影讓一處仿古建築成了格鬥聖地；但澳門人更常在這裡散步、看海、跑馬拉，這座城把喧騰與平靜放在同一段海岸上。',
        ],
        'photo_notes': ['最佳時段：黃昏或藍調', '構圖：環形石階向上收', '地點：中央擂台', '動作：站上擂台或看海'],
        'fact': '漁人碼頭・羅馬競技場位於澳門外港，環形石階可容數千觀眾，是《激戰》重要取景地。',
        'info': {
            'address': '澳門外港漁人碼頭（勵駿大道）',
            'transport': '外港碼頭步行約 10 分鐘；或由漁人碼頭渡輪',
            'open_time': '全日開放',
            'fee': '免費',
        },
        'route': '路線三・外港海濱',
        'route_final': '路線三・外港海濱',
        'gps': '22.1931,113.5556',
        '_gps_override': '22.1931,113.5556',
    },
]

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

# ── 路線頭站錨點（2026-10-17 軒哥拍板「固定外港三站直覺順序」）──
# 路線三・半島東 的外港三站（漁人碼頭→科學館→美高梅）同屬外港海濱一片、步行可達，
# 但書源首站是東望洋燈塔，純貪心重排會把三站排成「從美高梅倒走回漁人碼頭」，
# 且大橋→美高梅段 39min 偏長。這裡指定該線頭站按直覺順序（漁人碼頭出發順路走），
# 其餘 GPS 站再貪心最近鄰接在後面。值＝「路線名 → 頭站 scene 清單（依序）」。
ROUTE_ANCHORS = {
    '路線三・外港海濱': ['漁人碼頭・羅馬競技場', '澳門科學館', 'MGM金殿（澳門美高梅）'],
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
    # 本地補站併入（不動書源 book）：漁人碼頭等書源未收但路線需要的站。
    # 欄位對齊 content63.json，故下游 movie 匹配／gps／分組／重排流程完全一致。
    book_all = list(book) + [dict(s) for s in LOCAL_STATIONS]
    for i, s in enumerate(book_all):
        s = dict(s)  # 拷貝，不污染書源
        _fix = FACT_FIXES.get((s.get('scene') or '').strip())
        if _fix:
            _fix = dict(_fix)
            # 修正若改路線，必須一併覆蓋 route_final——line 401 導出時「route_final 優先於 route」，
            # 書源 route_final 會蓋過 FACT_FIXES['route']（科學館 2026-10-17 踩過：改 route 無效）。
            if 'route' in _fix and 'route_final' not in _fix:
                _fix['route_final'] = _fix['route']
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
        # FACT_FIXES 若明確提供 gps（如魔術店 700m 誤差覆寫），以修正值優先，
        # 否則會被上面 place_idx 的站內舊座標蓋掉。
        if _fix and _fix.get('gps'):
            gps = _fix['gps']
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
        # ── 2026-10-17 拆分（軒哥拍板整條線步行 ≤90min）：原 r1/r2/r3 三條拆成七條 ──
        '路線一A・中區下段': ('r1a-central-lower', '半島中區（下段）', '福隆新街到大三巴',
                        '從福隆新街的燈籠起步，經新馬路、戀愛巷，一路走到大三巴。這是澳門被拍得最密的舊城心臟——王家衛的宿命、杜琪峯的舊夢，都藏在一條街的轉角裡。'),
        '路線一B・崗頂龍嵩': ('r1b-mong-hau', '崗頂與龍嵩', '教堂與戲院之間',
                        '崗頂一帶是澳門安靜的一面：崗頂劇院、龍嵩正街，遊人不多，節奏很慢。適合想避開人潮、單純走一圈的人。'),
        '路線二A・內港下環': ('r2a-inner-harbour', '內港與下環', '市井與街坊',
                        '亞婆井、下環街、光復圍——這一段是澳門最市井的老城。港片在這裡拍過深夜、拍過失落，游客走過卻常常只是匆匆一瞥。'),
        '路線二B・司打口上段': ('r2b-sendomou', '司打口與上區', '苦力登岸與街角',
                        '司打口是舊碼頭苦力登岸的地方，聖若瑟修院、舊廣州大酒店、蠔里、白鴿巢公園一路向上走。這裡保留著澳門最真實的街區紋理。'),
        '路線三・外港海濱': ('r3a-outer-harbour', '外港海濱', '海邊三站與格鬥聖地',
                        '漁人碼頭、澳門科學館、澳門美高梅——外港海濱這一片，步行十幾分鐘就能串成一線。《激戰》的羅馬競技場、《遊龍戲鳳》的天幕廣場都在這裡，走完剛好一次下午。'),
        '路線三・望德堂葡京': ('r3b-sao-lazaro', '望德堂與葡京', '葡式斜巷與霓虹',
                        '望德堂的馬忌士街、瘋堂斜巷是葡式斜巷最集中的一段；轉個彎就是葡京與新葡京的霓虹。古老與浮華在這裡只隔幾分鐘。'),
        '路線三・媽閣西望洋': ('r3c-maca-tao', '媽閣・西望洋・澳門塔', '廟宇、海與半山',
                        '媽閣的香火、西望洋的斜坡、澳門塔的海景——這一線是澳門最有呼吸感的一段，走到半山回頭，整個海就在腳下。'),
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

    def merge_and_order(sts, anchors=None):
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
        # 2) GPS 最近鄰重排：無 GPS 站保持原槽位，有 GPS 站依序排。
        #    若該路線在 ROUTE_ANCHORS 指定了頭站，頭站按指定順序排在最前，
        #    其餘 GPS 站再從最後一個頭站起貪心最近鄰回填（外港三站直覺順序用）。
        slots = [j for j, s in enumerate(merged) if _gps_of(s)]
        if len(slots) > 2:
            seq = []
            # 先放錨點頭站（依 ROUTE_ANCHORS 指定順序，取其在 merged 中的實際槽位）
            for want in (anchors or []):
                hit = next((j for j in slots if merged[j].get('scene') == want), None)
                if hit is not None and hit not in seq:
                    seq.append(hit)
            # 再從 seq 末站（或原首站）起貪心最近鄰補齊其餘
            while len(seq) < len(slots):
                if seq:
                    cur = _gps_of(merged[seq[-1]])
                else:
                    seq.append(slots[0])
                    continue
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
        groups[k] = merge_and_order(groups[k], ROUTE_ANCHORS.get(k))

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

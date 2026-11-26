#!/usr/bin/env python3
# tools/_geo_guard.py
# 澳門電影專輯 地理座標預檢護欄（細粒度 / 建築級）
#
# 用途：
#   防止場地名稱與 GPS 張冠李戴（如「戀愛·電影館」被釘到永樂戲院座標、
#   「大三巴牌坊」被錯釘到鏡湖馬路/塔石）。對名稱含敏感地標關鍵字的場地，
#   比對其 GPS 是否落在該地標「核證座標」的容差半徑內；超出即標紅。
#
# 雙用：
#   - 命令列：python tools/_geo_guard.py [slug]   全專輯掃描或單篇預檢
#   - 模組：  from _geo_guard import run_guard
#            n = run_guard(posts=posts, verbose=False)  → 回傳違規數（0=全過）
#
# 核證座標來源：Nominatim，2026-10-16 由軒哥糾錯後核實。
import json, math, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "posts.json")


def parse_gps(s):
    if not s or "," not in s:
        return None
    # 支援「約 x, y / x2, y2」雙點（取第一點）
    try:
        first = s.replace("約", "").split("/")[0]
        la, lo = [float(x.strip()) for x in first.split(",")]
        return (la, lo)
    except Exception:
        return None


def dist_m(a, b):
    dlat = (a[0] - b[0]) * 111000.0
    dlon = (a[1] - b[1]) * 111000.0 * math.cos(math.radians(a[0]))
    return math.hypot(dlat, dlon)


# ── 核證座標（建築/巷弄/一帶，容差越細越嚴）──
# 僅收「現有資料中座標緊密聚集」的固定地標；大面積地標（媽閣/內港/亞婆井）
# 因散布 >500m 不收，以免假警報。
LANDMARKS = {
    # ── 核心敏感（已發生過張冠李戴/錯釘，最嚴）──
    "戀愛·電影館": dict(ref=(22.19733, 113.54056), tol=90,  note="戀愛巷9-13，大三巴後"),
    "戀愛電影館":  dict(ref=(22.19733, 113.54056), tol=90,  note="戀愛巷9-13，大三巴後"),
    "永樂戲院":    dict(ref=(22.20198, 113.54264), tol=100, note="大纜巷85D-85F，新橋"),
    "大三巴牌坊":  dict(ref=(22.19746, 113.54086), tol=90,  note="Ruins of St. Paul"),
    # ── 巷弄級 ──
    "戀愛巷":      dict(ref=(22.19733, 113.54056), tol=150, note="Travessa da Paixão"),
    "大纜巷":      dict(ref=(22.20198, 113.54264), tol=140, note="Cinema Alegria 所在巷"),
    "大三巴":      dict(ref=(22.19746, 113.54086), tol=230, note="含 大三巴街/斜巷/一帶"),
    # ── 擴充：緊聚類固定地標（核證 + 現有資料聚類一致）──
    "議事亭前地":  dict(ref=(22.19380, 113.54000), tol=150, note="Senado Square（大廣場，百米內仍屬）"),
    "議事亭":      dict(ref=(22.19380, 113.54000), tol=150, note="Senado Square"),
    "主教座堂":    dict(ref=(22.19348, 113.54154), tol=160, note="大堂/Igreja da Sé"),
    "崗頂":        dict(ref=(22.19227, 113.53816), tol=120, note="崗頂前地/劇院"),
    "聖老楞佐":    dict(ref=(22.19067, 113.53676), tol=140, note="風順堂"),
    "風順堂":      dict(ref=(22.19067, 113.53676), tol=140, note="St. Lawrence"),
    "路環聖方濟各": dict(ref=(22.11690, 113.55150), tol=150, note="Coloane Chapel（勿與大三巴側聖方濟各斜巷混）"),
    "倫敦人":      dict(ref=(22.14580, 113.56560), tol=220, note="Cotai 綜合度假村"),
    "威尼斯人":    dict(ref=(22.14950, 113.56370), tol=500, note="Cotai 巨型綜合度假村（~500m 跨度）"),
    "光復街":      dict(ref=(22.15400, 113.55960), tol=220, note="氹仔舊城區"),
}

# 新橋 堂區 bbox（lat, lon 範圍）—— 名稱含「新橋」但非戲院關鍵字時套用
XINQIAO_BBOX = dict(lat=(22.1985, 22.2050), lon=(113.5385, 113.5445))

# 刻意豁免（作者明知的「一帶」雙點等非錯釘；須註明理由）
EXEMPT = {
    ("macau-is-a-city-2019", "戀愛巷＋大三巴牌坊"):
        "作者刻意『戀愛巷＋大三巴一帶』雙點，非錯釘",
    ("macau-is-a-city-2019", "路環聖方濟各教堂＋黑沙龍爪角海岸徑"):
        "作者刻意『教堂＋黑沙海岸徑』雙點配對，非錯釘",
}


def scenes_of(p):
    mi = p.get("movieInfo", {})
    ms = mi.get("macauScenes")
    if isinstance(ms, dict):
        return ms.get("scenes", [])
    if isinstance(ms, list):
        return ms
    return []


def run_guard(posts=None, only=None, verbose=False):
    """對 macau-film 專輯做地理座標預檢。

    回傳違規（疑似錯置）數量；0 表示全過。
    posts: 文章 dict 清單（可從外部傳入，避免重複讀檔）；None 則自讀 P。
    only:  只查指定 slug（預檢單篇時用）；None 則全專輯。
    verbose: True 時額外印出所有匹配項距離明細（透明度）。
    """
    if posts is None:
        data = json.load(open(P, encoding="utf-8"))
        posts = data["posts"]

    violations, checked = [], 0
    detail = []  # (slug, nm, kw, dist, tol)

    for p in posts:
        if p.get("series") != "macau-film":
            continue
        slug = p.get("slug")
        if only and slug != only:
            continue
        for sc in scenes_of(p):
            for pl in sc.get("places", []):
                nm = pl.get("name", "")
                g = parse_gps(pl.get("gps", ""))
                if not g:
                    continue
                matched = [kw for kw in LANDMARKS if kw in nm]
                if not matched:
                    if "新橋" in nm:
                        inb = (XINQIAO_BBOX["lat"][0] <= g[0] <= XINQIAO_BBOX["lat"][1]
                               and XINQIAO_BBOX["lon"][0] <= g[1] <= XINQIAO_BBOX["lon"][1])
                        checked += 1
                        if not inb:
                            violations.append((slug, nm, pl.get("gps"), None,
                                               "新橋 bbox 外"))
                    continue
                # 取「最寬容」的那條規則：任一匹配關鍵字在容差內即過
                best = None
                for kw in matched:
                    d = dist_m(g, LANDMARKS[kw]["ref"])
                    if best is None or d < best[0]:
                        best = (d, kw)
                checked += 1
                detail.append((slug, nm, best[1], best[0], LANDMARKS[best[1]]["tol"]))
                if (slug, nm) in EXEMPT:
                    continue
                if best[0] > LANDMARKS[best[1]]["tol"]:
                    violations.append((slug, nm, pl.get("gps"), best[0],
                                       "距『%s』核證 %.0fm（容差 %dm）"
                                       % (best[1], best[0], LANDMARKS[best[1]]["tol"])))

    # ── 輸出 ──
    print("地理座標預檢（敏感地標 GPS 容差檢查）：掃描 %d 條" % checked)
    if not violations:
        print("  ✅ 全部通過：無張冠李戴／錯釘。")
    else:
        print("  ❌ 發現 %d 處疑似錯置：" % len(violations))
        for slug, nm, gps, d, why in violations:
            print("    [%s] %s  GPS=%s  → %s" % (slug, nm, gps, why))
        print("  （若屬刻意豁免，請加入 EXEMPT 並註明理由）")

    if verbose and not only:
        print("\n  --- 匹配項距離明細（透明度，依距離降冪）---")
        detail.sort(key=lambda x: -x[3])
        for slug, nm, kw, d, tol in detail:
            mark = "" if d <= tol else "  ⚠超容差"
            print("    [%s] %s →『%s』%.0fm / 容差%dm%s" % (slug, nm, kw, d, tol, mark))

    return len(violations)


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    n = run_guard(only=only, verbose=True)
    sys.exit(1 if n else 0)

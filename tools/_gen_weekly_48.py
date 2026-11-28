#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 tools/weekly-content/2026-11-23.sources.json 產生第 48 期（2026-11-23）週報 body HTML。

體例仿上一期（2026-11-16）：PART 01 總覽＋重點議題＋軒哥視角、PART 02 數據看板、
PART 03 十分類新聞、PART 04 演唱會／在地活動月曆、PART 05 來源與備註。
分析文字均按 2026-11-16～11-22 真實素材撰寫，不編造數字。
"""
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = HERE / "weekly-content" / "2026-11-23.sources.json"
OUT = HERE / "weekly-content" / "2026-11-23.body.html"

d = json.load(open(SRC, encoding="utf-8"))


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def clean(s):
    """清掉【本報訊】等前綴與多餘空白。"""
    s = re.sub(r"^【[^】]*】\s*", "", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_title(s):
    """標題：截斷【本報訊】／【綜合消息】／【特稿】等導語尾巴。

    2026-11-29：抓取端部分標題把內文整段塞進 title（如「大賽車4天11.8萬人次
    入場 【綜合消息】第73屆…」），此處遇到電頭標記即截斷，只留真正標題。
    """
    s = clean(s)
    s = re.split(r"\s*【(?:本報訊|綜合消息|特稿|即時新聞|本報綜合)】", s)[0]
    # 🔴 2026-11-29 軒哥裁定：賽程表是格蘭披治大賽車大項目，保留但濃縮成可讀標題，
    #    不要整串時刻表（原標題 121 字）。取「周五賽事程序」＋首個賽事名。
    if s.startswith("周五賽事程序"):
        m = re.search(r"(澳門格蘭披治電單車|澳門四級方程式大賽|澳門格蘭披治大賽車)", s)
        tail = m.group(1) if m else "重點賽事"
        return f"大賽車周五賽事程序（含{tail}）"
    return s.strip(" ，,。;；")


def items(cat):
    return d["sources"].get(cat, {}).get("items", [])


src_date = lambda it: (it.get("date") or "")[:10].replace("-", ".")[5:]  # MM.DD

# ── 十類關鍵詞分類規則（依標題與摘要）────────────────────────────
CATS = [
    (1, "時政與政府政策", "c1"), (2, "經濟與民生", "c2"), (3, "社會與文化", "c3"),
    (4, "旅遊、大型活動與會展盛事", "c4"), (5, "中葡商貿合作平台", "c5"),
    (6, "中華文化交流合作基地", "c6"), (7, "社團與社區活動", "c7"),
    (8, "大灣區·橫琴", "c8"), (9, "文化娛樂演唱會", "c9"), (10, "全球 AI 領域精選", "c10"),
]

RULES = [
    (8, ["橫琴", "灣區", "琴澳", "深合區", "粵澳", "一窗通", "單牌車", "自貿"]),
    (5, ["中葡", "葡語", "巴西", "葡國", "西語"]),
    (6, ["非遺", "中華文化", "中醫", "中藥", "文化藝術節"]),
    (9, ["演唱會", "音樂節", "音樂會", "影滙", "WORLD TOUR", "舞台", "舞者", "藝術展", "海報展"]),
    # 🔴 2026-11-29：軍團菌／衛局水質通報與六大綜合度假村酒店相關，維持歸類 4（旅遊），不當錯分。
    (4, ["大賽車", "美食節", "旅遊", "旅客", "酒店", "會展", "塔石藝墟", "觀光", "軍團菌", "度假村"]),
    # 🔴 AI 類門檻：只用明確 AI 詞，移除「智慧／數字／科技」等寬泛詞（原誤收油價、個資講座、就業調查）。
    (10, ["人工智能", "生成式AI", "大模型", "AI使用", "AI安全", "具身智能", "AI認證"]),
    # 🔴 2026-11-29 軒哥裁定：澳門涉外，區外政治可講；國家主席外事／APEC 歸時政類（比社會文化類貼切）。
    (1, ["施政", "法案", "立法會", "行政會", "法典", "政府", "岑浩輝", "黃少澤", "司長", "凍薪", "印花稅", "選舉",
         "習近平", "APEC", "亞太經合", "普京", "李在明", "特朗普", "元首級峰會"]),
    # 🔴 统计数据（生產總值／對外貿易／直接投資／私人建築）回歸經濟類，不再落入類 3 預設。
    (2, ["GDP", "經濟", "物價", "零售", "樓價", "租金", "就業", "金融", "中小企", "消費", "外匯", "稅",
         "生產總值", "對外商品貿易", "直接投資", "私人建築", "不動產交易", "人力資源需求"]),
    (7, ["社團", "長者", "兒童", "公益", "健兒", "社區", "同善堂", "托"]),
    (3, ["衛生", "低溫", "醫療", "醫生", "不孕", "減重", "慢性病", "禁煙", "教育", "高校", "巴士", "的士"]),
]

# 🔴 2026-11-29 軒哥裁定（覆蓋同日較早的過緊規則）：澳門本來就涉外、涉區外，
#    以下兩類均恢復收錄，不再剔除：
#    - 賽程表：每年格蘭披治大賽車是大項目，車手、奪冠者、國籍都可講。
#    - 區外政治／國家領導人外事：澳門涉外節點，區外政治當然可以講。
DROP_PATTERNS = []  # 暫無剔除規則；如真有重複／廣告再逐條加。

# 🔴 AI 類白名單：標題本身須含明確 AI 詞才准入；只在摘要命中（如「辦公室AI安全講座」）不算。
AI_TITLE_KW = ["人工智能", "生成式AI", "大模型", "AI使用", "AI安全", "具身智能", "AI認證", "AI"]

def should_drop(title):
    return any(re.search(p, title) for p in DROP_PATTERNS)

def classify(title, summary=""):
    t = title + " " + summary[:80]
    for cid, kws in RULES:
        if cid == 10:
            # AI 類：標題須命中；摘要命中不足以入類
            if any(k in title for k in AI_TITLE_KW):
                return cid
            continue
        if any(k in t for k in kws):
            return cid
    return 3


# 收集所有新聞（正報＋濠江＋力報＋DSEC），去重（標題近似）
seen = set()
news = []
for cat in ["正報", "濠江日報", "力報", "DSEC"]:
    for it in items(cat):
        title = clean_title(it.get("title", ""))
        if not title or title in seen:
            continue
        if should_drop(title):
            continue
        seen.add(title)
        summary = clean(it.get("summary", ""))
        news.append({
            "title": title,
            "summary": summary,
            "source": (it.get("source") or cat) + (" " + src_date(it) if src_date(it) else ""),
            "cat": classify(title, summary),
            "star": "★" if any(k in title for k in ["大賽車", "施政報告", "橫琴", "中葡", "非遺", "GDP"]) else "",
        })

print("新聞總數（去重後）:", len(news))
from collections import Counter
print("分類分布:", sorted(Counter(n["cat"] for n in news).items()))

# ── PART 01 總覽 ─────────────────────────────────────────────
OVERVIEW = (
    "本週澳門進入「施政報告＋大賽車」雙主線的高峰週：行政長官岑浩輝 11 月 16 日在立法會發表《2027 年財政年度施政報告》，"
    "連日來各範疇施政方針辯論密集展開；區外方面，深圳 APEC 領導人非正式會議 11 月 18 至 19 日舉行，"
    "國家主席習近平提出共商亞太合作大計、倡建世界灣區經濟合作聯盟，並先後會見俄羅斯總統普京與韓國總統李在明。"
    "社會面焦點落在立法會 11 月 20 日一般性通過《社團法律制度》法案；民生面，行政法務司司長黃少澤表示力爭今年落實橫琴單牌車北上，"
    "「粵澳社保一窗通」全面覆蓋灣區內地城市。經濟數據方面，統計暨普查局 11 月 20 日一連公佈多項第三季及十月數據："
    "首三季本地生產總值修訂為 3,162.2 億澳門元、實質增長 2.9%；10 月入境旅客 382.3 萬人次、按年升 10.1%；"
    "第三季零售業銷售額 182.9 億元、按年升 9.1%；10 月綜合消費物價指數按年升 1.49%。"
    "盛事面，第 73 屆澳門格蘭披治大賽車 11 月 19 至 22 日舉行，四天累計 11.8 萬人次入場，"
    "中國車手馬青驊在 TCR 世界巡迴賽澳門站次回合奪魁；第 26 屆澳門美食節 11 月 20 日開鑼、一連 17 天。"
)

CHIPS = [
    ("382.3 萬人次", "10 月入境旅客", "按年 +10.1%；首十月 3,600.5 萬 +8.6%"),
    ("3,162.2 億澳門元", "首三季本地生產總值（修訂值）", "實質 +2.9%；第三季 1,060.5 億 +0.1%"),
    ("+1.49%", "10 月綜合消費物價指數", "按月 +0.19%"),
]

HIGHLIGHTS = [
    ("A 組 ★★★ 必看（施政報告／大賽車／橫琴／社團法）",
     "★★★ 《2027 年財政年度施政報告》11 月 16 日發表（力報／新聞局）——提出力爭 GDP 正增長、落實「三五」規劃，"
     "明年六部門重整提升治理效能、公務員連續第三年凍薪、多項惠民措施加碼（增兩歲幼兒托費補助、初期供 50 個跨境養老院舍名額）。"
     "★★★ 第 73 屆格蘭披治大賽車（正報／tourism 局）——四天 11.8 萬人次入場，馬青驊奪 TCR 澳門站次回合冠軍，"
     "車手昨親身體驗澳門非遺，把體育盛事與文化敘事接在一起。★★★ 橫琴單牌車北上力爭今年落實（正報 11-21），"
     "配合「粵澳社保一窗通」覆蓋灣區內地九市、澳門經濟帳本首次計入在琴資產——琴澳一體化由基礎建設走向制度與民生對接。"
     "★★ 立法會一般性通過《社團法律制度》法案（正報／力報 11-20）——社團設立與監管統一由身份證明局主管，後續細則性審議值得關注。"),
    ("B 組 ★★ 經濟與產業（零售／樓市／中醫藥出海／中小企）",
     "★★ 第三季零售業銷售額 182.9 億元、按年 +9.1%，首三季 575.7 億元 +14.3%（DSEC 11-20），消費復甦勢頭延續；"
     "惟第三季住宅樓價指數 183.3、按季 -4.7%，平均租金每平方米 140 澳門元幾無變動，樓市仍處調整。"
     "★★ 澳門助力中藥揚帆出海（力報 11-20）——經澳門進口的海外中藥材、中成藥板塊成為「走出去」試點，"
     "呼應施政報告「中具有醫藥」產業多元方向。★★ 濠江日報連日評論「以大帶小」助力中小企、全面優化特區經濟治理佈局，"
     "冀引導基金與中小企政策落到社區——政策口碑能否轉為訂單，是下一季的觀察點。"),
    ("C 組 ★ 社會文化與區內外形勢",
     "★ 衛生局接獲 1 例軍團菌病例通報（正報 11-23），並呼籲關懷長者病患預防低溫症——入冬後公共衛生的常態提醒。"
     "★ 同善堂百年施藥路、從草根解暑飲到國家級非遺（力報 11-20）——民間慈善與非遺傳承的敘事，正是澳門基層社會的韌性所在。"
     "★ 區外方面，11 月 19 日一連串亞太經貿動態（中韓自貿談判進展、倡建世界灣區合作聯盟）見報，"
     "為澳門「內通外聯」的節點角色提供外部參照。"),
]

PERSPECTIVE = [
    ("澳門社團怎麼看？",
     "本週與社團界最相關的是《社團法律制度》法案 11 月 20 日獲立法會一般性通過，隨後進入常設委員會細則性審議。"
     "新制度把社團設立與監管統一歸口身份證明局，業界關注的合規成本、名稱「過冷河」等細節仍待條文落實——社團宜提前盤點自身章程與申報資料，"
     "避免在細則出爐後手忙腳亂。民生方面，初期提供 50 個跨境養老院舍名額、以輪候長者優先（力報 11-16），"
     "加上衛局呼籲預防低溫症，社團的價值正在於把這些政策翻譯成長者聽得懂、用得到的服務，"
     "並把「院舍名額不足」「跨境醫療銜接」這類基層聲音帶回政策桌上。"
     "政府建議：社會文化司轄下社會工作局可在跨境養老試點擴容前，先委託社團做一次需求與意願普查；"
     "身份證明局在細則審議階段應與社團代表保持溝通，讓合規要求清晰可預期。"),
    ("澳門青年企業家怎麼看？",
     "本週青年創業圈看到兩條線的交會：一是施政報告拋出的「三五」規劃、六部門重整與「以大帶小」中小企政策，"
     "二是橫琴單牌車北上、粵澳社保一窗通覆蓋灣區九市、經濟帳本首次計入在琴資產——制度與數據的打通，"
     "意味著青年企業家在琴澳兩地配置資源的行政成本正在下降。與此同時，第三季零售 +9.1%、十年旅客 +10.1% 的數字固然亮眼，"
     "但住宅樓價按季 -4.7%、公務員連續三年凍薪，提醒創業者擴張仍要留足現金流。"
     "小食攤成交價最高 1.2 萬元（力報 11-19）這類基層創業的熱度，說明小型業態仍有市場，關鍵是把人流轉成可持續的回頭客。"
     "政府建議：經濟財政司轄下經濟及科技發展局可把「引導基金」與中小企政策做成社區可及的申請窗口，"
     "並以橫琴單牌車與一窗通為樣板，公佈具體落地時間表，讓創業者敢於下注。"),
    ("澳門文化旅遊業者怎麼看？",
     "大賽車週是文旅業者的年度大考：四天 11.8 萬人次入場、美食節一連 17 天、塔石藝墟兩個週末接力——"
     "盛事密度已經足夠，問題在於把人流留在澳門、轉成消費。"
     "本週一個值得記下的細節是「車手親身體驗澳門非遺」：把賽車的國際目光接到非遺與在地文化上，"
     "正是「旅遊＋盛事」「旅遊＋美食」跨界融合的具體示範，也是施政報告提出深化的方向。"
     "10 月入境旅客 382.3 萬人次 +10.1%、首十月 3,600.5 萬人次已超疫前，客源基礎穩健；"
     "業者更該做的是把「一次過的觀眾」變成「有場次、可預約、有價格」的產品。"
     "政府建議：文化體育局可統籌把大賽車、美食節與藝墟打包成跨場次的聯票與深度遊路線，"
     "並以數據看板追蹤旅客平均逗留與消費，檢驗「旅遊＋」的實際成效。"),
]

# ── PART 02 數據看板 ──────────────────────────────────────────
DATA_ROWS = [
    ("入境旅客（10 月）", "3,823,243 人次", "按年 +10.1%", "2026 年 10 月", "11-20／統計暨普查局"),
    ("入境旅客（首十月）", "36,004,515 人次", "按年 +8.6%", "2026 年 1–10 月", "11-20／統計暨普查局"),
    ("本地生產總值（修訂值）", "3,162.2 億澳門元", "實質 +2.9%", "2026 年首三季", "11-13／統計暨普查局"),
    ("本地生產總值（第三季）", "1,060.5 億澳門元", "按年 +0.1%", "2026 年第三季", "11-13／統計暨普查局"),
    ("零售業銷售額", "182.9 億澳門元", "按年 +9.1%", "2026 年第三季", "11-20／統計暨普查局"),
    ("消費物價指數", "按年 +1.49%", "按月 +0.19%", "2026 年 10 月", "11-20／統計暨普查局"),
    ("住宅樓價指數", "183.3", "按季 −4.7%", "2026 年第三季", "11-06／統計暨普查局"),
    ("住宅平均租金", "每平方米 140 澳門元", "按季 +0.1%", "2026 年第三季", "11-13／統計暨普查局"),
    ("商舖平均租金", "每平方米 445 澳門元", "按季 −3.3%", "2026 年第三季", "11-13／統計暨普查局"),
    ("樓宇買賣", "1,828 個／60.2 億元", "住宅均價每平方米 60,232 元", "2026 年第三季", "11-20／統計暨普查局"),
    ("會展活動", "363 項", "與會者／觀眾 46.7 萬人次", "2026 年第三季", "11-13／統計暨普查局"),
    ("大賽車入場", "11.8 萬人次", "四天賽事", "11 月 19–22 日", "11-23／正報"),
]

# ── 來源 ─────────────────────────────────────────────────────
SOURCE_ROWS = [
    ("正報", "ok", "14", "列表中 14 則、詳情抓取 14 則"),
    ("濠江日報", "ok", "5", "headline + 澳門欄目共 5 則"),
    ("力報", "ok", "55", "歸檔 API 逐日抓取（視窗 11-16～11-22）"),
    ("DSEC 統計暨普查局", "ok", "26", "Playwright 渲染取得新聞 26 筆"),
    ("旅遊局 whatson", "ok", "63", "本週活動優先選取（原 191 筆）"),
    ("澳門日報", "error", "0", "圖片型電子報，無文字層，需 AI 讀圖；本週未納入"),
]
NOTES = [
    "統計週：2026.11.16 — 2026.11.22；出報日 2026-11-23（第 48 期）。",
    "數據看板全部取自統計暨普查局 11 月 6 日至 20 日公開新聞稿，未自行推算；變動方向按原文標示。",
    "澳門日報為圖片型電子報，本週無文字層可抓取，故其內容未納入分類新聞；讀者可以其官方渠道補閱。",
    "分析文字（總覽、重點議題、軒哥視角）為編者按本週公開素材所作的判斷，非官方立場。",
    "演唱會與在地活動月曆取自旅遊局 whatson，日期以主辦方公佈為準，出發前請再確認。",
]

# ── 渲染 ─────────────────────────────────────────────────────
def news_html(n):
    star = (f'<span style="color:var(--gold);font-weight:700;margin-right:4px">{esc(n["star"])}</span>'
            if n["star"] else "")
    desc = n["summary"] or n["title"]
    if len(desc) > 150:
        desc = desc[:150].rstrip("，、；。 ") + "。"
    return (f'        <div class="news-item"><div class="bullet" style="background:var(--{n["cvar"]})"></div>'
            f'<div class="content"><div class="title">{star}{esc(n["title"])}</div>'
            f'<div class="desc">{esc(desc)}</div>'
            f'<div class="source">{esc(n["source"])}</div></div></div>')

# 🔴 2026-11-29：小結改為「由本類實際收錄條目生成」，不再手寫固定句，
#    杜絕小結談到正文沒有的新聞（如舊版的「心寒影滙／AI人才認證」）。
FALLBACK_SUMMARY = {
    5: "本週中葡平台消息偏少，以葡語高校學生來澳深造等教育交流為主。",
    9: "本週文化娛樂收錄偏少，以在地舞蹈／演藝活動為主。",
    10: "本週無重大 AI 動態。",
}

def make_summary(cid, rows):
    """依實際條目生成小結：點出則數、主要來源與前若干標題焦點，不提未收錄者。"""
    if not rows:
        return FALLBACK_SUMMARY.get(cid, "本週暫無此類收錄。")
    lead = [clean_title(r["title"]) for r in rows[:3]]
    lead = [t for t in lead if t][:3]
    srcs = sorted({r["source"].split()[0] for r in rows if r.get("source")})
    src_txt = "、".join(srcs) if srcs else "多個來源"
    head = "；".join(lead)
    if cid == 9 and shows:
        venues = sorted({s["loc"].split("、")[0] for s in shows if s["loc"] != "—"})
        return (f"本週本類收錄 {len(rows)} 則新聞，另附旅遊局演出活動 {len(shows)} 場，"
                f"場地涵蓋{'、'.join(venues[:6])}。熱門演出包括：{head}。")
    return f"本週本類收錄 {len(rows)} 則，主要見於{src_txt}。焦點包括：{head}。"

# 🔴 2026-11-29：從旅遊局 whatson 抽出「表演」類活動，供第 9 類（演唱會）表格呈現。
#    軒哥指出澳門演唱會密集、六大博企皆是場地，原腳本只把旅遊局素材放 PART04 月曆，
#    第 9 類因此只剩 1 條舞者競賽——此處補上，與技能「演唱會表格」規範一致。
SHOW_KW = ["演唱", "音樂會", "相聲", "FAN-CON", "FANMEETING", "WORLD TOUR", "群星", "音樂節"]
# 溫和活動（嘉年華／派對／藝文）非演唱會演出，排除；「派對」不再作命中詞。
SHOW_EXCLUDE = ["狂歡派對", "藝文派對", "瘋狂派對", "嘉年華"]
shows = []
_seen_show = set()
for it in items("旅遊局"):
    title = clean(it.get("title", ""))
    ex = it.get("extra") or {}
    typ = "、".join(ex.get("types", []) or [])
    if not title or title in _seen_show:
        continue
    # 「表演」類一律收（含陳偉霆瘋狂派對等明星演出）；非表演類才排除溫和活動。
    if "表演" not in typ:
        if any(k in title for k in SHOW_EXCLUDE):
            continue
        if not any(k in title for k in SHOW_KW):
            continue
    _seen_show.add(title)
    shows.append({
        "title": title,
        "show": ex.get("showDate") or "—",
        "loc": "、".join(ex.get("location", []) or []) or "—",
        "typ": typ or "表演",
    })

SUMMARIES = {cid: make_summary(cid, [n for n in news if n["cat"] == cid]) for cid in range(1, 11)}

parts = []
# PART 01
ov = '  <!-- ===== 一、本週總覽 ===== -->\n  <div class="section" id="overview">\n    <div class="section-num">PART 01</div>\n    <h2 class="section-title">本週總覽</h2>\n    <div class="overview">\n      <p>' + esc(OVERVIEW) + '</p>\n    </div>\n    <div class="analysis-byline" style="margin-top:14px">發佈人：翁振軒（軒哥）· 粵港澳大灣區電子商會會長</div>\n      <div class="overview-highlights">\n'
for num, label, desc in CHIPS:
    ov += (f'        <div class="highlight-chip">\n          <div class="num">{esc(num)}</div>\n'
           f'          <div class="label">{esc(label)}</div>\n          <div class="desc">{esc(desc)}</div>\n        </div>\n')
ov += '      </div>\n  </div>\n'
parts.append(ov)

def analysis_section(title, partnum, items_):
    s = f'  <!-- ===== {title} ===== -->\n  <div class="section">\n    <div class="section-num">{partnum}</div>\n    <h2 class="section-title">{esc(title)}</h2>\n'
    for tag, text in items_:
        s += f'      <div class="analysis-item"><span class="analysis-tag">{esc(tag)}</span><p>{esc(text)}</p></div>\n'
    return s + '  </div>\n'

parts.append(analysis_section("軒哥重點議題（自動標星）", "PART 01b", HIGHLIGHTS))
parts.append(analysis_section("軒哥視角｜這些數字，三種人怎麼看", "PART 01c", PERSPECTIVE))

# PART 02
data = '  <!-- ===== 四、一週數據看板 ===== -->\n  <div class="section" id="data">\n    <div class="section-num">PART 02</div>\n    <h2 class="section-title">一週數據看板</h2>\n'
for label, value, change, period, src in DATA_ROWS:
    cls, color = "neu", "var(--c2)"
    if "−" in change or "-" in change or "跌" in change or "降" in change:
        cls, color = "neg", "var(--c6)"
    elif "+" in change or "升" in change or "增" in change:
        cls, color = "pos", "var(--c8)"
    m = re.search(r"([\d.]+)%", value)
    w = min(99, max(6, int(float(m.group(1))))) if m else 55
    data += (f'      <div class="data-card">\n        <div class="label">{esc(label)}</div>\n'
             f'        <div class="value">{esc(value)}</div>\n        <div class="change {cls}">{esc(change)}</div>\n'
             f'        <div class="period">{esc(period)}</div>\n'
             f'        <div class="data-bar"><div class="data-bar-fill" style="width:{w}%;background:{color}"></div></div>\n      </div>\n')
# 🔴 2026-11-29：移除與卡片重複的 12 行表格；卡片已含數值／變動／期間／發布日來源。
data += ('    <p style="font-size:14px;color:var(--ink-2);line-height:1.8;margin-top:12px">'
         '以上指標全部取自統計暨普查局 11 月 6 日至 20 日公開新聞稿及大賽車主辦單位公布，'
         '未自行推算；變動方向按原文標示，卡片右下角為數據期間與發布日／來源。</p>\n  </div>\n')
parts.append(data)

# PART 03
cat = '  <!-- ===== 五、分類新聞彙整 ===== -->\n  <div class="section">\n    <div class="section-num">PART 03</div>\n    <h2 class="section-title">分類新聞彙整</h2>\n'
for cid, ctitle, cvar in CATS:
    rows = [n for n in news if n["cat"] == cid]
    for n in rows:
        n["cvar"] = cvar
    cat += f'    <div class="category" id="cat{cid}">\n      <div class="category-header" style="background:var(--{cvar})">\n        <span class="cat-num">{cid:02d}</span>\n        <span class="cat-title">{esc(ctitle)}</span>\n        <span class="cat-count">{len(rows)} 條</span>\n      </div>\n      <div class="category-body">\n'
    if rows:
        for n in rows[:14]:
            cat += news_html(n) + '\n'
    else:
        cat += (f'        <div class="news-item"><div class="bullet" style="background:var(--{cvar})"></div>'
                f'<div class="content"><div class="title">（本週暫無此類收錄）</div></div></div>\n')
    # 第 9 類追加旅遊局「表演」活動表格（明星／場地／日期／類型）
    if cid == 9 and shows:
        cat += ('        <div style="margin:12px 0 6px;font-size:14px;color:var(--ink-2)">'
                f'以下為旅遊局收錄、統計週內及未來兩週的演出活動（共 {len(shows)} 場），'
                '涵蓋銀河、倫敦人、威尼斯人、新濠影滙等六大綜合度假村場地：</div>\n')
        cat += ('        <div class="overview" style="margin-top:6px"><table class="concert-table">\n'
                '  <thead><tr><th>活動</th><th>日期</th><th>場地</th><th>類型</th></tr></thead>\n  <tbody>\n')
        for s in shows:
            cat += (f'    <tr><td>{esc(s["title"])}</td><td>{esc(s["show"])}</td>'
                    f'<td>{esc(s["loc"])}</td><td>{esc(s["typ"])}</td></tr>\n')
        cat += '  </tbody>\n</table></div>\n'
    cat += (f'        <div class="category-summary" style="border-color:var(--{cvar})">'
            f'<strong>本週小結：</strong>{esc(SUMMARIES[cid])}</div>\n      </div>\n    </div>\n')
cat += '  </div>\n'
parts.append(cat)

# PART 04 月曆
cal = '  <!-- ===== 六、演唱會與在地活動月曆 ===== -->\n  <div class="section">\n    <div class="section-num">PART 04</div>\n    <h2 class="section-title">演唱會與澳門在地活動・整月月曆</h2>\n    <p style="font-size:15.5px;color:var(--ink-2);line-height:1.9;margin:10px 0">以下為旅遊局 whatson 收錄、本週仍可參與或即將登場的活動，日期以主辦方公佈為準。</p>\n'
cal += '    <div class="overview" style="margin-top:14px"><table class="concert-table">\n  <thead><tr><th>活動</th><th>日期</th><th>地點</th><th>類型</th></tr></thead>\n  <tbody>\n'
seen_act = set()
n_act = 0
for it in items("旅遊局"):
    title = clean(it.get("title", ""))
    if not title or title in seen_act:
        continue
    seen_act.add(title)
    ex = it.get("extra") or {}
    show = ex.get("showDate") or ""
    loc = "、".join(ex.get("location", []) or []) or "—"
    typ = "、".join(ex.get("types", []) or []) or "—"
    cal += f'    <tr><td>{esc(title)}</td><td>{esc(show)}</td><td>{esc(loc)}</td><td>{esc(typ)}</td></tr>\n'
    n_act += 1
    if n_act >= 45:
        break
cal += '  </tbody>\n</table></div>\n  </div>\n'
parts.append(cal)

# PART 05
srcs = '  <!-- ===== 七/八、來源與備註 ===== -->\n  <div class="section" id="sources">\n    <div class="section-num">PART 05</div>\n    <h2 class="section-title">來源與備註</h2>\n    <div class="overview"><table class="concert-table">\n  <thead><tr><th>來源</th><th>狀態</th><th>則數</th><th>說明</th></tr></thead>\n  <tbody>\n'
for r in SOURCE_ROWS:
    srcs += '    <tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>\n'
srcs += '  </tbody>\n</table></div>\n    <div class="source-grid" style="margin-top:16px"><div class="source-list"><h4>備註</h4><ul>\n'
for n in NOTES:
    srcs += f'      <li><span class="dot" style="background:var(--c8)"></span><span>{esc(n)}</span></li>\n'
srcs += '    </ul></div></div>\n  </div>\n'
parts.append(srcs)

body = "\n".join(parts)
OUT.write_text(body, encoding="utf-8")
print("✅ 已產出 body:", OUT.relative_to(ROOT))
print("   字數:", len(body), "| 新聞條:", body.count('class="news-item"'),
      "| 分類:", body.count('class="category"'), "| 數據卡:", body.count('class="data-card"'))

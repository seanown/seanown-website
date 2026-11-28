#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正第48期 sources.json 中 5 則濠江日報的標題／摘要錯配。

根因：抓取端誤用 https://hkdaily-api.bpprojects.com/v1/section_news/{id}/html?lang=en
該端點回傳的內文與標題錯位（舊文）；正確路徑為
https://www.houkongdailynews.com/instantNews/{id}（2026-11-29 實測五則全部對應）。
本腳本只修正本期的 sources.json，不改抓取腳本。冪等：可重複執行。
"""
import json
from pathlib import Path

SRC = Path(__file__).resolve().parent / "weekly-content" / "2026-11-23.sources.json"
d = json.load(open(SRC, encoding="utf-8"))

FIX = {
    "161699": (
        "凝聚社會共識確保各項經濟政策落實到位",
        "立法會今日上午9時至晚上9時辯論明年度（2027年）經濟財政領域施政方針，列席會議的經濟財政司司長吳惠嫻引介時表示，2026年是國家「十五五」規劃和澳門特區「三五」規劃的開局之年，澳門總體經濟穩中有進，綜合旅遊休閒業穩步發展，新興產業有序推進，公共財政保持穩健。她表示，特區政府將進一步強化跨範疇協作，持續聽取各界意見，凝聚社會共識，確保各項經濟政策落實到位。",
    ),
    "161701": (
        "全面優化特區經濟治理佈局",
        "立法會辯論明年度（2027年）經濟財政領域施政方針。經濟財政司司長吳惠嫻表示，明年全面優化特區經濟治理佈局，培育壯大新興產業，增強經濟韌性。將圍繞「1+4」多元產業發展方向，堅持有效市場與有為政府相結合，打造更自由、開放和具競爭力的營商環境，並發揮政府引導基金的引領作用，積極物色符合澳門長遠發展所需的項目投資。",
    ),
    "161703": (
        "“以大帶小”助力中小企業發展",
        "經濟財政司司長吳惠嫻表示，中小企業是經濟發展的基石，也是吸納就業、活躍市場的主力軍。明年將圍繞促進消費、拓客引流、品牌打造、宣傳推廣、財務支援等方面，全方位支持中小企業提升競爭力。推動綜合旅遊休閒企業開放供應鏈資源，「以大帶小」助力中小企業發展；增設針對餐飲行業的升級改造資助計劃，研究為合資格中小企業提供商標註冊的財政支援。",
    ),
    "161651": (
        "TCR世界巡迴賽澳門站次回合 中國車手馬青驊奪魁",
        "【即時新聞】澳門東望洋大賽—Kumho國際汽聯TCR世界巡迴賽澳門站次回合上午11時舉行。155號中國車手馬青驊造出2分29秒831最快圈速，首次在東望洋賽道上奪得冠軍；隊友111號瑞典車手比約克居次，105號匈牙利車手米捷利斯第三。196號西班牙車手阿斯哥拿以第10名完賽，奪得生涯第2座TCR世界巡迴賽車手年度冠軍，吉利車隊奪得2026年度車隊總冠軍。",
    ),
    "161704": (
        "優化就業支持體系 前瞻部署青年職涯規劃",
        "經濟財政司司長吳惠嫻表示，明年將主動出擊、前瞻部署，全面優化各項就業政策，着力保障本地居民優先就業。她表示，將加強收集近年畢業青年資料，主動聯繫進行就業配對，並與教育部門合作，將產業前景與職涯規劃觀念導入中學階段。研究推出面向近年畢業青年的就業支援資助計劃，以及資助科技企業增聘本地人才；同時要求大型企業釋出更多職位空缺予本地居民。",
    ),
}

CORRECT_URL = "https://www.houkongdailynews.com/instantNews/{id}"
WRONG_MARK = "hkdaily-api.bpprojects.com"

fixed = 0


def patch(it):
    global fixed
    url = it.get("url") or ""
    for aid, (title, summary) in FIX.items():
        if aid in url:
            assert WRONG_MARK in url, f"Unexpected url form: {url}"
            # 忽略零寬空白與空格數差異（原始標題有雙空格／隱藏字符）
            norm = lambda s: "".join(s.replace("\u200b", "").split())
            assert norm(it["title"]) == norm(title), (
                f"Title mismatch for {aid}: {it['title']!r}"
            )
            it["summary"] = summary
            it["url"] = CORRECT_URL.format(id=aid)
            fixed += 1
            return


# sources 與 all_items 兩處都要改
for it in d["sources"].get("濠江日報", {}).get("items", []):
    patch(it)
for it in d.get("all_items", []):
    patch(it)

# 五則在 sources 各一份、all_items 未必全收 ⇒ 至少 5、至多 10
assert 5 <= fixed <= 10, f"修正筆數異常: {fixed}"
json.dump(d, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"✅ 已修正 {fixed} 處（標題／摘要對應 + 網址改為正確路徑）")
for aid, (title, _) in FIX.items():
    print(f"   {aid}: {title}")

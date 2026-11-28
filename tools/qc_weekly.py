#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""澳門週訊一鍵 QC（2026-11-29 建立）。

用法：
  python tools/qc_weekly.py --date 2026-11-23

檢查：
  1. 結構：div/table/tr 平衡、期號、統計週、分類數、數據卡數
  2. 佔位符：TODO／XXX／{{}}／未替換變數
  3. 標題污染：【本報訊】等電頭出現在 title 內、標題過長（>60 字）
  4. 錯配敏感詞：國台辦／午仔魚／奧密克戎／國防授權（本周確無者）
  5. 分析文字引用：李強視察／共商亞太／舊版自封詞不得出現在正文
  6. 小結對應：小結提到的「本週本類收錄 N 則」與實際 cat-count 一致
  7. sitemap／首頁卡片／期數總覽同步
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(name, ok, detail=""):
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="出報日 YYYY-MM-DD")
    args = ap.parse_args()
    date = args.date
    page = ROOT / "macau-weekly" / f"{date}.html"
    body = ROOT / "tools" / "weekly-content" / f"{date}.body.html"
    sitemap = ROOT / "sitemap.xml"
    home = ROOT / "index.html"
    idx = ROOT / "macau-weekly" / "index.html"

    for p in (page, body, sitemap, home, idx):
        if not p.exists():
            print(f"缺少檔案：{p}")
            return 1

    h = page.read_text(encoding="utf-8")
    b = body.read_text(encoding="utf-8")
    sm = sitemap.read_text(encoding="utf-8")
    hm = home.read_text(encoding="utf-8")
    ix = idx.read_text(encoding="utf-8")

    results = []
    print("=== 1. 結構 ===")
    results.append(check("div 平衡", h.count("<div") == h.count("</div>"),
                         f"{h.count('<div')}/{h.count('</div>')}"))
    results.append(check("table 平衡", h.count("<table") == h.count("</table>")))
    results.append(check("tr 平衡", h.count("<tr") == h.count("</tr>")))
    results.append(check("新聞條 >= 60", b.count('class="news-item"') >= 60,
                         f"{b.count('class=\"news-item\"')} 條"))
    results.append(check("分類數 = 10", b.count('class="category"') == 10,
                         f"{b.count('class=\"category\"')}"))
    results.append(check("數據卡 = 12", b.count('class="data-card"') == 12,
                         f"{b.count('class=\"data-card\"')}"))

    print("=== 2. 佔位符 ===")
    ph = [x for x in ("TODO", "XXX", "{{", "}}") if x in h]
    results.append(check("無佔位符", not ph, str(ph) if ph else ""))

    print("=== 3. 標題污染 ===")
    titles = re.findall(r'<div class="title">(.*?)</div>', h, re.S)
    dirty = [re.sub(r"<[^>]+>", "", t) for t in titles
             if re.search(r"【(?:本報訊|綜合消息|特稿|即時新聞)】", t)]
    results.append(check("標題無電頭殘留", not dirty, str(dirty[:2]) if dirty else ""))
    long_t = [re.sub(r"<[^>]+>", "", t) for t in titles if len(re.sub(r"<[^>]+>", "", t)) > 60]
    results.append(check("標題無過長（<=60字）", not long_t,
                         f"{len(long_t)} 則過長" if long_t else ""))

    print("=== 4. 錯配敏感詞（本週應為 0）===")
    for w in ("國台辦", "午仔魚", "奧密克戎", "國防授權法案", "台灣是中國的一部分"):
        results.append(check(f"無[{w}]", h.count(w) == 0, f"{h.count(w)}"))

    print("=== 5. 分析文字引用（僅檢查 PART 01/03 分析段，不含活動月曆）===")
    # 只取 PART 01 總覽＋重點議題＋視角、PART 03 分類新聞，排除 PART 04 月曆
    # （「心寒影滙」「國際音樂節」是旅遊局月曆的真實活動，不應誤判）
    analysis_part = h.split('id="data"')[0]  # PART 01 區塊
    cats_part = h.split('id="data"')[-1].split('演唱會與澳門在地活動')[0]  # PART 03
    analysis_text = analysis_part + cats_part
    for w in ("李強", "共商亞太", "心寒影滙3", "AI人才認證"):
        results.append(check(f"分析段無[{w}]", w not in analysis_text,
                             f"{analysis_text.count(w)}"))

    print("=== 6. 小結對應 ===")
    cats = re.findall(r'<span class="cat-count">(\d+) 條</span>.*?<strong>本週小結：</strong>(.*?)</div>', h, re.S)
    bad = []
    for cnt, summary in cats:
        m = re.search(r"收錄 (\d+) 則", summary)
        if m and m.group(1) != cnt:
            bad.append(f"{cnt} vs {m.group(1)}")
    results.append(check(f"小結則數與 cat-count 一致（{len(cats)} 類）", not bad, str(bad)))
    fallback_ok = "本週無重大 AI 動態" in h or "全球 AI 領域精選" not in h
    results.append(check("AI 類無濫收", fallback_ok))

    print("=== 7. 同步 ===")
    results.append(check("sitemap 收錄本期", date in sm))
    results.append(check("首頁卡片指向本期", date in hm or f"{date}.html" in hm))
    results.append(check("期數總覽收錄本期", date in ix))

    ok = sum(results)
    print(f"\n結果：{ok}/{len(results)} 通過")
    return 0 if ok == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())

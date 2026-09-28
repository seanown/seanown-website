#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_body_from_json.py — 一鍵化：AI 直接讀 JSON 生成 body 草稿
=============================================================
吃 fetch_sources.py 產出的 `<出報日>.sources.json`，
產出 `<出報日>.body.html`（週報內容片段草稿），
結構與 2026-09-21.body.html 模板完全一致，可直接交給
build_weekly.py 套版。

產出內容（全部由 JSON 實際數據驅動，不編造）：
  1. 本週總覽：3 個 highlight-chip（取自最顯著 DSEC/旅遊局數據）＋ 自動摘要段
  2. 一週數據看板：從 DSEC 摘要正則抽取關鍵指標 → data-card（含安全 SVG 長條圖）
  3. 澳門日報頭條速覽：圖片型電子報，逐版列出整版圖＋AI-READ-IMAGE 標記（頭條由 AI 讀圖補）
  4. 分類新聞：10 個分類，依關鍵字為每則 item 自動歸類 → news-item（跳過澳門日報圖片項）
  5. 來源與備註：由 JSON 的 sources 狀態生成成功/失敗表

敘事段落（overview 摘要 / category-summary / 數據解讀）為「數據衍生種子文字」，
已可用作草稿；檔首標記 `<!-- GEN-DRAFT ... -->` 提示 AI 升級文筆，
並以 WebSearch 補充「演唱會」「全球 AI 精選」兩類（本抓取器來源不含）。

用法：
  python tools/gen_body_from_json.py --week 2026-09-28
  python tools/gen_body_from_json.py --json tools/weekly-content/2026-09-28.sources.json
  python tools/gen_body_from_json.py --week 2026-09-28 --out tools/weekly-content/2026-09-28.body.html
"""

import os
import re
import sys
import json
import argparse
import html
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# 10 個固定分類（id / 標題 / 顏色變數）
CATS = [
    ("1", "時政與政府政策", "c1"),
    ("2", "經濟與民生", "c2"),
    ("3", "社會與文化", "c3"),
    ("4", "旅遊、大型活動與會展盛事", "c4"),
    ("5", "中葡商貿合作平台", "c5"),
    ("6", "中華文化交流合作基地", "c6"),
    ("7", "社團與社區活動", "c7"),
    ("8", "大灣區·橫琴", "c8"),
    ("9", "文化娛樂演唱會", "c9"),
    ("10", "全球 AI 領域精選", "c10"),
]

# 分類關鍵字（按優先順序評分；命中越多分越高）
CAT_KW = {
    "9": ["演唱會", "音樂會", "演出", "歌手", "粉絲見面會", "k-pop", "kpop",
           "concert", "巡迴", "歌迷", "開騷", "音樂節", "演奏會"],
    "5": ["中葡", "葡語", "西語", "葡文", "wto", "mif", "智庫", "論壇",
           "伊比利亞", "葡語國家", "中國與葡"],
    "8": ["橫琴", "深合區", "大灣區", "粵澳", "琴澳", "中山", "深圳", "跨境",
           "珠海", "合作區", "廣東"],
    "6": ["中華文化", "文創", "孔子", "魯澳", "中華", "文物", "琉璃", "非遺",
           "武術", "中醫", "故宮", "敦煌", "書畫", "篆刻", "文化遺產"],
    "4": ["旅遊", "盛事", "煙花", "會展", "節慶", "世遺", "麥麥", "體驗館",
           "嘉年華", "燈飾", "休遊巴士", "打卡", "度假", "酒店業", "活動"],
    "3": ["社會", "治安", "司警", "罪案", "衛生", "醫療", "教育", "學校", "藝術",
           "博物館", "長者", "蚊", "滅蚊", "疾病", "社區", "文化", "展覽"],
    "7": ["社團", "商會", "婦聯", "工聯", "勞工", "會慶", "體育", "運動",
           "協會", "同鄉", "社團法"],
    "1": ["行政長官", "特首", "岑浩輝", "政府", "立法會", "政策", "司長", "部門",
           "公務員", "施政", "會議", "官員", "中聯辦", "行政法務"],
    "2": ["經濟", "博彩", "旅客", "消費", "物價", "失業", "就業", "樓市", "按揭",
           "外匯", "零售", "通脹", "物價指數", "薪酬", "租金", "貿易", "公司",
           "失業率", "入境", "gdp", "cpi", "統計", "匯率", "通關", "海關", "指數"],
    "10": ["ai", "人工智能", "機器人", "大模型", "智能體", "agent", "openai",
            "算力", "演算法", "深度學習", "生成式"],
}


def classify(title, summary):
    """回傳 (cat_id, score)。"""
    text = f"{title} {summary or ''}".lower()
    best, best_score = "2", 0  # 預設經濟民生
    for cid, kws in CAT_KW.items():
        score = sum(2 if kw.lower() in text else 0 for kw in kws)
        if score > best_score:
            best, best_score = cid, score
    return best, best_score


def md(date_str):
    """2026-09-28 -> 9/28；無日期回空。"""
    if not date_str:
        return ""
    try:
        d = datetime.date.fromisoformat(date_str)
        return f"{d.month}/{d.day}"
    except Exception:
        return ""


def esc(s):
    return html.escape(s or "", quote=True)


# ---------- 數據看板：從 DSEC 摘要抽取指標 ----------

def parse_metrics(items):
    """從 DSEC items 的正則抽取關鍵指標，回傳 list[dict]。"""
    out = []
    seen = set()
    pats = [
        # 綜合消費物價指數 按年上升 X%
        (r"綜合消費物價指數[^\d]{0,8}按年上升([\d.]+)%",
         lambda m: ("綜合消費物價指數", f"{m.group(1)}%", "按年", "pos"),
         "cpi"),
        # 本地居民失業率（X%）
        (r"本地居民失業率（?([\d.]+)%）",
         lambda m: ("本地居民失業率", m.group(1), "較上期", "neu"),
         "unemp"),
        # 就業不足率
        (r"就業不足率（?([\d.]+)%）",
         lambda m: ("就業不足率", m.group(1), "較上期", "neu"),
         "underemp"),
        # 入境旅客 N 人次 按年 +Y%
        (r"入境旅客[^\d]{0,6}([\d,]+)人次[^\d]{0,20}按年(上升|下跌|減少)([\d.]+)%",
         lambda m: ("入境旅客", f"{_wan(m.group(1))}", f"按年 {'+' if m.group(2)=='上升' else '-'}{m.group(3)}%",
                    "pos" if m.group(2) == "上升" else "neg"),
         "visitor"),
        # 酒店業客房平均入住率 X%
        (r"客房平均入住率為([\d.]+)%",
         lambda m: ("酒店業入住率", f"{m.group(1)}%", "高位運行", "pos"),
         "hotel"),
        # 零售業銷售額 N 億 按年 +Y%
        (r"零售業銷售額為([\d.]+)億[^\d]{0,20}按年(上升|下跌|增加|減少)([\d.]+)%",
         lambda m: ("零售業銷售額", f"{m.group(1)}億", f"按年 {'+' if m.group(2) in ('上升','增加') else '-'}{m.group(3)}%",
                    "pos" if m.group(2) in ("上升", "增加") else "neg"),
         "retail"),
    ]
    for it in items:
        if it.get("source") != "DSEC":
            continue
        s = it.get("summary") or ""
        d = it.get("date") or ""
        for pat, fn, key in pats:
            m = re.search(pat, s)
            if m and key not in seen:
                label, value, change, direction = fn(m)
                seen.add(key)
                out.append({
                    "label": label, "value": value, "change": change,
                    "period": d, "dir": direction,
                })
    return out


def _wan(s):
    """4478073 -> 447.8萬；1234 -> 1,234。"""
    try:
        n = int(s.replace(",", ""))
    except Exception:
        return s
    if n >= 10000:
        return f"{n/10000:.1f}萬"
    return f"{n:,}"


def bar_width(value):
    """百分比指標給 0–99 寬度；其餘給中性 55。"""
    m = re.search(r"([\d.]+)%", value)
    if m:
        return min(99, max(4, int(float(m.group(1)))))
    return 55


# ---------- 各區塊產生 ----------

def build_overview(items, cat_counts):
    """3 個 highlight-chip + 自動摘要段。"""
    # 取最顯著的 3 則（DSEC 有數字 或 旅遊局活動）作 chip
    chips_src = []
    for it in items:
        s = it.get("summary") or ""
        if it.get("source") == "DSEC" and re.search(r"[\d.]+%", s):
            chips_src.append(it)
        elif it.get("source") == "旅遊局":
            chips_src.append(it)
    chips_src = chips_src[:3]
    if len(chips_src) < 3:  # 不足則補最新 3 則
        for it in items:
            if it not in chips_src:
                chips_src.append(it)
            if len(chips_src) >= 3:
                break

    chips = []
    for it in chips_src:
        s = it.get("summary") or it.get("title") or ""
        m = re.search(r"([\d,]+\.?\d*)\s*(萬|億|%)", s)
        num = m.group(0) if m else "—"
        label = "數據" if it.get("source") == "DSEC" else "活動"
        chips.append(f'''        <div class="highlight-chip">
          <div class="num">{esc(num)}</div>
          <div class="label">{esc(label)}</div>
          <div class="desc">{esc((it.get('title') or '')[:28])}</div>
        </div>''')

    # 自動摘要段
    parts = []
    for cid, ctitle, _ in CATS:
        n = cat_counts.get(cid, 0)
        if n:
            parts.append(f"{ctitle} {n} 則")
    summary = (f"本週共收錄 {len(items)} 則新聞，來源涵蓋"
               + "、".join(parts[:6])
               + "。重點包括統計暨普查局（DSEC）一系列經濟數據發布，"
                 "以及旅遊局多項盛事與活動訊息；"
                 "時政、民生、大灣區與中華文化等議題並陳。"
                 "（此段為數據衍生草稿，請 AI 升級為連貫敘事。）")

    return f'''  <!-- ===== 一、本週總覽 ===== -->
  <div class="section" id="overview">
    <div class="section-num">PART 01</div>
    <h2 class="section-title">本週總覽</h2>
    <div class="overview">
      <p>{esc(summary)}</p>
      <div class="overview-highlights">
{chr(10).join(chips)}
      </div>
    </div>
  </div>
'''


def build_data_board(metrics):
    cards = []
    for m in metrics[:8]:
        cls = {"pos": "pos", "neg": "neg", "neu": "neu"}.get(m["dir"], "neu")
        w = bar_width(m["value"])
        color = {"pos": "var(--c8)", "neg": "var(--c6)", "neu": "var(--c2)"}[m["dir"]]
        cards.append(f'''      <div class="data-card">
        <div class="label">{esc(m['label'])}</div>
        <div class="value">{esc(m['value'])}</div>
        <div class="change {cls}">{esc(m['change'])}</div>
        <div class="period">{esc(m['period'])} · DSEC</div>
        <div class="data-bar"><div class="data-bar-fill" style="width:{w}%;background:{color}"></div></div>
      </div>''')

    # 安全 SVG 長條圖（只畫有百分比的指標，全數落於 viewBox 880 內）
    pct_metrics = [m for m in metrics if re.search(r"\d+%", m["value"])]
    svg = ""
    if pct_metrics:
        n = min(len(pct_metrics), 6)
        h = 40 + n * 46
        rows = []
        y = 30
        for m in pct_metrics[:n]:
            pct = float(re.search(r"([\d.]+)%", m["value"]).group(1))
            w = min(99, max(6, int(pct)))
            fill = "#1A6B52" if m["dir"] == "pos" else ("#A0333E" if m["dir"] == "neg" else "#7A7468")
            rows.append(f'''        <text x="6" y="{y+18}" font-size="13" font-weight="600" fill="#1A1A1A">{esc(m['label'][:10])}</text>
        <rect x="120" y="{y}" width="{w*7}" height="24" rx="3" fill="{fill}"/>
        <text x="{120+w*7+8}" y="{y+18}" font-size="14" font-weight="700" fill="{fill}">{esc(m['value'])}</text>''')
            y += 46
        svg = f'''    <div class="chart-card">
      <h3>本週關鍵指標 <span class="chart-unit">單位：% · DSEC</span></h3>
      <svg viewBox="0 0 880 {h}" role="img" aria-label="本週關鍵指標長條圖">
{chr(10).join(rows)}
      </svg>
    </div>'''
    else:
        svg = "    <!-- AI-POLISH: 本週無百分比指標，可加一張 SVG 圖表 -->\n"

    interpret = ("本週 DSEC 集中發布物價、就業、旅客與零售等宏觀數據，"
                 "具體升降請見上表；此段為種子文字，請 AI 補充「量與質」解讀。"
                 if metrics else
                 "本週抓取來源未含可解析的 DSEC 指標，數據看板待補。")

    return f'''  <!-- ===== 二、一週數據看板 ===== -->
  <div class="section" id="data">
    <div class="section-num">PART 02</div>
    <h2 class="section-title">一週數據看板</h2>

    <div class="data-grid">
{chr(10).join(cards) if cards else '      <!-- AI-POLISH: 待補 data-card（DSEC 指標） -->'}
    </div>

{svg}
    <div class="overview" style="margin-top:12px">
      <h3 style="font-size:17px;font-weight:600;color:var(--brand);margin-bottom:16px">數據解讀</h3>
      <p style="font-size:15px;color:var(--ink-2);margin-top:10px;line-height:1.8">{esc(interpret)}</p>
    </div>
  </div>
'''


def build_macaodaily(items, headlines=None):
    """澳門日報（圖片型電子報）：產生「讀圖」區塊。

    澳門日報每版只有一整張 398×584 圖片（無文字層／高清／PDF）。
    若已有 AI 讀圖產出的 headlines（key = "<date>|<sec>"），直接採用；
    未讀到的版次則列出 AI-READ-IMAGE 標記待補。此為「務必去澳門日報抓」的落地形式。
    """
    headlines = headlines or {}
    md_items = [it for it in items if (it.get("extra") or {}).get("needs_vision")]
    if not md_items:
        return ("  <!-- AI-POLISH: 未抓到澳門日報整版圖"
                "（請確認 fetch_sources.py 的 --md-pages > 0） -->\n")
    md_items.sort(key=lambda x: (x.get("date") or "",
                                 (x.get("extra") or {}).get("sec") or ""))
    rows = []
    pending = 0
    for it in md_items:
        ex = it.get("extra") or {}
        sec = ex.get("sec") or "?"
        date = it.get("date") or ""
        img = ex.get("image") or ""
        d = md(date)
        hl = headlines.get(f"{date}|{sec}")
        if hl:
            title = esc(hl.get("headline") or "（無標題）")
            sub = hl.get("sub") or ""
            desc_html = f'<div class="desc">{esc(sub)}</div>' if sub else ""
            flag = "" if hl.get("verified") else ' · 待核實'
            rows.append(f'''        <div class="news-item"><div class="bullet" style="background:var(--c1)"></div><div class="content"><div class="title">{title}<span style="color:var(--c6);font-size:12px;font-weight:400">{flag}</span></div>{desc_html}<div class="source">澳門日報 · {d} · {esc(sec)}版</div></div></div>''')
        else:
            pending += 1
            rows.append(f'''        <!-- AI-READ-IMAGE: {esc(img)} | 澳門日報 {date} {sec}版 | 本版約 {ex.get('articles')} 篇 -->
        <div class="news-item"><div class="bullet" style="background:var(--c1)"></div><div class="content"><div class="title">［待 AI 讀圖］澳門日報 {d} {sec}版 頭條</div><div class="desc">版次 {esc(sec)}｜本版約 {ex.get('articles')} 篇。整版圖：{esc(img)}</div><div class="source">澳門日報 · {d} · 圖片型電子報</div></div></div>''')
    n_days = len(set(it.get("date") for it in md_items))
    read_n = len(rows) - pending
    return f'''  <!-- ===== 澳門日報（圖片型電子報） ===== -->
  <div class="section" id="macaodaily">
    <div class="section-num">PART 03</div>
    <h2 class="section-title">澳門日報頭條速覽</h2>
    <div class="category" id="cat-md">
      <div class="category-header" style="background:var(--c1)">
        <span class="cat-num">MD</span>
        <span class="cat-title">澳門日報（各版頭條）</span>
        <span class="cat-count">{len(md_items)} 版</span>
      </div>
      <div class="category-body">
{chr(10).join(rows)}
        <div class="category-summary" style="border-color:var(--c1)">
          <strong>讀圖說明：</strong>澳門日報為圖片型電子報（每版一整張 398×584 圖），
          頭條由 AI 讀圖抽出（{n_days} 天 · 已讀 {read_n} 版／待讀 {pending} 版）；
          原圖解析度低，個別字元可能有辨識誤差，標「待核實」者請人工確認。
          內文因解析度不足不可讀（該站無文字層／無高清圖／無 PDF）；可用 <code>--md-pages N</code> 加大每日版次。
        </div>
      </div>
    </div>
  </div>
'''


def build_categories(items):
    # 歸類（跳過澳門日報圖片項：無文字，改由 build_macaodaily 讀圖處理）
    buckets = {cid: [] for cid, _, _ in CATS}
    for it in items:
        if (it.get("extra") or {}).get("needs_vision"):
            continue
        cid, _ = classify(it.get("title", ""), it.get("summary"))
        buckets[cid].append(it)

    blocks = []
    for cid, ctitle, cvar in CATS:
        lst = buckets.get(cid, [])
        n = len(lst)
        body = []
        for it in lst:
            title = esc(it.get("title") or "（無標題）")
            summ = it.get("summary")
            desc = f'<div class="desc">{esc(summ)}</div>' if summ else ""
            src = it.get("source") or "—"
            d = md(it.get("date"))
            src_line = f"{esc(src)} · {d}" if d else esc(src)
            body.append(f'''        <div class="news-item"><div class="bullet" style="background:var(--{cvar})"></div><div class="content"><div class="title">{title}</div>{desc}<div class="source">{src_line}</div></div></div>''')
        if not body:
            body.append(f'''        <div class="news-item"><div class="bullet" style="background:var(--{cvar})"></div><div class="content"><div class="title">（本週抓取來源未含此類）</div><div class="desc">請以 WebSearch 補充「{esc(ctitle)}」相關新聞（演唱會／AI 精選等來源不在自動抓取範圍）。</div></div></div>''')
        summary_txt = (f"本週收錄 {n} 則相關新聞。"
                       + (f"涵蓋「{(lst[0].get('title') or '')[:24]}」等。" if lst else "")
                       + "（此為種子文字，請 AI 升級為本週小結。）")
        block = f'''    <!-- Cat {cid}: {ctitle} -->
    <div class="category" id="cat{cid}">
      <div class="category-header" style="background:var(--{cvar})">
        <span class="cat-num">{cid.zfill(2)}</span>
        <span class="cat-title">{esc(ctitle)}</span>
        <span class="cat-count">{n} 條</span>
      </div>
      <div class="category-body">
{chr(10).join(body)}
        <div class="category-summary" style="border-color:var(--{cvar})">
          <strong>本週小結：</strong>{esc(summary_txt)}
        </div>
      </div>
    </div>'''
        blocks.append(block)

    return f'''  <!-- ===== 四、分類新聞 ===== -->
  <div class="section">
    <div class="section-num">PART 04</div>
    <h2 class="section-title">分類新聞彙整</h2>

{chr(10).join(blocks)}
  </div>
'''


def build_sources(sources):
    ok, fail = [], []
    for name, s in sources.items():
        if s.get("status") == "ok":
            ok.append(f"<li><span class=\"dot\" style=\"background:var(--c8)\"></span><span>{esc(name)}：{s.get('count')} 則（{esc(s.get('note',''))}）。</span></li>")
        elif s.get("status") == "partial":
            fail.append(f"<li><span class=\"dot\" style=\"background:var(--c6)\"></span><span>{esc(name)}：部分成功（{esc(s.get('note',''))}）。</span></li>")
        else:
            fail.append(f"<li><span class=\"dot\" style=\"background:var(--c6)\"></span><span>{esc(name)}：失敗（{esc(s.get('note',''))}）。</span></li>")

    rows = []
    for name, s in sources.items():
        st = {"ok": "✅ 成功", "partial": "⚠️ 部分成功", "error": "❌ 失敗"}.get(s.get("status"), "·")
        weeks = 0 if s.get("status") == "ok" else 1
        rows.append(f"<tr><td>{esc(name)}</td><td>{st}</td><td>{weeks}</td></tr>")

    return f'''  <!-- ===== 五、來源與備註 ===== -->
  <div class="section" id="sources">
    <div class="section-num">PART 05</div>
    <h2 class="section-title">來源與備註</h2>

    <div class="source-grid">
      <div class="source-list">
        <h4>✅ 成功來源</h4>
        <ul>
{chr(10).join(ok) if ok else '          <li><span class="dot" style="background:var(--c8)"></span><span>無</span></li>'}
        </ul>
      </div>
      <div class="source-list">
        <h4>⚠️ 失敗或部分失敗來源</h4>
        <ul>
{chr(10).join(fail) if fail else '          <li><span class="dot" style="background:var(--c8)"></span><span>無</span></li>'}
        </ul>
      </div>
    </div>

    <div class="overview" style="margin-top:16px">
      <h3 style="font-size:17px;font-weight:600;color:var(--brand);margin-bottom:14px">來源健康摘要</h3>
      <table class="concert-table">
        <thead><tr><th>來源</th><th>本週狀態</th><th>連續失敗週數</th></tr></thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
      <p style="font-size:14.5px;color:var(--ink-2);margin-top:14px;line-height:1.8">
        <strong>備註：</strong>本草稿由 <code>gen_body_from_json.py</code> 自動產生，數據全部來自抓取 JSON，未編造。
        澳門日報為圖片型電子報，已下載整版圖並見「澳門日報頭條速覽」區塊，頭條需 AI 讀圖補入（內文不可讀）；
        演唱會與全球 AI 精選兩類請以 WebSearch 補充。
      </p>
    </div>
  </div>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="出報日(週一) YYYY-MM-DD，對應 <出報日>.sources.json")
    ap.add_argument("--json", help="直接指定 sources.json 路徑")
    ap.add_argument("--out", help="輸出 body.html 路徑")
    args = ap.parse_args()

    if args.json:
        jpath = args.json
    else:
        issue = args.week or datetime.date.today().isoformat()
        jpath = os.path.join(HERE, "weekly-content", f"{issue}.sources.json")
    if not os.path.exists(jpath):
        print(f"❌ 找不到 {jpath}（請先跑 fetch_sources.py）")
        return 1

    with open(jpath, encoding="utf-8") as f:
        data = json.load(f)

    issue = args.week or os.path.splitext(os.path.basename(jpath))[0]

    # 澳門日報讀圖頭條（AI 讀圖後寫入 <issue>.macaodaily.json，key 為 "<date>|<sec>"）
    md_h_path = os.path.join(HERE, "weekly-content", f"{issue}.macaodaily.json")
    md_headlines = {}
    if os.path.exists(md_h_path):
        try:
            with open(md_h_path, encoding="utf-8") as f:
                md_headlines = json.load(f).get("headlines", {})
        except Exception:
            md_headlines = {}

    items = data.get("all_items", [])
    sources = data.get("sources", {})

    # 分類計數
    cat_counts = {}
    for it in items:
        cid, _ = classify(it.get("title", ""), it.get("summary"))
        cat_counts[cid] = cat_counts.get(cid, 0) + 1

    metrics = parse_metrics(items)

    body = (
        "<!-- GEN-DRAFT by gen_body_from_json.py · "
        "AI 請升級 overview/category-summary/數據解讀 三段敘事，並以 WebSearch 補充 演唱會/AI 精選；"
        "澳門日報區塊需逐張讀圖（AI-READ-IMAGE 標記）補入頭條 -->\n"
        + build_overview(items, cat_counts)
        + build_data_board(metrics)
        + build_macaodaily(items, md_headlines)
        + build_categories(items)
        + build_sources(sources)
    )

    if args.out:
        out_path = args.out
    else:
        out_path = os.path.join(HERE, "weekly-content", f"{issue}.body.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(body)

    print(f"✅ 已產出 body 草稿：{out_path}")
    print(f"   新聞 {len(items)} 則 → 分類：", {c: cat_counts.get(c, 0) for c, _, _ in CATS})
    print(f"   DSEC 指標卡 {len(metrics)} 張")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_to_weekly_body.py — 把 macau-news-digest skill 產出的 Markdown 週報
轉成 build_weekly.py 所需的「內容片段 HTML」（沿用既有 shell CSS 類別）。

輸出結構對應既有版式：
  PART 01 總覽     → <section id="overview">  （本週總覽 + 軒哥重點議題 + 軒哥視角）
  PART 02 數據看板 → <section id="data">      （一週數據看板：data-card 網格 + 表格）
  PART 03 分類     → <section> 內 10 個 <div class="category" id="catN">
  PART 04 演唱會月曆 → <section>              （concert-table）
  PART 05 來源     → <section id="sources">   （source-grid + 表格 + 備註）

用法：
  python md_to_weekly_body.py --md outputs/macau-weekly-2026-11-02.md \
      --out outputs/2026-11-02.body.html
"""
import argparse
import html
import pathlib
import re

# 10 個固定分類（id / 標題 / 顏色變數，與 build_weekly.py / gen_body_from_json.py 一致）
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


def esc(s):
    return html.escape(s or "", quote=True)


def is_sep(ln):
    """判斷是否為 markdown 分隔線（--- / *** / ___）。"""
    return bool(re.match(r"^[-*_]{3,}\s*$", ln.strip()))


def md_inline(s):
    """行內 markdown：保留 **粗體** → <strong>，移除多餘星號標記，其餘原樣轉義。"""
    s = s.replace("**", "\x00")  # 暫存粗體標記
    parts = s.split("\x00")
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            out.append(f"<strong>{esc(p)}</strong>")
        else:
            out.append(esc(p))
    return "".join(out)


def parse_table(lines):
    """Markdown 表格 → <table class="concert-table">（含 thead/tbody）。"""
    rows = [l for l in lines if l.strip().startswith("|")]
    if len(rows) < 3:
        return ""
    head = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    body_rows = []
    for r in rows[2:]:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if any(cells):
            body_rows.append(cells)
    thead = "<tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr>"
    tbody = ""
    for cells in body_rows:
        # 長度不齊時以 head 長度補齊
        cells = (cells + [""] * len(head))[: len(head)]
        tbody += "<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in cells) + "</tr>"
    return (
        '<table class="concert-table">\n'
        f"  <thead>{thead}</thead>\n"
        f"  <tbody>{tbody}</tbody>\n"
        "</table>"
    )


def parse_news_items(lines):
    """把分類內的 '- ' 項目轉成 news-item HTML 清單。"""
    items = []
    for ln in lines:
        m = re.match(r"^\s*-\s+(.*)$", ln)
        if not m:
            continue
        text = m.group(1).strip()
        # 星級
        stars = ""
        sm = re.match(r"^(★+)\s*", text)
        if sm:
            stars = sm.group(1)
            text = text[sm.end():]
        # 標題：**title** 或 至首個（
        title = None
        tm = re.match(r"\*\*(.+?)\*\*", text)
        if tm:
            title = tm.group(1)
            rest = text[tm.end():]
        else:
            pm = re.match(r"([^（]+)（", text)
            if pm:
                title = pm.group(1).strip()
                rest = text[pm.end() - 1:]  # 含（
            else:
                rest = text
        # 來源：（...）
        source = ""
        if title is not None:
            sm2 = re.search(r"（([^）]+)）", rest)
        else:
            sm2 = re.search(r"（([^）]+)）", text)
        if sm2:
            source = sm2.group(1)
        # 描述：去掉來源括號後，以 ：或 : 切
        desc_src = sm2.group(0) if sm2 else ""
        body = (rest if title is not None else text)
        body = body.replace(desc_src, "", 1) if desc_src else body
        # 去頭尾冒號
        body = re.sub(r"^[\s：:]+", "", body)
        # 星級標題
        star_html = f'<span style="color:var(--gold);font-weight:700;margin-right:4px">{esc(stars)}</span>' if stars else ""
        title_html = f'<div class="title">{star_html}{esc(title) if title else esc(body[:40])}</div>' if title else ""
        desc_html = f'<div class="desc">{md_inline(body)}</div>' if body else ""
        src_html = f'<div class="source">{esc(source)}</div>' if source else ""
        if not title:
            # 無標題時整段做 desc
            desc_html = f'<div class="desc">{md_inline(body)}</div>'
            title_html = ""
        items.append(
            f'        <div class="news-item"><div class="bullet" style="background:var(--{CAT_COLOR})"></div>'
            f'<div class="content">{title_html}{desc_html}{src_html}</div></div>'
        )
    return items


CAT_COLOR = "c2"  # 預設；迴圈內會覆寫


def build_overview(sec_lines, chips=None):
    """本週總覽 + 軒哥重點議題 + 軒哥視角。chips = 首頁同步用的 3 個 highlight-chip。"""
    # 切出三塊：總覽段 / 重點議題（## 二） / 軒哥視角（## 三）已在外部拆好，此處只處理「一」
    out = ['  <!-- ===== 一、本週總覽 ===== -->',
           '  <div class="section" id="overview">',
           '    <div class="section-num">PART 01</div>',
           '    <h2 class="section-title">本週總覽</h2>',
           '    <div class="overview">']
    para = []
    byline = ""
    for ln in sec_lines:
        if ln.strip().startswith(">") or ln.strip().startswith("**發佈人"):
            byline = re.sub(r"[*>]", "", ln).strip()
            continue
        if ln.strip().startswith("#"):
            continue
        if is_sep(ln):
            continue
        if ln.strip():
            para.append(ln.strip())
    if para:
        out.append(f'      <p>{md_inline(" ".join(para))}</p>')
    out.append("    </div>")
    if byline:
        out.append(f'    <div class="analysis-byline" style="margin-top:14px">{esc(byline)}</div>')
    # 3 個 highlight-chip（供首頁週訊卡片同步）
    if chips:
        chip_html = "\n".join(
            f'        <div class="highlight-chip">\n'
            f'          <div class="num">{esc(c["num"])}</div>\n'
            f'          <div class="label">{esc(c["label"])}</div>\n'
            f'          <div class="desc">{esc(c["desc"])}</div>\n'
            f'        </div>' for c in chips
        )
        out.append('      <div class="overview-highlights">\n' + chip_html + "\n      </div>")
    out.append("  </div>\n")
    return "\n".join(out)


def build_highlights(sec_lines):
    """## 二 軒哥重點議題。"""
    out = ['  <!-- ===== 二、軒哥重點議題 ===== -->',
           '  <div class="section">',
           '    <div class="section-num">PART 01b</div>',
           '    <h2 class="section-title">軒哥重點議題（自動標星）</h2>',
           '    <div class="overview">']
    cur_tag = None
    buf = []
    for ln in sec_lines:
        gm = re.match(r"^\s*\*\*(.+?)\*\*\s*$", ln.strip())
        if gm and ("組" in gm.group(1) or "必看" in gm.group(1) or "相關" in gm.group(1) or "參考" in gm.group(1)):
            if cur_tag is not None:
                out.append(f'      <div class="analysis-item"><span class="analysis-tag">{esc(cur_tag)}</span><p>{"<br>".join(md_inline(b) for b in buf)}</p></div>')
            cur_tag = gm.group(1)
            buf = []
            continue
        if ln.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
            buf.append(re.sub(r"^\d+\.\s*", "", ln.strip()))
        elif ln.strip() and cur_tag is None and not is_sep(ln):
            # 段落說明
            buf.append(ln.strip())
    if cur_tag is not None and buf:
        out.append(f'      <div class="analysis-item"><span class="analysis-tag">{esc(cur_tag)}</span><p>{"<br>".join(md_inline(b) for b in buf)}</p></div>')
    out.append("    </div>\n  </div>\n")
    return "\n".join(out)


def build_perspective(sec_lines):
    """## 三 軒哥視角（三段分析）。"""
    out = ['  <!-- ===== 三、軒哥視角 ===== -->',
           '  <div class="section">',
           '    <div class="section-num">PART 01c</div>',
           '    <h2 class="section-title">軒哥視角｜這些數字，三種人怎麼看</h2>',
           '    <div class="overview-analysis">']
    tag = None
    buf = []
    for ln in sec_lines:
        gm = re.match(r"^\s*\*\*(.+?)\*\*\s*$", ln.strip())
        if gm and ("怎麼看" in gm.group(1) or "視角" in gm.group(1)):
            if tag is not None:
                out.append(f'      <div class="analysis-item"><span class="analysis-tag">{esc(tag)}</span><p>{md_inline(" ".join(buf))}</p></div>')
            tag = gm.group(1)
            buf = []
            continue
        if ln.strip() and tag is not None and not ln.strip().startswith("#") and not is_sep(ln):
            buf.append(ln.strip())
    if tag is not None and buf:
        out.append(f'      <div class="analysis-item"><span class="analysis-tag">{esc(tag)}</span><p>{md_inline(" ".join(buf))}</p></div>')
    out.append("    </div>\n  </div>\n")
    return "\n".join(out)


def build_data_board(sec_lines):
    """## 四 一週數據看板 → data-card 網格 + 表格。回傳 (html, chips)。"""
    out = ['  <!-- ===== 四、一週數據看板 ===== -->',
           '  <div class="section" id="data">',
           '    <div class="section-num">PART 02</div>',
           '    <h2 class="section-title">一週數據看板</h2>']
    # 解析表格
    tbl_lines = [l for l in sec_lines if l.strip().startswith("|")]
    cards = []
    chips_raw = []
    if tbl_lines:
        rows = [l for l in tbl_lines if l.strip().startswith("|")]
        for r in rows[2:]:
            cells = [c.strip() for c in r.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            label, value = cells[0], cells[1]
            change = cells[2] if len(cells) > 2 else ""
            period = cells[3] if len(cells) > 3 else ""
            # 方向
            cls = "neu"
            color = "var(--c2)"
            if re.search(r"[-−](\d|Inf)", change) or "跌" in change or "降" in change or "減少" in change:
                cls, color = "neg", "var(--c6)"
            elif "+" in change or "升" in change or "增" in change or "漲" in change:
                cls, color = "pos", "var(--c8)"
            w = 55
            m = re.search(r"([\d.]+)%", value)
            if m:
                w = min(99, max(6, int(float(m.group(1)))))
            cards.append(
                f'      <div class="data-card">\n'
                f'        <div class="label">{esc(label)}</div>\n'
                f'        <div class="value">{esc(value)}</div>\n'
                f'        <div class="change {cls}">{esc(change)}</div>\n'
                f'        <div class="period">{esc(period)}</div>\n'
                f'        <div class="data-bar"><div class="data-bar-fill" style="width:{w}%;background:{color}"></div></div>\n'
                f'      </div>'
            )
            chips_raw.append({"label": label, "value": value, "change": change})
    # 選 3 個首頁 chip：優先 賭收 / GDP / 旅客，否則取前 3
    prio = ["博彩", "GDP", "旅客", "失業", "物價", "入住", "貿易", "支付"]
    ranked = sorted(chips_raw, key=lambda c: min((prio.index(k) for k in prio if k in c["label"]), default=99))
    picks = ranked[:3]
    chips = []
    for c in picks:
        chips.append({"num": c["value"], "label": c["label"], "desc": c["change"]})
    if cards:
        out.append('    <div class="data-grid">\n' + "\n".join(cards) + "\n    </div>")
    # 表格本體
    t = parse_table(tbl_lines)
    if t:
        out.append('    <div class="overview" style="margin-top:16px">' + t + "</div>")
    # 註
    for ln in sec_lines:
        if ln.strip().startswith("註："):
            out.append(f'    <p style="font-size:14.5px;color:var(--ink-3);margin-top:12px;line-height:1.8">{esc(ln.strip()[2:].strip())}</p>')
    out.append("  </div>\n")
    return "\n".join(out), chips


def build_categories(sec_lines):
    """## 五 分類新聞彙整 → 10 個 category 區塊。"""
    out = ['  <!-- ===== 五、分類新聞彙整 ===== -->',
           '  <div class="section">',
           '    <div class="section-num">PART 03</div>',
           '    <h2 class="section-title">分類新聞彙整</h2>']
    # 切子標題
    blocks = {}
    order = []
    cur = None
    buf = []
    for ln in sec_lines:
        m = re.match(r"^###\s*(\d+)\.\s*(.+?)\s*$", ln)
        if m:
            if cur is not None:
                blocks[cur] = buf
            cur = m.group(1)
            order.append(cur)
            buf = []
        elif ln.strip():
            buf.append(ln)
    if cur is not None:
        blocks[cur] = buf

    cat_map = {cid: ctitle for cid, ctitle, _ in CATS}
    for cid, cvar in [(c[0], c[2]) for c in CATS]:
        global CAT_COLOR
        CAT_COLOR = cvar
        lines = blocks.get(cid, [])
        body = parse_news_items(lines)
        # 本週小結
        summary = ""
        for ln in lines:
            sm = re.search(r"\*\*本週小結\*\*[：:]\s*(.*)", ln)
            if sm:
                summary = sm.group(1).strip()
        if not body:
            body = [f'        <div class="news-item"><div class="bullet" style="background:var(--{cvar})"></div>'
                    f'<div class="content"><div class="title">（本週暫無此類收錄）</div></div></div>']
        sum_html = f'        <div class="category-summary" style="border-color:var(--{cvar})"><strong>本週小結：</strong>{md_inline(summary)}</div>' if summary else ""
        n = len([b for b in body if "news-item" in b])
        out.append(
            f'    <!-- Cat {cid}: {cat_map.get(cid, "")} -->\n'
            f'    <div class="category" id="cat{cid}">\n'
            f'      <div class="category-header" style="background:var(--{cvar})">\n'
            f'        <span class="cat-num">{cid.zfill(2)}</span>\n'
            f'        <span class="cat-title">{esc(cat_map.get(cid, ""))}</span>\n'
            f'        <span class="cat-count">{n} 條</span>\n'
            f'      </div>\n'
            f'      <div class="category-body">\n' + "\n".join(body) + "\n" + sum_html +
            "      </div>\n    </div>"
        )
    out.append("  </div>\n")
    return "\n".join(out)


def build_concert_calendar(sec_lines):
    """## 六 演唱會與在地活動月曆。"""
    out = ['  <!-- ===== 六、演唱會與在地活動月曆 ===== -->',
           '  <div class="section">',
           '    <div class="section-num">PART 04</div>',
           '    <h2 class="section-title">演唱會與澳門在地活動・整月月曆</h2>']
    tbls = []
    cur = []
    for ln in sec_lines:
        if ln.strip().startswith("|"):
            cur.append(ln)
        else:
            if cur:
                tbls.append(cur)
                cur = []
            if ln.strip() and not ln.strip().startswith("#") and not is_sep(ln):
                # 觀察段落
                out.append(f'    <p style="font-size:15.5px;color:var(--ink-2);line-height:1.9;margin:10px 0">{md_inline(ln.strip())}</p>')
    if cur:
        tbls.append(cur)
    for t in tbls:
        out.append('    <div class="overview" style="margin-top:14px">' + parse_table(t) + "</div>")
    out.append("  </div>\n")
    return "\n".join(out)


def build_sources(sec_lines):
    """## 七 來源健康檢查 + ## 八 來源與備註 → sources 區塊。"""
    out = ['  <!-- ===== 七/八、來源與備註 ===== -->',
           '  <div class="section" id="sources">',
           '    <div class="section-num">PART 05</div>',
           '    <h2 class="section-title">來源與備註</h2>']
    tbl_lines = [l for l in sec_lines if l.strip().startswith("|")]
    if tbl_lines:
        out.append('    <div class="overview">' + parse_table(tbl_lines) + "</div>")
    # 備註清單
    notes = []
    for ln in sec_lines:
        if ln.strip().startswith("- ") and not ln.strip().startswith("|"):
            notes.append(re.sub(r"^\s*-\s*", "", ln.strip()))
        elif ln.strip().startswith("本週無來源"):
            notes.append(ln.strip())
    if notes:
        out.append('    <div class="source-grid" style="margin-top:16px"><div class="source-list"><h4>備註</h4><ul>')
        for n in notes:
            out.append(f'      <li><span class="dot" style="background:var(--c8)"></span><span>{md_inline(n)}</span></li>')
        out.append("    </ul></div></div>")
    out.append("  </div>\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    text = pathlib.Path(a.md).read_text(encoding="utf-8")
    # 去掉開頭 H1 與分隔線
    lines = text.splitlines()
    # 切分頂層 section（## ）
    sections = {}
    cur = None
    buf = []
    for ln in lines:
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            if cur is not None:
                sections[cur] = buf
            cur = m.group(1)
            buf = []
        else:
            if cur is not None:
                buf.append(ln)
    if cur is not None:
        sections[cur] = buf

    def find(keyword):
        for k, v in sections.items():
            if keyword in k:
                return v
        return []

    parts = []
    data_html, chips = build_data_board(find("數據看板"))
    parts.append(build_overview(find("本週總覽"), chips=chips))
    parts.append(build_highlights(find("重點議題")))
    parts.append(build_perspective(find("軒哥視角")))
    parts.append(data_html)
    parts.append(build_categories(find("分類新聞")))
    parts.append(build_concert_calendar(find("月曆")))
    parts.append(build_sources(find("來源健康") + find("來源與備註")))

    body = "\n".join(parts)
    pathlib.Path(a.out).write_text(body, encoding="utf-8")
    n_cat = body.count('class="category"')
    n_news = body.count('class="news-item"')
    print(f"✅ 已產出 body：{a.out}")
    print(f"   category 區塊：{n_cat} ｜ news-item：{n_news} ｜ chars：{len(body):,}")


if __name__ == "__main__":
    main()

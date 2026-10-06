#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳門新聞週報 HTML 產生器
------------------------------------------------------------
把「內容片段」套進固定版式（CSS + header + nav tabs + footer），
保證每期版式完全一致，避免每次手寫整份 HTML。

用法：
  python tools/build_weekly.py --no 39 --date 2026-09-21 --range "09.14 — 09.20" \
      --content tools/weekly-content/2026-09-21.body.html

輸出：
  macau-weekly/2026-09-21.html

版式骨架來源：
  tools/weekly_shell_pre.txt   （DOCTYPE ~ <body>，取自第 37 期）
  tools/weekly_shell_post.txt  （footer + 收尾，取自第 37 期）
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_DIR = ROOT / "macau-weekly"

# 週報固定十個分類（編號 → id / 短標籤）
CATS = [
    ("1", "時政"),
    ("2", "經濟民生"),
    ("3", "社會文化"),
    ("4", "旅遊盛事"),
    ("5", "中葡平台"),
    ("6", "中華文化"),
    ("7", "社團社區"),
    ("8", "大灣區"),
    ("9", "演唱會"),
    ("10", "AI 精選"),
]


# 期數總覽頁模板（自包含，不依賴本刊 CSS；用 .replace 注入 {count} / {cards} 避免與 CSS 大括號衝突）
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>澳門新聞週報 · 期數總覽</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  :root {
    --bg: #F5F2EC; --surface: #FFFFFF; --ink: #1A1A1A; --ink-2: #4A4A4A;
    --ink-3: #888; --line: #E0DDD5; --brand: #0B3D2E; --accent: #C75B12;
  }
  body {
    font-family: 'Noto Serif TC','Source Han Serif','PingFang TC','Microsoft JhengHei',serif;
    background: var(--bg); color: var(--ink); line-height: 1.7;
  }
  .header { background: var(--brand); color: #fff; padding: 44px 0 32px; text-align: center; }
  .header .tag {
    display: inline-block; font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
    color: #F0A050; border: 1px solid #F0A050; padding: 4px 12px; border-radius: 2px; margin-bottom: 14px;
  }
  .header h1 { font-size: 30px; font-weight: 700; letter-spacing: 2px; }
  .header .sub { font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 8px; letter-spacing: 1px; }
  .container { max-width: 760px; margin: 0 auto; padding: 0 24px; }
  .intro { text-align: center; color: var(--ink-3); font-size: 15px; margin: 28px 0 8px; }
  .grid { display: grid; grid-template-columns: 1fr; gap: 14px; padding: 18px 0 48px; }
  .issue-card {
    display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 4px 16px;
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
    padding: 18px 22px; text-decoration: none; color: var(--ink);
    transition: box-shadow .18s ease, transform .18s ease;
  }
  .issue-card:hover { box-shadow: 0 3px 14px rgba(0,0,0,0.07); transform: translateY(-1px); }
  .issue-no { grid-column: 1; grid-row: 1 / span 2; font-size: 20px; font-weight: 700; color: var(--brand); white-space: nowrap; }
  .issue-date { grid-column: 2; grid-row: 1; font-size: 16px; font-weight: 600; }
  .issue-range { grid-column: 2; grid-row: 2; font-size: 14px; color: var(--ink-3); }
  .issue-go { grid-column: 3; grid-row: 1 / span 2; color: var(--accent); font-weight: 600; font-size: 15px; white-space: nowrap; }
  .latest-chip {
    display: inline-block; font-size: 11px; font-weight: 600; color: #fff;
    background: var(--accent); padding: 2px 8px; border-radius: 3px; margin-left: 8px; vertical-align: middle;
  }
  .footer { text-align: center; color: var(--ink-3); font-size: 13px; padding: 0 0 36px; }
  @media (max-width: 560px) {
    .issue-card { grid-template-columns: 1fr; }
    .issue-no, .issue-date, .issue-range, .issue-go { grid-column: 1; grid-row: auto; }
    .issue-go { margin-top: 6px; }
  }
</style>
</head>
<body>
  <div class="header">
    <div class="container">
      <span class="tag">Macau Weekly Digest</span>
      <h1>澳門新聞週報 · 期數總覽</h1>
      <div class="sub">每週一出刊 · 共 {count} 期</div>
    </div>
  </div>
  <div class="container">
    <div class="intro">點擊任一期，查閱當週澳門新聞與數據看板。</div>
    <div class="grid">
{cards}
    </div>
    <div class="footer">WorkBuddy 自動化任務 · 期數總覽頁（自動生成）</div>
  </div>
</body>
</html>
"""


def build_index() -> None:
    """掃描 macau-weekly/*.html（排除 index.html），依出報日降冪生成期數總覽頁。"""
    rows = []
    for p in OUT_DIR.glob("*.html"):
        if p.name.lower() == "index.html":
            continue
        head = p.read_text(encoding="utf-8")
        m_no = re.search(r"第\s*(\d+)\s*期", head)
        m_rng = re.search(r"<title>澳門新聞週報\s*(.*?)</title>", head, re.S)
        no = m_no.group(1) if m_no else "?"
        rng = m_rng.group(1).strip() if m_rng else ""
        date = p.stem  # YYYY-MM-DD
        try:
            y, mth, d = date.split("-")
            date_cn = f"{y}年{int(mth)}月{int(d)}日"
        except Exception:
            date_cn = date
        rows.append((date, no, rng, date_cn, p.name))

    rows.sort(key=lambda r: r[0], reverse=True)  # 出報日降冪（最新在上）

    cards = []
    for i, (date, no, rng, date_cn, fname) in enumerate(rows):
        latest = ' <span class="latest-chip">最新</span>' if i == 0 else ""
        cards.append(
            f'      <a class="issue-card" href="{fname}">\n'
            f'        <span class="issue-no">第 {no} 期</span>\n'
            f'        <span class="issue-date">{date_cn} 出報{latest}</span>\n'
            f'        <span class="issue-range">統計週 {rng}</span>\n'
            f'        <span class="issue-go">查閱 →</span>\n'
            f'      </a>'
        )
    cards_html = "\n".join(cards)

    html = INDEX_TEMPLATE.replace("{count}", str(len(rows))).replace("{cards}", cards_html)
    idx = OUT_DIR / "index.html"
    idx.write_text(html, encoding="utf-8")
    print(f"✅ 已更新期數總覽 {idx.relative_to(ROOT)}  （共 {len(rows)} 期）")


def build_header(no: str, date_cn: str, rng: str) -> str:
    return (
        "<!-- ===== HEADER ===== -->\n"
        '<div class="header">\n'
        '  <div class="container">\n'
        '    <span class="header-tag">Macau Weekly Digest</span>\n'
        "    <h1>澳門新聞週報</h1>\n"
        f'    <div class="date">第 {no} 期 · {date_cn}（週一）出報</div>\n'
        f'    <div class="week-range">{rng}</div>\n'
        "  </div>\n"
        "</div>\n\n"
    )


def build_nav() -> str:
    rows = ['    <a class="nav-tab active" href="#overview">總覽</a>',
            '    <a class="nav-tab" href="#data">數據看板</a>']
    for cid, label in CATS:
        rows.append(f'    <a class="nav-tab" href="#cat{cid}">{label}</a>')
    rows.append('    <a class="nav-tab" href="#sources">來源</a>')
    return (
        "<!-- ===== NAV TABS ===== -->\n"
        '<div class="nav-tabs">\n'
        '  <div class="container" style="display: flex; gap: 0; padding: 0;">\n'
        + "\n".join(rows) + "\n"
        "  </div>\n"
        "</div>\n\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no", required=True, help="期號，如 39")
    ap.add_argument("--date", required=True, help="出報日 YYYY-MM-DD")
    ap.add_argument("--range", required=True, dest="rng", help="統計週，如 09.14 — 09.20")
    ap.add_argument("--content", required=True, help="內容片段 HTML 路徑")
    ap.add_argument("--source", default="澳門日報、政府新聞局 GCS、DSEC、力報等")
    ap.add_argument("--out", default="", help="輸出路徑（預設 macau-weekly/<date>.html）")
    a = ap.parse_args()

    pre = (HERE / "weekly_shell_pre.txt").read_text(encoding="utf-8")
    post = (HERE / "weekly_shell_post.txt").read_text(encoding="utf-8")

    # 內嵌 QR 庫（零外部依賴：分享按鈕的二維碼改由本機生成，不再呼叫 api.qrserver.com）
    qr_lib = (HERE / "qrcode.min.js").read_text(encoding="utf-8")
    pre = pre.replace("<body>", "<body>\n<script>\n" + qr_lib + "\n</script>\n", 1)

    content_path = pathlib.Path(a.content)
    if not content_path.is_absolute():
        content_path = ROOT / content_path
    content = content_path.read_text(encoding="utf-8")

    y, m, d = a.date.split("-")
    date_cn = f"{y}年{int(m)}月{int(d)}日"

    # 換 title
    pre = re.sub(r"<title>.*?</title>",
                 f"<title>澳門新聞週報 {a.rng}</title>",
                 pre, count=1, flags=re.S)

    # 換 footer 說明文字
    post = re.sub(
        r'<div>WorkBuddy 自動化任務 · .*?</div>',
        f'<div>第 {a.no} 期 · 統計週 {a.rng} · 資料來源：{a.source}</div>',
        post, count=1, flags=re.S)

    html = (pre
            + build_header(a.no, date_cn, a.rng)
            + build_nav()
            + '<div class="container">\n'
            + content.rstrip() + "\n"
            + "</div>\n\n"
            + post.lstrip("\n"))

    out = pathlib.Path(a.out) if a.out else (OUT_DIR / f"{a.date}.html")
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    build_index()

    # SVG 圖表溢出檢查（viewBox 寬 880，留 10px 安全邊界 → 上限 870）
    svg_over = []
    for m in re.finditer(r'<rect x="([0-9.]+)"[^>]*?width="([0-9.]+)"', html):
        x, w = float(m.group(1)), float(m.group(2))
        if x + w > 870:
            svg_over.append(f"rect x={x}+w={w}={x+w:.0f}")
    for m in re.finditer(r'<text x="([0-9.]+)"', html):
        if float(m.group(1)) > 870:
            svg_over.append(f"text x={m.group(1)}")

    # 基本體檢
    checks = {
        "期號": f"第 {a.no} 期" in html,
        "統計週": a.rng in html,
        "分類數": html.count('class="category"'),
        "新聞條數": html.count('class="news-item"'),
        "未替換佔位": ("TODO" not in html and "XXX" not in html and "{{" not in html),
        "SVG溢出": "無" if not svg_over else svg_over,
    }
    if svg_over:
        print("⚠️  偵測到 SVG 元素超出畫布，請修正後重跑：")
    print(f"✅ 已輸出 {out.relative_to(ROOT)}  ({len(html):,} chars)")
    for k, v in checks.items():
        print(f"   {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

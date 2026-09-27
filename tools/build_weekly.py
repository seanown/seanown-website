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

    # 基本體檢
    checks = {
        "期號": f"第 {a.no} 期" in html,
        "統計週": a.rng in html,
        "分類數": html.count('class="category"'),
        "新聞條數": html.count('class="news-item"'),
        "未替換佔位": ("TODO" not in html and "XXX" not in html and "{{" not in html),
    }
    print(f"✅ 已輸出 {out.relative_to(ROOT)}  ({len(html):,} chars)")
    for k, v in checks.items():
        print(f"   {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Insert 《鐵金剛狗場追兇》(1965) into data/posts.json.

num 由 bash 現算後傳入（sys.argv[1]），避免併行線撞號。
"""
import sys, json, re, io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "data" / "posts.json"
DRAFT = ROOT / "_draft_chase-at-the-canidrome-1965.md"
SLUG = "chase-at-the-canidrome-1965"
NUM = int(sys.argv[1])

body = DRAFT.read_text(encoding="utf-8").strip()

# --- 鐵律檢查 ---
assert body.startswith("<img"), "body must start with html img"
assert "![" not in body, "must use html img, not markdown ![]"

data = json.loads(POSTS.read_text(encoding="utf-8"))
posts = data["posts"]

assert NUM == max(int(p["num"]) for p in posts) + 1, f"撞號：expect {max(int(p['num']) for p in posts)+1}, got {NUM}"
assert all(p["slug"] != SLUG for p in posts), "slug 已存在"
assert all(int(p["num"]) != NUM for p in posts), "num 已存在"

# 金句框兩行必須緊鄰，避免署名掉出框外
body = re.sub(r"(>\s*[^\n]*)\n\n(>\s*——)", r"\1\n\2", body)

post = {
    "num": NUM,
    "title": "《鐵金剛狗場追兇》觀後感",
    "subtitle": "鐵金剛來到澳門，賭的是狗｜1965",
    "slug": SLUG,
    "series": "macau-film",
    "category": "影評",
    "date": "2026-09-30",
    "location": "澳門",
    "status": "已上線",
    "images": [f"assets/og/{SLUG}.jpg"],
    "body": body,
}

assert "body" in post and post["body"].strip(), "body 不可為空"
posts.append(post)

POSTS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

mf = [p for p in posts if p.get("series") == "macau-film"]
seq = sorted(mf, key=lambda p: (str(p["date"]), int(p["num"])))
idx = [p["slug"] for p in seq].index(SLUG) + 1
print(f"OK num={NUM} slug={SLUG} body_chars={len(body)}")
print(f"電影專輯第 {idx} / {len(seq)} 篇")

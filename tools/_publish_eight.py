# -*- coding: utf-8 -*-
"""把《八個兇手》(1965) 入庫 data/posts.json 為 num=98，並補 SLUGS、sitemap、build。"""
import json, io, os, re

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
POSTS = os.path.join(ROOT, "data", "posts.json")
DRAFT = os.path.join(ROOT, "_draft_八個兇手.md")
SLUG = "eight-murderers-1965"
NUM = 98

# --- 1. 讀草稿，剝掉 H1 與副標（照 #97 the-blazing-charmer-1959 慣例：body 由 <img> 起）---
raw = io.open(DRAFT, encoding="utf-8").read().strip("\n")
lines = raw.split("\n")
assert lines[0].startswith("# "), lines[0]
sub_i = next(i for i, l in enumerate(lines) if i > 0 and l.startswith("## "))
assert "｜1965" in lines[sub_i], lines[sub_i]
body = "\n".join(lines[sub_i + 1:]).strip("\n")

# 安全檢查
assert "![" not in body, "草稿仍有 markdown 圖片語法"
assert body.lstrip().startswith("<img"), body[:80]
print("body chars:", len(re.sub(r"\s", "", body)), "coords:", len(re.findall(r"22\.\d{4}", body)))
print("quote lines:", len([l for l in body.split("\n") if l.startswith("> ")]))

# --- 2. 入庫 ---
d = json.load(io.open(POSTS, encoding="utf-8"))
ps = d["posts"]
assert all(str(p.get("num")) != str(NUM) for p in ps), "num 98 已存在"
assert all(p.get("slug") != SLUG for p in ps), "slug 已存在"

ps.append({
    "num": NUM,
    "title": "《八個兇手》觀後感",
    "subtitle": "八個人那一天都到了，那棟樓已經不在了｜1965",
    "slug": SLUG,
    "series": "macau-film",
    "category": "影評",
    "date": "2026-09-30",
    "location": "澳門",
    "status": "已上線",
    "images": ["assets/og/%s.jpg" % SLUG],
    "body": body,
})
with io.open(POSTS, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write("\n")

# 型別完整性檢查
d2 = json.load(io.open(POSTS, encoding="utf-8"))
types = {}
for p in d2["posts"]:
    types[type(p["num"]).__name__] = types.get(type(p["num"]).__name__, 0) + 1
print("num types after write:", types)
print("total posts:", len(d2["posts"]))

# 輯內序號現算
mf = [p for p in d2["posts"] if p.get("series") == "macau-film"]
pub = [p for p in mf if p.get("status") != "整理中"]
pub.sort(key=lambda x: (x.get("date", ""), int(x["num"])))
idx = [p["slug"] for p in pub].index(SLUG) + 1
print("macau-film published:", len(pub), "| 本篇輯內序號:", idx)

# --- 3. SLUGS ---
bt = os.path.join(ROOT, "tools", "build_articles.py")
s = io.open(bt, encoding="utf-8").read()
if "'98': '%s'" % SLUG not in s:
    assert "'97': 'the-blazing-charmer-1959'," in s
    s = s.replace("    '97': 'the-blazing-charmer-1959',\n",
                  "    '97': 'the-blazing-charmer-1959',\n    '98': '%s',\n" % SLUG)
    io.open(bt, "w", encoding="utf-8").write(s)
    print("SLUGS patched")
else:
    print("SLUGS already present")

# --- 4. sitemap ---
sm = os.path.join(ROOT, "sitemap.xml")
t = io.open(sm, encoding="utf-8").read()
if "/article/%s/" % SLUG not in t:
    block = ("  <url>\n    <loc>https://seanown.org/article/%s/</loc>\n"
             "    <lastmod>2026-09-30</lastmod>\n  </url>\n" % SLUG)
    t = t.replace("</urlset>", block + "</urlset>")
    io.open(sm, "w", encoding="utf-8").write(t)
    print("sitemap patched")
else:
    print("sitemap already present")
print("sitemap url count:", t.count("<loc>"))

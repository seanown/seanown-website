# -*- coding: utf-8 -*-
"""《精武門》(1972) 入庫 posts.json（num 現算 max+1）、升 OG_VER、補 SLUGS。"""
import json, re, io, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_精武門.md")
VER = "20260930c"
SLUG = "fist-of-fury-1972"

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
newnum = max(int(p["num"]) for p in ps) + 1
print("newnum", newnum)

if any(p["slug"] == SLUG for p in ps):
    raise SystemExit("slug already exists")

raw = open(DRAFT, encoding="utf-8").read()
lines = raw.split("\n")
# 去掉首行 '# 標題'
if lines[0].startswith("# "):
    lines = lines[1:]
# 去掉「副標：」行
lines = [l for l in lines if not l.startswith("副標：")]
# 跳過第一個 ---
for i, l in enumerate(lines):
    if l.strip() == "---":
        lines = lines[i + 1:]
        break
body_txt = "\n".join(lines).strip("\n")

img = ('<img src="../../assets/og/%s-poster.jpg?v=%s" alt="%s 電影海報" '
       'style="column-span:all;width:min(100%%,520px);display:block;margin:8px auto 28px;'
       'border-radius:10px">' % (SLUG, VER, "Fist of Fury 1972"))
body = img + "\n\n" + body_txt

entry = {
    "num": newnum,
    "title": "《精武門》觀後感",
    "subtitle": "中國人唔係病夫：踢給白鴿巢的門柱聽｜1972",
    "slug": SLUG,
    "series": "macau-film",
    "category": "影評",
    "date": "2026-09-30",
    "location": "澳門",
    "status": "已上線",
    "images": ["assets/og/%s.jpg" % SLUG],
    "body": body,
}
ps.append(entry)
json.dump(d, open(PJ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("posts.json updated, total", len(ps))

# build_articles.py: SLUGS + OG_VER
s = open(BA, encoding="utf-8").read()
s = re.sub(r"OG_VER = '[0-9a-z]+'", "OG_VER = '%s'" % VER, s, count=1)
key = "'%d': '%s'," % (newnum, SLUG)
if key in s:
    print("SLUGS key already present")
else:
    # 插到 '74': ... 那行之後（或最後一個 macau-film 條目後）
    m = re.search(r"\n(\s*)'74': 'cleopatra-jones-casino-of-gold-1975',\}", s)
    if m:
        indent = m.group(1)
        s = s[:m.start()] + "\n%s'74': 'cleopatra-jones-casino-of-gold-1975',\n%s%s}" % (
            indent, indent, key) + s[m.end():]
    else:
        raise SystemExit("SLUGS anchor not found")
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, key))

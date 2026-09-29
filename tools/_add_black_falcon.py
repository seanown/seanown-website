# -*- coding: utf-8 -*-
"""《黑鷹》(1967) 入庫 posts.json（num 現算 max+1）、升 OG_VER、補 SLUGS。"""
import json, re, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_黑鷹.md")
VER = "20260930d"
SLUG = "black-falcon-1967"

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
newnum = max(int(p["num"]) for p in ps) + 1
print("newnum", newnum)
if any(p["slug"] == SLUG for p in ps):
    raise SystemExit("slug already exists")

raw = open(DRAFT, encoding="utf-8").read()
lines = raw.split("\n")
if lines[0].startswith("# "):
    lines = lines[1:]
lines = [l for l in lines if not l.startswith("副標：")]
for i, l in enumerate(lines):
    if l.strip() == "---":
        lines = lines[i + 1:]
        break
body_txt = "\n".join(lines).strip("\n")

img = ('<img src="../../assets/og/%s-poster.jpg?v=%s" alt="%s 電影海報" '
       'style="column-span:all;width:min(100%%,520px);display:block;margin:8px auto 28px;'
       'border-radius:10px">' % (SLUG, VER, "The Black Falcon 1967"))
body = img + "\n\n" + body_txt

ps.append({
    "num": newnum,
    "title": "《黑鷹》觀後感",
    "subtitle": "牆拆了兩百年，名字還在｜1967",
    "slug": SLUG,
    "series": "macau-film",
    "category": "影評",
    "date": "2026-09-30",
    "location": "澳門",
    "status": "已上線",
    "images": ["assets/og/%s.jpg" % SLUG],
    "body": body,
})
json.dump(d, open(PJ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("posts.json updated, total", len(ps))

s = open(BA, encoding="utf-8").read()
s = re.sub(r"OG_VER = '[0-9a-z]+'", "OG_VER = '%s'" % VER, s, count=1)
key = "'%d': '%s'," % (newnum, SLUG)
if key in s:
    print("SLUGS key already present")
else:
    m = re.search(r"\n(\s*)'75': 'fist-of-fury-1972',", s)
    if not m:
        raise SystemExit("SLUGS anchor not found")
    indent = m.group(1)
    s = s[:m.end()] + "\n%s%s" % (indent, key) + s[m.end():]
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, key))

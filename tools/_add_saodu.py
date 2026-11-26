# -*- coding: utf-8 -*-
"""《掃毒》(2013) 入庫 posts.json（num 現算 max+1）、升 OG_VER、補 SLUGS。"""
import json, re, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_掃毒.md")
VER = "20260930g"
SLUG = "the-white-storm-2013"

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
newnum = max(int(p["num"]) for p in ps) + 1
print("newnum", newnum)
assert newnum == 83, "num 撞號或位移：%s" % newnum
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
# 金句框兩行必須緊貼，否則被引擎拆成兩個 blockquote
body_txt = re.sub(r'(>\s*[^\n]*)\n\n(>\s*——)', r'\1\n\2', body_txt)

img = ('<img src="../../assets/og/%s-poster.jpg?v=%s" alt="%s 電影海報" '
       'style="column-span:all;width:min(100%%,520px);display:block;margin:8px auto 28px;'
       'border-radius:10px">' % (SLUG, VER, "The White Storm 2013"))
body = img + "\n\n" + body_txt

ps.append({
    "num": newnum,
    "title": "《掃毒》觀後感",
    "subtitle": "阿偉已經死了，你挑的嘛偶像｜2013",
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
assert re.search(r"OG_VER = '20260930f'", s), "OG_VER 已被併行線改過：%s" % re.search(r"OG_VER = '[0-9a-z]+'", s).group(0)
s = re.sub(r"OG_VER = '[0-9a-z]+'", "OG_VER = '%s'" % VER, s, count=1)
key = "'%d': '%s'," % (newnum, SLUG)
if key in s:
    raise SystemExit("SLUGS key already present")
m = re.search(r"\n(\s*)'82': 'a-night-in-hong-kong-1961',", s)
if not m:
    raise SystemExit("SLUGS anchor not found")
indent = m.group(1)
s = s[:m.end()] + "\n%s%s" % (indent, key) + s[m.end():]
# 撞號保險
assert len(re.findall(r"^\s*'%d':" % newnum, s, re.M)) == 1, "SLUGS 撞號"
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, key))

# -*- coding: utf-8 -*-
"""《險角》(2001) 入庫 posts.json（num 現算 max+1）、升 OG_VER、補齊 SLUGS（含併行線漏補的 84/85）。"""
import json, re, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_險角.md")
VER = "20260930i"
SLUG = "sharp-gun-2001"
EXPECT_NUM = 86
EXPECT_VER = "20260930h"

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
newnum = max(int(p["num"]) for p in ps) + 1
print("newnum", newnum)
assert newnum == EXPECT_NUM, "num 撞號或位移：%s" % newnum
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
body_txt = re.sub(r'(>\s*[^\n]*)\n\n(>\s*——)', r'\1\n\2', body_txt)

img = ('<img src="../../assets/og/%s-poster.jpg?v=%s" alt="%s 電影海報" '
       'style="column-span:all;width:min(100%%,520px);display:block;margin:8px auto 28px;'
       'border-radius:10px">' % (SLUG, VER, "Sharp Gun 2001"))
body = img + "\n\n" + body_txt

ps.append({
    "num": newnum,
    "title": "《險角》觀後感",
    "subtitle": "別以為這就是真實的澳門｜2001",
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
m0 = re.search(r"OG_VER = '([0-9a-z]+)'", s)
assert m0.group(1) == EXPECT_VER, "OG_VER 已被併行線改過：%s" % m0.group(1)
s = re.sub(r"OG_VER = '[0-9a-z]+'", "OG_VER = '%s'" % VER, s, count=1)

# 先補齊併行線漏掉的 SLUGS（posts.json 已有但字典缺號 → build 會生成 post-NN fallback 目錄）
missing = {"84": "macao-enfer-du-jeu-1939", "85": "young-and-dangerous-1996"}
slug_of = {str(p["num"]): p["slug"] for p in ps}
anchor = re.search(r"\n(\s*)'83': 'the-white-storm-2013',", s)
if not anchor:
    raise SystemExit("SLUGS anchor not found")
indent = anchor.group(1)
add = []
for k, v in missing.items():
    if not re.search(r"^\s*'%s':" % k, s, re.M):
        assert slug_of.get(k) == v, "slug 對不上：%s vs %s" % (slug_of.get(k), v)
        add.append("%s'%s': '%s'," % (indent, k, v))
add.append("%s'%d': '%s'," % (indent, newnum, SLUG))
s = s[:anchor.end()] + "\n" + "\n".join(add) + s[anchor.end():]

for k in list(missing.keys()) + [str(newnum)]:
    assert len(re.findall(r"^\s*'%s':" % k, s, re.M)) == 1, "SLUGS 撞號或重複：%s" % k
# 全站一致性：posts.json 每個 num 都要在 SLUGS 裡有號
keys = set(re.findall(r"^\s*'(\d+)':", s, re.M))
for p in ps:
    assert str(p["num"]) in keys, "SLUGS 仍缺號：%s (%s)" % (p["num"], p["slug"])
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, add))

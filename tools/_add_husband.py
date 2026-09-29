# -*- coding: utf-8 -*-
"""《午夜招魂》(1964) 入庫 posts.json（num 現算 max+1）、升 OG_VER、補 SLUGS（自動補齊任何缺號）。"""
import json, re, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_小姐的丈夫.md")
VER = "20260930k"
SLUG = "the-husband-of-a-lady-1965"
EXPECT_NUM = 90
EXPECT_VER = "20260930j"
ANCHOR_NUM = "88"

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
       'border-radius:10px">' % (SLUG, VER, "The Husband of a Lady 1965"))
body = img + "\n\n" + body_txt

ps.append({
    "num": newnum,
    "title": "《小姐的丈夫》觀後感",
    "subtitle": "她隱瞞身分，澳門不問身分｜1965",
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

# 缺號自動補齊：posts.json 有、SLUGS 沒有的號全部補上（併行線常漏）
have = set(re.findall(r"^\s*'(\d+)':", s, re.M))
slug_of = {str(p["num"]): p["slug"] for p in ps}
todo = [k for k in sorted(slug_of, key=int) if k not in have]
print("SLUGS 缺號自動補齊:", todo)

anchor = re.search(r"\n(\s*)'%s': '%s'," % (ANCHOR_NUM, slug_of[ANCHOR_NUM]), s)
if not anchor:
    raise SystemExit("SLUGS anchor not found")
indent = anchor.group(1)
tail = [str(newnum)] + [k for k in todo if k != str(newnum)]
add = ["%s'%s': '%s'," % (indent, k, slug_of[k]) for k in tail]
s = s[:anchor.end()] + "\n" + "\n".join(add) + s[anchor.end():]

for k in set(todo) | {str(newnum)}:
    assert len(re.findall(r"^\s*'%s':" % k, s, re.M)) == 1, "SLUGS 撞號或重複：%s" % k
keys = set(re.findall(r"^\s*'(\d+)':", s, re.M))
for p in ps:
    assert str(p["num"]) in keys, "SLUGS 仍缺號：%s (%s)" % (p["num"], p["slug"])
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, add))

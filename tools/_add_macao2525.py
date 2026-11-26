# -*- coding: utf-8 -*-
"""《Macao 2525》(2021) 入庫 posts.json（num 現算 max+1）、OG_VER 自動進位、補 SLUGS（自動補齊任何缺號）。"""
import json, re, os, sys

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_macao2525.md")
SLUG = "macao-2525-2021"
EXPECT_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 96

# ---- OG_VER：開工那一刻現讀現進位，不寫死期望值 ----
_s = open(BA, encoding="utf-8").read()
_cur = re.search(r"OG_VER = '([0-9a-z]+)'", _s).group(1)
assert _cur[-1].isalpha() and _cur[-1] != "z", "OG_VER 尾字元無法進位：%s" % _cur
VER = _cur[:-1] + chr(ord(_cur[-1]) + 1)
print("OG_VER", _cur, "->", VER)

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
body_txt = "\n".join(lines).strip("\n")
body_txt = re.sub(r'(>\s*[^\n]*)\n\n(>\s*——)', r'\1\n\2', body_txt)

img = ('<img src="../../assets/og/%s-poster.jpg?v=%s" alt="%s 電影海報" '
       'style="column-span:all;width:min(100%%,520px);display:block;margin:8px auto 28px;'
       'border-radius:10px">' % (SLUG, VER, "Macao 2525 2021"))
body = img + "\n\n" + body_txt

ps.append({
    "num": newnum,
    "title": "《Macao 2525》觀後感",
    "subtitle": "最後剩下的那座城，是澳門｜2021",
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

# 缺號自動補齊：posts.json 有、SLUGS 沒有的號全部補上（併行線常漏）
have = set(re.findall(r"^\s*'(\d+)':", s, re.M))
slug_of = {str(p["num"]): p["slug"] for p in ps}
todo = [k for k in sorted(slug_of, key=int) if k not in have]
print("SLUGS 缺號自動補齊:", todo)

# anchor 取 SLUGS 字典最後一條（不寫死號碼，避免併行線位移）
pairs = list(re.finditer(r"^[ \t]*'(\d+)': '([^']+)',", s, re.M))
if not pairs:
    raise SystemExit("SLUGS anchor not found")
anchor = pairs[-1]
indent = re.match(r"^([ \t]*)", anchor.group(0)).group(1)
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

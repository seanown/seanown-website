# -*- coding: utf-8 -*-
"""《堂口故事》(2008) / 《堂口故事2：愛情在城》(2011) / 《堂口故事3：心亂疑城》(2015) /
《過雲雨》(2017) 四部本地粵語片 入庫 posts.json。

- num 現算 max+1（依 ITEMS 順序 133/134/135/136）
- OG_VER 自動進位一次（l -> m）
- 補 SLUGS（自動補齊任何缺號）
- 這四篇暫不掛 movieInfo / images（海報＋OG 圖為第二階段），
  避免上線後出現破圖；待海報生成後再補。
"""
import json, re, os, sys
from datetime import date

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DATE = date.today().isoformat()

# (draft 檔名, slug, title, subtitle, filmYear)
ITEMS = [
    ("_draft_macao-stories-2008.md", "macao-stories-2008",
     "《堂口故事》觀後感", "澳門城市電影的誕生｜2008", 2008),
    ("_draft_love-in-the-city-2011.md", "love-in-the-city-2011",
     "《堂口故事2：愛情在城》觀後感", "真正屬於澳門的愛情拼盤｜2011", 2011),
    ("_draft_restless-city-2015.md", "restless-city-2015",
     "《堂口故事3：心亂疑城》觀後感", "那個充滿血光的恐怖澳門｜2015", 2015),
    ("_draft_passing-rain-2017.md", "passing-rain-2017",
     "《過雲雨》觀後感", "雨隨雲至，雲過雨停｜2017", 2017),
]

# ---- OG_VER：開工那一刻現讀現進位 ----
_s = open(BA, encoding="utf-8").read()
_cur = re.search(r"OG_VER = '([0-9a-z]+)'", _s).group(1)
assert _cur[-1].isalpha(), "OG_VER 尾字元非字母：%s" % _cur
VER = (_cur + "a") if _cur[-1] == "z" else (_cur[:-1] + chr(ord(_cur[-1]) + 1))
print("OG_VER", _cur, "->", VER, "| date", DATE)

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
slug_of = {str(p["num"]): p["slug"] for p in ps}
for slug, _, _, _, _ in ITEMS:
    assert not any(p["slug"] == slug for p in ps), "slug already exists: " + slug

newnum = max(int(p["num"]) for p in ps)
print("current max num", newnum)

for (draft, slug, title, subtitle, fy) in ITEMS:
    newnum += 1
    raw = open(os.path.join(ROOT, draft), encoding="utf-8").read()
    lines = raw.split("\n")
    if lines[0].startswith("# "):
        lines = lines[1:]
    lines = [l for l in lines if not l.startswith("副標：")]
    body = "\n".join(lines).strip("\n")
    # 金句框：若 quote 與 —— 署名之間有空行，合併為同一 blockquote
    body = re.sub(r'(>\s*[^\n]*)\n\n(>\s*——)', r'\1\n\2', body)
    assert "{{PREV_COUNT}}" not in body, "不應含 PREV_COUNT"
    ps.append({
        "num": newnum,
        "title": title,
        "subtitle": subtitle,
        "slug": slug,
        "series": "macau-film",
        "category": "",
        "date": DATE,
        "location": "澳門",
        "status": "已上線",
        "images": [],
        "filmYear": fy,
        "body": body,
    })
    slug_of[str(newnum)] = slug
    print("added", newnum, slug, "| filmYear", fy)

json.dump(d, open(PJ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("posts.json updated, total", len(ps))

# ---- 寫回 build_articles.py：OG_VER + SLUGS ----
s = open(BA, encoding="utf-8").read()
s = re.sub(r"OG_VER = '[0-9a-z]+'", "OG_VER = '%s'" % VER, s, count=1)

have = set(re.findall(r"^\s*'(\d+)':", s, re.M))
todo = [k for k in sorted(slug_of, key=int) if k not in have]
pairs = list(re.finditer(r"^[ \t]*'(\d+)': '([^']+)',", s, re.M))
assert pairs, "SLUGS anchor not found"
anchor = pairs[-1]
indent = re.match(r"^([ \t]*)", anchor.group(0)).group(1)
add = ["%s'%s': '%s'," % (indent, k, slug_of[k]) for k in sorted(todo, key=int)]
s = s[:anchor.end()] + "\n" + "\n".join(add) + s[anchor.end():]

for k in todo:
    assert len(re.findall(r"^\s*'%s':" % k, s, re.M)) == 1, "SLUGS 撞號：%s" % k
keys = set(re.findall(r"^\s*'(\d+)':", s, re.M))
for p in ps:
    assert str(p["num"]) in keys, "SLUGS 仍缺號：%s (%s)" % (p["num"], p["slug"])
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, add))

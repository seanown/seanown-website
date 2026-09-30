# -*- coding: utf-8 -*-
"""《b420》(2005) 入庫 posts.json（num 現算 max+1）、OG_VER 自動進位、補 SLUGS（自動補齊缺號）。

與 _add_blazing.py 的差別：
1. 草稿結構為「img / 空 / # 標題 / 空 / ## 副標 / 空 / 正文…---…散場之後…---…附錄」——
   **不砍任何段落**，全部原樣入庫（散場之後與附錄都保留）。
2. OG_VER 尾字母到了 'z' 時自動換下一天的前綴重新從 'a' 起（本輪正好撞上）。
3. img 的 ?v= 一律對齊進位後的新值（並行線連跳也不會對不上）。

冪等：slug 已存在則直接結束，不重複入庫。
"""
import json, re, os, sys, datetime

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_b420-2005.md")
SLUG = "b420-2005"
TITLE = "《b420》觀後感"
SUBTITLE = "澳門成為世界遺產的前一年｜2005"
EXPECT_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 111

# ---- OG_VER：開工那一刻現讀現進位，不寫死期望值 ----
_s = open(BA, encoding="utf-8").read()
_cur = re.search(r"OG_VER = '([0-9a-z]+)'", _s).group(1)
prefix, tail = _cur[:8], _cur[8:]
if tail == "z":
    nd = datetime.date(int(prefix[:4]), int(prefix[4:6]), int(prefix[6:8])) + datetime.timedelta(days=1)
    VER = nd.strftime("%Y%m%d") + "a"
else:
    assert tail.isalpha(), "OG_VER 尾字元異常：%s" % _cur
    VER = prefix + chr(ord(tail) + 1)
print("OG_VER", _cur, "->", VER)

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
newnum = max(int(p["num"]) for p in ps) + 1
print("newnum", newnum)
assert newnum == EXPECT_NUM, "num 撞號或位移：%s != %s" % (newnum, EXPECT_NUM)
if any(p["slug"] == SLUG for p in ps):
    print("slug 已存在，跳過（冪等）")
    sys.exit(0)

raw = open(DRAFT, encoding="utf-8").read()
lines = raw.split("\n")
title = lines[2].lstrip("# ").strip()
subtitle = lines[4].replace("## ", "").strip()
assert title == TITLE, repr(title)
assert subtitle == SUBTITLE, repr(subtitle)

body = raw.strip("\n")
assert body.count("![") == 0, "草稿含 markdown 圖片語法"
# 引句框兩行必須緊鄰
body = re.sub(r"(>\s*[^\n]*)\n\n(>\s*——)", r"\1\n\2", body)
# img 的 ?v= 對齊新值
body, n = re.subn(r"(" + SLUG + r"-poster\.jpg\?v=)[0-9a-zA-Z]+", r"\g<1>" + VER, body)
assert n == 1, "海報 img 的 ?v= 替換次數異常：%d（應為 1）" % n

ps.append({
    "num": newnum,
    "title": title,
    "subtitle": subtitle,
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

# 缺號自動補齊（併行線常漏）
have = set(re.findall(r"^\s*'(\d+)':", s, re.M))
slug_of = {str(p["num"]): p["slug"] for p in ps}
todo = [k for k in sorted(slug_of, key=int) if k not in have]
print("SLUGS 缺號自動補齊:", todo)

pairs = list(re.finditer(r"^[ \t]*'(\d+)': '([^']+)',", s, re.M))
if not pairs:
    raise SystemExit("SLUGS anchor not found")
anchor = pairs[-1]
indent = re.match(r"^([ \t]*)", anchor.group(0)).group(1)
tail_nums = [str(newnum)] + [k for k in todo if k != str(newnum)]
add = ["%s'%s': '%s'," % (indent, k, slug_of[k]) for k in tail_nums]
s = s[:anchor.end()] + "\n" + "\n".join(add) + s[anchor.end():]

for k in set(todo) | {str(newnum)}:
    assert len(re.findall(r"^\s*'%s':" % k, s, re.M)) == 1, "SLUGS 撞號或重複：%s" % k
keys = set(re.findall(r"^\s*'(\d+)':", s, re.M))
for p in ps:
    assert str(p["num"]) in keys, "SLUGS 仍缺號：%s (%s)" % (p["num"], p["slug"])
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, add))

# 複核
d2 = json.load(open(PJ, encoding="utf-8"))
q = [x for x in d2["posts"] if x["slug"] == SLUG][0]
print("入庫：num=%s | %s | body %d chars" % (q["num"], SLUG, len(q["body"])))
pub = sorted([x for x in d2["posts"] if x.get("series") == "macau-film" and x.get("status") != "整理中"],
             key=lambda x: (x["date"], int(x["num"])))
idx = [int(x["num"]) for x in pub].index(int(q["num"])) + 1
print("輯內序號：第 %d / %d 篇" % (idx, len(pub)))

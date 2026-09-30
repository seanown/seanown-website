# -*- coding: utf-8 -*-
"""《Aspectos de Macau》(1923) 入庫 posts.json（num 現算 max+1）、OG_VER 沿用現值、補 SLUGS（含 newnum 本身）。

以 _add_forbidden.py 為底，差異：
1. 草稿在 drafts/aspectos-de-macau-1923.body.md（不在 ROOT _draft_）。
2. 正文無 {{PREV_COUNT}} 佔位符（軒哥新規：不寫「第 N 篇」），故不填。
3. 全站 max num=118 -> newnum=119；SLUGS 現 max=118 但未含 119（未被併行線預佔），
   故修正原 forbidden 腳本「tail_nums 排除 newnum」的邏輯，把 newnum 也寫入 SLUGS。
4. date 用上線日 2026-09-30。

冪等：slug 已存在則直接結束，不重複入庫。
"""
import json, re, os, sys

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "drafts", "aspectos-de-macau-1923.body.md")
SLUG = "aspectos-de-macau-1923"
EXPECT_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 119

# ---- OG_VER：沿用當前值，不進位（海報八件套已生成，避免 ?v= 錯位） ----
_s = open(BA, encoding="utf-8").read()
_cur = re.search(r"OG_VER = '([0-9a-z]+)'", _s).group(1)
VER = _cur
print("OG_VER use current", VER)

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
print("title", title)
print("subtitle", subtitle)

body = "\n".join(lines).strip("\n")
assert body.count("![") == 0, "草稿含 markdown 圖片語法"
assert "{{PREV_COUNT}}" not in body, "仍有未替換的佔位符"
# 引句框兩行必須緊鄰（無空白行則不變）
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

# ---- 更新 build_articles.py：OG_VER 沿用 + SLUGS 補齊（含 newnum） ----
s = open(BA, encoding="utf-8").read()
s = re.sub(r"OG_VER = '[0-9a-z]+'", "OG_VER = '%s'" % VER, s, count=1)

have = set(re.findall(r"^\s*'(\d+)':", s, re.M))
slug_of = {str(p["num"]): p["slug"] for p in ps}
todo = [k for k in sorted(slug_of, key=int) if k not in have]
print("SLUGS 缺號待補：", todo)

pairs = list(re.finditer(r"^[ \t]*'(\d+)': '([^']+)',", s, re.M))
if not pairs:
    raise SystemExit("SLUGS anchor not found")
anchor = pairs[-1]
indent = re.match(r"^([ \t]*)", anchor.group(0)).group(1)
# 修正：把所有缺號（含 newnum）都補進 SLUGS，插在 anchor（最後一筆）之後
add = ["%s'%s': '%s'," % (indent, k, slug_of[k]) for k in todo]
s = s[:anchor.end()] + "\n" + "\n".join(add) + s[anchor.end():]

for k in set(todo):
    assert len(re.findall(r"^\s*'%s':" % k, s, re.M)) == 1, "SLUGS 撞號或重複：%s" % k
keys = set(re.findall(r"^\s*'(\d+)':", s, re.M))
for p in ps:
    assert str(p["num"]) in keys, "SLUGS 仍缺號：%s (%s)" % (p["num"], p["slug"])
open(BA, "w", encoding="utf-8").write(s)
print("build_articles.py updated: OG_VER=%s, SLUGS+%s" % (VER, add))

# ---- 複核 ----
d2 = json.load(open(PJ, encoding="utf-8"))
q = [x for x in d2["posts"] if x["slug"] == SLUG][0]
print("入庫：num=%s | %s | body %d chars" % (q["num"], SLUG, len(q["body"])))
pub = sorted([x for x in d2["posts"] if x.get("series") == "macau-film" and x.get("status") != "整理中"],
             key=lambda x: (x["date"], int(x["num"])))
idx = [int(x["num"]) for x in pub].index(int(q["num"])) + 1
print("輯內序號：第 %d / %d 篇" % (idx, len(pub)))

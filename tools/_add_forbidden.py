# -*- coding: utf-8 -*-
"""《Forbidden》(1953) 入庫 posts.json（num 現算 max+1）、OG_VER 自動進位、補 SLUGS（自動補齊缺號）。

與 _add_b420.py 的差別：
1. 草稿結構含 PREV_COUNT 佔位符，入庫前現算輯內已上線篇數並轉中文數字填入。
2. img 已由草稿內建，不從頭生成。

冪等：slug 已存在則直接結束，不重複入庫。
"""
import json, re, os, sys, datetime

CN = '零一二三四五六七八九'


def cn(n):
    """1-999 轉中文數字（67 -> 六十七）。"""
    if n < 10:
        return CN[n]
    if n < 20:
        return '十' + (CN[n % 10] if n % 10 else '')
    if n < 100:
        return CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')
    if n < 1000:
        s = CN[n // 100] + '百'
        r = n % 100
        if r == 0:
            return s
        if r < 10:
            return s + '零' + CN[r]
        return s + cn(r)
    return str(n)


ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_forbidden-1953.md")
SLUG = "forbidden-1953"
EXPECT_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 115

# ---- OG_VER：開工那一刻現讀，不再進位 ----
# 本輪海報八件套已於入庫前生成，並行線改動已將 OG_VER 推到 f。
# 直接使用當前 OG_VER，避免海報版本與 body img ?v= 錯位。
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

# --- 輯內已上線篇數現算，填 {{PREV_COUNT}} 佔位符 ---
PUB = [p for p in ps if p.get("series") == "macau-film" and p.get("status") != "整理中"]
PREV_CN = cn(len(PUB))
lines = [l.replace("{{PREV_COUNT}}", PREV_CN) for l in lines]
print("輯內已上線 %d 篇 -> 佔位符填「%s」" % (len(PUB), PREV_CN))

body = "\n".join(lines).strip("\n")
assert body.count("![") == 0, "草稿含 markdown 圖片語法"
assert "{{PREV_COUNT}}" not in body, "仍有未替換的佔位符"
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
# 如果 newnum 已經在 SLUGS 裡（本輪被並行線預支），不要重複插入
tail_nums = [k for k in todo if k != str(newnum)]
add = ["%s'%s': '%s'," % (indent, k, slug_of[k]) for k in tail_nums]
s = s[:anchor.end()] + "\n" + "\n".join(add) + s[anchor.end():]

for k in set(todo):
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

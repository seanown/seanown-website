# -*- coding: utf-8 -*-
"""《Forbidden》(1953) 改稿：以草稿重寫 posts.json 的 body（num／SLUGS／date 全不動）。

背景：軒哥 2026-09-30 指示「不要再寫第 N 篇、也不要再用『不在場的澳門』框架，
改從角色切入」→ 第一節改為 Victor Sen Yung 飾的鋼琴師 Allan（全片唯一執法者），
原第五節「鋼琴師是警察」改為「你在澳門贏不了他的」，並移除全部篇數指稱。
"""
import json, re, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "_draft_forbidden-1953.md")
SLUG = "forbidden-1953"

_s = open(BA, encoding="utf-8").read()
VER = re.search(r"OG_VER = '([0-9a-z]+)'", _s).group(1)
print("OG_VER", VER)

raw = open(DRAFT, encoding="utf-8").read()
lines = raw.split("\n")
title = lines[2].lstrip("# ").strip()
subtitle = lines[4].replace("## ", "").strip()
print("title", title)
print("subtitle", subtitle)

body = "\n".join(lines).strip("\n")
assert body.count("![") == 0, "草稿含 markdown 圖片語法"
assert "{{PREV_COUNT}}" not in body, "仍有未替換的佔位符"
# 引句框兩行必須緊鄰
body = re.sub(r"(>\s*[^\n]*)\n\n(>\s*——)", r"\1\n\2", body)
# img 的 ?v= 對齊現值
body, n = re.subn(r"(" + SLUG + r"-poster\.jpg\?v=)[0-9a-zA-Z]+", r"\g<1>" + VER, body)
assert n == 1, "海報 img 的 ?v= 替換次數異常：%d（應為 1）" % n

d = json.load(open(PJ, encoding="utf-8"))
ps = d["posts"]
hit = [p for p in ps if p["slug"] == SLUG]
assert len(hit) == 1, "找不到或重複：%s (%d)" % (SLUG, len(hit))
p = hit[0]
before = len(p["body"])
p["title"] = title
p["subtitle"] = subtitle
p["body"] = body
json.dump(d, open(PJ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("body %d -> %d chars" % (before, len(body)))

# 複核
d2 = json.load(open(PJ, encoding="utf-8"))
q = [x for x in d2["posts"] if x["slug"] == SLUG][0]
assert q["num"] == p["num"], "num 被動到"
print("複核：num=%s | %s | body %d chars" % (q["num"], SLUG, len(q["body"])))
i_s = q["body"].find("散場之後")
i_a = q["body"].find("跟著電影遊澳門")
assert i_s > i_a > 0, "篇序錯位：散場之後必須在附錄之後"
print("篇序 OK：附錄 %d < 散場之後 %d" % (i_a, i_s))
bq = re.findall(r"^> (.+)$", q["body"], re.M)
print("金句框", len([x for x in bq if not x.startswith("——")]))
print("座標", len(re.findall(r"22\.\d{4,}, ?113\.\d{4,}", q["body"])))

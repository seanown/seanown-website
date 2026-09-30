# -*- coding: utf-8 -*-
"""《Aspectos de Macau》(1923) 改稿：以草稿重寫 posts.json 的 body（num／SLUGS／date 全不動）。

背景：軒哥 2026-09-30 上線後微調「散場之後」段——修視角 bug（作者即軒哥，不寫「軒哥點了它」），
並把「這輯」明確為「這電影專輯」。以 _update_forbidden_body.py 為底，DRAFT 指向 drafts/。
"""
import json, re, os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
PJ = os.path.join(ROOT, "data", "posts.json")
BA = os.path.join(ROOT, "tools", "build_articles.py")
DRAFT = os.path.join(ROOT, "drafts", "aspectos-de-macau-1923.body.md")
SLUG = "aspectos-de-macau-1923"

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
print("金句框", len([x for x in re.findall(r"^> (.+)$", q["body"], re.M) if not x.startswith("——")]))
print("座標", len(re.findall(r"22\.\d{4,}, ?11[34]\.\d{4,}", q["body"])))
# 新稿關鍵句
print("含『軒哥點了它』(應為 0):", q["body"].count("軒哥點了它"))
print("含『這電影專輯』(應為 1):", q["body"].count("這電影專輯"))

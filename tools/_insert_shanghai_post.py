# -*- coding: utf-8 -*-
"""#67《上海驚情》Stage 3 入庫：status 整理中→已上線、date=上線日、body 前插 raw HTML 海報 img。

鐵律：
- 正文海報一律用 raw HTML <img>（markdown img 會被 md_to_html 丟掉，#68 教訓）
- posts.json 的 num 欄位保持原格式（字串/整數並存），不可被 json 往返轉型
- OG_VER 不升版：本篇為全新 slug 檔名，無既有快取問題，避免全站 ?v= 一齊變動
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "posts.json")
SLUG = "shanghai-surprise-1986"

IMG = ('<img src="../../assets/og/shanghai-surprise-1986-poster.jpg?v=20260930b" '
       'alt="《上海驚情》電影海報" '
       'style="column-span:all;width:min(100%,520px);display:block;margin:8px auto 28px;border-radius:10px">')

with io.open(PATH, encoding="utf-8") as f:
    d = json.load(f)

p = next(x for x in d["posts"] if x.get("slug") == SLUG)
assert p["status"] == "整理中", "unexpected status: %s" % p["status"]

if not p["body"].startswith("<img "):
    p["body"] = IMG + "\n\n" + p["body"]
p["status"] = "已上線"
p["date"] = "2026-09-30"

with io.open(PATH, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# 覆核：num 型別未被打散
types = {}
for x in d["posts"]:
    types.setdefault(type(x["num"]).__name__, []).append(x["num"])
print("num types:", {k: len(v) for k, v in types.items()})
print("target num:", repr(p["num"]), type(p["num"]).__name__)

# 輯內序號現算（排除整理中，依 date/num）
def key(x):
    return (x.get("date", ""), int(str(x["num"])))

mf = [x for x in d["posts"] if x.get("series") == "macau-film"]
pub = sorted([x for x in mf if x.get("status") != "整理中"], key=key)
slugs = [x["slug"] for x in pub]
print("macau-film published:", len(pub))
print("position:", slugs.index(SLUG) + 1, "/", len(pub))
print("body md img:", p["body"].count("!["), "| quotes:", p["body"].count("\n> "), "| h3:", p["body"].count("\n### "))
print("DONE")

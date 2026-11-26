# -*- coding: utf-8 -*-
"""#68《憨豆先生大戰特務》入庫 posts.json（2026-09-29 上線）。"""
import json, io

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
DRAFT = ROOT + r"\_draft_66_johnny-english-reborn.md"
POSTS = ROOT + r"\data\posts.json"
SLUG = "johnny-english-reborn-2011"
NUM = 68
VER = "20260929m"

raw = io.open(DRAFT, encoding="utf-8").read()
lines = raw.split("\n")
# 去掉開頭 # 主標 與 ## 副標 兩行（進 title/subtitle 欄位）
assert lines[0].startswith("# 《憨豆先生大戰特務》觀後感"), lines[0]
assert lines[2].startswith("## 副標："), lines[2]
body = "\n".join(lines[3:]).strip()

poster = ('<img src="../../assets/og/' + SLUG + '-poster.jpg?v=' + VER +
          '" alt="《憨豆先生大戰特務》電影海報" '
          'style="column-span:all;width:min(100%,520px);display:block;'
          'margin:8px auto 28px;border-radius:10px">')
body = poster + "\n\n" + body

entry = {
    "num": NUM,
    "title": "《憨豆先生大戰特務》觀後感",
    "subtitle": "澳門的金菠蘿，收留了一個笨特工｜2011",
    "slug": SLUG,
    "series": "macau-film",
    "category": "澳門電影",
    "date": "2026-09-29",
    "location": "澳門",
    "status": "已上線",
    "images": ["assets/og/" + SLUG + ".jpg"],
    "body": body,
}

data = json.load(io.open(POSTS, encoding="utf-8"))
assert not any(str(p.get("num")) == str(NUM) for p in data["posts"]), "num 撞號！"
assert not any(p.get("slug") == SLUG for p in data["posts"]), "slug 撞號！"
data["posts"].append(entry)

with io.open(POSTS, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("posts.json 已入庫：num", NUM, "| body", len(body), "chars | 總篇數", len(data["posts"]))

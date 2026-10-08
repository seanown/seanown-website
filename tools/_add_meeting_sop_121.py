# -*- coding: utf-8 -*-
"""把「高效會議主持 SOP」寫入 data/posts.json（num 121，青年實戰第 7 篇）。

頁面結構（依軒哥 2026-10-08 確認）：
  ① 本堂重點（三句話）→ keypoints 欄位，由 build_keypoints() 插在正文前
  ② 正文五節→ body
  ③ 附錄 SOP 十節        → body 尾部
  ④ 演講稿 14 頁         → deck 欄位，由 build_deck() 插在正文後
"""
import io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'drafts', '108-高效會議主持SOP.md')
DST = os.path.join(ROOT, 'data', 'posts.json')
NUM = '121'
SLUG = 'meeting-ends-things-begin'

CAPS = [
    '會議不是討論，是一筆要交付結果的交易',
    '本堂講什麼：三章十四頁',
    '第一章｜我們把會開成了什麼',
    '四個小時的真正去向',
    '真正用於決策的時間，不超過十五分鐘',
    '第二章｜主持人不是最會講的人',
    '主持人的三個「不是」',
    '主持節奏：五段口訣',
    '現場：把話從自己嘴裡轉到別人嘴裡',
    '第三章｜會議結束了，事情才開始',
    '正式會議決策流程八步',
    '討論與表決，是兩個階段',
    '附錄：前二十四小時檢核',
    '第一堂 · 高效會議主持 SOP 總表',
]

def main():
    body = io.open(SRC, encoding='utf-8').read()

    with io.open(DST, encoding='utf-8') as f:
        data = json.load(f)
    posts = data['posts']

    if any(str(p.get('num')) == NUM for p in posts):
        print('num %s 已存在，中止' % NUM); sys.exit(1)
    if any(p.get('slug') == SLUG for p in posts):
        print('slug %s 已存在，中止' % SLUG); sys.exit(1)

    entry = {
        "num": 121,
        "title": "會議結束了，事情才開始",
        "subtitle": "第一堂 · 高效會議主持 SOP｜把會議從流程還原成一筆要交付結果的交易",
        "category": "生活隨筆",
        "date": "2026-10-08",
        "location": "澳門",
        "status": "已上線",
        "images": ["assets/images/posts/deck-meeting-sop/deck-01.jpg"],
        "body": body,
        "slug": SLUG,
        "series": "youth-crossover",
        "keypoints": [
            "主持人不是最會講的人，是讓會議產生結果的人。",
            "開場快、內容穩、轉場快、高潮慢、結尾快而有力。",
            "散會前一定要把「誰、做什麼、何時完成」白紙黑字定下來。",
        ],
        "deck": {
            "title": "高效會議主持 SOP",
            "hint": "把整堂課拆成十四頁：三章正文＋一本可列印的現場操作手冊，"
                    "下方任選一頁可全屏放映。",
            "pages": [
                {"img": "assets/images/posts/deck-meeting-sop/deck-%02d.jpg" % (i + 1), "cap": c}
                for i, c in enumerate(CAPS)
            ],
        },
    }
    posts.append(entry)

    with io.open(DST, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))

    print('已寫入 num %s ｜ %s' % (NUM, entry['title']))
    print('  series   : youth-crossover（青年實戰，第 7 篇）')
    print('  category : 生活隨筆')
    print('  body 字數: %d' % len(body))
    print('  keypoints: %d 句' % len(entry['keypoints']))
    print('  deck: %d 頁' % len(entry['deck']['pages']))
    print('  posts 總數: %d' % len(posts))


if __name__ == '__main__':
    main()
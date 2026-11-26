# -*- coding: utf-8 -*-
"""把第二堂文章寫入 posts.json（num 122）。

🔴 為何用Python 而不是手改：
posts.json 是 108 篇的資料源，內嵌 JSON 若被寫壞會讓首頁文章列表全空
（2026-09-03 曾因此空白一週）。用 json.load/json.dump 保證格式正確。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'drafts', '122-商務禮儀與典禮SOP.md')
DST = os.path.join(ROOT, 'data', 'posts.json')

TITLE = '禮儀不是形式，是讓每個人被舒服地對待'
SUBTITLE = '第二堂 · 商務禮儀與典禮SOP｜五種典禮的底層邏輯與現場應變'
SLUG = 'etiquette-is-not-form'
CATEGORY = '生活隨筆'
SERIES = 'youth-crossover'
DATE = '2026-10-08'
LOCATION = '澳門'
COVER = 'assets/images/posts/122-cover.jpg'
DECK_TITLE = '第二堂 · 商務禮儀與典禮 SOP'
DECK_DIR = 'deck-etiquette-122'

KEYPOINTS = [
    '禮儀不是形式，是讓每個人站在他應該站的位置上，被尊重，也舒服。',
    '右為尊、中為大、左右左——判定基準是「請看你的左右手」，不是觀眾的視角。',
    '對外涉外右為上、對內政務左為上；分不清時，上台前問一句最可靠。',
]


def md_to_html(md):
    """把草稿 Markdown 轉成 HTML，走與 build_articles.py 相同規則：
    - 表格必須是 GFM 表格（有序列表會被判定違禁條列）
    - 二級標題成<section>
    """
    lines = md.split('\n')
    out = []
    i = 0
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append('</ul>')
            in_ul = False

    while i < len(lines):
        ln = lines[i].rstrip()

        # GFM 表格
        if ln.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|?\s*$', lines[i + 1]):
            close_ul()
            head = [c.strip() for c in ln.strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            out.append('<div class="tbl-wrap"><table>')
            out.append('<thead><tr>' + ''.join('<th>%s</th>' % h for h in head) + '</tr></thead>')
            out.append('<tbody>')
            for r in rows:
                out.append('<tr>' + ''.join('<td>%s</td>' % c for c in r) + '</tr>')
            out.append('</tbody></table></div>')
            continue

        # 二級標題
        if ln.startswith('## '):
            close_ul()
            t = ln[3:].strip()
            out.append('<h2>%s</h2>' % t)
            i += 1
            continue

        # 三級標題
        if ln.startswith('### '):
            close_ul()
            out.append('<h3>%s</h3>' % ln[4:].strip())
            i += 1
            continue

        # 引用（金句）
        if ln.startswith('> '):
            close_ul()
            out.append('<blockquote>%s</blockquote>' % ln[2:].strip())
            i += 1
            continue

        # 無序列表
        if ln.strip().startswith('- '):
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append('<li>%s</li>' % ln.strip()[2:].strip())
            i += 1
            continue

        close_ul()
        if ln.strip():
            out.append('<p>%s</p>' % ln.strip())
        i += 1

    close_ul()
    return '\n'.join(out)


def main():
    raw = open(SRC, encoding='utf-8').read()

    # 去掉標題行與「來源／適用」兩個引用行（它們是素材註記，不進正文）
    body_md = re.sub(r'^# .*\n+', '', raw)
    body_md = re.sub(r'^> (來源|適用)：.*\n?', '', body_md, flags=re.M)
    #🔴 草稿裡附錄標題誤寫「第一堂」，這是第二堂 → 直接改正
    body_md = body_md.replace('附錄：第一堂 · 商務禮儀與典禮 SOP',
                              '附錄：第二堂 · 商務禮儀與典禮 SOP')
    body_html = md_to_html(body_md)

    data = json.load(open(DST, encoding='utf-8'))
    posts = data['posts']

    # 防重複
    if any(str(p.get('num')) == '122' for p in posts):
        print('!! num 122 已存在，中止')
        return
    if any(p.get('slug') == SLUG for p in posts):
        print('!! slug 已存在，中止')
        return

    entry = {
        'num': 122,
        'title': TITLE,
        'subtitle': SUBTITLE,
        'category': CATEGORY,
        'date': DATE,
        'location': LOCATION,
        'status': '已上線',
        'images': [COVER],
        'body': body_html,
        'slug': SLUG,
        'series': SERIES,
        'keypoints': KEYPOINTS,
        'deck': {
            'title': DECK_TITLE,
            'hint': '14 頁演講稿',
            'pages': [
                {'img': '%s/deck-%02d.jpg' % (DECK_DIR, n), 'cap': cap}
                for n, cap in [
                    (1, '禮儀不是形式，是讓每個人被舒服地對待'),
                    (2, '今天談什麼'),
                    (3, '被尊重，也舒服'),
                    (4, '台上那三秒鐘'),
                    (5, '排位置的底碼：九個字'),
                    (6, '章節：排位'),
                    (7, '「右」是誰的右'),
                    (8, '兩套規則，相反'),
                    (9, '五種場景，五套邏輯'),
                    (10, '章節：五種場景'),
                    (11, '宴會五細節與頒獎六步'),
                    (12, '出狀況怎麼辦'),
                    (13, '講的不是動作，而是分寸'),
                    (14, '附錄：完整 SOP 總表'),
                ]
            ],
        },
    }
    posts.append(entry)
    data['posts'] = posts

    with open(DST, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 驗證
    chk = json.load(open(DST, encoding='utf-8'))['posts']
    mine = [p for p in chk if str(p.get('num')) == '122'][0]
    n = len(re.sub(r'<[^>]+>', '', mine['body']))
    print('寫入完成')
    print('  文章總數: %d' % len(chk))
    print('  num 122 散文淨字數: %d' % n)
    print('  keypoints: %d 條' % len(mine['keypoints']))
    print('  deck 頁數: %d' % len(mine['deck']['pages']))
    print('  JSON 重新解析: OK')


if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-
"""把第三堂文章寫入 posts.json（num 123）。

🔴 與 122 版相同的 md_to_html 轉換器（避免兩份邏輯不一致）。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'drafts', '123-領導力傳承與危機管理.md')
DST = os.path.join(ROOT, 'data', 'posts.json')

TITLE = '領導是做對的事，管理是把事做對'
SUBTITLE = '第三堂 · 商會幹部領導力與危機管理｜從做對的事到交出位置'
SLUG = 'leadership-and-crisis'
CATEGORY = '澳門觀察'
SERIES = 'youth-crossover'
DATE = '2026-10-08'
LOCATION = '澳門'
COVER = 'assets/images/posts/123-cover.jpg'
DECK_TITLE = '第三堂 · 商會幹部領導力與危機管理'
DECK_DIR = 'deck-leadership-123'

KEYPOINTS = [
    '領導是做對的事，管理是把事做對——但商會的權力來源是人心，不是職位。',
    '組織的資產不是錢、不是場地，是信任；危機時提領的就是你當初存進去的。',
    '真正的傳承不是交位置，是把經驗、信任、責任一起交出去。',
]


def md_to_html(md):
    """Markdown → HTML。表格必須是 GFM（有序列表會被判定違禁條列）。"""
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

        if ln.startswith('## '):
            close_ul(); out.append('<h2>%s</h2>' % ln[3:].strip()); i += 1; continue
        if ln.startswith('### '):
            close_ul(); out.append('<h3>%s</h3>' % ln[4:].strip()); i += 1; continue
        if ln.startswith('> '):
            close_ul(); out.append('<blockquote>%s</blockquote>' % ln[2:].strip()); i += 1; continue
        if ln.strip().startswith('- '):
            if not in_ul:
                out.append('<ul>'); in_ul = True
            out.append('<li>%s</li>' % ln.strip()[2:].strip()); i += 1; continue

        close_ul()
        if ln.strip():
            out.append('<p>%s</p>' % ln.strip())
        i += 1

    close_ul()
    return '\n'.join(out)


def main():
    raw = open(SRC, encoding='utf-8').read()
    body_md = re.sub(r'^# .*\n+', '', raw)
    body_md = re.sub(r'^> (來源|適用)：.*\n?', '', body_md, flags=re.M)
    body_html = md_to_html(body_md)

    data = json.load(open(DST, encoding='utf-8'))
    posts = data['posts']

    if any(str(p.get('num')) == '123' for p in posts):
        print('!! num 123 已存在，中止'); return
    if any(p.get('slug') == SLUG for p in posts):
        print('!! slug 已存在，中止'); return

    caps = [
        (1, '領導是做對的事，管理是把事做對'),
        (2, '今天談什麼'),
        (3, '組織的資產是信任'),
        (4, '辦活動不等於解決問題'),
        (5, '領導力三個基本功'),
        (6, '章節：衝突與團隊'),
        (7, '領導與管理的分野'),
        (8, '衝突處理三步走'),
        (9, 'SBI 回饋法與雁隊理論'),
        (10, '六種商數'),
        (11, '危機五個心'),
        (12, '傳承不是交位置'),
        (13, '留下的是人，不是活動'),
        (14, '附錄：完整 SOP 總表'),
    ]
    entry = {
        'num': 123,
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
            'pages': [{'img': '%s/deck-%02d.jpg' % (DECK_DIR, n), 'cap': c} for n, c in caps],
        },
    }
    posts.append(entry)
    data['posts'] = posts
    with open(DST, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    chk = json.load(open(DST, encoding='utf-8'))['posts']
    mine = [p for p in chk if str(p.get('num')) == '123'][0]
    n = len(re.sub(r'<[^>]+>', '', re.sub(r'<table>[\s\S]*?</table>', '', mine['body'])))
    print('寫入完成')
    print('  文章總數: %d' % len(chk))
    print(' 散文淨字數: %d' % n)
    print('  keypoints: %d 條' % len(mine['keypoints']))
    print('  deck 頁數: %d' % len(mine['deck']['pages']))
    print('  有序列表 <ol>: %d（必須 0）' % mine['body'].count('<ol'))
    print(' JSON 重新解析: OK')


if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-
"""把《「琉光璃彩」淄博琉璃藝術展澳門開幕》寫入 data/posts.json。

num=132（max(num)=131，130 為歷史缺號）；slug=luminous-brilliance-zibo-liuli；
category=生活隨筆、series=life-essays、single_col=true；29 張現場照已由
tools/_conv_132.py 轉入 assets/images/posts/132-N.jpg（#1=陳莉致辭、#29=開幕主視覺）。
冪等：已存在同 slug／num 則跳過。用法：python tools/_inject_132.py [num]
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BODY = os.path.join(ROOT, 'tools', '_body_132.md')
NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 132
SLUG = 'luminous-brilliance-zibo-liuli'


def main():
    with io.open(POSTS, encoding='utf-8') as f:
        d = json.load(f)
    posts = d['posts']
    if any(str(p.get('num')) == str(NUM) or p.get('slug') == SLUG for p in posts):
        print('already injected, skip')
        return
    with io.open(BODY, encoding='utf-8') as f:
        body = f.read().strip()
    assert '\u3000' not in body, 'body 不應含全角空格'
    assert '{{' not in body and '待補' not in body, 'body 不應有佔位符'
    imgs = ['assets/images/posts/%d-%d.jpg' % (NUM, i) for i in range(1, 30)]
    for rel in imgs:
        assert os.path.isfile(os.path.join(ROOT, rel)), 'missing ' + rel
    post = {
        'title': '「琉光璃彩」淄博琉璃藝術展澳門開幕',
        'subtitle': '三千年的窯火，讓澳門多一扇面向世界的窗｜2026',
        'category': '生活隨筆',
        'date': '2026-10-16',
        'location': '澳門 · 保利美高梅博物館',
        'images': imgs,
        'body': body,
        'status': '已上線',
        'num': NUM,
        'slug': SLUG,
        'series': 'life-essays',
        'single_col': True,
    }
    posts.append(post)
    with io.open(POSTS, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('injected num=%d slug=%s, total posts=%d' % (NUM, SLUG, len(posts)))


if __name__ == '__main__':
    main()

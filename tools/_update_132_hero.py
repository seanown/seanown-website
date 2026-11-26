# -*- coding: utf-8 -*-
"""#132 換抬頭：images[0] 改用開幕主視覺（原 132-29 內容，已重編為 132-1.jpg）。

軒哥 2026-10-16 01:33 指示「文章的抬頭也用這一個重新改」——他貼的截圖與
132-29.jpg 同一機位（341×240 小圖），故直接用全分辨率原圖當 hero，29 張舊照
整體後移保持原順序（舊 1→新 2 … 舊 29→新 30）。冪等。
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SLUG = 'luminous-brilliance-zibo-liuli'
N = 30


def main():
    with io.open(POSTS, encoding='utf-8') as f:
        d = json.load(f)
    post = next((p for p in d['posts'] if p.get('slug') == SLUG), None)
    assert post, 'slug not found: ' + SLUG
    want = ['assets/images/posts/132-%d.jpg' % i for i in range(1, N + 1)]
    for rel in want:
        assert os.path.isfile(os.path.join(ROOT, rel)), 'missing ' + rel
    if post.get('images') == want:
        print('already updated, skip')
        return
    assert post.get('images') == ['assets/images/posts/132-%d.jpg' % i for i in range(1, 30)], \
        'images 陣列不符合預期，終止'
    post['images'] = want
    with io.open(POSTS, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('updated images: 30 entries, hero = 132-1.jpg（開幕主視覺）')


if __name__ == '__main__':
    main()

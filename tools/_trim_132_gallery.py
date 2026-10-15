# -*- coding: utf-8 -*-
"""#132 移除圖廊收尾重複圖：images 由 30 項降為 29 項。

背景（2026-10-16 軒哥確認移除）：換抬頭時舊 132-29（開幕主視覺）的內容
同時留在新 132-1（hero）與新 132-30（圖廊最後一張），讀者會看到同一張
圖出現兩次。移除圖廊那張，回到軒哥原本 29 張照片的篇貌（hero 1＋圖廊 28）。

其餘 29 條 URL 內容不變（hero 132-1 與圖廊 132-2..132-29 都沒動），
故不升 ?v= 版本號；只刪陣列末項。132-30.jpg 檔案本身 git rm（成為孤兒檔）。
冪等。
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SLUG = 'luminous-brilliance-zibo-liuli'
DROP = 'assets/images/posts/132-30.jpg?v=2'
N_AFTER = 29


def main():
    with io.open(POSTS, encoding='utf-8') as f:
        d = json.load(f)
    post = next((p for p in d['posts'] if p.get('slug') == SLUG), None)
    assert post, 'slug not found: ' + SLUG
    imgs = post.get('images') or []
    if len(imgs) == N_AFTER and DROP not in imgs:
        print('already trimmed, skip')
        return
    assert len(imgs) == 30, 'images 陣列非 30 項：%d' % len(imgs)
    assert imgs[-1] == DROP, '末項不是預期的重複圖：%s' % imgs[-1]
    post['images'] = imgs[:-1]
    with io.open(POSTS, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('trimmed: %d -> %d entries, dropped %s' % (len(imgs), N_AFTER, DROP))


if __name__ == '__main__':
    main()

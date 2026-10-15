# -*- coding: utf-8 -*-
"""#132 圖片破快取：images 全部附 ?v=2。

背景（2026-10-16 軒哥回報「抬頭還是沒換成功」）：
排查後確認伺服器端早已正確——線上 article 頁 HTML 引用 132-1.jpg，
curl 下下來的 132-1.jpg 就是開幕典禮主視覺（1320×990）。真正原因是
netlify.toml 對 /assets/* 設了一年 immutable 快取，而換抬頭那次重編號
（舊 1→新 2 … 舊 29→新 1）等於 30 個 URL 全部「同檔名換內容」，
瀏覽器一年內都不會重新抓，只看得到舊的陳莉致辭照。

og 圖用 ?v=OG_VER 破快取是同一坑（2026-09-28 踩過）；這裡對單篇圖片設版本：
posts.json images 附 ?v=2 後，文章頁 hero/gallery、輯頁縮圖（tl_img）、
首頁卡（wsrc 的正則對帶 query 路徑不再轉 .webp，直出版本化 jpg，反而少一次
注定 404 的 webp 請求）全部換成新 URL，任何訪客（含軒哥，普通重整載入即可，
HTML 是 must-revalidate）都會拿到新版。

版本號語意：2 = 第二版圖序（換抬頭重編號後）。下次再換內容升 3。冪等。
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SLUG = 'luminous-brilliance-zibo-liuli'
VER = '2'
N = 30


def main():
    with io.open(POSTS, encoding='utf-8') as f:
        d = json.load(f)
    post = next((p for p in d['posts'] if p.get('slug') == SLUG), None)
    assert post, 'slug not found: ' + SLUG
    imgs = post.get('images') or []
    assert len(imgs) == N, 'images 陣列非 %d 項：%d' % (N, len(imgs))
    base = ['assets/images/posts/132-%d.jpg' % i for i in range(1, N + 1)]
    want = [x + '?v=' + VER for x in base]
    if post.get('images') == want:
        print('already versioned, skip')
        return
    # 允許「乾淨路徑」或「已帶其他版本」兩種起點，但后者先檢查版本號
    if all(('?v=' in x) for x in imgs):
        old_ver = imgs[0].split('?v=')[-1]
        assert old_ver != VER, '版本號未變，終止'
        print('note: 舊版本 ?v=%s → 新版本 ?v=%s' % (old_ver, VER))
    post['images'] = want
    with io.open(POSTS, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('versioned %d image URLs with ?v=%s' % (len(want), VER))


if __name__ == '__main__':
    main()

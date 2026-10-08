# -*- coding: utf-8 -*-
"""檢查 sitemap 完整性：posts.json 中所有「已上線」文章都必須出現在 sitemap.xml。

背景：sitemap.xml 是手動維護的（沒有生成腳本），2026-10-09 發現
#122/#123兩篇已上線文章漏了，導致搜尋引擎抓不到。這支腳本就是為杜絕同類問題。

用法：python tools/check_sitemap.py
離線模式（只比對本機檔案）→ exit 0/1
"""
import json, re, sys, os, argparse
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SITEMAP = os.path.join(ROOT, 'sitemap.xml')
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'


def collect_sitemap_locs(path):
    """回傳 sitemap 內所有 <loc> 文字。"""
    txt = open(path, encoding='utf-8').read()
    try:
        root = ET.fromstring(txt)
        return {e.text.strip() for e in root.iter(NS + 'loc') if e.text}
    except ET.ParseError as e:
        print(f'  [FAIL] sitemap.xml 不是合法 XML：{e}')
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-online', action='store_true',
                    help='直接抓線上 sitemap 比對（部署後用）')
    a = ap.parse_args()

    data = json.load(open(POSTS, encoding='utf-8'))
    posts = data['posts']
    online = [p for p in posts if p.get('status') == '已上線']

    print('=' * 60)
    print('sitemap 完整性檢查')
    print('=' * 60)
    print(f'  posts.json 總篇數：{len(posts)}')
    print(f'  status=已上線　　：{len(online)}')

    if a.check_online:
        import urllib.request
        target = 'https://seanown.org/sitemap.xml'
        print(f'  來源：線上 {target}')
        raw = urllib.request.urlopen(target, timeout=30).read().decode('utf-8')
        try:
            root = ET.fromstring(raw)
            locs = {e.text.strip() for e in root.iter(NS + 'loc') if e.text}
        except ET.ParseError as e:
            print(f'  [FAIL] 線上 sitemap 不是合法 XML：{e}')
            return 1
    else:
        target = SITEMAP
        print(f'  來源：本機 {SITEMAP}')
        locs = collect_sitemap_locs(SITEMAP)
        if locs is None:
            return 1

    print(f'  sitemap 內 <loc> 條目：{len(locs)}')

    # 反向：sitemap 有但posts.json 沒有（多半是頁面刪了但沒清sitemap）
    valid = set()
    for p in online:
        slug = p.get('slug') or f"post-{p['num']}"
        valid.add(f'https://seanown.org/article/{slug}/')

    missing = sorted(valid - locs)
    # 只針對 article/ 開頭比對，其他類型頁面（/movie/、/book/）不納入
    art_in_sitemap = {u for u in locs if '/article/' in u}
    orphan = sorted(art_in_sitemap - valid)

    print()
    if missing:
        print(f'  [FAIL] 已上線但不在 sitemap：{len(missing)} 篇')
        for u in missing:
            n = u.split('/article/')[1].strip('/')
            print(f'         {u}')
    else:
        print(f'  [PASS] 所有已上線文章都在sitemap（{len(valid)} 篇）')

    if orphan:
        print(f'  [WARN] sitemap 有、但 posts.json 查無此篇：{len(orphan)} 篇')
        for u in orphan:
            print(f'         {u}')
    else:
        print('  [PASS] sitemap 內無孤兒條目')

    # 完整性：沒有重複 loc
    dup = len(locs) != len(set(locs))
    if len(list(locs)) != len(locs):
        print(f'  [WARN] sitemap 有重複 <loc>')

    print()
    print('=' * 60)
    print('結果：' + ('ALL PASS' if not missing and not orphan else 'FAIL'))
    print('=' * 60)
    return 0 if (not missing and not orphan) else 1


if __name__ == '__main__':
    sys.exit(main())
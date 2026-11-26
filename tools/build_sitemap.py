# -*- coding: utf-8 -*-
"""自動檢查並補齊 sitemap.xml —— 根治「手動維護 sitemap 會漏文章」。

背景：2026-10-09 發現 #122/#123 兩篇 status=已上線 的文章沒有列進 sitemap，
搜尋引擎抓不到。根因是 sitemap.xml 為手動維護、沒有任何生成腳本。

設計原則（刻意保守）：
  **只補缺漏，不改既有條目。**
  現有 sitemap 的 lastmod / changefreq / priority 是歷年累積、人工調過的
  （實測混有 weekly/0.8、無參數、monthly/0.6 等四種組合），批量重寫會
  意外改變既有 SEO 優先級。因此本腳本：
    1. 保留全部既有 <url> 條目，順序與內容完全不動
    2. 只把「已上線但不在sitemap」的文章append 到 </urlset> 之前
    3. 附帶偵測孤兒條目（sitemap 有但 posts.json 查無）並回報，不自動刪

新增條目沿用目前最新文章的慣例：lastmod 取文章 date、monthly、priority 0.7。

用法：
  python tools/build_sitemap.py            # 檢查＋補齊並寫入本機 sitemap.xml
  python tools/build_sitemap.py --check    # 唯讀檢查本機，有缺漏 exit 1
  python tools/build_sitemap.py --check-online   # 唯讀檢查線上 sitemap
"""
import io, json, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SITEMAP = os.path.join(ROOT, 'sitemap.xml')
SITE = 'https://seanown.org'

ENTRY_RE = re.compile(r'<\s*url\s*>.*?<\s*/\s*url\s*>', re.S)
LOC_RE = re.compile(r'<loc>\s*(.*?)\s*</loc>', re.S)

# 新增文章條目的固定參數（沿用 2026-10 新增條目的慣例）
NEW_CF = 'monthly'
NEW_PRI = '0.7'


def load_online():
    """回傳 [(slug, date_str, num)]，只含 status=已上線 且有 slug 的文章。"""
    data = json.load(io.open(POSTS, encoding='utf-8'))
    out, noslug = [], []
    for p in data['posts']:
        if p.get('status') != '已上線':
            continue
        slug = (p.get('slug') or '').strip()
        if not slug:
            noslug.append(p.get('num'))
            continue
        out.append((slug, (p.get('date') or '').strip(), str(p.get('num', ''))))
    # 日期新到舊；同日依 num 數字新到舊
    def key(it):
        try:
            n = int(it[2])
        except (TypeError, ValueError):
            n = 0
        return (it[1] or '0000-00-00', n)
    out.sort(key=key, reverse=True)
    return out, noslug


def fetch_online_sitemap():
    import urllib.request
    url = SITE + '/sitemap.xml'
    raw = urllib.request.urlopen(url, timeout=30).read().decode('utf-8')
    return raw


def analyse(txt, online):
    """回傳 (existing_locs, missing, orphan)。"""
    entries = ENTRY_RE.findall(txt)
    locs = []
    for e in entries:
        m = LOC_RE.search(e)
        if m:
            locs.append(m.group(1).strip())
    have = set(locs)
    want = {'%s/article/%s/' % (SITE, s): (s, d, n) for s, d, n in online}

    missing = []
    for u, meta in want.items():
        if u not in have:
            missing.append((u, meta))
    art_have = {u for u in have if '/article/' in u}
    orphan = sorted(art_have - set(want))
    return entries, missing, orphan


def main():
    check_only = '--check' in sys.argv
    on_line = '--check-online' in sys.argv

    if on_line:
        txt = fetch_online_sitemap()
        src = '線上 ' + SITE + '/sitemap.xml'
    else:
        txt = io.open(SITEMAP, encoding='utf-8').read()
        src = '本機 sitemap.xml'

    online, noslug = load_online()
    entries, missing, orphan = analyse(txt, online)

    print('=' * 62)
    print('sitemap 自動檢查（只補缺漏，不改既有條目）')
    print('=' * 62)
    print(f'  來源：{src}')
    print(f'  posts.json 已上線：{len(online)} 篇')
    print(f'  sitemap 既有條目：{len(entries)} 條')

    if noslug:
        print(f'  ⚠ 已上線但沒有 slug（無法生成網址）：{noslug}')

    if missing:
        print()
        print(f'  [缺漏] 已上線但不在 sitemap：{len(missing)} 篇')
        for u, (slug, d, n) in missing:
            print(f'     + /article/{slug}/   （#{n}  {d}）')
    else:
        print('  [OK] 所有已上線文章都在 sitemap')

    if orphan:
        print()
        print(f'  [WARN] sitemap 有、但 posts.json 查無此篇：{len(orphan)} 篇')
        for u in orphan:
            print(f'     ? {u}')
        print('     → 需人工確認是文章下架還是 slug 改過（不自動刪）')

    # --- 寫入模式 ---
    if check_only or on_line:
        # --check 與 --check-online 一律唯讀：線上缺漏要靠本機 build 修正，
        # 不可直接把線上內容寫回本機檔案（否則會覆蓋本機尚未部署的改動）。
        print()
        print('  模式：唯讀檢查（不寫入）')
        bad = bool(missing or orphan or noslug)
        print('  結果：' + ('FAIL' if bad else 'ALL PASS'))
        print('=' * 62)
        return 1 if bad else 0

    if not missing:
        print()
        print('  無缺漏，sitemap.xml 未變動')
        print('=' * 62)
        return 0

    # 把新增條目插到 </urlset> 之前，縮排與現有單行條目一致
    add = []
    for u, (slug, d, n) in missing:
        lm = d or date.today().isoformat()
        add.append('  <url><loc>%s</loc><lastmod>%s</lastmod>'
                   '<changefreq>%s</changefreq><priority>%s</priority></url>'
                   % (u, lm, NEW_CF, NEW_PRI))
    idx = txt.rindex('</urlset>')
    head = txt[:idx].rstrip('\n')
    new_txt = head + '\n' + '\n'.join(add) + '\n</urlset>\n'
    io.open(SITEMAP, 'w', encoding='utf-8', newline='\n').write(new_txt)
    print()
    print(f'  已補入 {len(add)} 條到 sitemap.xml')
    print('=' * 62)
    return 0


if __name__ == '__main__':
    sys.exit(main())
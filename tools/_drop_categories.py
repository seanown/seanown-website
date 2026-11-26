#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
刪除分類体系，只留專輯。軒哥 2026-10-10 決定。

背景：/articles/ 上「專輯」與「分類」高度重疊——7 個分類裡 5 個完全等同於某個專輯。
「影評 44 + 澳門電影 39 = 83」剛好等於 macau-film 專輯的 83 篇，等於同一批文章掛兩個名。

本腳本做兩件事：
  1. 調整 series 歸屬（把跨專輯的文章收斂）
     - category == 澳門觀察 → 加入 macau-reader（澳門解碼）
     - category == 生活隨筆 且 num != 124 → 加入 youth-crossover（青年實戰）
       （#124《在南孔聖地…龍遊返鄉》經軒哥指定留在 life-essays）
  2. 清空 category 欄位
     - 前端不再顯示分類；後台欄位與原始值保留在 _category_archive.json 以備恢復

macau-film 專輯完全不動（83 篇不變）。
"""
import io, json, os, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SERIES = os.path.join(ROOT, 'data', 'series.json')
ARCHIVE = os.path.join(ROOT, 'data', '_category_archive.json')

# 保留在 life-essays 的例外（軒哥指定）
# 注意：posts.json 的 num 是「字串」不是整數，必須用字串比對，
# 否則 num in {124} 永遠 False，例外規則會失效（2026-10-10 踩過）。
KEEP_IN_LIFE = {'124'}

# 移動規則：category → 目標專輯（加入，不移除原歸屬；若原已有該專輯則不重複加）
RULES = {
    '澳門觀察': 'macau-reader',
    '生活隨筆': 'youth-crossover',
}


def main():
    raw = json.load(io.open(POSTS, encoding='utf-8'))
    # posts.json 頂層是 {"posts": [...]}，必須保留外層結構，只改裡面的文章
    wrapped = isinstance(raw, dict)
    posts = raw['posts'] if wrapped else raw
    sname = {x['id']: (x.get('name') or x.get('title'))
             for x in json.load(io.open(SERIES, encoding='utf-8')).get('series', [])}

    def slist(p):
        s = p.get('series')
        return list(s) if isinstance(s, list) else ([s] if s else [])

    before = collections.Counter()
    for p in posts:
        for x in slist(p):
            if x:
                before[x] += 1

    archive = []
    moved = []          # (num, title, series_before, series_after, reason)
    recategorized = []  # (num, category)

    for p in posts:
        num = p.get('num')
        num_s = str(num)                      # num 在 posts.json 裡是字串
        title = (p.get('title') or '')[:26]
        cat = p.get('category')
        s0 = list(slist(p))

        # ── 1. series 調整 ──
        # 軒哥指定的例外：#124《在南孔聖地…龍遊返鄉》留在 life-essays，不加青年實戰
        if num_s in KEEP_IN_LIFE:
            pass
        else:
            tgt = RULES.get(cat)
            if tgt:
                new = list(s0)
                # 1) 加入目標專輯（已在則不重複）
                if tgt not in new:
                    new.append(tgt)
                # 2) 單棲化：只移除「遷移來源專輯」，其餘原屬專輯一律保留
                #    例如 life-essays → youth-crossover：移掉 life-essays，
                #    但 cultural-ip-global → macau-reader 絕不能移掉 cultural-ip-global，
                #    否則文化出海專輯會被清空（2026-10-10 踩過）。
                if tgt == 'youth-crossover' and 'life-essays' in new:
                    new = [x for x in new if x != 'life-essays']
                if new != s0:
                    p['series'] = new
                    moved.append((num, title, s0, new,
                                  'category「%s」→ 專輯改掛「%s」'
                                  % (cat, sname.get(tgt, tgt))))

        # ── 2. 清空 category（先存檔）──
        if cat:
            archive.append({'num': num, 'slug': p.get('slug'),
                            'title': p.get('title'), 'category': cat})
            recategorized.append((num, cat))
            p['category'] = ''

    after = collections.Counter()
    for p in posts:
        for x in slist(p):
            if x:
                after[x] += 1

    # ── 寫檔（保留 {"posts": [...]} 外層結構）──
    out = {'posts': posts} if wrapped else posts
    with io.open(POSTS, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with io.open(ARCHIVE, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'note': 'category 欄位原始值備份。恢復分類時把對應 num 的 category 填回即可。',
                   'archived_at': '2026-10-10', 'items': archive},
                  f, ensure_ascii=False, indent=1)

    # ── 報告 ──
    print('=== 專輯篇數變化 ===')
    for k in sorted(before, key=lambda x: -after[x]):
        b, a = before[k], after[k]
        d = a - b
        tag = '不變' if d == 0 else ('+%d' % d if d > 0 else str(d))
        print('  %-10s %3d → %3d篇  (%s)' % (sname.get(k, k), b, a, tag))
    print('\n文章總數：%d（不變）' % len(posts))
    print('macau-film：%d → %d篇' % (
        before['macau-film'], after['macau-film']))

    print('\n=== series 調整（%d 篇）===' % len(moved))
    for num, title, s0, s1, why in moved:
        print('  #%s %s' % (num, title))
        print('      %s' % ' + '.join(s0))
        print('   →  %s' % ' + '.join(s1))
        print('      理由：%s' % why)

    print('\n=== 清空 category（%d 篇，值已備份）===' % len(recategorized))
    cc = collections.Counter(c for _, c in recategorized)
    for k, v in cc.most_common():
        print('  %-10s %3d 篇' % (k, v))
    print('\n備份：data/_category_archive.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
# -*- coding: utf-8 -*-
"""about「可以核實的數字」區塊：數字全部從資料動態生成，勿手寫。

2026-10-17 軒哥指示：「應該做 media.json 這種生成啊，這些數字都是會變的嘛。」
此前四個數字全是手寫 HTML，實測已發現兩處過時錯誤：
  · 職務數寫 13 項，頁面實際有 14 張職務卡（用「創辦人暨董事總經理」展開的主卡 + 13 項其餘，
    但可見的具名職務卡其實是 14 張）
  · 文章數寫 107 篇，posts.json 實際 119 篇

用法：python tools/build_about_facts.py [--check]
  --check 只檢查是否需要更新（不一致時 exit 1），供日後驗收用
資料來源：
  媒體數 ← data/media.json（條目數／附連結數／來源家數／可點擊連結總數／跨平台條目）
  職務數 ← about/index.html 內 role-sum 卡片數（頁面自身即為佐證）
  文章數 ← data/posts.json 已上線文章總數（posts.json 是站內全部文章的單一來源）
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABOUT = os.path.join(ROOT, 'about', 'index.html')
MEDIA_JSON = os.path.join(ROOT, 'data', 'media.json')
POSTS_JSON = os.path.join(ROOT, 'data', 'posts.json')
# 🔴 投資企業名單：軒哥 2026-10-17 指示「投資過的企業」要取代「80+ 語種」那張卡，
# 並說會另做一份完整清單。**在軒哥提供真實名單之前，此處留空——絕不填假數字或假公司名**，
# 因為「可以核實的數字」區塊的立點就是無法核實者不列。此檔存在即表示名單已備妥。
INVEST_JSON = os.path.join(ROOT, 'data', 'investments.json')


def invest_facts():
    """已投資企業：讀 data/investments.json。

    🔴 檔案不存在 → 回傳 None，代表「名單尚未提供」，此時第三張卡維持「80+ 語種」原樣，
    不做任何猜測或填補。檔案格式：
      {"investments": [{"name": "公司名", "sector": "領域", "year": "年份", "note": "備註"}]}
    """
    if not os.path.exists(INVEST_JSON):
        return None
    try:
        d = json.load(io.open(INVEST_JSON, encoding='utf-8'))
    except (ValueError, IOError):
        return None
    items = d.get('investments') or []
    if not items:
        return None
    sectors = [x.get('sector') for x in items if (x.get('sector') or '').strip()]
    years = sorted({(x.get('year') or '')[:4] for x in items if (x.get('year') or '')[:4].isdigit()})
    return {
        'n': len(items),
        # 領域分佈：同一大類（如「食品製造」）可能多家，取前綴分組後統計，避免每家自成一類
        'n_sector': len({(s or '').split('（')[0].strip() for s in sectors}) or 1,
        'sectors': sorted({(s or '').split('（')[0].strip() for s in sectors}),
        'years': ('%s–%s' % (years[0], years[-1])) if years else '',
    }


def media_facts():
    d = json.load(io.open(MEDIA_JSON, encoding='utf-8'))['media']
    total = len(d)
    with_url = sum(1 for x in d if x.get('url'))
    no_url = total - with_url
    sources = len({(x.get('source') or '').strip() for x in d if (x.get('source') or '').strip()})
    # 可點擊連結：主連結 + extra_urls
    clicks = sum(1 + len(x.get('extra_urls') or []) for x in d)
    multi = [x for x in d if x.get('extra_urls')]
    years = sorted({(x.get('date') or '')[:4] for x in d if (x.get('date') or '')[:4].isdigit()})
    return {
        'total': total, 'with_url': with_url, 'no_url': no_url,
        'sources': sources, 'clicks': clicks,
        'multi': multi, 'years': (years[0], years[-1]) if years else ('', ''),
    }


def role_count(html):
    """職務數＝頁面內具名職務卡數（role-sum），頁面自身即為可點開核實的佐證。"""
    return len(re.findall(r'<summary class="role-sum">', html))


def column_count():
    """已發布文章總數＝posts.json 內 status 為已上線者（posts.json 是站內文章單一來源）。"""
    posts = json.load(io.open(POSTS_JSON, encoding='utf-8'))['posts']
    live = [p for p in posts if (p.get('status') or '已上線') == '已上線']
    return len(live) or len(posts)


def build_blocks(mf, n_role, n_col):
    y0, y1 = mf['years']

    def multi_desc():
        if not mf['multi']:
            return ''
        parts = []
        for x in mf['multi']:
            name = re.sub(r'（.*?）', '', (x.get('source') or '')).strip()
            if name:
                parts.append(name)
        return '、'.join(parts)

    md = multi_desc()
    # md 為空時整句略過跨平台描述，避免出現「：一則同時具備…」的斷句
    cross = ('跨平台部分：%s 一則同時具備多個官方平台來源（官方網頁／Facebook／X／YouTube），'
             '全站合計 %d 個可點擊連結。' % (md, mf['clicks'])) if md else \
            '全站合計 %d 個可點擊連結。' % mf['clicks']
    # 🔴 軒哥 2026-10-17 指示：各卡下方的「佐證：…」說明屬**對內部交代**，對外不顯示。
    # 因此本區塊只輸出數字與標籤（n / l），不輸出 src。區塊副標亦已改為不提佐證。
    return (
        '<div class="n">%d 則</div>\n'
        '<div class="l">公開媒體報導（%s–%s）</div>' % (mf['total'], y0, y1)
    ), (
        '<div class="n">%d 項</div>\n'
        '<div class="l">現任企業與協會職務</div>' % n_role
    ), (
        '<div class="n">80+ 語種</div>\n'
        '<div class="l">多語種內容生成能力</div>'
    ), (
        '<div class="n">%d 篇</div>\n'
        '<div class="l">已發布文章（含 87 篇澳門電影專輯）</div>' % n_col
    )


def main():
    check = '--check' in sys.argv
    html = io.open(ABOUT, encoding='utf-8').read()

    mf = media_facts()
    n_role = role_count(html)
    n_col = column_count()

    media_b, role_b, lang_b, col_b = build_blocks(mf, n_role, n_col)
    # 第三張卡：若 investments.json 已備妥，改為「已投資企業」，否則維持「80+ 語種」
    iv = invest_facts()
    if iv:
        yr = ('（%s）' % iv['years']) if iv['years'] else ''
        lang_b = ('<div class="n">%d 項</div>\n'
                  '<div class="l">投資過的項目%s</div>' % (iv['n'], yr))
    cards_block = ('<div class="fact">\n%s\n</div>\n<div class="fact">\n%s\n</div>\n'
                  '<div class="fact">\n%s\n</div>\n<div class="fact">\n%s\n</div>'
                  % (media_b, role_b, lang_b, col_b))

    # 定位並重建整個 <div class="facts"> 區塊。
    # 🔴 結構固定（每張卡 4 行）：<div class="facts"> / 重複的 <div class="fact">…</div> /
    #    最後一行 </div></div>。故取「<div class="facts"> 行」到「第一個含兩個 </div> 的行」之間整段替換。
    lines = html.split('\n')
    try:
        i_open = next(i for i, l in enumerate(lines) if '<div class="facts">' in l)
    except StopIteration:
        print('[ERROR] about/index.html 找不到 <div class="facts"> 區塊，未改動')
        return
    i_close = None
    for i in range(i_open + 1, len(lines)):
        if lines[i].count('</div>') >= 2:
            i_close = i
            break
    if i_close is None:
        print('[ERROR] about/index.html 的 facts 區塊找不到容器收尾（</div></div>），未改動')
        return

    old_block = '\n'.join(lines[i_open:i_close + 1])
    new_block = ('<div class="facts">\n' + cards_block
                 + '\n' + lines[i_close])
    new_html = '\n'.join(lines[:i_open] + [new_block] + lines[i_close + 1:])

    # 同步「展開其餘 13 項」這類帶數字的 UI 文案
    total_roles = n_role
    first_is_summary = '創辦人暨董事總經理' in old_block or '創辦人暨董事總經理' in html
    rest = total_roles - 1 if first_is_summary else total_roles
    new_html = re.sub(r'展開其餘 \d+ 項', '展開其餘 %d 項' % rest, new_html)

    changed = (new_block != old_block)
    if check:
        if changed:
            print('[CHANGED] about/index.html 的數字需更新（跑 python tools/build_about_facts.py）')
            for k, v in (('媒體則數', mf['total']), ('附連結', mf['with_url']),
                         ('來源家數', mf['sources']), ('職務', n_role), ('專欄文章', n_col)):
                print('   %s = %s' % (k, v))
            sys.exit(1)
        print('[OK] about/index.html 數字與資料一致')
        return

    if changed:
        io.open(ABOUT, 'w', encoding='utf-8', newline='\n').write(new_html)
        print('[OK] about/index.html 已更新')
    else:
        print('[--] about/index.html 已是最新，無需改動')
    print('  媒體 %d 則／附連結 %d／來源 %d 家／可點擊連結 %d／跨平台條目 %d'
          % (mf['total'], mf['with_url'], mf['sources'], mf['clicks'], len(mf['multi'])))
    print('  職務 %d 項（展開其餘 %d 項）／專欄文章 %d 篇' % (n_role, rest, n_col))
    if iv:
        print('  投資過的項目 %d 項（第三張卡已切換）' % iv['n'])
    else:
        exists = os.path.exists(INVEST_JSON)
        print('  ⚠️ 提醒：投資項目名單尚未填入 → 第三張卡仍是「80+ 語種」。')
        print('     軒哥 2026-10-17 指示要改成「投資過的項目」，並說會另做完整名單。')
        print('     %s：把 %d 家企業逐家填進 investments 陣列，'
              % ('檔案已建立但 investments 為空' if exists else '檔案 data/investments.json 尚未建立',
                 21))
        print('     重跑本腳本即自動換卡（只需 name 必填，sector／year／stage 可選）。')
        print('     ⚠️ 在拿到真實名單前不會填入任何推測的名稱——此區塊立點為「無法核實者不列」。')


if __name__ == '__main__':
    main()

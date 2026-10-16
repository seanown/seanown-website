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
    media_src = (
        '佐證：本網站「媒體報導」頁逐則列出，共 %d 則、來源 %d 家。其中 %d 則附原文連結，'
        '另 %d 則為現場紀錄、無公開原文（已如實標註，不計入附連結數）。%s'
        % (mf['total'], mf['sources'], mf['with_url'], mf['no_url'], cross)
    )
    return (
        '<div class="n">%d 則</div>\n'
        '<div class="l">公開媒體報導（%s–%s）</div>\n'
        '<div class="src">%s</div>' % (mf['total'], y0, y1, media_src)
    ), (
        '<div class="n">%d 項</div>\n'
        '<div class="l">現任企業與協會職務</div>\n'
        '<div class="src">佐證：下方「企業職務與社會參與」點開標題即可逐項查看，'
        '包含龍遊集團、東望洋集團、粵港澳大灣區電子商會等具名機構。</div>' % n_role
    ), (
        '<div class="n">80+ 語種</div>\n'
        '<div class="l">多語種內容生成能力</div>\n'
        '<div class="src">佐證：平台技術規格（80 語種內容生成與全球投放）；'
        '語言數量以平台實際支援清單為準，非市場成效數字。</div>'
    ), (
        '<div class="n">%d 篇</div>\n'
        '<div class="l">已發布文章（含 87 篇澳門電影專輯）</div>\n'
        '<div class="src">佐證：本網站「專欄文章」與「澳門電影專輯」頁，逐篇標示日期與分類，'
        '內容公開可讀。</div>' % n_col
    )


def main():
    check = '--check' in sys.argv
    html = io.open(ABOUT, encoding='utf-8').read()

    mf = media_facts()
    n_role = role_count(html)
    n_col = column_count()

    media_b, role_b, lang_b, col_b = build_blocks(mf, n_role, n_col)
    new_block = '<div class="fact">\n%s\n</div>\n<div class="fact">\n%s\n</div>\n' \
                '<div class="fact">\n%s\n</div>\n<div class="fact">\n%s\n</div>' \
                % (media_b, role_b, lang_b, col_b)

    # 定位舊的四個 fact 區塊：從第一個 <div class="fact"> 到 fact-note 之前
    start = html.index('<div class="fact">')
    end = html.index('<p class="fact-note">')
    old_block = html[start:end]
    new_html = html[:start] + new_block + html[end:]

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


if __name__ == '__main__':
    main()

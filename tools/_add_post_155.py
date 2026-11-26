# -*- coding: utf-8 -*-
"""把《誤判》影評收進 data/posts.json（num=155, slug=the-prosecutor-2024）。

正文取 WORKBUDDY 任務整理/影評_誤判2024_草稿.md 第一個 '---' 分隔線之前的部分
（＝正文 v16 定稿，不含撰寫備註、不含上線準備包）。

冪等：已存在 num=155 時先移除再重新寫入。
防撞號：num 統一轉 int 取 max+1 並斷言 ==155；斷言 slug 未被佔用。
movieInfo.macauScenes 留空（{}）→ build_articles.py 只掛單按鈕、不渲染空場景塊。
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, 'data', 'posts.json')
DRAFT = 'C:/Users/user/WorkBuddy/WORKBUDDY 任務整理/影評_誤判2024_草稿.md'

raw = io.open(DRAFT, encoding='utf-8').read()
body = raw.split('\n---\n', 1)[0].strip()

assert body.startswith('### 一、一部本來不寫的片'), 'body 開頭不符'
assert '### 散場之後：〈那幾秒〉' in body, '散場之後標題不符'
assert '## 撰寫備註' not in body, '備註誤入 body'
assert '## 上線準備包' not in body, '準備包誤入 body'
assert body.rstrip().endswith('幾秒鐘。'), 'body 結尾不符'
quote_lines = [l for l in body.splitlines() if l.startswith('> ')]
assert len(quote_lines) == 12, '金句框應為 6 組共 12 行，實得 %d' % len(quote_lines)

d = json.load(io.open(PJ, encoding='utf-8'))
posts = d['posts']

# 防撞號：全站 num 有 26 篇字串、111 篇整數，必須統一轉 int
nums = [int(p['num']) for p in posts if str(p.get('num', '')).isdigit()]
assert max(nums) + 1 == 155, '編號不是 155，實得 %d' % (max(nums) + 1)
assert 'the-prosecutor-2024' not in [p.get('slug') for p in posts], 'slug 已被佔用'

movieInfo = {
    'title': '《誤判》',
    'englishName': 'The Prosecutor',
    'year': 2024,
    'director': '甄子丹（導演、監製、主演）',
    'writer': '待補',
    'genre': '犯罪／動作／律政劇情',
    'releaseDate': '2024-12-21（香港、澳門）、2024-12-27（中國大陸、台灣地區、新加坡等地）',
    'actors': [
        {'name': '甄子丹', 'role': '霍子豪'},
        {'name': '張智霖', 'role': '歐柏文'},
        {'name': '許冠文', 'role': '大法官'},
        {'name': '吳鎮宇', 'role': '待補'},
        {'name': '張天賦', 'role': '李景威'},
        {'name': '鄭則仕', 'role': '包鼎'},
        {'name': '朱栢康', 'role': '嫌犯代表律師'},
        {'name': '黑鬼 Joe（Black Joe）', 'role': '小弟（澳門演員，一手觀察）'},
    ],
    'synopsis': (
        '改編自二〇一六年香港一宗真實冤案，人稱「馬家健案」。一名青年把地址借給朋友代收包裹，'
        '巴西寄來的一公斤可卡因落在他名下；辯護律師與師爺勸他認罪換減刑，他認了，換來二十七年。'
        '前督察霍子豪在一宗首腦因證據不足脫罪的案件中辭職，轉讀法律，七年後回到律政司任檢控官；'
        '他在庭上反過來質問自己帶來的證人，追查替犯罪集團處理合約與黑錢的律師歐柏文。'
        '甄子丹導演、監製兼主演，黃百鳴聯合監製，全片主要攝影在香港。'
    ),
    'scenesLabel': '跟著電影重走《誤判》',
    'macauScenes': {},
    'source': (
        '澳門日報（全片於香港取景及搭景拍攝）、星島日報〈誤判｜解構電影 7 大冷知識〉、'
        '香港電影資料庫 HKMDB、英皇戲院上映資料、ETtoday、WMOOV、百度百科「歐柏文」條、'
        '黑鬼 Joe 公開條目（戲劇欄列 2024《誤判》）、軒哥一手觀影'
    ),
}

post = {
    'num': 155,
    'title': '《誤判》觀後感',
    'category': '',
    'date': '2026-11-14',
    'location': '澳門',
    'status': '已上線',
    'images': ['assets/og/the-prosecutor-2024.jpg'],
    'body': body,
    'slug': 'the-prosecutor-2024',
    'series': 'macau-film',
    'subtitle': '一部本來不寫的片｜2024',
    'filmYear': 2024,
    'movieInfo': movieInfo,
}

before = len(d['posts'])
d['posts'] = [p for p in d['posts'] if str(p.get('num')) != '155']
d['posts'].append(post)
assert len(d['posts']) == before + 1, '篇數不對'

with io.open(PJ, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')

print('OK: %d -> %d 篇；num=155 (int)；slug=the-prosecutor-2024；body %d 字；'
      '金句框 6 組；macauScenes 空 → 單 CTA'
      % (before, len(d['posts']), len(body)))

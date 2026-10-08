# -*- coding: utf-8 -*-
"""線上實測：確認 about 頁改動在正式站真的生效。

為什麼 curl 不夠：grep 會連 HTML 註解裡的字一起抓到。「人生軌跡」在原始碼
出現 2 次是因為它被包在還原註解內（這是刻意的，可還原），但渲染後
使用者看不到。必須讀 rendered DOM 才能分辨。
"""
import sys

URL = 'https://seanown.org/about/'

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('NO_PLAYWRIGHT')
    sys.exit(2)

fails = []


def check(label, cond, detail=''):
    print('[%s] %s %s' % ('PASS' if cond else 'FAIL', label, detail))
    if not cond:
        fails.append(label)


with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={'width': 1280, 'height': 1000})
    pg.goto(URL, wait_until='domcontentloaded')
    body = pg.inner_text('body')

    check('L1 線上自我介紹＝定稿版',
          '澳門台商、連續創業者、投資人、作家' in body)
    check('L2 線上無「人生軌跡」（僅存於還原註解）', '人生軌跡' not in body)
    check('L3 線上無「給非專業讀者的一行解釋」', '給非專業讀者的一行解釋' not in body)
    check('L4 線上無「13 項具名職務」副標', '13 項具名職務' not in body)
    check('L5 線上無「若下列方向不符你的需求」', '若下列方向不符你的需求' not in body)
    check('L6 線上無 MBTI／INFJ', 'INFJ' not in body)
    check('L7 線上保留現職與書名連結',
          '澳門龍遊集團創辦人' in body
          and pg.locator('a[href="/book/shou-deng-ren-ying-ji/"]').count() > 0)
    check('L8 祖籍浙江龍遊仍在（學歷區塊）', '祖籍浙江龍遊' in body)

    # 職務摺疊
    det = pg.locator('details.roles-fold')
    check('L9 職務摺疊預設收合', det.count() == 1 and not det.evaluate('e => e.open'))
    check('L10 收合時只見創辦人那一項',
          pg.locator('.roles-fold-sum .t').inner_text().strip() == '創辦人暨董事總經理')
    pg.click('details.roles-fold > summary')
    pg.wait_for_timeout(250)
    check('L11 點擊展開 12 項', pg.locator('.roles-fold .roles .role:visible').count() == 12)

    # 導航下拉
    check('L12 線上「關於我 ▾」下拉存在', pg.locator('.tnav details.nav-drop').count() == 1)
    check('L13 第一排無獨立聯絡鈕',
          pg.locator('.tnav > a[href="/contact/"]:visible').count() == 0)
    pg.click('.tnav details.nav-drop > summary')
    pg.wait_for_timeout(250)
    check('L14 下拉可展開且聯絡可見',
          pg.locator('.tnav .nav-menu a[href="/contact/"]').is_visible())

    # 手機版最關鍵：導航不能空
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto(URL, wait_until='domcontentloaded')
    check('L15 手機版導航非空（可見項目數 %d）'
          % m.locator('.tnav a:visible').count(),
          m.locator('.tnav a:visible').count() >= 1)

    # 服務與合作仍隱藏
    check('L16 「服務與合作」線上仍不可見',
          pg.locator('.tnav a[href="/services/"]:visible').count() == 0)

    # 文章頁抽樣
    a = br.new_page(viewport={'width': 1280, 'height': 1000})
    a.goto('https://seanown.org/article/leadership-and-crisis/',
           wait_until='domcontentloaded')
    check('L17 文章頁線上也有下拉',
          a.locator('.tnav details.nav-drop').count() == 1)

    br.close()

print('\n' + '=' * 50)
if fails:
    print('ONLINE FAILED %d:' % len(fails))
    for f in fails:
        print('  - %s' % f)
    sys.exit(1)
print('ONLINE ALL PASS')

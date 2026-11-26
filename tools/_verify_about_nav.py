# -*- coding: utf-8 -*-
"""驗證 about 頁 7 項調整 + 全站導航下拉。

為什麼一定要用瀏覽器渲染，不能用 grep：
1. HTML 註解在原始碼裡是「存在的文字」，grep 找不到也分不出註解內外，
   只有渲染後的 DOM 才知道它到底顯示不顯示。
2. <details> 預設是否收合、.nav-mcta 在手機版是否真的 display:block，
   都是算繪後才確定的事。
3. CSS 選擇器是否命中，要看 computed style。

跑法：python tools/_verify_about_nav.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('NO_PLAYWRIGHT')
    sys.exit(2)

PAGES = {
    'about': 'about/index.html',
    'home': 'index.html',
    'contact': 'contact/index.html',
    'article': 'article/2046/index.html',
    'media': 'media/index.html',
    'services': 'services/index.html',
    'book': 'book/shou-deng-ren-ying-ji/index.html',
}

fails = []


def check(label, cond, detail=''):
    tag = 'PASS' if cond else 'FAIL'
    if not cond:
        fails.append(label)
    print('[%s] %s %s' % (tag, label, detail))


with sync_playwright() as pw:
    br = pw.chromium.launch()

    # ---------- A. about 頁：5 處刪除（渲染後不可見） ----------
    pg = br.new_page(viewport={'width': 1280, 'height': 1000})
    pg.goto('file:///' + os.path.join(ROOT, PAGES['about']).replace('\\', '/'))
    pg.wait_for_load_state('domcontentloaded')
    body = pg.inner_text('body')

    check('A1 「給非專業讀者的一行解釋」已移除',
          '給非專業讀者的一行解釋' not in body)
    # 只驗 pos-card 內那個 .plain 區塊已消失。
    # 注意：「雙算力」一詞在「可以合作的方向」卡片正文裡仍存在（未要求刪），
    # 所以不能用全頁文字搜索來判定，必須鎖定 .pos-card 內。
    check('A1b pos-card 內的白話解釋區塊已移除',
          pg.locator('.pos-card .plain').count() == 0)
    check('A1c pos-card 內不再有「雙算力」解釋',
          '雙算力' not in pg.inner_text('.pos-card'))
    check('A2 「人生軌跡」整塊已移除',
          '人生軌跡' not in body)
    check('A2b 人生軌跡內容（1978 台北）已隨區塊移除',
          '跨域半生，以行踐諾' not in body)
    check('A3 「13 項具名職務」副標已移除',
          '13 項具名職務' not in body)
    check('A4 「第三方可查證的紀錄」副標已移除',
          '以下為具名機構的公開頁面或報導原文' not in body)
    check('A5 「若下列方向不符你的需求」已移除',
          '若下列方向不符你的需求' not in body)
    check('A6 「白話說明我做什麼」已移除',
          '白話說明我做什麼' not in body)

    # ---------- B. 自我介紹（軒哥 2026-10-08 定稿版） ----------
    # 注意：本組斷言已跟著軒哥第二次改稿更新。舊版是《守燈人影記》
    # 書籍作者簡介（含星象、柏克萊、MBTI），已被本人定稿版取代，
    # 不要拿舊版文字當斷言——那會測出已刪掉的內容。
    check('B1 四個身分定位已上線',
          '澳門台商、連續創業者、投資人、作家' in body)
    check('B2 跨界視野句已上線', '造就跨界的觀察視野' in body)
    check('B3 澳門平台與串聯使命已上線',
          '中西交匯的獨特平台' in body and '串聯澳門與內地與國際資源' in body)
    check('B4 三個領域已上線',
          'AI+產業' in body and '中華文創' in body and '青年領域' in body)
    check('B5 影像文化觀察句保留',
          '長年觀察澳門的城市變遷與影像文化' in body)
    check('B6 現職句保留（龍遊集團創辦人）', '澳門龍遊集團創辦人' in body)
    check('B7 現職句保留（大灣區電子商會會長）', '粵港澳大灣區電子商會會長' in body)
    check('B8 現職句保留（ECI 理事長）', 'ECI@澳門創新專委會理事長' in body)
    check('B9 書名連到書籍頁',
          pg.locator('a[href="/book/shou-deng-ren-ying-ji/"]').count() > 0)
    check('B10 MBTI 已拿掉', 'INFJ-AH' not in body)
    check('B11 星象段已拿掉', '井宿與鬼宿' not in body)
    # 出生背景改由下方「學歷背景」區塊承接，不可整頁消失
    check('B12 出生年與祖籍仍在頁面（學歷區塊）',
          '1978' in pg.inner_text('.box:has(h3:text("學歷背景"))')
          or ('一九七八年生' in body and '祖籍浙江龍遊' in body))
    check('B13 學歷區塊確實載有祖籍與出生年',
          '祖籍浙江龍遊' in pg.inner_text('.box:has-text("學歷背景")'))

    # ---------- C. 職務摺疊 ----------
    det = pg.locator('details.roles-fold')
    check('C1 details.roles-fold 存在', det.count() == 1)
    check('C2 預設收合', det.count() == 1 and not det.evaluate('e => e.open'))
    roles = pg.locator('.roles-fold .roles .role')
    check('C3 展開後共 13 項職務（1 在 summary + 12 在內）',
          roles.count() == 12)
    # 點擊展開
    pg.click('details.roles-fold > summary')
    pg.wait_for_timeout(200)
    check('C4 點擊後展開', det.evaluate('e => e.open') is True)
    vis = pg.locator('.roles-fold .roles .role').first.is_visible()
    check('C5 展開後職務可見', vis)
    # 預設狀態下，內層 12 項應該不可見（收合時）
    pg.click('details.roles-fold > summary')
    pg.wait_for_timeout(200)
    hidden_ok = not pg.locator('.roles-fold .roles .role').first.is_visible()
    check('C6 收合時內層 12 項不可見', hidden_ok)

    # ---------- D. about 頁導航下拉 ----------
    check('D1 關於我下拉存在', pg.locator('.tnav details.nav-drop').count() == 1)
    menu_links = pg.locator('.tnav .nav-menu a')
    check('D2 下拉內有 2 個項目（關於我／聯絡）',
          menu_links.count() == 2)
    # 下拉預設收合時文字讀不到（display 無內容），要先展開再讀文字。
    # 這裡只驗 href，文字在 D5 展開後驗。
    hrefs = [h for h in menu_links.evaluate_all('els => els.map(e => e.getAttribute("href"))')]
    check('D3 下拉項目連結正確',
          hrefs == ['/about/', '/contact/'], str(hrefs))
    check('D4 第一排已無獨立聯絡鈕（PC）',
          pg.locator('.tnav > a.cta:not(.nav-mcta)').count() == 0)
    # 展開下拉，確認聯絡可點
    pg.click('.tnav details.nav-drop > summary')
    pg.wait_for_timeout(200)
    check('D5 下拉可展開且聯絡可見',
          pg.locator('.tnav .nav-menu a[href="/contact/"]').is_visible())
    txts = [t.strip() for t in menu_links.all_inner_texts()]
    check('D5b 展開後下拉文字正確', txts == ['關於我', '聯絡'], str(txts))
    check('D6 展開後 summary 箭頭旋轉（[open] 生效）',
          pg.locator('.tnav details.nav-drop').evaluate('e => e.open') is True)
    pg.click('.tnav details.nav-drop > summary')
    pg.wait_for_timeout(150)

    # ---------- E. 手機版導航不能空（最關鍵的陷阱） ----------
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto('file:///' + os.path.join(ROOT, PAGES['about']).replace('\\', '/'))
    m.wait_for_load_state('domcontentloaded')
    vis_ctas = m.locator('.tnav a.cta:visible').count()
    check('E1 about 手機版有可見的聯絡鈕（不能全空）', vis_ctas >= 1,
          'visible cta=%d' % vis_ctas)
    mct = m.locator('.tnav a.nav-mcta')
    check('E2 mobile-only 複本存在', mct.count() == 1)
    if mct.count() == 1:
        check('E3 mobile-only 複本在手機版可見', mct.is_visible())
    check('E4 手機版下拉已隱藏',
          m.locator('.tnav details.nav-drop:visible').count() == 0)

    # ---------- F. 全站每一頁：手機版導航都非空 ----------
    print('\n--- F. 全站逐頁掃描（手機版導航非空） ---')
    empty = []
    for key, rel in PAGES.items():
        if key == 'home':
            continue  # 首頁另有一套 nav，沒有 .tnav
        mm = br.new_page(viewport={'width': 390, 'height': 844})
        mm.goto('file:///' + os.path.join(ROOT, rel).replace('\\', '/'))
        mm.wait_for_load_state('domcontentloaded')
        n = mm.locator('.tnav a:visible').count()
        if n == 0:
            empty.append(rel)
        mm.close()
    check('F1 這 6 頁手機版導航皆有可見項目', not empty, str(empty))

    # ---------- G. 全站：服務與合作仍隱藏、聯絡不再坐第一排 ----------
    print('\n--- G. 全站逐頁掃描（服務與合作隱藏 / 聯絡位置） ---')
    svc_visible = []
    contact_top = []
    for key, rel in PAGES.items():
        if key == 'home':
            continue
        d = br.new_page(viewport={'width': 1280, 'height': 1000})
        d.goto('file:///' + os.path.join(ROOT, rel).replace('\\', '/'))
        d.wait_for_load_state('domcontentloaded')
        if d.locator('.tnav a[href="/services/"]:visible, .nav-menu a[href="/services/"]:visible').count() > 0:
            svc_visible.append(rel)
        # 第一排（tnav 的直接子元素 a）裡不該再有聯絡
        if d.locator('.tnav > a[href="/contact/"]:visible').count() > 0:
            contact_top.append(rel)
        d.close()
    check('G1 「服務與合作」全站不可見', not svc_visible, str(svc_visible))
    check('G2 聯絡不再坐第一排（全站）', not contact_top, str(contact_top))

    # ---------- H. 少量文章頁抽樣（確認 rebuild 生效） ----------
    print('\n--- H. 文章頁抽樣 ---')
    # ---------- H. 全站文章頁掃描（確認 rebuild 真的套用） ----------
    print('\n--- H. 全站文章頁掃描 ---')
    adir = os.path.join(ROOT, 'article')
    all_arts = sorted(
        d for d in os.listdir(adir)
        if os.path.isdir(os.path.join(adir, d))
    )
    bad_drop, bad_mcta, bad_mobile = [], [], []
    mm = br.new_page(viewport={'width': 390, 'height': 844})
    for slug in all_arts:
        rel = 'article/%s/index.html' % slug
        f = 'file:///' + os.path.join(ROOT, rel).replace('\\', '/')
        d = br.new_page(viewport={'width': 1280, 'height': 1000})
        d.goto(f)
        d.wait_for_load_state('domcontentloaded')
        if d.locator('.tnav details.nav-drop').count() != 1:
            bad_drop.append(slug)
        if d.locator('.tnav a.nav-mcta').count() != 1:
            bad_mcta.append(slug)
        d.close()
        mm.goto(f)
        mm.wait_for_load_state('domcontentloaded')
        if mm.locator('.tnav a:visible').count() == 0:
            bad_mobile.append(slug)
    mm.close()
    print('    （掃描 %d 篇文章頁）' % len(all_arts))
    check('H1 全站文章頁都有「關於我」下拉', not bad_drop, str(bad_drop[:6]))
    check('H2 全站文章頁都有手機版聯絡複本', not bad_mcta, str(bad_mcta[:6]))
    check('H3 全站文章頁手機版導航皆非空', not bad_mobile, str(bad_mobile[:6]))

    # ---------- I. 首頁導航 ----------
    h = br.new_page(viewport={'width': 1280, 'height': 1000})
    h.goto('file:///' + os.path.join(ROOT, PAGES['home']).replace('\\', '/'))
    h.wait_for_load_state('domcontentloaded')
    check('I1 首頁有關於我下拉', h.locator('.nav-right details.nav-drop').count() == 1)
    # 驗 href（收合時文字讀不到），文字在 I2b 展開後驗
    hh = h.locator('.nav-menu a').evaluate_all('els => els.map(e => e.getAttribute("href"))')
    check('I2 首頁下拉連結正確', hh == ['/about/', '/contact/'], str(hh))
    h.click('.nav-right details.nav-drop > summary')
    h.wait_for_timeout(200)
    hm = [t.strip() for t in h.locator('.nav-menu a').all_inner_texts()]
    check('I2b 首頁展開後下拉文字正確', hm == ['關於我', '聯絡'], str(hm))
    check('I2c 首頁聯絡可點', h.locator('.nav-menu a[href="/contact/"]').is_visible())
    check('I3 首頁第一排已無聯絡鈕',
          h.locator('.nav-right > a.nav-cta').count() == 0)
    check('I4 首頁 hero 洽談合作鈕仍在（轉換不斷）',
          h.locator('a[href="/contact/"]').count() >= 5)
    # 首頁手機版也要能看到關於我
    hm2 = br.new_page(viewport={'width': 390, 'height': 844})
    hm2.goto('file:///' + os.path.join(ROOT, PAGES['home']).replace('\\', '/'))
    hm2.wait_for_load_state('domcontentloaded')
    check('I5 首頁手機版下拉可見', hm2.locator('.nav-right details.nav-drop').is_visible())

    br.close()

print('\n' + '=' * 56)
if fails:
    print('FAILED %d:' % len(fails))
    for f in fails:
        print('  - %s' % f)
    sys.exit(1)
print('ALL PASS')

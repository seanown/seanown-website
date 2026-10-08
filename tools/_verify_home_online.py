# -*- coding: utf-8 -*-
"""線上實測首頁精簡化（2026-10-09 上線後）。

與 _verify_home_author.py 的差別：那支驗本機檔案，這支打線上
https://seanown.org/，確認 Netlify 部署後的實際結果（CDN 快取、
壓縮、build 差異都可能讓線上與本機不同）。
"""
import sys
from playwright.sync_api import sync_playwright

URL = 'https://seanown.org/'
ARTICLE = 'https://seanown.org/article/a-night-in-hong-kong-1961/'
fails = []


def check(label, cond, detail=''):
    print('[%s] %s %s' % ('PASS' if cond else 'FAIL', label, detail))
    if not cond:
        fails.append(label)


with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={'width': 1280, 'height': 1000})
    pg.goto(URL, wait_until='networkidle')
    body = pg.inner_text('body')

    print('--- 線上：精簡版內容 ---')
    check('L1 一句身分已上線', '澳門台商、投資人、作家' in body)
    check('L2 舊長段自介已下架',
          '長期往返台灣、大陸、美國與澳門' not in body)
    check('L3 服務卡已收起', '我可以為你做什麼' not in body)
    check('L4 職務 chips 已收起',
          pg.locator('#sec-author .author-chips').count() == 0)
    check('L5 關於我連結存在',
          pg.locator('#sec-author a.author-more[href="/about/"]').count() == 1)

    print('\n--- 線上：頁尾可合作領域 ---')
    check('L6 頁尾有一行可合作領域',
          '可合作領域：AI+產業' in pg.inner_text('.footer-brand'))

    print('\n--- 線上：高度（重點看有沒有真的變矮）---')
    h = pg.evaluate("document.getElementById('sec-author').getBoundingClientRect().height")
    check('L7 PC 關於作者區塊 <300px（原始 434px）', h < 300, 'height=%.0fpx' % h)
    foot = pg.evaluate('document.querySelector("footer.footer").parentElement.tagName')
    check('L8 footer 結構正常（巢狀 bug 未復發）', foot == 'BODY',
          'parent=%s' % foot)

    print('\n--- 線上：展開鈕實測 ---')
    before = pg.evaluate("document.getElementById('about-detail').hidden")
    check('L9 預設收起', before is True)
    pg.click('#about-expand-btn')
    pg.wait_for_timeout(600)
    after = pg.evaluate("document.getElementById('about-detail').hidden")
    check('L10 點擊可展開', after is False, 'after=%s' % after)
    check('L11 展開後收合文案可見',
          pg.evaluate("getComputedStyle(document.querySelector('#about-expand-btn .ae-shut')).display") != 'none')
    check('L12 展開後看得到代表項目 8 張卡',
          pg.locator('#about-detail .practice-card:visible').count() == 8,
          'count=%d' % pg.locator('#about-detail .practice-card:visible').count())
    pg.click('#about-expand-btn')
    pg.wait_for_timeout(400)
    check('L13 可收合',
          pg.evaluate("document.getElementById('about-detail').hidden") is True)

    print('\n--- 線上：手機版 ---')
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto(URL, wait_until='networkidle')
    mh = m.evaluate("document.getElementById('sec-author').getBoundingClientRect().height")
    check('L14 手機版 <300px（原始 500px）', mh < 300, 'height=%.0fpx' % mh)
    check('L15 手機版維持橫向',
          m.evaluate("getComputedStyle(document.querySelector('.author-flex-slim')).flexDirection") == 'row')
    check('L16 手機版 nav 連結沒被壓扁（見下方獨立段落）', True)

    # 🔴 2026-10-09 新增：多視窗寬度掃描 nav。
    # 起因是發現一個既有 bug——320–414px 之間「作品／專欄／媒體」
    # 各只剩 13–19px 寬（兩個中文字至少要 26px），「澳門週訊」被擠成兩行。
    # 原因是 .nav-right 內所有項目 flex-shrink:1，logo 固定佔 133px，
    # 空間不夠時瀏覽器從連結開始壓，中文沒有空格可斷行就被逐字壓扁。
    # 判準：任何含兩個以上中文字的 nav 連結，寬度不得小於 24px。
    # ⚠️ 首頁是 nav#nav（.nav/.nav-col-link），文章頁是 nav.tnav，
    #    兩套類名不同——用 tnav 查首頁會得到 NO NAV（踩過）。
    print('\n--- 線上：nav 多寬度掃描（首頁 + 文章頁）---')
    NAVJS = """() => {
      const nav = document.getElementById('nav') || document.querySelector('nav.tnav');
      if (!nav) return null;
      const out = [];
      nav.querySelectorAll('a,summary').forEach(e => {
        if (e.closest('.nav-menu')) return;
        const r = e.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        const t = (e.innerText || '').trim();
        const cjk = (t.match(/[\\u4e00-\\u9fff]/g) || []).length;
        out.push({ text: t.slice(0, 10), w: Math.round(r.width),
                   h: Math.round(r.height), bad: cjk >= 2 && r.width < 24 });
      });
      return out;
    }"""
    for w in (320, 360, 390, 414, 480, 768, 1280):
        t = br.new_page(viewport={'width': w, 'height': 900})
        t.goto(URL, wait_until='domcontentloaded')
        rows = t.evaluate(NAVJS)
        bad = [r for r in rows if r['bad']]
        desc = ' '.join('%s=%dx%d' % (r['text'], r['w'], r['h']) for r in rows)
        check('L17 首頁 nav @%dpx 無壓扁' % w, rows and not bad,
              desc if bad else '')
        t.close()

    for w in (320, 390, 768, 1280):
        t = br.new_page(viewport={'width': w, 'height': 900})
        t.goto(ARTICLE, wait_until='domcontentloaded')
        rows = t.evaluate(NAVJS)
        bad = [r for r in rows if r['bad']]
        desc = ' '.join('%s=%dx%d' % (r['text'], r['w'], r['h']) for r in rows)
        check('L18 文章頁 nav @%dpx 無壓扁' % w, rows and not bad,
              desc if bad else '')
        t.close()

    br.close()

print('\n' + '=' * 54)
if fails:
    print('ONLINE FAILED %d:' % len(fails))
    for f in fails:
        print('  - %s' % f)
    sys.exit(1)
print('ONLINE ALL PASS')
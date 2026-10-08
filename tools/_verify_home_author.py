# -*- coding: utf-8 -*-
"""驗證首頁「關於作者」精簡版（2026-10-09）。

風險點在於我手動搬動過 author-flex / author-main 的 </div>：
少一個就會讓後面整個 footer 被吸進 author-flex，版面大亂，
而單看原始碼很難發現（div 允許缺數量的瀏覽器糾錯）。
所以這支腳本重點查 DOM 結構與實際版面高度，不只是查文字在不在。
"""
import os
import sys

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

    # ⚠️ 第一版這裡寫成先用 networkidle 載入線上首頁、再用 __file__ 拼字串組
    # file:// 路徑。結果拼錯路徑、實際載入的是線上舊版，導致 A2/A3/A7 全部
    # 誤判 FAIL（線上還沒有這次改動）。正確做法是用 os.path 明確組出根目錄。
    LOCAL = 'file:///' + os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'index.html').replace('\\', '/')
    pg.goto(LOCAL, wait_until='domcontentloaded')
    print('（驗證本機檔案：%s）' % LOCAL)
    body = pg.inner_text('body')

    print('--- A. 精簡版內容 ---')
    check('A1 一句身分已上線', '澳門台商、投資人、作家' in body)
    check('A2 頭像仍在', pg.locator('#sec-author .author-photo').count() == 1)
    check('A3 關於我連結存在',
          pg.locator('#sec-author a.author-more[href="/about/"]').count() == 1)
    check('A4 「我可以為你做什麼」已收起',
          '我可以為你做什麼' not in body)
    check('A5 三張服務卡已收起',
          pg.locator('#sec-author .help-card').count() == 0)
    # ⚠️ 2026-10-09 修正第一版的判斷。
    # 第一版斷言「展開按鈕不存在」並標成 PASS，但那是錯的取捨：
    # 按鈕一拿掉，#about-detail 裡的 9 個 section 就永久看不到了，
    # 其中「代表項目」（8 張 practice-card）與「數據 stats-bar」
    # 在 /about/ 頁根本不存在，等於首頁從此少掉兩塊內容。
    # 軒哥說的是「全部折疊起來」——折疊暗示能展開，所以按鈕要留，
    # 只是從搶視線的大按鈕降級成低調小鈕。
    eb = pg.locator('#sec-author button#about-expand-btn')
    check('A6 展開鈕仍在（降級為低調小鈕，非移除）', eb.count() == 1)
    check('A6b 展開鈕文案是精簡版「＋更多經歷」',
          '＋更多經歷' in (eb.inner_text() if eb.count() else ''))
    check('A6c 預設為收起狀態',
          pg.locator('#about-detail[hidden]').count() == 1)
    check('A7 舊的長段自介已移除',
          '長期往返台灣、大陸、美國與澳門' not in body)
    check('A8 職務 chips 已從首頁收起',
          pg.locator('#sec-author .author-chips').count() == 0)

    print('\n--- B. 頁尾可合作領域 ---')
    check('B1 頁尾有可合作領域一行',
          '可合作領域：AI+產業' in pg.inner_text('.footer-brand'))
    check('B2 頁尾品牌簡介＝定稿版',
          '澳門台商、投資人、作家' in pg.inner_text('.footer-brand'))
    check('B3 頁尾仍留聯絡管道',
          pg.locator('.footer a[href="/contact/"]').count() >= 1)

    print('\n--- C. 🔴 DOM 結構完整性（我手動搬過 </div>） ---')
    # footer 必須是 body 的直接子孫，不能被吸進 section/div
    foot_parent = pg.evaluate('document.querySelector("footer.footer").parentElement.tagName')
    check('C1 footer 是 body 直接子層（未被吸進其他區塊）',
          foot_parent == 'BODY', 'parent=%s' % foot_parent)

    # ⚠️ 第一版這裡寫成「sec-author 內不能有 section」，是錯的斷言：
    # 首頁所有 section（sec-services、sec-projects…）本來就都在
    # <main id="page-home"> 裡，是正常的兄弟關係，不是巢狀。
    # 第二版抓「有沒有其他區塊的 id 成為 sec-author 的子孫」—— 也錯，
    # 因為 #about-detail（展開完整經歷）本來就住在 sec-author 裡，
    # 裡面合法包含 sec-services／sec-projects／sec-stats／sec-media 四塊。
    # 第三版（正確）：這四塊的合法位置是「在 #about-detail 底下」；
    # 如果它們直接掛在 sec-author 下、或出現在 about-detail 之外，
    # 才叫巢狀溢出。判法＝沿著 parent 鏈往上找，必須先遇到 about-detail。
    swallowed = pg.evaluate("""() => {
      const s = document.getElementById('sec-author');
      const det = document.getElementById('about-detail');
      const ids = ['sec-contact','sec-services','sec-projects',
                   'sec-stats','sec-media','sec-subscribe','sec-weekly',
                   'sec-articles','sec-films','sec-focus'];
      const bad = [];
      for (const id of ids) {
        const e = document.getElementById(id);
        if (!e) continue;
        let p = e.parentElement, inAuthor = false, inDetail = false;
        while (p) {
          if (p.id === 'about-detail') { inDetail = true; break; }
          if (p.id === 'sec-author') { inAuthor = true; break; }
          p = p.parentElement;
        }
        // 在 sec-author 內卻沒窩在 about-detail 裡 → 巢狀溢出
        if (inAuthor && !inDetail) bad.push(id + '(溢出)');
      }
      return bad;
    }""")
    check('C2 其他區塊沒有巢狀溢出「關於作者」邊界', not swallowed, str(swallowed))
    # 四塊本來就住 about-detail 裡，位置正確
    inside = pg.evaluate("""() => {
      const det = document.getElementById('about-detail');
      return ['sec-services','sec-projects','sec-stats','sec-media']
        .filter(id => det && det.contains(document.getElementById(id)));
    }""")
    check('C2b 展開區四塊仍在 about-detail 內（位置正確）',
          len(inside) == 4, str(inside))
    # 精簡版高度：原本 434px（PC）／500px（手機）。
    # 內容本身只有 106px，剩餘是章節標題＋副標＋分隔線＋內距的必要成本，
    # 所以門檻設 300px 而非 200px——重點是比原本少約 40%，且手機版
    # 已從 500 降到 270。
    # ⚠️ 這條斷言與 D1 是同一件事，本檔只留一處，避免重複報錯看不出真正問題。
    # 服務卡確實不在渲染樹裡
    check('C4 渲染後仍無 help-card',
          pg.locator('.help-card:visible').count() == 0)

    print('\n--- D. 首頁焦點是否落在作品 ---')
    for sel, name in [('#sec-series', '專輯'),
                      ('#sec-articles, .cards-grid, #sec-weekly', '文章/作品'),
                      ('#sec-author', '關於作者')]:
        n = pg.locator(sel).count()
        print('    %-10s selector=%-34s count=%d' % (name, sel, n))
    ah = pg.evaluate("document.getElementById('sec-author').getBoundingClientRect().height")
    check('D1 關於作者不再佔大版面（<300px，原始 434px）', ah < 300,
          'height=%.0fpx' % ah)

    print('\n--- E. 手機版 ---')
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto(LOCAL, wait_until='domcontentloaded')
    mh = m.evaluate("document.getElementById('sec-author').getBoundingClientRect().height")
    check('E1 手機版關於作者區塊也矮（<300px，原始 500px）', mh < 300,
          'height=%.0fpx' % mh)
    # 手機版必須維持橫向，否則 author-flex 會因 column 疊高（實測 202px）
    mdir = m.evaluate("getComputedStyle(document.querySelector('.author-flex-slim')).flexDirection")
    check('E1b 手機版維持橫向排列（flex-direction=row）', mdir == 'row',
          'dir=%s' % mdir)
    check('E2 手機版關於我連結可點',
          m.locator('#sec-author a.author-more').is_visible())
    mf = m.evaluate('document.querySelector("footer.footer").parentElement.tagName')
    check('E3 手機版 footer 結構也正常', mf == 'BODY', 'parent=%s' % mf)

    print('\n--- F. 展開鈕實測（點下去真的能開）---')
    # 🔴 這段是為了抓一個實際踩過的坑：按鈕內含兩個 span（.ae-open／.ae-shut）
    # 由 CSS 依 aria-expanded 切換，而 JS 原本用 eb.textContent=... 改文案，
    # 那會把兩個 span 洗掉，之後再也切不出收合文案。所以要實際點開看狀態。
    before = pg.evaluate("document.getElementById('about-detail').hidden")
    pg.click('#about-expand-btn')
    pg.wait_for_timeout(500)
    after = pg.evaluate("document.getElementById('about-detail').hidden")
    check('F1 點擊後展開區由隱藏變顯示', before is True and after is False,
          'before=%s after=%s' % (before, after))
    exp = pg.get_attribute('#about-expand-btn', 'aria-expanded')
    check('F2 aria-expanded 同步為 true', exp == 'true', 'aria=%s' % exp)
    ae_shut = pg.evaluate("""() => {
      const el = document.querySelector('#about-expand-btn .ae-shut');
      return el ? getComputedStyle(el).display : 'MISSING';
    }""")
    ae_open = pg.evaluate("""() => {
      const el = document.querySelector('#about-expand-btn .ae-open');
      return el ? getComputedStyle(el).display : 'MISSING';
    }""")
    check('F3 兩個文案 span 都還在（沒被 textContent 洗掉）',
          ae_shut != 'MISSING' and ae_open != 'MISSING',
          'open=%s shut=%s' % (ae_open, ae_shut))
    check('F4 展開後收合文案可見、開啟文案隱藏',
          ae_shut != 'none' and ae_open == 'none',
          'open=%s shut=%s' % (ae_open, ae_shut))
    # 展開後那些只有首頁有的內容應該看得到
    for sel, nm in [('#about-detail .practice-card', '代表項目 practice-card'),
                    ('#sec-stats', '數據 stats-bar'),
                    ('#sec-media', '媒體報導')]:
        n = pg.locator(sel + ':visible').count()
        check('F5 展開後看得到「%s」' % nm, n > 0, 'count=%d' % n)
    # 再點一次收合
    pg.click('#about-expand-btn')
    pg.wait_for_timeout(400)
    check('F6 再點一次可收合',
          pg.evaluate("document.getElementById('about-detail').hidden") is True)

    br.close()

print('\n' + '=' * 54)
if fails:
    print('FAILED %d:' % len(fails))
    for f in fails:
        print('  - %s' % f)
    sys.exit(1)
print('ALL PASS')

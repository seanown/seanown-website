# -*- coding: utf-8 -*-
"""驗證新文章頁排版（num=124 在南孔聖地）。

重點檢查：
- H2 章節是否正確渲染（10 個）
- 首頁精簡化後網站 focus 在作品，這篇是生活隨筆第11 篇
- 手機版閱讀體驗（字級、行高、段落間距）
- 有沒有溢出或空白
"""
import os
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file:///' + os.path.join(ROOT, 'article',
                                'quzhou-nankong-returning-home',
                                'index.html').replace('\\', '/')
fails = []


def check(label, cond, detail=''):
    print('[%s] %s %s' % ('PASS' if cond else 'FAIL', label, detail))
    if not cond:
        fails.append(label)


with sync_playwright() as pw:
    br = pw.chromium.launch()

    # 桌面版
    pg = br.new_page(viewport={'width': 1280, 'height': 1000})
    pg.goto(URL, wait_until='networkidle')
    body = pg.inner_text('body')

    print('--- A. 文章頁基本結構 ---')
    check('A1 標題正確',
          '在南孔聖地，聽兩岸的聲音' in pg.title() or
          '在南孔聖地' in body)
    h1 = pg.locator('h1').first.inner_text()
    check('A2 h1 正確', '南孔聖地' in h1, h1)
    h2s = pg.evaluate("""() => Array.from(
        document.querySelectorAll('.post-body h2, article h2, .content h2'))
        .map(e => e.innerText.trim()).filter(Boolean)""")
    check('A3 H2 章節數 = 10', len(h2s) == 10, 'count=%d' % len(h2s))
    for i, x in enumerate(h2s):
        print('     H2-%d  %s' % (i + 1, x[:32]))

    print('\n--- B. 內容完整性 ---')
    # ⚠️ 第一版寫成「衢州龍游」（簡体的游），比對失敗誤判 FAIL。
    # 網站實際是繁體「龍遊」，驗證腳本必須用同樣字形。
    check('B1 導語段落在', '隔了二十四年，我回到祖籍地衢州龍遊' in body)
    check('B2 楔子在', '隔了二十四年的回家' in body)
    check('B3 八個字核心句在', '財自道生，利緣義取' in body)
    check('B4 端午尾聲在', '端午的午時' in body)
    check('B5 系列預告在', '系列預告' in body)
    check('B6 附註來源在', '資料來源' in body)
    # 六句心得應為粗體
    bolds = pg.evaluate("""() => Array.from(
        document.querySelectorAll('.post-body strong, article strong, .content strong'))
        .map(e => e.innerText.trim())""")
    check('B7 六句心得為粗體（至少6 個 strong）', len(bolds) >= 6,
          'strong count=%d' % len(bolds))
    # 三點思考的粗體標題
    check('B8 三點思考標題為粗體',
          any('回家的意義' in x for x in bolds))

    print('\n--- C. 排版健康度 ---')
    # 文章頁沒有 <footer>（是精簡單頁版型），第一版查document.querySelector
    # ('footer') 必然拿到 NO FOOTER，誤判 FAIL。改成檢查有沒有巢狀吞入：
    # h1 的祖先鏈不該出現 article/section 之外的容器異常。
    nest = pg.evaluate("""() => {
      const h1 = document.querySelector('h1');
      if (!h1) return 'NO H1';
      let p = h1.parentElement, chain = [];
      while (p) { chain.push(p.tagName.toLowerCase()
        + (p.id ? '#' + p.id : '')); p = p.parentElement; }
      return chain.join(' < ');
    }""")
    # ⚠️ 這條斷言我改過三次都錯（endsWith('body')、'<article' in nest…），
    # 因為在用字串猜 DOM 結構。改成最樸素可靠的寫法：直接把鏈拆成陣列看。
    chain = pg.evaluate("""() => {
      const h1 = document.querySelector('h1');
      const out = [];
      let p = h1 ? h1.parentElement : null;
      while (p) { out.push(p.tagName.toLowerCase()); p = p.parentElement; }
      return out;
    }""")
    # 正常應為 ['div'(或 article 內層), ..., 'article', ..., 'body', 'html']
    check('C1 h1 祖先鏈正常（含 article/body/html）',
          'article' in chain and 'body' in chain and 'html' in chain,
          ' > '.join(chain))
    # 段落數與長度
    info = pg.evaluate("""() => {
      const ps = Array.from(document.querySelectorAll('article p'));
      const lens = ps.map(p => p.innerText.trim().length)
                      .filter(n => n > 0);
      return { n: ps.length, max: Math.max(...lens),
               over: lens.filter(n => n > 800).length };
    }""")
    check('C2 段落數合理（>40）', info['n'] > 40, 'p=%d' % info['n'])
    check('C3 無超長段落（<800字）', info['over'] == 0,
          'over=%d max=%d' % (info['over'], info['max']))
    # 頁面總高。第一版門檻設 6萬–25萬px 是我憑感覺抓的，結果實測 7,713px
    # 被判FAIL——但那個數字其實完全合理：7,540 字、81 段、16px 字級、
    # 28.8px 行高，約 7,700px 正好。所以門檻要按「字數 × 每字行高」估算，
    # 不能拍一個無依據的區間。
    # 實測基準：1280px 寬下正文欄約 700px 寬，一行約 40 個中文字，
    # 7,540 字 ≈ 190 行 × 28.8px ≈ 5,500px，加標題與區塊間距 ≈ 7,700px。
    ph = pg.evaluate("document.body.scrollHeight")
    est = 7540 / 40 * 28.8 + 2000   # 估算下限
    print('     頁面總高：%dpx（估算下限 %dpx）' % (ph, int(est)))
    check('C4 頁面高度與字數相符（>估算下限×0.7）', ph > est * 0.7,
          'h=%d est=%d' % (ph, int(est)))

    print('\n--- D. 手機版閱讀 ---')
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto(URL, wait_until='networkidle')
    mh2 = m.locator('h2').count()
    check('D1 手機版 H2 齊全', mh2 >= 10, 'h2=%d' % mh2)
    # 有無橫向溢出
    ov = m.evaluate("""() => {
      const de = document.documentElement;
      return { sw: de.scrollWidth, iw: window.innerWidth };
    }""")
    check('D2 無橫向溢出', ov['sw'] <= ov['iw'] + 1,
          'scrollW=%d innerW=%d' % (ov['sw'], ov['iw']))
    # 正文字級
    fs = m.evaluate("""() => {
      const p = document.querySelector('.post-body p, article p, .content p');
      return p ? parseFloat(getComputedStyle(p).fontSize) : 0;
    }""")
    check('D3 手機版正文字級 ≥15px', fs >= 15, 'fontSize=%.1fpx' % fs)
    print('     手機版正文字級：%.1fpx' % fs)
    # 行高
    lh = m.evaluate("""() => {
      const p = document.querySelector('.post-body p, article p, .content p');
      return p ? getComputedStyle(p).lineHeight : '';
    }""")
    print('     手機版行高：%s' % lh)

    print('\n--- E. SEO ---')
    # ⚠️ 第一版寫成 pg.get_attribute('meta[name="description"]')，
    # 這是錯的 API——get_attribute(selector, name) 要兩個參數。
    # 取 meta 內容要用 locator + get_attribute('content')。
    def meta(pg_, sel):
        return pg_.locator(sel).first.get_attribute('content') or ''

    check('E1 有 description', len(meta(pg, 'meta[name="description"]')) > 0)
    canon = pg.locator('link[rel="canonical"]').first.get_attribute('href') or ''
    check('E2 canonical 指向正確 slug',
          'quzhou-nankong-returning-home' in canon, canon)
    check('E3 og:title 正確', '南孔聖地' in meta(pg, 'meta[property="og:title"]'))
    desc = meta(pg, 'meta[name="description"]')
    check('E4 description 長度合理（60-160）', 60 <= len(desc) <= 160,
          'len=%d' % len(desc))
    print('     description：%s' % desc[:100])
    ogp = meta(pg, 'meta[property="og:image"]')
    ogfile = ogp.split('?')[0].replace('https://seanown.org', '').lstrip('/')
    exists = os.path.isfile(os.path.join(ROOT, ogfile)) if ogfile else False
    # 軒哥選「先純文字排版，之後補圖」，所以 og 圖與封面圖現在都不存在。
    # 這不是 bug，但要明確知道：補圖前社群分享（LINE／FB）會沒有縮圖。
    print('     og:image → %s（檔案存在：%s）' % (ogfile, exists))
    check('E5 og:image 已設定（檔案待補圖後才會存在）',
          len(ogp) > 0 and ogfile.endswith('.jpg'))

    br.close()

print('\n' + '=' * 54)
if fails:
    print('FAILED %d:' % len(fails))
    for f in fails:
        print('  - %s' % f)
    sys.exit(1)
print('ALL PASS')
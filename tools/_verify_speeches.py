# -*- coding: utf-8 -*-
# 驗證文章頁的「致詞稿附錄」（spx）區塊。
#
# 重點：不只看 HTML 有沒有，而是實際點擊展開、讀 computed style，
# 因為 CSS 花括號不平衡時 HTML 完全正常但樣式整段失效。

import pathlib
import sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / 'article' / 'quzhou-nankong-returning-home' / 'index.html'
SPK = ['仇開明', '潘曉輝', '徐莽', '周錫瑋', '趙青沣',
       '龍遊縣人民政府領導', '主辦方代表', '龍遊產業主管部門代表']


def main():
    fails = []

    def chk(cond, label, extra=''):
        tag = 'PASS' if cond else 'FAIL'
        print('[%s] %s%s' % (tag, label, ('  ' + extra) if extra else ''))
        if not cond:
            fails.append(label)

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 390, 'height': 844})
        pg.goto(PAGE.as_uri())

        print('--- A. 結構 ---')
        chk(pg.locator('.spx').count() == 1, 'A1 附錄區塊唯一')
        chk(pg.locator('.spx-item').count() == 8, 'A2 共有 8 篇致詞稿',
            'count=%d' % pg.locator('.spx-item').count())
        chk(pg.locator('.spx-panel').count() == 8, 'A3 對應 8 個展開面板')
        t = pg.locator('.spx-title').inner_text()
        chk('8' in t, 'A4 標題標示篇數', t)

        print('--- B. 樣式生效（CSS 平衡）---')
        rules = pg.evaluate(
            "()=>{let n=0;for(const s of document.styleSheets)"
            "{try{if(s.cssRules)n+=s.cssRules.length}catch(e){}}return n}")
        chk(rules >= 140, 'B1 CSS 規則數正常（>=140）', 'rules=%d' % rules)
        bg = pg.evaluate(
            "()=>getComputedStyle(document.querySelector('.spx')).backgroundColor")
        chk('247' in bg or '241' in bg, 'B2 附錄底色已套用', bg)
        nw = pg.evaluate(
            "()=>getComputedStyle(document.querySelector('.spx-no')).borderTopLeftRadius")
        chk(nw.startswith('50%'), 'B3 序號為圓形', nw)

        print('--- C. 展開互動 ---')
        p1 = pg.locator('#spx-p-1')
        chk(not p1.is_visible(), 'C1 初始為收合')
        pg.locator('.spx-item').first.locator('.spx-head').click()
        pg.wait_for_timeout(420)
        chk(p1.is_visible(), 'C2 點擊後展開')
        d = pg.evaluate(
            "()=>getComputedStyle(document.querySelector('#spx-p-1')).display")
        chk(d == 'block', 'C3 展開後 display 生效', d)
        txt = pg.locator('#spx-p-1').inner_text()
        chk('百位台商' in txt or '衢州' in txt, 'C4 內文有實際文字',
            '%d 字' % len(txt))
        chk(len(txt) > 600, 'C5 內文長度合理', '%d 字' % len(txt))

        print('--- D. 同一時間只開一篇 ---')
        pg.locator('.spx-item').nth(4).locator('.spx-head').click()
        pg.wait_for_timeout(420)
        n_open = pg.evaluate("()=>document.querySelectorAll('.spx-panel.is-on').length")
        chk(n_open == 1, 'D1 只開一篇', 'open=%d' % n_open)
        chk(p1.is_visible() is False, 'D2 前一篇已自動收合')

        print('--- E. 再點收合 ---')
        pg.locator('.spx-item').nth(4).locator('.spx-head').click()
        pg.wait_for_timeout(420)
        n_open = pg.evaluate("()=>document.querySelectorAll('.spx-panel.is-on').length")
        chk(n_open == 0, 'E1 再點可收合', 'open=%d' % n_open)

        print('--- F. 講者與誠信標註 ---')
        alltxt = pg.locator('.spx').inner_text()
        for s in SPK:
            chk(s in alltxt, 'F 講者「%s」在列' % s)
        chk('未收錄姓名' in alltxt, 'F9 姓名未錄者有誠信標註')
        chk('未經第三方' in alltxt or '未經第三方來源核實' in alltxt,
            'F10 保留未核實聲明')

        print('--- G. 手機版排版 ---')
        ovf = pg.evaluate(
            "()=>document.documentElement.scrollWidth>window.innerWidth")
        chk(not ovf, 'G1 無橫向溢出')
        pad = pg.evaluate(
            "()=>getComputedStyle(document.querySelector('#spx-p-5')).paddingLeft")
        chk(pad in ('0px', '0'), 'G2 展開面板手機版縮排已移除', pad)
        fs = pg.evaluate(
            "()=>{const p=document.querySelector('.spx-body p');"
            "return p?getComputedStyle(p).fontSize:'none'}")
        chk(fs.replace('px', '').replace('.', '').isdigit()
            and float(fs.replace('px', '')) >= 15, 'G3 內文字級 >=15px', fs)
        # 手機版應為全展開（不設限高），避免嵌套捲動與頁面滾動打架
        mh = pg.evaluate(
            "()=>{const e=document.querySelector('#spx-p-5 .spx-scroll');"
            "return e?getComputedStyle(e).maxHeight:'none'}")
        chk(mh == 'none', 'G4 手機版全展開（無嵌套捲動）', mh)
        mo = pg.evaluate(
            "()=>{const e=document.querySelector('#spx-p-5 .spx-scroll');"
            "return e?getComputedStyle(e).overflowY:'none'}")
        chk(mo == 'visible', 'G5 手機版 overflow 為 visible', mo)

        print('--- H. 桌面版 ---')
        pg2 = b.new_page(viewport={'width': 1440, 'height': 900})
        pg2.goto(PAGE.as_uri())
        pg2.locator('.spx-item').nth(4).locator('.spx-head').click()
        pg2.wait_for_timeout(420)
        pad2 = pg2.evaluate(
            "()=>getComputedStyle(document.querySelector('#spx-p-5')).paddingLeft")
        chk(pad2 not in ('0px', '0'), 'H1 桌面版有縮排對齊', pad2)
        ovf2 = pg2.evaluate(
            "()=>document.documentElement.scrollWidth>window.innerWidth")
        chk(not ovf2, 'H2 桌面版無溢出')
        dh = pg2.evaluate(
            "()=>getComputedStyle("
            "document.querySelector('#spx-p-5 .spx-scroll')).maxHeight")
        chk(dh == '560px', 'H3 桌面版保留 560px 限高捲動', dh)

        pg2.close()
        b.close()

    print()
    if fails:
        print('=== %d 項 FAIL：%s ===' % (len(fails), '、'.join(fails)))
        return 1
    print('=== ALL PASS ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())

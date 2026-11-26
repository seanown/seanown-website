# -*- coding: utf-8 -*-
# 全站文章頁回歸抽查：用瀏覽器實際讀 computed style，
# 確認 CSS 修復後既有頁面（手機版導航、系列晶片、雙欄版型）都正常。
#
# 重點：CSS 花括號不平衡時，HTML 結構與 grep 完全看不出來，
# 只有 computed style 會暴露問題 —— 所以這一層不能省。

import pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 抽查頁面：含電影頁、專欄頁、生活隨筆、新文章
SAMPLES = [
    'article/poker-king-2009/index.html',        # 電影類
    'article/leadership-and-crisis/index.html',  # 澳門觀察
    'article/etiquette-is-not-form/index.html',  # 生活隨筆
    'article/quzhou-nankong-returning-home/index.html',  # 新文章
    'article/jizhan/index.html',                 # 早期編號
]

JS = r"""
() => {
  const o = {};
  const h1 = document.querySelector('h1');
  o.h1 = h1 ? h1.textContent.trim().slice(0, 24) : null;

  // 樣式表能否讀到 + 規則數（花括號不平衡時規則數會異常偏低）
  let rules = 0;
  for (const s of document.styleSheets) {
    try { if (s.cssRules) rules += s.cssRules.length; } catch (e) {}
  }
  o.rules = rules;

  // 手機版導航：非 logo 與聯絡鈕的連結應隱藏
  const links = [...document.querySelectorAll('.tnav a')];
  o.navVisible = links.filter(a => a.offsetParent !== null
      && !a.classList.contains('nav-mcta')).length;
  const mcta = document.querySelector('.nav-mcta');
  o.mctaVisible = mcta ? mcta.offsetParent !== null : false;

  // 專輯晶片（若此頁有）
  const bar = document.querySelector('.sj-bar');
  if (bar) {
    const cs = getComputedStyle(bar);
    o.sjDisplay = cs.display;
    const chip = document.querySelector('.sj-bar .sj-chip');
    o.chipRadius = chip ? getComputedStyle(chip).borderTopLeftRadius : null;
  }

  // 版型與溢出
  o.scrollW = document.documentElement.scrollWidth;
  o.innerW = window.innerWidth;
  const ab = document.querySelector('.abody');
  o.fontSize = ab ? getComputedStyle(ab).fontSize : null;
  o.pCount = document.querySelectorAll('.abody p').length;
  return o;
}
"""

def main():
    ok = True
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for rel in SAMPLES:
            f = ROOT / rel
            if not f.exists():
                print('[SKIP] %s 不存在' % rel)
                continue
            pg = b.new_page(viewport={'width': 390, 'height': 844})
            pg.goto(f.as_uri())
            r = pg.evaluate(JS)
            pg.close()

            issues = []
            if r['h1'] is None:
                issues.append('無 h1')
            if r['rules'] < 60:
                issues.append('CSS 規則數異常偏低(%d)，可能花括號不平衡' % r['rules'])
            if r['navVisible'] != 0:
                issues.append('手機版導航未隱藏(%d 個可見)' % r['navVisible'])
            if not r['mctaVisible']:
                issues.append('聯絡鈕未顯示')
            if r.get('sjDisplay') and r['sjDisplay'] != 'flex':
                issues.append('sj-bar display=%s' % r['sjDisplay'])
            if r.get('chipRadius') and r['chipRadius'] != '999px':
                issues.append('晶片圓角未生效(%s)' % r['chipRadius'])
            if r['scrollW'] > r['innerW']:
                issues.append('橫向溢出 %d>%d' % (r['scrollW'], r['innerW']))

            tag = 'PASS' if not issues else 'FAIL'
            if issues:
                ok = False
            print('[%s] %s' % (tag, rel))
            print('       h1=%s | rules=%d | nav可見=%d | 聯絡鈕=%s'
                  % (r['h1'], r['rules'], r['navVisible'], r['mctaVisible']))
            if r.get('sjDisplay'):
                print('       sj-bar=%s | chip圓角=%s' % (r['sjDisplay'], r['chipRadius']))
            print('       字級=%s | 段落=%d | 溢出=%s'
                  % (r['fontSize'], r['pCount'], r['scrollW'] > r['innerW']))
            for i in issues:
                print('       !! %s' % i)
        b.close()
    print()
    print('=== %s ===' % ('ALL PASS' if ok else 'HAS FAIL'))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())

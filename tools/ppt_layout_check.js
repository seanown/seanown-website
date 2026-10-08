const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// 用法：node ppt_layout_check.js [deck目錄] [截圖輸出子目錄]
// 不傳參數時預設指向第一堂（高效會議主持SOP），保持既有行為。
const DECK = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.resolve('C:/Users/user/WorkBuddy/Seanown.org/高效會議主持SOP');
const FILE = 'file:///' + path.join(DECK, 'index.html').replace(/\\/g, '/');
// 截圖一律寫到各自的 deck 目錄下，避免不同簡報互相覆蓋
const SHOTS = path.join(DECK, 'shots');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const page = await browser.newPage({ viewport: { width: 1400, height: 860 } });
  await page.goto(FILE, { waitUntil: 'networkidle' });

  const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
  console.log('总页数: ' + total + '\n');

  const problems = [];

  for (let i = 0; i < total; i++) {
    await page.evaluate(n => { location.hash = n + 1; }, i);
    await page.waitForTimeout(140);

    const issues = await page.evaluate((idx) => {
      const el = document.querySelectorAll('.slide')[idx];
      el.style.transform = 'none';
      const issues = [];
      const dR = el.getBoundingClientRect();

      if (el.scrollWidth > 1281) issues.push('横向溢出 ' + el.scrollWidth + 'px');
      if (el.scrollHeight > 721) issues.push('纵向溢出 ' + el.scrollHeight + 'px');

      const bad = [];
      el.querySelectorAll('*').forEach(n => {
        const b = n.getBoundingClientRect();
        if (b.width === 0 || b.height === 0) return;
        const dx = Math.round(b.right - dR.right);
        const dy = Math.round(b.bottom - dR.bottom);
        const dl = Math.round(b.left - dR.left);
        const dt = Math.round(b.top - dR.top);
        if (dx > 2 || dy > 2 || dl < -2 || dt < -2) {
          const cls = (typeof n.className === 'string' && n.className)
            ? '.' + n.className.split(' ').filter(Boolean).join('.') : '';
          bad.push(n.tagName + cls + ' 右+' + dx + ' 下+' + dy + ' 左' + dl + ' 上' + dt);
        }
      });
      if (bad.length) issues.push('越界 ' + bad.length + ' 个: ' + bad.slice(0, 3).join(' | '));

      const sq = [];
      el.querySelectorAll('*').forEach(n => {
        if (n.children.length) return;
        const txt = (n.textContent || '').trim();
        if (txt.length < 4) return;
        const fs2 = parseFloat(getComputedStyle(n).fontSize);
        const b = n.getBoundingClientRect();
        if (b.height > fs2 * 6 && b.width < fs2 * 1.9) {
          sq.push('"' + txt.slice(0, 16) + '" w=' + Math.round(b.width) + ' h=' + Math.round(b.height));
        }
      });
      if (sq.length) issues.push('竖排挤压 ' + sq.length + ' 处: ' + sq.slice(0, 3).join(' | '));

      el.style.transform = '';
      return issues;
    }, i);

    console.log('P' + String(i + 1).padStart(2, '0') + '  ' + (issues.length ? 'FAIL' : 'OK  ') +
      (issues.length ? '  ' + issues.join(' ;; ') : ''));
    if (issues.length) problems.push(i + 1);
  }

  if (!fs.existsSync(SHOTS)) fs.mkdirSync(SHOTS, { recursive: true });
  const p2 = await browser.newPage({ viewport: { width: 1320, height: 790 } });
  await p2.goto(FILE, { waitUntil: 'networkidle' });
  for (let i = 0; i < total; i++) {
    await p2.evaluate(n => { location.hash = n + 1; }, i);
    await p2.waitForTimeout(120);
    const el = await p2.$('.slide.on');
    if (el) await el.screenshot({ path: path.join(SHOTS, 'p' + String(i + 1).padStart(2, '0') + '.png') });
  }
  console.log('\n截图已输出: ' + SHOTS);
  console.log(problems.length ? '有问题页: ' + problems.join(', ') : '全部 ' + total + ' 页通过');

  await browser.close();
})();

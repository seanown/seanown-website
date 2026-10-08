// 驗證文章頁的微信分享按鈕：按鈕存在、位置正確、點了能開遮罩、能生出 QR、複製連結正確
const path = require('path');
const fs = require('fs');

const TARGET = process.argv[2]
  || 'file:///C:/Users/user/WorkBuddy/Seanown.org/article/quzhou-nankong-returning-home/index.html';
const SHOT_DIR = process.argv[3]
  || 'C:/Users/user/WorkBuddy/Seanown.org/shots-share';

// playwright 裝在 WorkBuddy 的 managed workspace
const PW = 'C:/Users/user/.workbuddy/binaries/node/workspace/node_modules/playwright';

(async () => {
  const { chromium } = require(PW);

  // 系統已裝瀏覽器（ms-playwright 的 chromium 沒下載），直接沿用系統 Chrome
  const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

  let browser;
  try {
    browser = await chromium.launch({ executablePath: CHROME });
  } catch (e) {
    console.log('PLAYWRIGHT_FAIL: ' + String(e).slice(0, 120));
    process.exit(2);
  }
  const page = await browser.newPage({ viewport: { width: 1080, height: 900 } });
  // 每次都取最新檔案，避免改完 SVG 仍看到舊的 console error
  await page.route('**/*', route => route.continue({ headers: { ...route.request().headers(), 'cache-control': 'no-cache' } }));
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + String(e).slice(0, 160)));

  await page.goto(TARGET, { waitUntil: 'load' });
  await page.waitForTimeout(600);

  const btn = await page.$('#wkShareFab');
  console.log('按鈕存在: ' + (btn ? 'YES' : 'NO'));
  if (btn) {
    const box = await btn.boundingBox();
    console.log('位置: x=' + Math.round(box.x) + ' y=' + Math.round(box.y)
      + ' w=' + Math.round(box.width) + ' h=' + Math.round(box.height));
    console.log('釘在右上角: ' + (box.x > 900 && box.y < 120 ? 'YES' : 'NO'));
    console.log('文案: ' + (await btn.textContent()).trim());
    console.log('背景色: ' + (await btn.evaluate(el => getComputedStyle(el).backgroundColor)));

    await btn.click();
    await page.waitForTimeout(700);

    const open = await page.evaluate(() => document.getElementById('wkShareMask').classList.contains('open'));
    console.log('點擊後遮罩開啟: ' + (open ? 'YES' : 'NO'));

    const qr = await page.evaluate(() => {
      const img = document.getElementById('wkQr');
      return { src: (img && img.src || '').slice(0, 40), w: img ? img.naturalWidth : 0 };
    });
    console.log('QR 圖片產生: ' + (qr.src.startsWith('data:image') ? 'YES' : 'NO') + ' (' + qr.w + 'px)');

    const canonical = await page.evaluate(() => {
      const c = document.querySelector('link[rel="canonical"]');
      return c ? c.href : 'NONE';
    });
    console.log('連結來源 canonical: ' + canonical);

    const tip = await page.evaluate(() => {
      const t = document.querySelector('.wk-share-tip');
      return t ? t.textContent.replace(/\s+/g, ' ').trim().slice(0, 40) : 'NONE';
    });
    console.log('提示文案: ' + tip + '...');

    fs.mkdirSync(SHOT_DIR, { recursive: true });
    await page.screenshot({ path: path.join(SHOT_DIR, 'share-open.png') });
    console.log('截圖: share-open.png');
  }

  console.log('JS 錯誤數: ' + errors.length);
  errors.slice(0, 4).forEach(e => console.log('  ERR ' + e));

  await browser.close();
})();

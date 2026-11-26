const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SITE = 'C:/Users/user/WorkBuddy/Seanown.org';
const DECK = path.join(SITE, 'slides', 'meeting-sop');
const FILE = 'file:///' + path.join(DECK, 'index.html').replace(/\\/g, '/');
const OUT = path.join(SITE, 'assets', 'images', 'posts', 'deck-meeting-sop');

(async () => {
  if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome' });
  // 視窗高度 = 720(投影片) + 70(控制條) → fit() 的scale 恰好為 1，
  // 投影片完整落在控制條之上，不會被疊到；若視窗太矮控制條會壓進截圖
  const page = await browser.newPage({ viewport: { width: 1280, height: 790 }, deviceScaleFactor: 1 });
  await page.goto(FILE, { waitUntil: 'networkidle' });
  // 截圖模式：#ctrl（底部控制條）與 #bar（頂部進度條）是 position:fixed，
  // 會疊在投影片上被一起拍進去 → 取圖時隱藏
  await page.addStyleTag({ content: '#ctrl,#bar{display:none !important}' });
  const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
  console.log('总页数: ' + total);

  const CAPTIONS = [
    '封面：會議不是Discussion，是一筆交易',
    '目錄：三章十四頁',
    '章01 扉頁：我們把會開成了什麼',
    '四小時的真正去向',
    '真正用於決策：不超過十五分鐘',
    '章02 扉頁：主持人不是最會講的人',
    '主持人的三個「不是」',
    '主持節奏：五段口訣',
    '現場：把話轉到別人嘴裡',
    '章03 扉頁：會議結束了，事情才開始',
    '正式會議決策流程八步',
    '討論與表決，兩個階段',
    '附錄：前24 小時檢核',
    '高效會議主持 SOP 總表',
  ];

  for (let i = 0; i < total; i++) {
    // 用頁面內建的 show() 切頁，不靠 .slide.on 的 CSS 類別（避免抓到尚未渲染的頁）
    await page.evaluate(n => { window.__go(n); }, i);
    await page.waitForTimeout(260);
    const el = await page.$('.slide.on');
    if (!el) { console.log('P' + (i + 1) + ' 未找到 .slide.on'); continue; }
    const name = 'deck-' + String(i + 1).padStart(2, '0') + '.jpg';
    await el.screenshot({ path: path.join(OUT, name), type: 'jpeg', quality: 78 });
    console.log('P' + String(i + 1).padStart(2, '0') + '  ' + (CAPTIONS[i] || '') + '  -> ' + name);
  }
  await browser.close();
  console.log('\n输出目录: ' + OUT);
})();
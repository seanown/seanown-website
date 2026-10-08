const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SITE = 'http://127.0.0.1:8899';
const OUT = path.resolve('C:/Users/user/WorkBuddy/Seanown.org/_verify_meeting');

(async () => {
  if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome' });

  // ---------- 桌機：重點卡 + 演講稿區塊 ----------
  const d = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  await d.goto(SITE + '/article/meeting-ends-things-begin/', { waitUntil: 'networkidle' });

  const kp = await d.$('.kp');
  if (kp) { await kp.scrollIntoViewIfNeeded(); await d.waitForTimeout(300);
    await kp.screenshot({ path: path.join(OUT, 'desktop-kp.png') }); console.log('desktop-kp  OK'); }

  const dk = await d.$('.dk');
  if (dk) { await dk.scrollIntoViewIfNeeded(); await d.waitForTimeout(400);
    await d.screenshot({ path: path.join(OUT, 'desktop-dk.png') }); console.log('desktop-dk  OK'); }

  // 附錄第一張表格
  const tbl = await d.$('.tbl-wrap');
  if (tbl) { await tbl.scrollIntoViewIfNeeded(); await d.waitForTimeout(300);
    await d.screenshot({ path: path.join(OUT, 'desktop-table.png') }); console.log('desktop-table OK'); }

  // 全文溢出檢查
  const issues = await d.evaluate(() => {
    const out = [];
    const de = document.documentElement;
    if (de.scrollWidth > de.clientWidth + 1) out.push('頁面橫向溢出 ' + de.scrollWidth + ' > ' + de.clientWidth);
    const ab = document.querySelector('.abody');
    if (ab) {
      // .abody 在 PC 是雙欄；確認重點卡與演講稿有跨欄（column-span:all 生效）
      const kpEl = document.querySelector('.kp'), dkEl = document.querySelector('.dk');
      const spanW = ab.getBoundingClientRect().width;
      if (kpEl && Math.abs(kpEl.getBoundingClientRect().width - spanW) > 4)
        out.push('重點卡未跨欄：' + Math.round(kpEl.getBoundingClientRect().width) + ' vs ' + Math.round(spanW));
      if (dkEl && Math.abs(dkEl.getBoundingClientRect().width - spanW) > 4)
        out.push('演講稿未跨欄：' + Math.round(dkEl.getBoundingClientRect().width) + ' vs ' + Math.round(spanW));
      if (ab.scrollHeight > 0 && ab.scrollWidth > ab.clientWidth + 2)
        out.push('.abody 橫向溢出 ' + ab.scrollWidth + ' > ' + ab.clientWidth);
    }
    // 圖片全部載入成功
    document.querySelectorAll('.dk-item img').forEach(im => {
      if (!im.complete || im.naturalWidth === 0) out.push('縮圖載入失敗: ' + im.getAttribute('src'));
    });
    return out;
  });
  console.log(issues.length ? '桌機問題:\n  ' + issues.join('\n  ') : '桌機：無問題');

  // ---------- 手機 ----------
  const m = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true });
  await m.goto(SITE + '/article/meeting-ends-things-begin/', { waitUntil: 'networkidle' });
  const mIssues = await m.evaluate(() => {
    const out = [];
    const de = document.documentElement;
    if (de.scrollWidth > de.clientWidth + 1) out.push('手機頁面橫向溢出 ' + de.scrollWidth + ' > ' + de.clientWidth);
    const ab = document.querySelector('.abody');
    if (ab && ab.scrollWidth > ab.clientWidth + 2) out.push('手機 .abody 溢出 ' + ab.scrollWidth + ' > ' + ab.clientWidth);
    // 重點卡序號圓點不可被裁切
    const li = document.querySelector('.kp-list li');
    if (li) { const b = li.getBoundingClientRect(); if (b.right > de.clientWidth + 1) out.push('重點卡 li 越界 right=' + Math.round(b.right)); }
    // 演講稿按鈕要滿版好按
    const btn = document.querySelector('.dk-btn');
    if (btn) { const b = btn.getBoundingClientRect(); if (b.width < de.clientWidth * 0.7) out.push('放映按鈕過窄 ' + Math.round(b.width)); }
    return out;
  });
  console.log(mIssues.length ? '手機問題:\n  ' + mIssues.join('\n  ') : '手機：無問題');

  await m.screenshot({ path: path.join(OUT, 'mobile-top.png'), fullPage: false });
  const mkp = await m.$('.kp');
  if (mkp) { await mkp.scrollIntoViewIfNeeded(); await m.waitForTimeout(300);
    await m.screenshot({ path: path.join(OUT, 'mobile-kp.png') }); }
  const mdk = await m.$('.dk');
  if (mdk) { await mdk.scrollIntoViewIfNeeded(); await m.waitForTimeout(300);
    await m.screenshot({ path: path.join(OUT, 'mobile-dk.png') }); }
  console.log('手機截圖完成');

  await browser.close();
  console.log('\n輸出: ' + OUT);
})();
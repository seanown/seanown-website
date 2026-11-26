// 首屏精簡效果驗證：桌面 + 行動兩個尺寸截圖
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const url = 'file:///' + path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/');

  for (const [name, w, h] of [['desktop', 1280, 900], ['tablet', 820, 1180], ['mobile', 390, 844]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);

    // 檢測關鍵元素的實際可見性
    const check = await page.evaluate(() => {
      const ids = ['hero-name', 'hero-main-msg', 'hero-subtitle', 'hero-slogan'];
      const out = {};
      for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) { out[id] = 'NOT_FOUND'; continue; }
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        out[id] = (cs.display === 'none' || cs.visibility === 'hidden')
          ? 'HIDDEN'
          : `VISIBLE (${Math.round(r.width)}x${Math.round(r.height)}, display=${cs.display})`;
      }
      const trust = document.querySelector('.hero-trust');
      out['.hero-trust'] = !trust ? 'NOT_FOUND'
        : (getComputedStyle(trust).display === 'none' ? 'HIDDEN' : 'VISIBLE');
const btns = document.querySelector('.hero-buttons');
    const br = btns ? btns.getBoundingClientRect() : null;
    out['.hero-buttons'] = br ? `VISIBLE (y=${Math.round(br.top)})` : 'NOT_FOUND';
    // 主標題行數估算（用高度 / 行高）
    const h1 = document.getElementById('hero-main-msg');
    if (h1) {
      const cs = getComputedStyle(h1);
      const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2;
      const lines = Math.round(h1.getBoundingClientRect().height / lh);
      out['主標題行數'] = `${lines} 行 (font-size=${cs.fontSize})`;
    }
    // 是否溢出視口寬度
    out['橫向溢出'] = document.documentElement.scrollWidth > window.innerWidth + 2
      ? `YES (${document.documentElement.scrollWidth} > ${window.innerWidth})` : 'NO';
    return out;
    });

    console.log(`\n[${name} ${w}x${h}]`);
    for (const [k, v] of Object.entries(check)) console.log(`  ${k.padEnd(18)} ${v}`);

    await page.screenshot({ path: path.resolve(__dirname, `../_shots/hero-${name}.png`) });
    await page.close();
  }
  await browser.close();
  console.log('\n截圖輸出至 _shots/hero-{desktop,mobile}.png');
})();
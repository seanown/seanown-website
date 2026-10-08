# -*- coding: utf-8 -*-
"""線上驗證：CSSOM 規則數 + 致詞稿展開互動 + 手機版晶片 + 橫向溢出"""
import asyncio, json, sys
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
ART = "https://seanown.org/article/quzhou-nankong-returning-home/"
# 門檻按頁型分：文章頁是完整模板（115-150），列表／系列頁是簡化模板（55-70）
PAGES = [
    (ART, 100, True),# 文章頁：門檻 100、必須有 sj-
    ("https://seanown.org/article/casino-tycoon-1992/", 100, True),
    ("https://seanown.org/", 100, True),
    ("https://seanown.org/articles/", 50, True),      # 列表頁：簡化模板
    ("https://seanown.org/series/life-essays/", 50, False),  # 系列頁：本就無 sj- 元素
]

R = []

def chk(name, cond, extra=""):
    R.append((bool(cond), name, extra))

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()

        # ===== A. 全站 CSSOM 規則數 =====
        ctx = await b.new_context(viewport={"width": 390, "height": 844},
                                  user_agent=UA, is_mobile=True)
        print("=== A. 全站 CSSOM 規則數（正常 115-150，bug 時 30）===")
        for url, th, need_sj in PAGES:
            pg = await ctx.new_page()
            await pg.goto(url, wait_until="load", timeout=45000)
            n = await pg.evaluate(
                "()=>document.styleSheets.length?([...document.styleSheets]"
                ".reduce((a,s)=>{try{return a+s.cssRules.length}catch(e){return a}},0)):0")
            sj = await pg.evaluate(
                "()=>{try{return [...document.styleSheets].reduce((a,s)=>{try{"
                "return a+[...s.cssRules].filter(r=>r.selectorText&&"
                "/(sj-|sj\\b)/.test(r.selectorText)).length}catch(e){return a}},0)}"
                "catch(e){return -1}}")
            # 有 sj- 元素才要求有 sj- 規則
            has_sj_els = await pg.evaluate(
                "()=>{let f=false;document.querySelectorAll('*').forEach(e=>{"
                "if(e.className&&typeof e.className==='string'&&/(^|\\s)sj-/.test(e.className))"
                "f=true});return f}")
            ok = n >= th
            tag = f"{'PASS' if ok else 'FAIL'}  {n:4d}條(門檻{th})  sj-規則 {sj:2d}條  sj-元素 {'有' if has_sj_els else '無'}  {url}"
            print(f"  {tag}")
            chk(f"CSSOM {n}條 {url}", ok)
            if need_sj or has_sj_els:
                chk(f"sj- 規則 {url}", sj > 0, f"實得 {sj}")
            await pg.close()

        # ===== B. 新文章：手機版晶片不擠一行 =====
        print("\n=== B. 手機版「按專輯逛」晶片 ===")
        pg = await ctx.new_page()
        await pg.goto(ART, wait_until="load", timeout=45000)
        chip = await pg.evaluate("""()=>{
          const c=document.querySelector('.sj, .series-chip, [class*=sj-]');
          if(!c) return null;
          const r=c.getBoundingClientRect();
          const cs=getComputedStyle(c);
          return {w:Math.round(r.width),h:Math.round(r.height),disp:cs.display};
        }""")
        if chip:
            ok = chip["h"] > 20
            print(f"  {'PASS' if ok else 'FAIL'}  晶片 {chip['w']}x{chip['h']} display={chip['disp']}")
            chk("手機版晶片高度正常", ok, str(chip))
        else:
            print("  SKIP  未找到晶片元素")
            chk("找到晶片元素", False)

        # ===== C. 致詞稿：8 篇都在列 =====
        print("\n=== C. 致詞稿 8 篇結構 ===")
        cnt = await pg.evaluate("()=>document.querySelectorAll('.spx-item').length")
        chk("8 篇致詞稿", cnt == 8, f"實得 {cnt}")
        print(f"  {'PASS' if cnt==8 else 'FAIL'}  spx-item = {cnt}")

        nos = await pg.evaluate(
            "()=>[...document.querySelectorAll('.spx-no')].map(e=>e.textContent.trim())")
        print(f"  序號: {nos}")

        cav = await pg.evaluate("()=>document.querySelectorAll('.spx-cav').length")
        chk("誠信標註存在", cav >= 3, f"{cav} 處")
        print(f"  {'PASS' if cav>=3 else 'FAIL'}  未錄姓名標註 = {cav} 處")

        spk = await pg.evaluate(
            "()=>[...document.querySelectorAll('.spx-by')].map(e=>e.textContent.trim().slice(0,20))")
        print(f"  講者 {len(spk)} 位:")
        for i, s in enumerate(spk, 1):
            print(f"    {i}. {s}")

        # ===== D. 手機版全展開（不嵌套滾動）=====
        print("\n=== D. 手機版展開行為 ===")
        btn0 = pg.locator(".spx-head").first
        await btn0.scroll_into_view_if_needed()
        await btn0.click()
        await pg.wait_for_timeout(500)
        m = await pg.evaluate("""()=>{
          const p=document.querySelector('.spx-panel.is-on');
          if(!p) return null;
          const sc=p.querySelector('.spx-scroll');
          const cs=sc?getComputedStyle(sc):null;
          return {maxH:cs?cs.maxHeight:'-',ovf:cs?cs.overflowY:'-',
                  h:Math.round(p.getBoundingClientRect().height)};
        }""")
        if m:
            ok = (m["maxH"] == "none")
            print(f"  {'PASS' if ok else 'FAIL'}  手機版 max-height={m['maxH']} overflow-y={m['ovf']} 展開高={m['h']}px")
            chk("手機版全展開", ok, str(m))
        else:
            chk("手機版展開", False)

        # 展開數量應為 1
        openN = await pg.evaluate("()=>document.querySelectorAll('.spx-panel.is-on').length")
        chk("同時只開一篇", openN == 1, f"實得 {openN}")
        print(f"  {'PASS' if openN==1 else 'FAIL'}  同時展開 = {openN} 篇")

        # 點第 3 篇 → 第 1 篇應自動收合
        await pg.locator(".spx-head").nth(2).scroll_into_view_if_needed()
        await pg.locator(".spx-head").nth(2).click()
        await pg.wait_for_timeout(450)
        openN2 = await pg.evaluate("()=>document.querySelectorAll('.spx-panel.is-on').length")
        firstClosed = await pg.evaluate(
            "()=>document.querySelector('.spx-head').getAttribute('aria-expanded')")
        chk("切換時互斥", openN2 == 1, f"實得 {openN2}")
        chk("前一篇已收合", firstClosed == "false", str(firstClosed))
        print(f"  {'PASS' if openN2==1 and firstClosed=='false' else 'FAIL'}  互斥切換（展開 {openN2} 篇、前篇 aria={firstClosed}）")

        # ===== E. 無橫向溢出 =====
        ovf = await pg.evaluate(
            "()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        chk("手機版無橫向溢出", ovf <= 1, f"溢出 {ovf}px")
        print(f"  {'PASS' if ovf<=1 else 'FAIL'}  橫向溢出 = {ovf}px")

        await pg.close()
        await ctx.close()

        # ===== F. 桌面版限高 560px =====
        print("\n=== E. 桌面版展開行為 ===")
        ctx2 = await b.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA)
        pg2 = await ctx2.new_page()
        await pg2.goto(ART, wait_until="load", timeout=45000)
        await pg2.locator(".spx-head").first.scroll_into_view_if_needed()
        await pg2.locator(".spx-head").first.click()
        await pg2.wait_for_timeout(450)
        d = await pg2.evaluate("""()=>{
          const sc=document.querySelector('.spx-panel.is-on .spx-scroll');
          if(!sc) return null;
          const cs=getComputedStyle(sc);
          return {maxH:cs.maxHeight,ovf:cs.overflowY,h:Math.round(sc.getBoundingClientRect().height)};
        }""")
        if d:
            ok = d["maxH"] == "560px" and d["ovf"] == "auto"
            print(f"  {'PASS' if ok else 'FAIL'}  桌面版 max-height={d['maxH']} overflow-y={d['ovf']} 視窗高={d['h']}px")
            chk("桌面版 560px 限高", ok, str(d))
        else:
            chk("桌面版展開", False)

        dovf = await pg2.evaluate(
            "()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        chk("桌面版無橫向溢出", dovf <= 1, f"溢出 {dovf}px")
        print(f"  {'PASS' if dovf<=1 else 'FAIL'}  桌面版橫向溢出 = {dovf}px")

        await pg2.screenshot(path="_shots/live_desktop_spx.png")
        await pg2.close(); await ctx2.close(); await b.close()

    print("\n" + "=" * 58)
    ok = sum(1 for c, _, _ in R if c)
    print(f"線上驗證：{ok}/{len(R)} PASS")
    print("=" * 58)
    bad = [(n, e) for c, n, e in R if not c]
    if bad:
        print("\n未通過：")
        for n, e in bad:
            print(f"  FAIL  {n}  {e}")
        sys.exit(1)
    print("\n全部通過。")

asyncio.run(main())
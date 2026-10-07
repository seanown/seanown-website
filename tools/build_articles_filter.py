#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章列表「分類＋年份＋搜尋」三重篩選面板 —— 單一來源（single source of truth）

背景
----
1. build_articles.py 原本有兩層 bug：
   - cat_btns 算好了卻沒對應的 {cats} 佔位符 → 分類按鈕從未輸出到 HTML（CSS/JS 都在，DOM 不在）
   - CATS 常數漏了「澳門電影」「影評」，而這兩類合計 83 篇（全部 107 篇裡的大頭）
2. articles/index.html 是靜態產物，107 張卡混排，訪客無法掃讀。

用法
----
python tools/build_articles_filter.py            # 直接升級靜態產物 articles/index.html
python -c "import sys;sys.path.insert(0,'tools');import build_articles_filter as f;print(f.panel_bundle({...}, {...}, 107)['html'])"

本檔提供三個可匯出函式：
  scan_cards(html)      -> (cats Counter, years Counter, total int)
  panel_bundle(cats, years, total) -> {'html':..., 'style':..., 'js':...}
  apply_to_html(html)   -> 新版 HTML（冪等，可重跑）
"""
import re
import os
import sys
import html as _html
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'articles', 'index.html')

# 訪客優先看到的順序（非字母排序）
CAT_ORDER = ['澳門觀察', '澳門電影', '影評', '生活隨筆', '文化隨筆', '行走見聞', '閱讀筆記']
NON_FILM_CATS = {'澳門觀察', '生活隨筆', '文化隨筆', '行走見聞', '閱讀筆記'}


def esc(s):
    return _html.escape(str(s), quote=True)


# ---------------------------------------------------------------- 掃描
def scan_cards(s):
    """回傳 (cats, years, total)。

    重點：不要用「data-cat 與 data-fy 必須同時出現且順序固定」的框 regex ——
    產業文章卡只有 data-cat 沒有 data-fy，會被整批漏掉（107 → 83）。
    """
    cats = Counter()
    for c in re.findall(r'<a class="lc-card[^"]*"[^>]*?\bdata-cat="([^"]*)"', s):
        cats[c] += 1
    years = Counter()
    for y in re.findall(r'<a class="lc-card[^"]*"[^>]*?\bdata-fy="([^"]*)"', s):
        years[y] += 1
    total = len(re.findall(r'<a class="lc-card[^"]*"', s))
    return cats, years, total


# ---------------------------------------------------------------- 面板
def panel_bundle(cats, years, total):
    ordered = [c for c in CAT_ORDER if c in cats] + \
              [c for c in sorted(cats) if c not in CAT_ORDER]

    btns = ['<button class="lc-cat on" data-c="全部" type="button">全部 <span>%d</span></button>' % total]
    for c in ordered:
        btns.append('<button class="lc-cat" data-c="%s" type="button">%s <span>%d</span></button>'
                    % (esc(c), esc(c), cats[c]))
    cat_html = '\n        '.join(btns)

    opts = ['<option value="">全部年份</option>']
    for y in sorted(years, key=lambda x: (-len(x), x), reverse=True):
        opts.append('<option value="%s">%s 年（%d）</option>' % (y, y, years[y]))
    yr_html = '\n        '.join(opts)

    panel = '''<div class="filter-panel" id="filter-panel">
  <div class="fp-top">
    <div class="fp-search">
      <label for="fp-q" class="sr-only">搜尋文章標題或內文摘要</label>
      <input type="search" id="fp-q" placeholder="搜尋文章標題、關鍵字…" autocomplete="off">
      <button type="button" class="fp-clear" id="fp-clear" hidden aria-label="清除搜尋關鍵字">&times;</button>
    </div>
    <div class="fp-count" id="fp-count" role="status" aria-live="polite">顯示全部 {total} 篇</div>
  </div>
  <div class="fp-row">
    <span class="fp-label" id="fp-cat-label">分類</span>
    <div class="fp-cats" role="group" aria-labelledby="fp-cat-label">
      {cat_html}
    </div>
  </div>
  <div class="fp-row">
    <span class="fp-label" id="fp-year-label">作品年份</span>
    <div class="fp-years">
      <label for="fp-year" class="sr-only">依電影作品上映年份篩選</label>
      <select id="fp-year" aria-describedby="fp-tip">
        {yr_html}
      </select>
      <span class="fp-tip" id="fp-tip">僅電影文章有上映年份；產業文章請用上方分類或搜尋。</span>
    </div>
  </div>
  <div class="fp-empty" id="fp-empty" hidden>
    <p>找不到符合條件的文章。</p>
    <button type="button" class="fp-reset" id="fp-reset">清除全部篩選條件</button>
  </div>
</div>'''.format(total=total, cat_html=cat_html, yr_html=yr_html)

    style = '''
/* ===== 文章列表三重篩選（分類＋年份＋搜尋）===== */
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px;border-radius:4px}
.filter-panel{position:sticky;top:62px;z-index:41;background:rgba(255,255,255,.97);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:18px 24px 16px;box-shadow:0 6px 18px rgba(2,8,32,.05)}
.fp-top{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:14px}
.fp-search{position:relative;flex:1 1 320px;min-width:220px}
.fp-search input{width:100%;padding:11px 40px 11px 42px;border:1.5px solid var(--line);border-radius:999px;font-size:14.5px;font-family:inherit;background:#fff;color:var(--text);transition:border-color .2s,box-shadow .2s}
.fp-search input::placeholder{color:#98A2B3}
.fp-search input:hover{border-color:#C4CEDA}
.fp-search input:focus{border-color:var(--blue);outline:none;box-shadow:0 0 0 3px rgba(0,38,118,.1)}
.fp-search::before{content:'';position:absolute;left:16px;top:50%;width:13px;height:13px;margin-top:-8px;border:2px solid #98A2B3;border-radius:50%;pointer-events:none}
.fp-search::after{content:'';position:absolute;left:27px;top:calc(50% + 5px);width:6px;height:2px;background:#98A2B3;transform:rotate(45deg);pointer-events:none}
.fp-clear{position:absolute;right:8px;top:50%;transform:translateY(-50%);width:26px;height:26px;border:none;border-radius:50%;background:#EEF1F5;color:var(--gray);font-size:17px;line-height:1;cursor:pointer;transition:background .2s,color .2s}
.fp-clear:hover{background:var(--blue);color:#fff}
.fp-count{font-size:13.5px;color:var(--gray);font-weight:600;white-space:nowrap;font-variant-numeric:tabular-nums}
.fp-count b{color:var(--blue);font-size:15px}
.fp-row{display:flex;align-items:flex-start;gap:12px;margin-bottom:10px}
.fp-row:last-of-type{margin-bottom:0}
.fp-label{flex:0 0 auto;font-size:12px;letter-spacing:2px;color:var(--gray);font-weight:700;padding-top:8px}
.fp-cats{display:flex;flex-wrap:wrap;gap:8px;flex:1}
.lc-cat{border:1.5px solid var(--line);background:#fff;border-radius:999px;padding:7px 16px;font-size:13.5px;font-weight:600;color:var(--text);cursor:pointer;transition:border-color .2s,background .2s,color .2s;font-family:inherit}
.lc-cat span{font-size:11.5px;color:var(--gray);margin-left:4px;font-weight:600}
.lc-cat:hover{border-color:var(--gold)}
.lc-cat.on{background:var(--blue);border-color:var(--blue);color:#fff}
.lc-cat.on span{color:var(--gold)}
.fp-years{display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex:1}
.fp-years select{padding:8px 14px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit;background:#fff;color:var(--text);cursor:pointer;transition:border-color .2s,box-shadow .2s}
.fp-years select:hover{border-color:var(--gold)}
.fp-years select:focus{border-color:var(--blue);outline:none;box-shadow:0 0 0 3px rgba(0,38,118,.1)}
.fp-years select:disabled{opacity:.45;cursor:not-allowed}
.fp-tip{font-size:12.5px;color:#98A2B3;flex:1 1 240px;min-width:200px}
.fp-empty{text-align:center;padding:26px 0 6px}
.fp-empty p{color:var(--gray);font-size:15px;margin-bottom:12px}
.fp-reset{border:1.5px solid var(--blue);background:#fff;color:var(--blue);border-radius:999px;padding:8px 20px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;transition:background .2s,color .2s}
.fp-reset:hover{background:var(--blue);color:#fff}
@media(max-width:620px){
  .filter-panel{padding:14px 16px 12px}
  .fp-row{flex-direction:column;gap:7px}
  .fp-label{padding-top:0}
  .fp-search{flex:1 1 100%}
  .fp-count{font-size:12.5px}
}
@media(max-width:900px){.filter-bar{display:none}}
'''

    js = '''(function(){
  var panel=document.getElementById('filter-panel');
  if(!panel)return;
  var cards=Array.prototype.slice.call(document.querySelectorAll('.lc-card'));
  var btns=Array.prototype.slice.call(panel.querySelectorAll('.lc-cat'));
  var q=document.getElementById('fp-q');
  var yearSel=document.getElementById('fp-year');
  var clearBtn=document.getElementById('fp-clear');
  var countEl=document.getElementById('fp-count');
  var emptyEl=document.getElementById('fp-empty');
  var resetBtn=document.getElementById('fp-reset');
  var cat='全部', year='', kw='';
  var NON_FILM={'澳門觀察':1,'生活隨筆':1,'文化隨筆':1,'行走見聞':1,'閱讀筆記':1};

  function syncYearEnabled(){
    // 產業文章沒有「上映年份」，選到那些分類時把年份篩選關掉並清值，
    // 否則使用者會撞見 0 篇的假象。
    var off=(cat!=='全部' && NON_FILM[cat]);
    yearSel.disabled=!!off;
    if(off){ yearSel.value=''; year=''; }
  }

  function apply(){
    syncYearEnabled();
    var kwLow=kw.trim().toLowerCase();
    var shown=0;
    cards.forEach(function(card){
      var okCat=(cat==='全部')||(card.getAttribute('data-cat')===cat);
      var fy=card.getAttribute('data-fy')||'';
      var okYear=!year||(fy===year);
      var okKw=!kwLow||((card.textContent||'').toLowerCase().indexOf(kwLow)>-1);
      var vis=okCat&&okYear&&okKw;
      card.classList.toggle('hide',!vis);
      if(vis)shown++;
    });
    var filtered=(kw.trim()||cat!=='全部'||year);
    countEl.innerHTML=filtered
      ? '符合條件 <b>'+shown+'</b> 篇（共 '+cards.length+' 篇）'
      : '顯示全部 '+cards.length+' 篇';
    emptyEl.hidden=shown>0;
    clearBtn.hidden=!kw;
  }

  btns.forEach(function(b){
    b.addEventListener('click',function(){
      btns.forEach(function(x){x.classList.remove('on')});
      b.classList.add('on');
      cat=b.getAttribute('data-c');
      apply();
    });
  });
  q.addEventListener('input',function(){kw=q.value;apply();});
  yearSel.addEventListener('change',function(){year=yearSel.value;apply();});
  clearBtn.addEventListener('click',function(){q.value='';kw='';apply();q.focus();});
  resetBtn.addEventListener('click',function(){
    q.value='';kw='';yearSel.value='';year='';cat='全部';
    btns.forEach(function(x){x.classList.toggle('on',x.getAttribute('data-c')==='全部')});
    apply();q.focus();
  });
  apply();
})();'''

    return {'html': panel, 'style': style, 'js': js}


# ---------------------------------------------------------------- 套用
def apply_to_html(s):
    cats, years, total = scan_cards(s)
    if not total:
        raise SystemExit('[ABORT] 找不到 .lc-card，請確認目標檔是否正確')
    b = panel_bundle(cats, years, total)

    # 1. 舊的 filter-bar（含按鈕）→ 移除
    s = re.sub(r'<div class="filter-bar"[^>]*>.*?</div>\s*', '', s, flags=re.S)

    # 2. 樣式：移除舊版 filter-panel 區塊（冪等），再注入新版
    s = re.sub(r'\n+/\* ===== 文章列表三重篩選（分類＋年份＋搜尋）===== \*/.*?(?=\n</style>)',
               '', s, flags=re.S)
    s = re.sub(r'\n+/\* ===== 三重篩選面板（分類＋年份＋搜尋）===== \*/.*?(?=\n</style>)',
               '', s, flags=re.S)

    # 3. 舊的分類 JS → 移除（兩種寫法都要涵蓋）
    s = re.sub(r'\n*\(function\(\)\{\s*var SITE=.*?\}\)\(\);\s*', '\n', s, flags=re.S)
    s = re.sub(r'\n*\(function\(\)\{\s*var panel=document\.getElementById\(\'filter-panel\'\).*?\}\)\(\);\s*',
               '\n', s, flags=re.S)

    # 4. 注入樣式
    if '<style>' in s:
        s = s.replace('</style>', b['style'] + '</style>', 1)

    # 5. 注入面板（放在 ser-jump 之後、grid 之前）
    if 'id="filter-panel"' not in s:
        anchor = '<main class="grid"'
        if anchor not in s:
            raise SystemExit('[ABORT] 找不到 <main class="grid" 錨點')
        s = s.replace(anchor, b['html'] + '\n\n' + anchor, 1)

    # 6. 注入 JS（放在最後一個 </script> 之前，即 </body> 前）
    if "getElementById('filter-panel')" not in s:
        idx = s.rfind('</script>')
        if idx == -1:
            s = s.replace('</body>', '<script>\n' + b['js'] + '\n</script>\n</body>', 1)
        else:
            s = s[:idx].rstrip('\n') + '\n' + b['js'] + '\n' + s[idx:]

    return s, cats, years, total, b


def main():
    s = open(TARGET, encoding='utf-8').read()
    s2, cats, years, total, _ = apply_to_html(s)
    open(TARGET, 'w', encoding='utf-8').write(s2)

    ordered = [c for c in CAT_ORDER if c in cats] + \
              [c for c in sorted(cats) if c not in CAT_ORDER]
    print('[OK] %s' % TARGET)
    print('     分類 %d 類：%s' % (len(ordered), '、'.join('%s(%d)' % (c, cats[c]) for c in ordered)))
    print('     作品年份 %d 個：%s–%s' % (len(years), min(years) if years else '-', max(years) if years else '-'))
    print('     卡片總數 %d（篩選面板涵蓋全部，非僅電影）' % total)
    assert total == sum(cats.values()), '分類加總 %d != 卡片 %d' % (sum(cats.values()), total)
    print('     [CHECK] 分類加總 == 卡片總數 ✓')


if __name__ == '__main__':
    main()
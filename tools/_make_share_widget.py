#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
從 macau-weekly.html 抽出「微信分享」元件，產出 share-widget.js。

用法：
    python _make_share_widget.py

輸出：
    assets/share-widget.js   （含 QR 庫 + CSS + HTML + JS，可直接注入任何頁面）

設計要點（對應 build_articles.py 的文章頁）：
  1. 網頁無法直接調用微信分享（沒有 JS API），所以用「二維碼 + 複製連結」。
     手機掃碼 → 在微信裡打開 → 右上角 ··· → 發送給朋友。
  2. 連結自動取當前頁 canonical／網址，不需為每篇硬編碼。
  3. 冪等：注入前先檢查有沒有 share-widget，有就跳過，避免重複插入。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'macau-weekly.html')
OUT = os.path.join(ROOT, 'assets', 'share-widget.js')

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def extract(lines, start, end):
    """取出 1-based 行範圍（含兩端）"""
    return '\n'.join(lines[start - 1:end])


def main():
    if not os.path.exists(SRC):
        print('找不到來源檔：%s' % SRC)
        return 1

    html = io.open(SRC, encoding='utf-8').read()
    lines = html.split('\n')

    # ── 1. QR Code 庫（212 ~ 2511，含 <script> 與 </script>）──
    qr_lib = extract(lines, 212, 2511)
    assert 'QR Code Generator for JavaScript' in qr_lib, 'QR 庫抓取失敗'
    assert qr_lib.strip().endswith('</script>'), 'QR 庫結尾不是 </script>'

    # ── 2. 分享按鈕 CSS（151 ~ 208；209 行是 </style>，不要抓，
    #       否則輸出時會出現兩個 </style>，script 提前閉合 → qrcode is not defined）──
    css = extract(lines, 151, 208)
    assert '.wk-share-fab' in css, 'CSS 抓取失敗'
    assert '</style>' not in css, 'CSS 區塊誤含 </style>'

    # ── 3. HTML（2514 ~ 2527：按鈕 + 遮罩 + 卡片。
    #       邊界很重要：2528 是空行，2529 起是週報自己的 header，
    #       多抓就會把「Macau Weekly Digest」標題帶進每一篇文章頁。──
    btn_html = extract(lines, 2514, 2527)
    assert 'wkShareFab' in btn_html, '按鈕 HTML 抓取失敗'
    assert 'wk-header' not in btn_html, '誤抓週報 header'
    assert 'Macau Weekly' not in btn_html, '誤抓週報標題'

    # ── 4. JS（2613 ~ 2660：分享邏輯）──
    js = extract(lines, 2614, 2660)
    assert 'openShare' in js, 'JS 抓取失敗'

    # ── 組裝 ──
    # 修寫：週報版 shareUrl() 是拼 macau-weekly 路徑，
    #       文章頁版改成「取當前頁網址」。
    js = js.replace(
        """  function shareUrl() {
    var d = window.__wkCurrent;
    if (!d) { try { d = new URLSearchParams(window.location.search).get('p'); } catch (e) {} }
    if (d) return 'https://seanown.org/macau-weekly/' + d + '.html';
    return 'https://seanown.org/macau-weekly.html';
  }""",
        """  function shareUrl() {
    // 優先取 canonical，其次用當前網址（去掉 hash 與 utm 參數）
    var c = document.querySelector('link[rel="canonical"]');
    if (c && c.href) return c.href;
    var u = new URL(window.location.href);
    u.hash = '';
    ['utm_source','utm_medium','utm_campaign','utm_term','utm_content']
      .forEach(function (k) { u.searchParams.delete(k); });
    return u.toString();
  }""")

    # 換掉微信 icon 的 SVG。
    # 來源碼（macau-weekly.html）用壓縮寫法 `-1.1.4-1`，SVG 數字解析器會讀成畸形數字，
    # Chrome 丟 `<path> attribute d: Expected number`，icon 少一隻眼睛。2026-10-09 修。
    # 解法不是加空格（加了仍在後續 token 報錯），而是整段換成「每個數字都完整寫出」的版本。
    import re as _re
    _svg_old = _re.search(r'<svg viewBox="0 0 24 24" aria-hidden="true">.*?</svg>',
                          btn_html, _re.S)
    assert _svg_old, '找不到 SVG 區塊'
    _svg_new = (
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<path fill="#fff" d="M8.7 3 C4.9 3 1.8 5.7 1.8 9 c0 1.9 1.1 3.6 2.8 4.7 L3.7 15.8 l2.3 -1.2 '
        'c0.9 0.3 1.9 0.4 2.7 0.4 h0.6 c-0.2 -0.6 -0.3 -1.2 -0.3 -1.9 c0 -3 2.7 -5.3 6.1 -5.3 h0.5 '
        'C14.7 5.3 12 3 8.7 3 Z M6.2 8.1 c0.6 0 1 0.5 1 1 s-0.4 1 -1 1 s-1 -0.5 -1 -1 s0.4 -1 1 -1 Z '
        'M11.2 8.1 c0.6 0 1 0.5 1 1 s-0.4 1 -1 1 s-1 -0.5 -1 -1 s0.4 -1 1 -1 Z"/>'
        '<path fill="#fff" d="M22.2 13.9 c0 -2.7 -2.5 -4.9 -5.5 -4.9 s-5.5 2.2 -5.5 4.9 s2.5 4.9 5.5 4.9 '
        'c0.7 0 1.3 -0.1 1.9 -0.3 l1.9 1 l-0.5 -1.7 c1.4 -0.9 2.2 -2.2 2.2 -3.9 Z '
        'M14.9 13 c0.5 0 0.8 0.4 0.8 0.8 s-0.3 0.8 -0.8 0.8 s-0.8 -0.4 -0.8 -0.8 S14.4 13 14.9 13 Z '
        'M18.7 13 c0.5 0 0.8 0.4 0.8 0.8 s-0.3 0.8 -0.8 0.8 s-0.8 -0.4 -0.8 -0.8 S18.2 13 18.7 13 Z"/>'
        '</svg>')
    btn_html = btn_html.replace(_svg_old.group(0), _svg_new)
    # 驗證沒有壓縮寫法的畸形數字
    for _d in _re.findall(r' d="([^"]+)"', _svg_new):
        assert not _re.search(r'(?<![\d.])\d*\.\d+\.\d*', _d), 'SVG 仍有畸形數字'

    # 卡片副標改成通用說明
    btn_html = btn_html.replace(
        '<div class="wk-sub">澳門新聞週報 · 掃碼分享</div>',
        '<div class="wk-sub" id="wkShareSub">掃碼分享 · 手機微信開啟</div>')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = []
    # 注意：不要在 <script> / <style> 之外留裸的註解或文字，
    # 瀏覽器會當成文字節點直接渲染在頁面上（2026-10-09 踩過，QR 卡片上方漏出註解）。
    # 註解放進 <script> 內，且每行都是完整的 /* ... */，不可跨行拼接。
    _banner = (
        '/* 微信分享元件｜從 macau-weekly.html 抽出，注入文章頁用。*/\n'
        '/* 產生時間：2026-10-09｜來源：tools/_make_share_widget.py */\n'
        '/* 三段結構：QR 庫(script) + CSS(style) + 按鈕HTML與JS(script)。缺一段按鈕就不動。*/'
    )
    out.append(qr_lib.replace('<script>', '<script>\n' + _banner, 1))
    out.append('')
    out.append('<style>')
    out.append(css)
    out.append('</style>')
    out.append('')
    out.append(btn_html)
    out.append('')
    out.append('<script>')
    out.append(js)
    out.append('</script>')

    text = '\n'.join(out)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(text)

    # ── 出廠前自我檢查（2026-10-09 三次踩坑後加的護欄）──
    problems = []
    # 1. script/style 標籤必須配對
    if text.count('<script>') != text.count('</script>'):
        problems.append('script 標籤不配對：%d 開 / %d 閉'
                        % (text.count('<script>'), text.count('</script>')))
    if text.count('<style>') != text.count('</style>'):
        problems.append('style 標籤不配對：%d 開 / %d 閉'
                        % (text.count('<style>'), text.count('</style>')))
    # 2. script/style 之外不該有裸的 JS（會被當文字渲染出現在頁面上）。
    #    按鈕本身是合法 HTML（<button>…微信分享…</button>），所以只抓「看起來像 JS」的行：
    #    含 ; 或 () 或 var/function 關鍵字，且不是純中文文字。
    stripped = re.sub(r'<script>.*?</script>', '', text, flags=re.S)
    stripped = re.sub(r'<style>.*?</style>', '', stripped, flags=re.S)
    leaked = []
    for l in stripped.split('\n'):
        s = l.strip()
        if not s or s.startswith('<'):
            continue
        # 純文字節點（按鈕文案等）不算；疑似 JS 才算
        if re.search(r'[;{}]|^\s*(var|function|if|for|while|return|document|window)\b', s):
            leaked.append(s)
    if leaked:
        problems.append('script/style 外有疑似裸 JS %d 行：%s'
                        % (len(leaked), leaked[0][:50]))
    # 3. 不可帶入來源頁的其他區塊
    for bad in ('Macau Weekly', '澳門新聞週報', 'wk-header', '期數存檔'):
        if bad in text:
            problems.append('誤帶入來源頁內容：%s' % bad)
    # 4. 每個 script 區塊都要能通過 JS 語法解析
    import subprocess
    for i, blk in enumerate(re.findall(r'<script>(.*?)</script>', text, re.S)):
        tmp = os.path.join(os.path.dirname(OUT), '_syntax_check.js')
        io.open(tmp, 'w', encoding='utf-8', newline='\n').write(blk)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.remove(tmp)
        if r.returncode != 0:
            problems.append('script 區塊 %d 語法錯誤：%s'
                            % (i + 1, r.stderr.strip().split('\n')[1][:60]
                               if len(r.stderr.strip().split('\n')) > 1 else r.stderr[:60]))
    if problems:
        print('❌ 元件自我檢查失敗：')
        for p in problems:
            print('   - ' + p)
        return 1

    print('已產生：%s（%d 行，%.1f KB）'
          % (OUT, len(text.split('\n')), os.path.getsize(OUT) / 1024.0))
    print('自我檢查通過：標籤配對 / 無裸內容 / 無誤帶內容 / JS 語法 OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())

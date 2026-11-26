# -*- coding: utf-8 -*-
"""2026-10-09 導覽列瘦身：聯絡、媒體從全站導覽列下架（軒哥決定：把自己藏深一點）。

- 5 個靜態頁（about/contact/media/services/book）的 <nav class="tnav"> 整塊換成
  關於我／作品／專欄 三項直鏈（原本的「關於我」下拉只剩一項，改直鏈）。
- 清掉手機版「只留 cta」的隱藏規則（.tnav a:not(.cta){display:none} 等），
  讓手機版直接顯示三個連結；nav-drop／nav-mcta 相關規則一併移除。
- 文章頁 112 篇由 build_articles.py 模板負責，不在本腳本範圍。
- 首頁 index.html 導覽結構不同，另行手改。
"""
import io, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 每頁自己的路徑 → 該頁導覽裡對應連結加 aria-current="page"
PAGES = [
    'about/index.html',
    'contact/index.html',
    'media/index.html',
    'services/index.html',
    'book/shou-deng-ren-ying-ji/index.html',
]

NAV_COMMENT = (
    '\n<!-- 2026-10-09 軒哥決定：把自己藏深一點。聯絡、媒體從導覽列下架（頁面本身保留），\n'
    '     導覽列只留 關於我／作品／專欄 三項直鏈；「服務與合作」維持 2026-10-08 的隱藏。\n'
    '     聯絡／媒體入口改收在 /about/ 頁內（摺疊區與頁尾 CTA）。-->'
)


def build_nav(cur):
    a = ' aria-current="page"' if cur == 'about' else ''
    return ('<nav class="tnav" aria-label="網站導覽">%s\n'
            '  <a href="/about/"%s>關於我</a>\n'
            '  <a href="/series/">作品</a>\n'
            '  <a href="/articles/">專欄</a>\n'
            '</nav>' % (NAV_COMMENT, a))


CSS_FIXES = [
    # 手機版「只留 cta」隱藏規則 → 移除，讓三個連結在手機直接顯示
    (r'\s*\.tnav a:not\(\.cta\)\{display:none\}', ''),
    (r'\s*\.tnav \.nav-drop\{display:none\}', ''),
    (r'\s*\.tnav \.nav-mcta\{display:(?:none|block)\}', ''),
    (r'@media\(min-width:861px\)\{\.tnav \.nav-mcta\{display:none\}\}', ''),
]


def main():
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        html = io.open(p, encoding='utf-8').read()
        cur = rel.split('/')[0]
        new_nav = build_nav(cur)
        html2, n = re.subn(r'<nav class="tnav"[^>]*>.*?</nav>',
                           lambda m: new_nav, html, count=1, flags=re.S)
        ncss = 0
        for pat, rep in CSS_FIXES:
            html2, k = re.subn(pat, rep, html2)
            ncss += k
        io.open(p, 'w', encoding='utf-8', newline='\n').write(html2)
        print('%-40s nav=%d css=%d' % (rel, n, ncss))


if __name__ == '__main__':
    main()

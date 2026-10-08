# -*- coding: utf-8 -*-
"""全站文章頁 <style> 花括號平衡檢查。

背景：文章頁的 CSS 變數若某行少一個右括號（或多一對雙花括號），
瀏覽器會把後續所有規則吞進未閉合區塊，導致樣式「整段消失」，
但 HTML 結構與 grep 完全看不出來 —— 只能靠平衡檢查 + computed style 驗證。

本腳本掃描 article/*/index.html、series/*/index.html、movie/*/index.html，
抽出第一個 <style> 區塊，檢查 { } 是否平衡，並定位第一個未閉合規則。
"""
import io, os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check(path):
    """回傳 (花括號是否平衡, 第一個未閉合規則描述, 規則總數)"""
    try:
        s = io.open(path, encoding='utf-8').read()
    except Exception as e:
        return None, 'READ_ERR:%s' % e, 0
    if '<style>' not in s:
        return None, 'NO_STYLE', 0
    a = s.index('<style>')
    b = s.index('</style>', a)
    css = s[a + 7:b]
    if css.count('{') != css.count('}'):
        # 找第一個未閉合規則
        depth = 0
        start = None
        for ln in css.split('\n'):
            if start is None and ln.count('{'):
                start = ln.strip()[:70]
            depth += ln.count('{') - ln.count('}')
            if depth == 0:
                start = None
        return False, 'UNBALANCED {=%d }=%d  首個未閉合: %s' % (
            css.count('{'), css.count('}'), start or '(?)'), 0
    return True, 'OK {=%d }=%d' % (css.count('{'), css.count('}')), 0


def main():
    pats = ['article/*/index.html', 'series/*/index.html',
            'movie/*/index.html', 'articles/index.html', 'index.html']
    files = []
    for p in pats:
        files += glob.glob(os.path.join(ROOT, p))
    files = sorted(set(files))

    bad = []
    ok = 0
    nostyle = 0
    for f in files:
        good, msg, _ = check(f)
        if good is None:
            nostyle += 1
            continue
        if good:
            ok += 1
        else:
            bad.append((os.path.relpath(f, ROOT).replace('\\', '/'), msg))

    print('掃描檔案總數 :', len(files))
    print('平衡通過     :', ok)
    print('無 style 標籤:', nostyle)
    print('不平衡（需修）:', len(bad))
    print()
    if bad:
        print('=== 不平衡清單 ===')
        for name, msg in bad:
            print('  %s' % name)
            print('      %s' % msg)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
"""批量修正 macau-film 輯的篇序版式：把「散場之後」結尾段搬到附錄之後。

鐵律：`---` → 附錄（跟著電影遊澳門《片名》）→ 聲明段 → 一、主場景 → 二、小眾隱藏場景 → **散場之後：〈短語〉**

⚠️ 只處理「結尾段」型散場之後，不處理「正文編號章節」型：
   正文章節（如 `## 五、散場之後`）屬正文結構，搬到附錄後會破壞文章，
   一律跳過並列在 SKIP_AS_SECTION。

用法：
    python tools/_fix_sanchang_order.py          # dry-run，只列印不做改動
    python tools/_fix_sanchang_order.py --apply  # 真正寫入 data/posts.json

冪等：已正確的篇章（散場在附錄之後）會跳過，重複執行不會二次搬移。
"""
import json, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
APPLY = '--apply' in sys.argv

# 正文章節型（如 `## 五、散場之後`）——不可搬
SECTION_RE = re.compile(r'^#{2,4}\s*[一二三四五六七八九十]+、散場之後\s*$', re.M)


def seg_start(body):
    """回傳「結尾段型」散場之後的行首索引；若只有正文章節型則回傳 -1。"""
    for m in re.finditer(r'散場之後', body):
        st = body.rfind('\n', 0, m.start()) + 1
        line = body[st:body.find('\n', st) if body.find('\n', st) > 0 else len(body)]
        if SECTION_RE.match(line):
            continue          # 正文章節，跳過
        return st
    return -1


def main():
    data = json.load(io.open(POSTS, encoding='utf-8'))
    moved, skipped_ok, skipped_sec, problem = [], [], [], []

    for p in data['posts']:
        if p.get('series') != 'macau-film':
            continue
        slug, num = p['slug'], p['num']
        body = p['body']
        ma = re.search(r'跟著電影遊澳門|跟著《', body)
        if not ma:
            skipped_sec.append((num, slug, '無附錄'))
            continue

        i_s = seg_start(body)
        if i_s < 0:
            skipped_sec.append((num, slug, '無結尾段散場（可能只有正文章節型）'))
            continue
        if i_s > ma.start():
            skipped_ok.append((num, slug))       # 已正確
            continue

        # 散場段終點：下一個 `---` 分隔線 或 附錄標題（取較早者）
        j = body.find('\n---', i_s)
        k = ma.start()
        cands = [x for x in (j, k) if x > i_s]
        if not cands:
            problem.append((num, slug, '找不到散場段終點'))
            continue
        end = min(cands)

        seg = body[i_s:end].strip('\n')
        rest = body[end:].lstrip('\n')
        if rest.startswith('---'):
            rest = rest[3:].lstrip('\n')
        new = body[:i_s].rstrip('\n') + '\n\n' + rest.rstrip('\n') + '\n\n' + seg + '\n'

        # 自檢
        a2 = re.search(r'跟著電影遊澳門|跟著《', new)
        assert a2 and new.find('散場之後') > a2.start() > 0, '搬移後順序仍錯：%s' % slug
        assert len(new) == len(body) - (len(body) - len(new))  # 不長度守恆也可，僅防呆
        moved.append((num, slug, len(body), len(new)))
        p['body'] = new

    print('=== dry-run ===' if not APPLY else '=== APPLY ===')
    print('搬移 %d 篇：' % len(moved))
    for num, slug, a, b in sorted(moved, key=lambda x: int(x[0])):
        print('   #%s %-34s %d -> %d chars' % (num, slug, a, b))
    print('已正確跳過 %d 篇' % len(skipped_ok))
    print('不搬（正文章節型／缺件）%d 篇' % len(skipped_sec))
    for num, slug, why in sorted(skipped_sec, key=lambda x: int(x[0])):
        print('   #%s %-34s %s' % (num, slug, why))
    if problem:
        print('異常：', problem)

    if APPLY and moved:
        json.dump(data, io.open(POSTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('\n已寫入 data/posts.json')
    elif not APPLY:
        print('\n（未寫入，加 --apply 才會真正修改）')


if __name__ == '__main__':
    main()

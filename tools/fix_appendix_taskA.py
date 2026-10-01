#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task A: 移除 macau-film 影評 body 中殘留的「跟著電影遊澳門」附錄段落。
僅處理「已建電影資訊頁（有 movieInfo）」的 21 部；附錄遷移早該完成，殘留是 bug。
保留「散場之後」：若散場之後在附錄標記之後，則接回；若在之前，則本就在保留區。

清理邏輯：
- 找到第一個「含『跟著電影遊澳門』的整行」行首作為附錄起點 i_app。
- 若 body 中『散場之後』存在且位置 > i_app：結果 = body[:i_app] + 散場之後之後內容。
- 否則：結果 = body[:i_app]（截掉附錄到結尾）。
- 同時兼容舊式 '## 附錄' / '附錄：跟著電影遊澳門' 標記。

用法：
  python fix_appendix_taskA.py --dry     # 只印處理前後對照，不寫入
  python fix_appendix_taskA.py --apply   # 寫回 posts.json
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, 'data', 'posts.json')

# 21 部有 movieInfo 且 body 含『跟著電影遊澳門』殘留名單
TARGET = [
    'hai-shang-hua-1986','when-i-fall-in-love-with-both','everyday-is-valentine',
    'macau-is-a-city-2019','black-falcon-1967','miracles-1989',
    'love-is-a-many-splendored-thing-1955','flaming-brothers-1987','double-relation-1966',
    'the-fatal-raid-2019','vengeance-2009','poker-king-2009','the-untold-story-1993',
    'chase-at-the-canidrome-1965','riki-oh-1991','madalena-2021','lets-sing-2021',
    'b420-2005','dragon-1993','bicycle-man-1997','o-regresso-1989',
]

def find_appendix_start(body):
    """回傳『行首附錄標頭』起點（含該行行首），找不到回傳 -1。
    只認真正的附錄標頭，不認行內書名/活動提及（如「文化局『跟著電影遊澳門』節目」）。
    """
    pos = 0
    for ln in body.split('\n'):
        s = ln.strip()
        if (re.match(r'^#+\s*跟著電影遊澳門', s)
                or re.match(r'^#*\s*附錄：跟著電影遊澳門', s)
                or re.match(r'^#+\s*附錄', s)):
            return pos
        pos += len(ln) + 1  # +1 為換行符
    return -1

def clean_body(body):
    body = re.sub(r'^\s*<img[^>]*>\s*', '', body)
    i_app = find_appendix_start(body)
    if i_app < 0:
        return body.strip() + '\n' if body.strip() else body
    i_sc = body.find('散場之後')
    if i_sc >= 0 and i_sc > i_app:
        # 散場在附錄後：保留附錄前的正文 + 散場之後內容
        body = body[:i_app].rstrip() + '\n\n' + body[i_sc:]
    else:
        # 散場在附錄前（或無）：截掉附錄起到結尾
        body = body[:i_app].rstrip()
    return body.strip() + '\n' if body.strip() else body

def main():
    dry = '--dry' in sys.argv
    apply = '--apply' in sys.argv
    if not (dry or apply):
        dry = True
    d = json.load(open(PJ, encoding='utf-8'))
    changed = []
    for p in d['posts']:
        if p.get('series') != 'macau-film':
            continue
        if p['slug'] not in TARGET:
            continue
        if not p.get('movieInfo'):
            print('!! 跳過(無movieInfo):', p['slug'])
            continue
        old = p['body']
        new = clean_body(old)
        if new != old:
            changed.append(p['slug'])
            if dry:
                # 確認無殘留場景 GPS 記號與附錄字樣
                residual = '跟著電影遊澳門' in new
                sc_kept = '散場之後' in new if '散場之後' in old else '(原文無)'
                print('—'*60)
                print('SLUG:', p['slug'])
                print('  附錄字樣仍殘留(new):', residual, '| 散場之後保留:', sc_kept)
                print('  舊長度', len(old), '-> 新長度', len(new), '(刪除', len(old)-len(new), ')')
                print('  --- NEW TAIL (最後 500 字) ---')
                print(new[-500:])
    if apply and changed:
        for p in d['posts']:
            if p['slug'] in changed:
                p['body'] = clean_body(p['body'])
        json.dump(d, open(PJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('\n[APPLY] 已寫回', len(changed), '部:', changed)
    else:
        print('\n[DRY] 預計變更', len(changed), '部:', changed)

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""修「散場之後」歸位：散場之後應在影評正文，不該只出現在電影資訊頁。

依 skill「澳門電影影評寫作法」§1：影評頁結構＝正文＋`## 散場之後`，全專輯 100% 有。
§0 鐵則：影評頁正文＝純散文＋散場之後，不放結構化附錄；場景資料進 movieInfo.macauScenes。

判準（全 89 篇普查後定）：
  · foot 為「散場之後」全文（長散文，>300 字）→ 從 macauScenes 移除，並確保正文有該段
  · foot 為取景補充／片後備註（短說明，<300 字）→ 保留在電影資訊頁，屬合理設計
"""
import json
import io
import re

POSTS = 'data/posts.json'
THRESHOLD = 300          # 字數門檻：超過視為「散場之後」全文
LONG_FOOT = {'138', '139'}


def norm(s):
    return re.sub(r'\s+', '', (s or '').replace('#', '').replace('>', ''))


def split_sanchang(body):
    """回傳 (正文, 散場段含標題行) 或 (body, None)。"""
    i = body.find('散場之後')
    if i < 0:
        return body, None
    j = body.rfind('---', 0, i)
    if j < 0:
        return body, None
    return body[:j].rstrip(), body[j:].lstrip()


def main():
    with io.open(POSTS, encoding='utf-8') as f:
        d = json.load(f)
    posts = d['posts']

    report = []
    for p in posts:
        num = str(p.get('num', '')).strip()
        if p.get('series') != 'macau-film':
            continue
        mi = p.get('movieInfo') or {}
        sc = mi.get('macauScenes')
        if not isinstance(sc, dict):
            continue
        foot = sc.get('foot', '') or ''

        # 只處理長篇 foot
        if len(foot) < THRESHOLD:
            continue

        body = p.get('body') or ''
        head, seg = split_sanchang(body)

        if seg is None:
            # 正文沒有「散場之後」→ 從 foot 補回正文
            new_seg = '### 散場之後：\n\n' + foot.strip() + '\n'
            p['body'] = body.rstrip() + '\n\n---\n\n' + new_seg
            act = '從 foot 補回正文'
        else:
            # 正文已有 → 確認內容一致（正文含標題行，foot 不含）
            body_txt = re.sub(r'^###\s*', '', seg.split('\n', 1)[0]).strip()
            act = ('正文已有且內容一致（僅移除 foot）'
                   if norm(seg)[len(norm(body_txt)):][:200] == norm(foot)[:200]
                   or norm(foot)[:200] in norm(seg)
                   else '⚠️ 正文與 foot 內容不一致，需人工確認')

        # 從電影資訊頁移除（散場之後不回電影頁）
        sc['foot'] = ''
        report.append((num, p.get('slug'), len(foot), act))

    with io.open(POSTS, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print('處理', len(report), '篇')
    for num, slug, L, act in report:
        print(f'  num {num} {slug} foot {L} 字 → {act}')

    # 驗證
    print('\n=== 驗證 ===')
    with io.open(POSTS, encoding='utf-8') as f:
        d2 = json.load(f)
    mf = [p for p in d2['posts'] if p.get('series') == 'macau-film']
    miss = [p.get('slug') for p in mf if '散場之後' not in (p.get('body') or '')]
    print('正文缺「散場之後」：', len(miss), miss)
    still = []
    for p in mf:
        sc = (p.get('movieInfo') or {}).get('macauScenes')
        f = (sc.get('foot', '') if isinstance(sc, dict) else '') or ''
        if len(f) >= THRESHOLD:
            still.append((p.get('num'), p.get('slug'), len(f)))
    print('foot 仍 >=300 字：', len(still), still)


if __name__ == '__main__':
    main()
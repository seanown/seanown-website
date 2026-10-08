# -*- coding: utf-8 -*-
# 把「發布版_8篇發言稿」轉成結構化 JSON，供文章頁的「致詞稿附錄」區塊使用。
#
# 輸出 data/speeches.json，結構如下：
#
# {
#   "event": "第三屆長三角·大灣區百位台商走進衢州暨衢台經貿交流活動",
#   "date": "2026 年 6 月",
#   "place": "浙江衢州龍遊",
#   "items": [
#     {
#       "no": 1,
#       "title": "開幕致辭：兩岸融合的大勢，大陸經濟的底氣",
#       "speaker": "仇開明",
#       "role": "海峽兩岸關係協會副會長",
#       "lead": "海峽兩岸關係協會副會長仇開明在活動開幕式上的致辭全文。",
#       "body": "<p>…</p>",
#       "note": "本篇為活動現場錄音整理，致辭中的數字與事例均為致辭人所述。"
#     }
#   ]
# }

# 解析規則（依 8 篇實際格式）：
#   第 1 行  # 【兩岸紀行】標題
#   接著     **演講人：姓名｜職務**
#            **場合：…**
#            **時間：…**
#   --- 分隔
#   **【導語】** …            → lead
#   正文段落 …                → body
#   > **金句**：「…」          → 併入 body（blockquote）
#   **附註**：…                → note
#   **系列**：…                → 丟棄（改由站上做互鏈）
#   **分類建議**：…            → 丟棄


import io
import json
import os
import re

SRC = r'C:\Users\user\DoubaoWork\chats\2026-10-08\new-chat-2\發布版_8篇發言稿_可貼WorkBuddy'
OUT = 'data/speeches.json'

# 依發布順序（即致詞在活動現場的發言順序）
ORDER = [
    '01_仇開明_開幕致辭_發布版.md',
    '02_潘曉輝_歡迎致辭_發布版.md',
    '03_龍遊縣政府領導_文化推介_發布版.md',
    '04_徐莽_致辭_發布版.md',
    '05_周錫瑋_中國的康莊大道_發布版.md',
    '06_趙青沣_超聲波高端機床_發布版.md',
    '07_主辦方代表_營商環境致辭_發布版.md',
    '08_龍遊產業推介_發布版.md',
]


def inline(t):
    """極簡行內：粗體 + 跳脫 HTML"""
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    return t


def parse(path):
    s = io.open(path, encoding='utf-8').read().replace('\r\n', '\n')
    lines = s.split('\n')

    d = {'title': '', 'speaker': '', 'role': '', 'caveat': '', 'lead': '', 'body': '', 'note': ''}

    # 標題：# 【兩岸紀行】xxx → 去掉前綴
    for ln in lines:
        m = re.match(r'^#\s*(?:【兩岸紀行】)?\s*(.+)$', ln.strip())
        if m:
            d['title'] = m.group(1).strip()
            break

    # 演講人：姓名｜職務（職務可能為空或含「（…）」補述）
    m = re.search(r'\*\*演講人[：:]\s*(.+?)\*\*', s)
    if m:
        v = m.group(1).strip()
        if '｜' in v:
            sp, role = v.split('｜', 1)
        else:
            sp, role = v, ''
        sp, role = sp.strip(), role.strip()
        # 括號內的補述（如「（現場錄音未收錄姓名，以職務呈現）」）
        # 拆成獨立欄位，讓 speaker 只保留姓名或本職稱
        mm = re.search(r'^(.*?)（(.+)）\s*$', sp)
        if mm:
            sp = mm.group(1).strip()
            sp_caveat = mm.group(2).strip()
        else:
            sp_caveat = ''
        d['speaker'] = sp
        d['role'] = role
        d['caveat'] = sp_caveat

    # 導語
    m = re.search(r'\*\*【導語】\*\*\s*(.+)', s)
    if m:
        d['lead'] = m.group(1).strip()

    # 附註
    m = re.search(r'\*\*附註\*\*[：:]\s*(.+)', s)
    if m:
        d['note'] = m.group(1).strip()

    # 正文：從【導語】之後，到第一個 **附註** 之前
    start = 0
    mi = re.search(r'\*\*【導語】\*\*', s)
    if mi:
        start = mi.end()
    end = len(s)
    for tag in ('**附註**', '**系列**', '**分類建議**'):
        k = s.find(tag, start)
        if k != -1:
            end = min(end, k)
    seg = s[start:end]

    out, buf = [], []

    def flush():
        if not buf:
            return
        para = ' '.join(x.strip() for x in buf if x.strip())
        buf.clear()
        if not para:
            return
        if para.startswith('>'):
            out.append('<blockquote>%s</blockquote>' % inline(para.lstrip('> ').strip()))
        else:
            out.append('<p>%s</p>' % inline(para))

    for ln in seg.split('\n'):
        t = ln.strip()
        if not t or re.match(r'^-{3,}$', t):
            flush()
            continue
        if t.startswith('>'):
            flush()
            out.append('<blockquote>%s</blockquote>' % inline(t.lstrip('> ').strip()))
            continue
        m = re.match(r'^(#{2,4})\s+(.*)$', t)
        if m:
            flush()
            lv = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lv, inline(m.group(2).strip()), lv))
            continue
        buf.append(t)
    flush()

    d['body'] = '\n'.join(out)
    return d


def main():
    items = []
    for i, fn in enumerate(ORDER, 1):
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print('[SKIP] %s' % fn)
            continue
        d = parse(p)
        d['no'] = i
        # 讓 JSON 保持固定欄位順序
        items.append({
            'no': d['no'], 'title': d['title'], 'speaker': d['speaker'],
            'role': d['role'], 'caveat': d['caveat'], 'lead': d['lead'],
            'body': d['body'], 'note': d['note'],
        })
        print('[%d] %-38s %s｜%s（正文 %d 段）'
              % (i, d['title'][:36], d['speaker'], d['role'][:16],
                 d['body'].count('<p>') + d['body'].count('<blockquote>')))

    data = {
        'event': '第三屆長三角·大灣區百位台商走進衢州暨衢台經貿交流活動',
        'date': '2026 年 6 月',
        'place': '浙江衢州龍遊',
        'items': items,
    }
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(data, ensure_ascii=False, indent=2))
    print()
    print('已輸出 %s，共 %d 篇' % (OUT, len(items)))


if __name__ == '__main__':
    main()

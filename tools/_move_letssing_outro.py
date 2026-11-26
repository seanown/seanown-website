import json, io, re

d = json.load(open('data/posts.json', encoding='utf-8'))
e = [x for x in d['posts'] if x.get('slug') == 'lets-sing-2021'][0]
L = e['body'].splitlines()

# 冪等保護：若散場之後已在附錄之後（出現在附錄標題行之後），則跳過
i_app = next(i for i, l in enumerate(L) if l.startswith('## 跟著電影遊澳門'))
i_out = next((i for i, l in enumerate(L) if '散場之後' in l), None)
assert i_out is not None, '找不到散場之後'
if i_out > i_app:
    print('散場之後已在附錄之後，跳過')
    raise SystemExit

# 1. 取出散場之後整段（標題行 → 下一個 '---' 之前）
end = next(i for i in range(i_out, len(L)) if L[i].strip() == '---')
seg = L[i_out:end]
# 去掉尾部空行
while seg and seg[-1].strip() == '':
    seg.pop()
seg[0] = '### 散場之後：〈還沒散的那一場〉'      # 補 ### 層級（與 105/106 一致）

# 2. 從原位置刪除（含其後多餘空行）
rest = L[:i_out] + L[end:]
while rest and rest[-1].strip() == '':
    rest.pop()
# 原位置前方若留雙空行，收成單空行
while len(rest) >= 2 and rest[-1].strip() == '' and rest[-2].strip() == '':
    rest.pop()

# 3. 接到文末
newL = rest + [''] + ['### ' + seg[0][4:]] + seg[1:]
e['body'] = '\n'.join(newL)

with io.open('data/posts.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# 結構檢查
L2 = e['body'].splitlines()
for i, l in enumerate(L2):
    s = l.strip()
    if s.startswith('### ') or s.startswith('## ') or s.startswith('---') or s.startswith('**證據等級**'):
        print(f'{i:4d}: {s[:60]}')

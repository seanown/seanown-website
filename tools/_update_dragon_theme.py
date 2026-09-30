import json, io, re

d = json.load(open('data/posts.json', encoding='utf-8'))
e = [x for x in d['posts'] if x.get('slug') == 'dragon-1993'][0]

old = e['body']
m = re.search(r'<img src="../../assets/og/dragon-1993-poster\.jpg\?v=[^"]+"[^>]*>', old)
assert m, '找不到原海報 IMG 行'
IMG = m.group(0)

t = open('_draft_李小龍傳.md', encoding='utf-8').read().splitlines()
body = '\n'.join(l for i, l in enumerate(t) if i not in (0, 1, 2, 3)).strip()
assert '{{PREV_COUNT}}' in body, '佔位符不見了'
body = body.replace('{{PREV_COUNT}}', '八十')

e['title'] = '《李小龍傳》觀後感'
e['subtitle'] = '他把中華文化打向世界，那一夜的街道是澳門的｜1993'
e['body'] = IMG + '\n\n' + body

with io.open('data/posts.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('title:', e['title'])
print('subtitle:', e['subtitle'])
print('body 長度:', len(e['body']), '| 佔位殘留:', '{{PREV_COUNT}}' in e['body'])
print('第八十篇:', '第八十篇' in e['body'], '| 中華文化:', '中華文化' in e['body'])

import json, io

d = json.load(open('data/posts.json', encoding='utf-8'))
e = [x for x in d['posts'] if x.get('slug') == 'lets-sing-2021'][0]
b = e['body']
assert '前六十六篇追的是' in b and '前面那六十六篇裡' in b, '預期字串不存在，冪等保護觸發'
b = b.replace('前六十六篇追的是', '前七十篇追的是')
b = b.replace('前面那六十六篇裡', '前面那七十篇裡')
assert b.count('六十六篇') == 1, '應只剩「寫到第六十六篇的時候」一處'
e['body'] = b
with io.open('data/posts.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('posts.json 已改：警告框＋「前面那七十篇裡」；保留力王指稱 1 處')

# 同步草稿源頭
t = open('_draft_熱唱吧.md', encoding='utf-8').read()
t2 = t.replace('前六十六篇追的是', '前七十篇追的是').replace('前面那六十六篇裡', '前面那七十篇裡')
open('_draft_熱唱吧.md', 'w', encoding='utf-8').write(t2)
print('草稿已同步')

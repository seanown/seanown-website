# -*- coding: utf-8 -*-
"""補寫《慾望之城》(city-of-desire-2001) 缺漏的「散場之後：〈偷來的鏡頭〉」內文。
冪等：若 body 已含收束句則跳過。僅改 posts.json 的 body 欄位，num/date/slug 全不動。
"""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')

SLUG = 'city-of-desire-2001'
HEADING = '### 散場之後：〈偷來的鏡頭〉'
SENTINEL = '鏡頭是偷來的，但城市不是。'

OUTRO = (
    '那些被偷拍的女子，後來去了哪裡，沒有人知道。電影沒有交代，現實也不會有人替她們寫續集。'
    '她們留在片中的，只有一雙換衣服的手、一個化妝的側臉、一排等待上場的背影——沒有名，沒有對白，'
    '連一句「我願意被拍」都沒有留下。吳君如說她們神態自若，那是因為她們以為鏡頭後面沒有人。'
    '\n\n'
    '二十多年過去，拿攝影機的人換了一批又一批。今天的手機比當年的機器更小，人人都是導演，人人都在拍別人。'
    '可是「誰有權把誰放進畫面裡」這道題，澳門到現在還沒能完全自己作答。'
    '龐奴當年那句「是時候有一部澳門人自己發聲的作品」，至今仍懸在那裡，像一盞沒人去關的燈。'
    '\n\n'
    '我每次路過新口岸，都會想起二〇〇一年四月一日那個凌晨。警車來過，攝影機來過，然後都走了。'
    '留下來的，是這座城自己——它不說話，不代表它沒有話要說。'
    '只是有些話，要等拿攝影機的那個人，終於是澳門人自己的那一天，才會被聽見。'
    '\n\n'
    + SENTINEL
)

data = json.load(io.open(POSTS, encoding='utf-8'))
posts = data['posts']
target = next((p for p in posts if p.get('slug') == SLUG), None)
assert target is not None, '找不到 slug=%s' % SLUG

body = target['body']
if SENTINEL in body:
    print('已含收束句，跳過（冪等）')
else:
    assert HEADING in body, '找不到 heading：%s' % HEADING
    assert body.rstrip().endswith(HEADING), 'heading 不在 body 結尾，結構異常'
    target['body'] = body.rstrip() + '\n\n' + OUTRO + '\n'
    io.open(POSTS, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('已補寫 散場之後 內文，body 現 %d 字' % len(target['body']))

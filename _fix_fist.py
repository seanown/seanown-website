# -*- coding: utf-8 -*-
import json, io

NEW_TAIL = (
    '\n\n## 散場之後\n\n'
    '二〇二二年十月，澳門影視製作文化協會為了慶祝世界視聽遺產日，在戀愛·電影館放映《精武門》四K修復版。'
    '協會理事長陳麗斯在致辭時說，一九七二年首映的《精武門》是李小龍的經典代表作之一，電影曾在白鴿巢公園門口取景拍攝。'
    '同一場活動還發布了一條叫「英雄追夢憶澳門」的主題電影旅遊路線，把在澳門取景的電影串成旅遊路線，'
    '讓觀眾和旅客用視聽的角度重看這些景點。\n\n'
    '旅遊局長去了，文化局去了，教青局去了。一塊從來沒有真正存在過的上海牌匾，五十三年後變成了一條澳門的旅遊路線。\n\n'
    '這大概是替身城市最好的結局：你替別人活了一次，最後那一次也變成了你自己的。'
)

d = json.load(open('data/posts.json', encoding='utf-8'))
for p in d['posts']:
    if p.get('slug') == 'fist-of-fury-1972':
        mi = p.setdefault('movieInfo', {})
        mi['scenesLabel'] = '跟著電影重走《精武門》'
        b = p.get('body', '')
        i = b.find('散場之後')
        if i == -1:
            b = b.rstrip() + NEW_TAIL
        else:
            j = b.find('\n---\n', 0, i)   # 找到散場之後之前的第一條 --- 分隔線，連同殘留的 ## 一起清掉
            if j == -1:
                j = i
            b = b[:j].rstrip() + NEW_TAIL
        p['body'] = b
        print('fist 更新：scenesLabel=跟著電影重走《精武門》，散場之後已替換為 2022 放映會版本')
        print('body 結尾 60 字：', repr(b[-60:]))
        break

json.dump(d, open('data/posts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

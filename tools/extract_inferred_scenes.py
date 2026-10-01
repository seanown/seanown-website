#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""從 12 部純資料卡影評 body 抽取「跟著電影遊澳門」附錄，轉成 movieInfo.macauScenes（推論補充）。
僅產出 JSON 供檢視，不寫入 posts.json。"""
import json, re
from pathlib import Path

POSTS = json.loads(Path('data/posts.json').read_text(encoding='utf-8'))['posts']
TARGETS = ['dan-shen-nan-nv','macao-enfer-du-jeu-1939','young-and-dangerous-1996',
           'city-of-desire-2001','the-husband-of-a-lady-1965','the-blazing-charmer-1959',
           'eight-murderers-1965','tianchangdijiu-1955','zhuixiongji-1965',
           'jin-zhi-yu-ye-1959','cleopatra-jones-casino-of-gold-1975','yellow-peril-1984']

COORD = r'(\d{2}\.\d+,\s*\d{3}\.\d*)'
DISCLAIMER = ('以下地點整理自影評正文，屬「推論補充」，未經實地查證，僅供讀者參考。'
              '實際是否為本片拍攝點請以現場為準；標 ⚠️ 者為時代地標或同區參照，非確認機位。')

def find_slice(body, slug):
    starts = []
    for kw in ['跟著電影遊澳門', '### 一、主場景', '一、主場景', '主場景（核心打卡）']:
        i = body.find(kw)
        if i >= 0:
            starts.append(i)
    s = min(starts) if starts else -1
    if s < 0:
        m = re.search(COORD, body)
        if m:
            # 取第一個座標之前最近的一個 ## 標題作為起點（dan-shen 用）
            pre = body[:m.start()]
            hi = pre.rfind('\n## ')
            s = hi + 1 if hi >= 0 else max(0, m.start() - 250)
    if s < 0:
        s = 0
    # 結尾：附錄之後的第一個「散場之後」所在行行首（搜尋範圍從 s 之後開始，
    # 避免誤抓附錄之前就已出現的散場之後；若附錄在散場之後之後，則切到全文尾）
    idx = body.find('散場之後', s + 1)
    if idx >= 0:
        nl = body.rfind('\n', 0, idx)
        e = nl + 1 if nl >= 0 else idx
    else:
        e = len(body)
    return body[s:e]

def clean_desc(txt):
    # 移除座標行、證據等級行等，壓成段落；保留現況／現場細節／今天去 等描述
    lines = []
    for ln in txt.split('\n'):
        ln = ln.strip()
        if not ln:
            continue
        # 整行是座標或證據等級 → 丟棄（座標已另以 GPS 晶片呈現）
        if re.match(r'^[-*]?\s*(座標|證據等級)[:：]', ln):
            continue
        # 去掉前導 bullet 符號
        ln = re.sub(r'^[-*]\s*', '', ln)
        # 去掉行首的 ✅ / ⚠️ 標記（已寫進免責聲明語境）
        ln = re.sub(r'^[✅⚠️]\s*', '', ln)
        # 去掉可能殘留的變體選擇子 / 零寬空白
        ln = re.sub(r'^[\uFE0F\u200B\ufeff]*', '', ln).strip()
        lines.append(ln)
    out = ' '.join(lines)
    out = re.sub(r'\s+', ' ', out).strip()
    return out

def parse_star_style(slice_text):
    # 以 ### 分節
    secs = re.split(r'^###\s+(.+)$', slice_text, flags=re.M)
    # secs[0] 是前導（可能含溯源說明），之後成對 (title, body)
    intro_extra = secs[0].strip()
    scenes = []
    for i in range(1, len(secs), 2):
        title = secs[i].strip()
        body_sec = secs[i+1]
        places = []
        # 以 **N. Name** 或 **① Name** 分 place（支援阿拉伯數字與帶圈數字）
        parts = re.split(r'^\*\*\s*([0-9①-⑨]+)[.\、]?\s*(.+?)\*\*', body_sec, flags=re.M)
        # parts[0] 節前導，之後成對 (num, name, block)
        for j in range(1, len(parts), 3):
            num = parts[j]
            raw = parts[j+1]
            name = re.sub(r'[✅⚠️]', '', raw).strip()
            # 移除名稱尾端可能殘留的座標（如「葡京酒店｜22.1897931, 113.544」）
            name = re.sub(r'[\|｜]\s*\d{2}\.\d+,\s*\d{3}\.\d*.*$', '', name).strip()
            block = parts[j+2]
            gps_m = re.search(COORD, block) or re.search(COORD, raw)
            gps = gps_m.group(1).replace(' ', '') if gps_m else ''
            desc = clean_desc(block)
            places.append({'name': name, 'gps': gps,
                           'map': ('https://www.google.com/maps?q=%s' % gps) if gps else '',
                           'desc': desc, 'camera': ''})
        if places:
            scenes.append({'section': title, 'places': places})
    return intro_extra, scenes

def parse_dan_shen(slice_text):
    # 以 ## 分節，每節一個地點
    secs = re.split(r'^##\s+(.+)$', slice_text, flags=re.M)
    scenes = []
    places = []
    for i in range(1, len(secs), 2):
        name = secs[i].strip()
        block = secs[i+1]
        if 'GPS' not in block and not re.search(COORD, block):
            continue
        gps_m = re.search(COORD, block)
        gps = gps_m.group(1).replace(' ', '') if gps_m else ''
        desc = clean_desc(block)
        places.append({'name': name, 'gps': gps,
                       'map': ('https://www.google.com/maps?q=%s' % gps) if gps else '',
                       'desc': desc, 'camera': ''})
    if places:
        scenes.append({'section': '影評正文中的澳門場景', 'places': places})
    return '', scenes

def build(slug):
    p = next(x for x in POSTS if x['slug'] == slug)
    body = p['body']
    slice_text = find_slice(body, slug)
    if slug == 'dan-shen-nan-nv':
        intro_extra, scenes = parse_dan_shen(slice_text)
    else:
        intro_extra, scenes = parse_star_style(slice_text)
    # 若未解析出 places（jin / cleopatra 等無結構附錄），做單一說明 place
    if not scenes:
        if slug == 'jin-zhi-yu-ye-1959':
            # 抽取「新馬路／國際酒店」相關段落
            m = re.search(r'[^。]*新馬路[^。]*。?', body)
            txt = m.group(0).strip() if m else clean_desc(slice_text)
            scenes = [{'section': '影評正文場景說明', 'places': [
                {'name': '新馬路（國際酒店一帶）', 'gps': '', 'map': '',
                 'desc': txt, 'camera': ''}]}]
        elif slug == 'cleopatra-jones-casino-of-gold-1975':
            note = ('本片澳門場景全為香港片廠搭景，澳門境內無實際取景地；下方僅轉錄影評對「澳門想像」的討論，供讀者理解，非可前往的拍攝點。')
            scenes = [{'section': '影評正文場景說明', 'places': [
                {'name': '附註：本片澳門場景為香港片廠搭景', 'gps': '', 'map': '',
                 'desc': note, 'camera': ''}]}]
        else:
            txt = clean_desc(slice_text)
            if len(txt) > 600:
                txt = txt[:600] + '…'
            scenes = [{'section': '影評正文場景說明', 'places': [
                {'name': '附註：本片澳門場景說明', 'gps': '', 'map': '',
                 'desc': txt, 'camera': ''}]}]
    intro = DISCLAIMER
    if intro_extra:
        intro = DISCLAIMER + '\n\n' + clean_desc(intro_extra)
    mi = p.get('movieInfo', {})
    title = mi.get('title', p.get('title', ''))
    label = '跟著電影重走《%s》（推論補充）' % title.strip('《》')
    return {
        'slug': slug,
        'scenesLabel': label,
        'macauScenes': {'intro': intro, 'scenes': scenes, 'foot': ''},
        'n_places': sum(len(s['places']) for s in scenes)
    }

if __name__ == '__main__':
    out = {}
    for slug in TARGETS:
        r = build(slug)
        out[slug] = r
        print('=== %s | places=%d | sections=%d ===' % (slug, r['n_places'], len(r['macauScenes']['scenes'])))
        print('  label:', r['scenesLabel'])
        for s in r['macauScenes']['scenes']:
            print('   ·', s['section'], '->', len(s['places']), 'places')
            for pl in s['places'][:3]:
                print('       -', pl['name'][:24], '| gps=', pl['gps'] or '—')
    Path('tools/inferred_scenes_draft.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n已寫入 tools/inferred_scenes_draft.json')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第八輪（batch8）合併腳本：把 4 個 agent 產出的 patch JSON 合進 data/posts.json，
清理 body（移除開頭內嵌海報、移除 ## 附錄 區塊但保留 散場之後），
修正 china-dolls-1992 的空 scenesLabel / 空 macauScenes 瑕疵（改為純資料卡）。
不跑 build（由主流程另跑，便於先驗證 build 模板修正）。
"""
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "data", "posts.json")
PATCHES = [
    os.path.join(ROOT, "tools", "patch_batch8_a.json"),
    os.path.join(ROOT, "tools", "patch_batch8_b.json"),
    os.path.join(ROOT, "tools", "patch_batch8_c.json"),
    os.path.join(ROOT, "tools", "patch_batch8_d.json"),
]
BATCH_SLUGS = [
    "dan-shen-nan-nv", "skyfall", "jin-zhi-yu-ye-1959", "macao-enfer-du-jeu-1939",
    "city-of-desire-2001", "the-husband-of-a-lady-1965", "forbidden-1953",
    "cleopatra-jones-casino-of-gold-1975", "young-and-dangerous-1996", "yellow-peril-1984",
    "tianchangdijiu-1955", "the-blazing-charmer-1959", "eight-murderers-1965",
    "zhuixiongji-1965", "china-dolls-1992", "macao-2525-2021",
]
# china-dolls 無澳門實景，agent 誤填 空 scenesLabel + 空 macauScenes，強制降為純資料卡
PURE_DATA_FORCE = {"china-dolls-1992"}

def clean_body(body):
    body = re.sub(r'^\s*<img[^>]*>\s*', '', body)
    candidates = []
    for marker in ['## 附錄', '附錄：跟著電影遊澳門']:
        i = body.find(marker)
        if i >= 0:
            candidates.append(i)
    if not candidates:
        return body.strip() + '\n' if body.strip() else body
    i_app = min(candidates)
    i_sc = body.find('散場之後')
    if i_sc >= 0 and i_sc > i_app:
        body = body[:i_app].rstrip() + '\n\n' + body[i_sc:]
    else:
        body = body[:i_app].rstrip()
    return body.strip() + '\n' if body.strip() else body

def sanitize_actors(actors):
    out = []
    for a in (actors or []):
        if isinstance(a, dict):
            name = str(a.get('name', '') or '').strip()
            role = str(a.get('role', '') or '').strip()
            if name:
                out.append({'name': name, 'role': role})
        elif isinstance(a, str) and a.strip():
            out.append({'name': a.strip()})
    return out

def sanitize_movieinfo(mi):
    mi['title'] = str(mi.get('title', '') or '').strip()
    mi['englishName'] = str(mi.get('englishName', '') or '').strip()
    try:
        mi['year'] = int(mi['year'])
    except (ValueError, TypeError):
        mi['year'] = ''
    mi['director'] = str(mi.get('director', '') or '').strip()
    mi['writer'] = str(mi.get('writer', '') or '').strip()
    mi['genre'] = str(mi.get('genre', '') or '').strip()
    mi['synopsis'] = str(mi.get('synopsis', '') or '').strip()
    mi['source'] = str(mi.get('source', '') or '').strip()
    mi['scenesLabel'] = str(mi.get('scenesLabel', '') or '').strip()
    mi['actors'] = sanitize_actors(mi.get('actors'))
    if 'releaseDate' in mi:
        mi['releaseDate'] = str(mi['releaseDate'] or '').strip() or None
    ms = mi.get('macauScenes')
    if not isinstance(ms, dict):
        ms = {}
    scenes = ms.get('scenes')
    if not isinstance(scenes, list):
        scenes = []
    clean_scenes = []
    for sc in scenes:
        if not isinstance(sc, dict):
            continue
        section = str(sc.get('section', '') or '').strip()
        places = []
        for pl in (sc.get('places') or []):
            if not isinstance(pl, dict):
                continue
            name = str(pl.get('name', '') or '').strip()
            gps = str(pl.get('gps', '') or '').strip()
            if not name or not gps:
                continue
            places.append({
                'name': name,
                'gps': gps,
                'map': str(pl.get('map', '') or '').strip() or ('https://www.google.com/maps/search/?api=1&query=' + gps.replace(' ', '')),
                'desc': str(pl.get('desc', '') or '').strip(),
                'camera': str(pl.get('camera', '') or '').strip(),
            })
        if section and places:
            clean_scenes.append({'section': section, 'places': places})
    # 有場景才填充 intro/foot/scenes；無場景保持空 dict，避免 CTA 雙按鈕指向空錨點與空白「澳門場景」標題
    if clean_scenes:
        mi['macauScenes'] = {
            'intro': str(ms.get('intro', '') or '').strip(),
            'foot': str(ms.get('foot', '') or '').strip(),
            'scenes': clean_scenes,
        }
    else:
        mi['macauScenes'] = {}
    return mi

def main():
    data = json.load(open(POSTS, encoding="utf-8"))
    posts = {p["slug"]: p for p in data["posts"]}
    patch_all = {}
    for pf in PATCHES:
        pj = json.load(open(pf, encoding="utf-8"))
        for item in pj:
            patch_all[item["slug"]] = item.get("movieInfo", item)
        print(f"[載入] {pf}: {len(pj)} 部")
    applied = 0
    for slug in BATCH_SLUGS:
        if slug not in patch_all:
            print(f"[跳過] {slug}: patch 無此片"); continue
        p = posts.get(slug)
        if not p:
            print(f"[錯誤] {slug}: posts.json 找不到"); continue
        mi = sanitize_movieinfo(patch_all[slug])
        if slug in PURE_DATA_FORCE:
            # 強制移除場景相關鍵，確保純資料卡（無雙按鈕、無空白「澳門場景」標題）
            mi.pop('scenesLabel', None)
            mi.pop('macauScenes', None)
        p["movieInfo"] = mi
        old_body = p.get("body", "")
        p["body"] = clean_body(old_body)
        applied += 1
        n_scenes = len(mi.get('macauScenes', {}).get('scenes', []))
        n_places = sum(len(s['places']) for s in mi.get('macauScenes', {}).get('scenes', []))
        print(f"[合併] {slug}: scenes={n_scenes} places={n_places} body {len(old_body)}-> {len(p['body'])}")
    json.dump(data, open(POSTS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n[寫入] posts.json 完成，合併 {applied} 部")

if __name__ == "__main__":
    main()

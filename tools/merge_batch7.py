#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第七輪合併腳本：把 3 個 agent 產出的 patch JSON 合進 data/posts.json，
清理 body（移除開頭內嵌海報、移除 ## 附錄 區塊但保留 ### 散場之後），
補齊缺的直/橫海報 PNG（本輪 6 部資源已齊全，預期 no-op），然後跑 build_articles.py。
軒哥授權直上線，不經確認。
"""
import json, re, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "data", "posts.json")
PATCHES = [
    os.path.join(ROOT, "tools", "patch_batch7_a.json"),
    os.path.join(ROOT, "tools", "patch_batch7_b.json"),
    os.path.join(ROOT, "tools", "patch_batch7_c.json"),
]
BATCH_SLUGS = [
    "love-is-a-many-splendored-thing-1955",
    "a-night-in-hong-kong-1961",
    "ghost-returns-at-midnight-1964",
    "double-relation-1966",
    "aspectos-de-macau-1923",
    "o-regresso-1989",
]

def clean_body(body):
    body = re.sub(r'^\s*<img[^>]*>\s*', '', body)
    # 附錄區塊起點候選：標準 '## 附錄' 與 aspectos 變體 '附錄：跟著電影遊澳門'
    candidates = []
    for marker in ['## 附錄', '附錄：跟著電影遊澳門']:
        i = body.find(marker)
        if i >= 0:
            candidates.append(i)
    if not candidates:
        return body.strip() + '\n' if body.strip() else body
    i_app = min(candidates)
    i_sc = body.find('散場之後')  # 放寬：兼容 '### 散場之後' / '## 四、散場之後' / '### 散場之後：…' 等
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
        mi['macauScenes'] = ms
    ms['intro'] = str(ms.get('intro', '') or '').strip()
    ms['foot'] = str(ms.get('foot', '') or '').strip()
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
    ms['scenes'] = clean_scenes
    return mi

def ensure_posters():
    """本輪 6 部海報資源已齊全，預期 no-op；保留通用補齊邏輯以策安全。"""
    try:
        from PIL import Image
    except ImportError:
        return
    og = os.path.join(ROOT, "assets", "og")
    for slug in BATCH_SLUGS:
        src_v = os.path.join(og, slug + "-poster.jpg")
        dst_v = os.path.join(og, slug + "-poster.png")
        src_h = os.path.join(og, slug + "-cover.jpg")
        dst_h = os.path.join(og, slug + "-poster-land.png")
        if os.path.exists(src_v) and not os.path.exists(dst_v):
            Image.open(src_v).convert("RGB").save(dst_v); print(f"  + {slug}-poster.png")
        if os.path.exists(src_h) and not os.path.exists(dst_h):
            Image.open(src_h).convert("RGB").save(dst_h); print(f"  + {slug}-poster-land.png")

def main():
    data = json.load(open(POSTS, encoding="utf-8"))
    posts = {p["slug"]: p for p in data["posts"]}
    patch_all = {}
    for pf in PATCHES:
        if not os.path.exists(pf):
            print(f"[警告] patch 不存在：{pf}"); continue
        pj = json.load(open(pf, encoding="utf-8"))
        patch_all.update(pj)
        print(f"[載入] patch: {len(pj)} 部 -> {list(pj.keys())}")
    applied = 0
    for slug in BATCH_SLUGS:
        if slug not in patch_all:
            print(f"[跳過] {slug}: patch 無此片"); continue
        p = posts.get(slug)
        if not p:
            print(f"[錯誤] {slug}: posts.json 找不到"); continue
        raw = patch_all[slug]
        mi = sanitize_movieinfo(raw.get("movieInfo", raw))
        p["movieInfo"] = mi
        p["body"] = clean_body(p.get("body", ""))
        applied += 1
        n_places = sum(len(s["places"]) for s in mi.get("macauScenes", {}).get("scenes", []))
        print(f"[合併] {slug}: scenes={len(mi.get('macauScenes',{}).get('scenes',[]))} places={n_places} body_len={len(p['body'])}")
    json.dump(data, open(POSTS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n[寫入] posts.json 完成，合併 {applied} 部")
    ensure_posters()
    print("\n[build] 執行 build_articles.py ...")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_articles.py")], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-1500:] if r.stdout else "")
    if r.returncode != 0:
        print("[build 錯誤]", r.stderr[-2000:]); sys.exit(1)
    print("[build] 完成")

if __name__ == "__main__":
    main()

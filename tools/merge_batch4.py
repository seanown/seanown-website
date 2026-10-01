#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第四輪合併腳本：把 4 個 agent 產出的 patch JSON 合進 data/posts.json，
清理 body（移除開頭內嵌海報、移除 ## 附錄 區塊但保留 ### 散場之後），
補齊 isabella/huayang-nianhua 缺的直/橫海報 PNG，然後跑 build_articles.py。

用法：由主 agent 在收齊 4 份 patch 後執行，不經使用者確認（軒哥授權直上線）。
"""
import json, re, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "data", "posts.json")
PATCHES = {
    "A": os.path.join(ROOT, "tools", "patch_batch4_a.json"),
    "B": os.path.join(ROOT, "tools", "patch_batch4_b.json"),
    "C": os.path.join(ROOT, "tools", "patch_batch4_c.json"),
    "D": os.path.join(ROOT, "tools", "patch_batch4_d.json"),
}
BATCH_SLUGS = {
    "A": ["bufeng-zhuiying","isabella","huayang-nianhua","sisterhood-2016","lan-yan-huo-2000"],
    "B": ["hai-shang-hua-1986","when-i-fall-in-love-with-both","indiana-jones-temple-of-doom","vengeance-2009","poker-king-2009"],
    "C": ["the-untold-story-1993","riki-oh-1991","sharp-gun-2001","black-falcon-1967","sentenced-to-hang-1989"],
    "D": ["pedicab-driver-1989","dragon-1993","chase-at-the-canidrome-1965","the-fatal-raid-2019","casino-tycoon-2-1992"],
}

def clean_body(body):
    # 1) 移除開頭內嵌海報 <img>
    body = re.sub(r'^\s*<img[^>]*>\s*', '', body)
    # 2) 移除 ## 附錄 區塊（保留 ### 散場之後 之後的內容）
    i_app = body.find('## 附錄')
    if i_app >= 0:
        i_sc = body.find('### 散場之後')
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
    # 確保必要欄位存在且型別正確
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
    # macauScenes 結構檢查
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
    """isabella / huayang-nianhua 缺直式(poster.png)與橫式(poster-land.png)；
    現有 poster.jpg=1024x1536(直)、cover.jpg=1536x1024(橫)，轉檔補齊。"""
    from PIL import Image
    og = os.path.join(ROOT, "assets", "og")
    for slug in ["isabella", "huayang-nianhua"]:
        src_v = os.path.join(og, slug + "-poster.jpg")
        dst_v = os.path.join(og, slug + "-poster.png")
        src_h = os.path.join(og, slug + "-cover.jpg")
        dst_h = os.path.join(og, slug + "-poster-land.png")
        if os.path.exists(src_v) and not os.path.exists(dst_v):
            Image.open(src_v).convert("RGB").save(dst_v)
            print(f"  + 生成 {slug}-poster.png (直式)")
        if os.path.exists(src_h) and not os.path.exists(dst_h):
            Image.open(src_h).convert("RGB").save(dst_h)
            print(f"  + 生成 {slug}-poster-land.png (橫式)")

def main():
    data = json.load(open(POSTS, encoding="utf-8"))
    posts = {p["slug"]: p for p in data["posts"]}
    patch_all = {}
    for b, pf in PATCHES.items():
        if not os.path.exists(pf):
            print(f"[警告] patch {b} 不存在：{pf}")
            continue
        pj = json.load(open(pf, encoding="utf-8"))
        patch_all.update(pj)
        print(f"[載入] patch {b}: {len(pj)} 部")

    applied = 0
    for b, slugs in BATCH_SLUGS.items():
        for slug in slugs:
            if slug not in patch_all:
                print(f"[跳過] {slug}: patch 無此片")
                continue
            p = posts.get(slug)
            if not p:
                print(f"[錯誤] {slug}: posts.json 找不到")
                continue
            mi = sanitize_movieinfo(patch_all[slug]["movieInfo"])
            p["movieInfo"] = mi
            p["body"] = clean_body(p.get("body", ""))
            applied += 1
            n_scenes = len(mi.get("macauScenes", {}).get("scenes", []))
            n_places = sum(len(s["places"]) for s in mi.get("macauScenes", {}).get("scenes", []))
            print(f"[合併] {slug}: scenes={n_scenes} places={n_places} body_len={len(p['body'])}")

    json.dump(data, open(POSTS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n[寫入] posts.json 完成，合併 {applied} 部")
    ensure_posters()

    print("\n[build] 執行 build_articles.py ...")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_articles.py")],
                       cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-1500:] if r.stdout else "")
    if r.returncode != 0:
        print("[build 錯誤]", r.stderr[-2000:])
        sys.exit(1)
    print("[build] 完成")

if __name__ == "__main__":
    main()

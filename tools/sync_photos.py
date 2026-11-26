#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_photos.py — 把 H 槽桌面「文章照片」資料夾裡的圖，同步到網站靜態結構。

用法（在倉庫根目錄執行）:
  python tools/sync_photos.py            # 正式同步（複製新圖 + 寫入 posts.json）
  python tools/sync_photos.py --dry-run  # 只預覽會改什麼，不動檔案

邏輯:
  - 來源: H:/桌面/文章照片/<編號> <標題>/  下的 jpg/jpeg/png/webp
  - 目標: assets/images/posts/<編號>-<序號>.jpg
  - 對照 data/posts.json 的 num 欄，把新圖路徑補進該篇的 images[] 陣列
  - 內容去重: 用 md5 比對，同一張圖（即使檔名不同/重複放）只會有一份，絕不產生重複照片
  - 冪等: 已存在的圖不會再次複製；只處理來源有、目標沒有的圖
  - HEIC 等瀏覽器不支援的格式會跳過並提示（建議先轉 jpg）
"""
import os
import sys
import json
import glob
import hashlib
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_BASE = "H:/桌面/文章照片"
DEST_DIR = os.path.join(REPO, "assets", "images", "posts")
POSTS_JSON = os.path.join(REPO, "data", "posts.json")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_source_folder(num):
    matches = glob.glob(os.path.join(SRC_BASE, f"{num}*"))
    matches = [m for m in matches if os.path.isdir(m)]
    return matches[0] if matches else None


def existing_state():
    """回傳 (已佔用序號 dict[num]->set, 現有圖片 hash 集合)。"""
    used = {}
    hashes = set()
    if not os.path.isdir(DEST_DIR):
        return used, hashes
    for f in os.listdir(DEST_DIR):
        if f.lower().endswith(IMG_EXTS):
            try:
                num = f.split("-")[0]
                idx = int(f[f.index("-") + 1: f.rfind(".")])
                used.setdefault(num, set()).add(idx)
            except (ValueError, IndexError):
                pass
            try:
                hashes.add(md5_of(os.path.join(DEST_DIR, f)))
            except OSError:
                pass
    return used, hashes


def main():
    dry = "--dry-run" in sys.argv
    if not os.path.isdir(SRC_BASE):
        print(f"[錯誤] 來源資料夾不存在: {SRC_BASE}")
        sys.exit(1)
    os.makedirs(DEST_DIR, exist_ok=True)

    with open(POSTS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    posts = data.get("posts", [])

    used, known_hashes = existing_state()
    copied = 0
    skipped_dup = 0
    updated_posts = 0

    for p in posts:
        num = p.get("num")
        if not num:
            continue
        src = find_source_folder(num)
        if not src:
            continue
        files = sorted(
            f for f in os.listdir(src)
            if f.lower().endswith(IMG_EXTS)
        )
        if not files:
            continue
        images = list(p.get("images") or [])
        next_idx = (max(used.get(num, set())) + 1) if used.get(num) else 1
        for fname in files:
            spath = os.path.join(src, fname)
            try:
                h = md5_of(spath)
            except OSError:
                continue
            if h in known_hashes:
                skipped_dup += 1
                continue
            target_rel = f"assets/images/posts/{num}-{next_idx}.jpg"
            target_abs = os.path.join(REPO, target_rel)
            if dry:
                print(f"[dry-run] 會複製 {num}: {fname} -> {target_rel}")
            else:
                shutil.copy2(spath, target_abs)
                images.append(target_rel)
                known_hashes.add(h)
                print(f"[ok] 複製 {num}: {fname} -> {target_rel}")
            copied += 1
            next_idx += 1
        # 讓 images 陣列順序 = 序號由小到大，九宮格才穩定
        images.sort(
            key=lambda s: int(s.split("/")[-1].split("-")[1].split(".")[0])
            if s.endswith(IMG_EXTS) else 0
        )
        if images != (p.get("images") or []):
            p["images"] = images
            updated_posts += 1

    if not dry:
        with open(POSTS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n完成：新複製 {copied} 張（跳過重複 {skipped_dup} 張），"
              f"更新 {updated_posts} 篇文章的 images。")
        if copied:
            print("提醒：記得 git add -A 並提交（或到後台 Publish）才會上線。")
    else:
        print(f"\n[dry-run] 預計新複製 {copied} 張（會跳過重複 {skipped_dup} 張），"
              f"將更新 {updated_posts} 篇。")


if __name__ == "__main__":
    main()

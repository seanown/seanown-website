# SEAN OWN | 翁振軒 — Personal Website (with CMS)

個人IP官方網站，內建 Decap CMS 後台，可視化編輯文章和媒體報導。

## 網站網址
- 正式網域：https://seanown.com（待綁定）
- 預覽：https://seanown.netlify.app
- 後台：https://seanown.netlify.app/admin

## 技術架構
- 純靜態 HTML / CSS / JavaScript
- **Decap CMS**（原 Netlify CMS）— 可視化內容管理後台
- **Netlify Identity** — 後台登錄驗證
- marked.js — Markdown 渲染
- 響應式設計，中英雙語

## 目錄結構
```
seanown-website/
├── index.html              # 主頁面
├── admin/
│   ├── index.html          # CMS 後台入口
│   └── config.yml          # CMS 配置（定義可編輯字段）
├── data/
│   ├── posts.json          # 文章數據（後台可編輯）
│   └── media.json          # 媒體報導數據（後台可編輯）
├── assets/
│   └── images/
│       ├── avatar-1x1.jpg  # 頭像
│       └── banner-16x9.jpg # 橫幅
└── README.md
```

## 如何使用後台發布文章

### 第一步：開啟 Netlify Identity
1. 登錄 app.netlify.com → 進入你的網站項目
2. 左側菜單 → **Integrations** → 搜索 **Identity** → Enable
3. 在 Identity 設置中 → **Registration** → 選擇 **Invite only**（只允許邀請的人登錄）
4. 點 **Invite users** → 輸入你的郵箱 → 發送邀請
5. 去郵箱點擊邀請鏈接，設置密碼

### 第二步：登錄後台
1. 打開 `你的網址/admin`（如 seanown.netlify.app/admin）
2. 點 **Login with Netlify Identity**
3. 輸入郵箱和密碼

### 第三步：發布文章
1. 左側選擇 **文章管理** → **所有文章**
2. 點 **Add** 添加新文章
3. 填寫：標題、分類（AI前瞻/灣區澳門/商道思辨）、日期、摘要、圖標(emoji)、正文
4. 正文支持 Markdown 格式
5. 點右上角 **Publish** → 網站自動更新

### 第四步：添加媒體報導
1. 左側選擇 **媒體報導** → **所有報導**
2. 點 **Add** 添加新報導
3. 填寫：標題、來源、日期、連結URL
4. 點 **Publish**

## 本地預覽
```bash
python -m http.server 8080
# 打開 http://localhost:8080
```

## 部署到 Netlify
1. 將此倉庫上傳到 GitHub
2. Netlify → Add new site → Import an existing project → 選擇 GitHub 倉庫
3. 構建命令留空，發布目錄留空（根目錄）
4. 部署完成後，按上面步驟開啟 Identity

## 更新網站其他內容
- **頭像/橫幅圖片**：替換 `assets/images/` 裡的文件
- **個人簡介/身份/經歷**：直接編輯 `index.html` 對應區塊
- **文章和媒體報導**：通過 `/admin` 後台可視化編輯

## 聯絡
- Email: seanown@gmail.com
- Website: seanown.com

---
*座右銘：財自道生 · 利緣義取*

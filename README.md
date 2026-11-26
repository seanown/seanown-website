# SEAN OWN | 翁振軒 — Personal Website（with CMS）

個人 IP 官方網站，內建 Decap CMS 後台，可視化編輯文章與媒體報導。

## 網站網址
- 正式網域：https://seanown.org
- 預覽：https://seanown.netlify.app
- 後台：https://seanown.netlify.app/admin

## 技術架構
- 純靜態 HTML / CSS / JavaScript
- **Decap CMS**（原 Netlify CMS）— 可視化內容管理後台
- **Netlify Identity** — 後台登錄驗證
- marked.js — Markdown 渲染
- 響應式設計，繁體中文

## 目錄結構（2026-09 現狀）
```
seanown.org/
├── index.html                 # 主頁（含 hero / 最新文章 / 關於 / 聯絡）
├── articles/index.html        # 文章列表頁（可按專欄篩選 + 搜尋）
├── article/<slug>/index.html  # 單篇文章頁（24 篇，每篇一個資料夾）
├── admin/                    # Decap CMS 後台（index.html + config.yml）
├── admin-simple.html         # 輕量後台入口
├── data/
│   ├── posts.json            # 文章數據（後台可編輯，24 篇）
│   ├── series.json           # （已退役）2026-09-24 起分類單軌化，僅保留空檔案供相容
│   ├── site-text.json        # 全站文案（hero / 身份 / 關於 / 聯絡等）
│   └── media.json            # 媒體報導數據
├── assets/
│   ├── images/               # 文章配圖、頭像、橫幅
│   └── og/                   # 每篇文章的社交分享圖 <slug>.jpg（自動兜底封面）
├── images/media/             # 媒體報導縮圖
├── macau-35-plan-report.html # 澳門三五規劃產業報告專頁
├── macau-budget-article.html # 財政決算分析文
├── macau-budget-ledger.html  # 財政賬本互動數據頁
├── macau-weekly.html         # 澳門週訊
├── reports.html              # 研究報告專區
├── hdi-starfield/            # HDI 數據星圖
├── netlify.toml
├── robots.txt
└── sitemap.xml
```

## 分類體系（2026-09-24 單軌化）
本站**只使用一套分類**：專欄 `category`。原「專題輯（series）」體系與專欄 100% 重疊（每個輯都是某個專欄的子集），已整體退役：導覽入口、輯頁、文章頁輯導航、列表頁輯面板全部移除，`series.json` 僅保留空檔案。

| 專欄 `category` | 篇數 |
|---|---|
| 澳門觀察 | 10 |
| 生活隨筆 | 7 |
| 文化隨筆 | 3 |
| 閱讀筆記 | 2 |
| 行走見聞 | 2 |

`posts.json` 每篇文章欄位：`num`（序號，**保持原始格式勿轉型**，生成器以零填充字串對應 slug）、`title`、`category`、`date`、`location`、`status`、`images`（陣列，缺圖時前台自動用 `assets/og/<slug>.jpg` 兜底）、`body`（Markdown）、`slug`、`no_focus`（可空，設 true 則不進首頁焦點卡）。

## 改完數據必須重跑生成器
`article/*`、`articles/index.html` 全部由 `tools/build_articles.py` 從 `data/*.json` 生成。改 `posts.json` 後務必執行：
```bash
python tools/build_articles.py
```

## 如何使用後台發布文章
1. 開啟 Netlify Identity（app.netlify.com → 網站 → Integrations → Identity → Enable → Invite only → 邀請你的郵箱）。
2. 打開 `你的網址/admin` → Login with Netlify Identity。
3. 左側「文章管理 → 所有文章 → Add」：填標題、分類（專欄）、日期、摘要、圖標、正文（支援 Markdown）。
4. 右上角 Publish → 網站自動更新。

## 本地預覽
```bash
python -m http.server 8080
# 打開 http://localhost:8080
```

## 部署到 Netlify
1. 倉庫上傳 GitHub。
2. Netlify → Add new site → Import an existing project → 選 GitHub 倉庫。
3. 構建命令留空，發布目錄留空（根目錄）。
4. 部署後開啟 Identity（見上）。

## 更新網站其他內容
- **頭像 / 橫幅**：替換 `assets/images/` 的檔案。
- **全站文案（關於 / 身份 / 聯絡等）**：編輯 `data/site-text.json`。
- **文章與媒體報導**：通過 `/admin` 後台，或編輯 `data/posts.json`、`data/media.json`。

## 聯絡
- Email: seanown@gmail.com
- Website: seanown.org

---
*座右銘：財自道生 · 利緣義取*

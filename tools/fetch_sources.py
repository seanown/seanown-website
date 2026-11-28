#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_sources.py — 澳門週報多來源新聞抓取器（零依賴，只用標準庫）

抓取來源（2026-09-28 驗證可用）：
  1. 正報      : 靜態 HTML  — https://www.chengpou.com.mo/news.html
  2. 濠江日報  : JSON API  — https://hkdaily-api.bpprojects.com/v1/section_news/headline
  3. 旅遊局    : JSON API  — https://www.macaotourism.gov.mo/api/enf/whatson?lang=zh-hant
  4. DSEC 統計局: 靜態 HTML — https://www.dsec.gov.mo/zh-MO/Statistic/News（Playwright 渲染）
  5. 力報 Exmoo: 靜態 HTML — https://www.exmoo.com/ 首頁 article/<id>.html（2026-09-28 驗證可用）
  6. 澳門日報  : 圖片型電子報 — https://www.macaodaily.com/（每日下載整版圖，AI 讀圖抽標題）

備註：
  - 澳門日報為「圖片型電子報」：詳情頁無 <p> 正文、版面用 <area> 熱點圖，
    每版一整張 JPEG（/page/<n>/<YYYY-MM>/<DD>/<SEC>/<id>.jpg），全站統一 398×584，
    無文字層、無高清版本（_big/_l/_h 皆 404）、無 PDF。→ 純 HTML/OCR 內文不可行；
    可行的是「下載整版圖 → 由多模態 AI 讀圖抽各版標題」（大標題可讀，內文因解析度不足不可讀）。
    本抓取器每日下載前 N 版（預設 2：A01 要聞 + A02）整版圖，並記錄當日全部版次數量。
  - 週範圍語意：--week <出報日(週一)> 表示「該週一出報」，統計的是「剛結束的那一週」，
    故抓取視窗 = 出報日-7天 ~ 出報日-1天（上週一至週日），與 SKILL「統計週 = 上週一至週日」一致。

產出：
  tools/weekly-content/<出報日>.sources.json
  {
    "generated_at": <ISO>,
    "week_range": {"start","end","label"},
    "sources": { <來源名>: {"status","count","note","items":[...]} },
    "all_items": [ 扁平化、依日期倒序，供週報直接引用 ]
  }

  單筆 item schema:
    { "source","title","url","date"(YYYY-MM-DD|null),"summary"(null|str),
      "category"(null|str),"extra":{...} }

用法：
  python fetch_sources.py                      # 預設抓「上週一~週日」
  python fetch_sources.py --week 2026-09-28    # 指定出報日（週一），統計該週
  python fetch_sources.py --days 7             # 抓最近 N 天（忽略週邊界）
  python fetch_sources.py --out myfile.json    # 自訂輸出檔
"""

import os
import re
import sys
import json

# ---------- 自我修復：確保 DSEC 抓取使用具 Playwright 的 venv Python ----------
# WorkBuddy 應用更新會重建 vendor Python 的 site-packages，導致預設 python 失去
# playwright，使 DSEC（JS 動態載入）抓取恆為 0 筆。此處偵測：若當前解譯器無
# playwright，且 venv Python（已裝 playwright + chromium）存在，則自動以 venv 重新
# 執行本腳本，避免每次更新後都要手動改自動化作業命令。
_VENV_PYTHON = r"C:\Users\user\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

def _ensure_playwright_interpreter():
    try:
        import playwright  # noqa: F401
        return
    except Exception:
        pass
    venv = _VENV_PYTHON
    cur = (sys.executable or "").replace("\\", "/").lower()
    if os.path.exists(venv) and cur != venv.replace("\\", "/").lower():
        try:
            os.execv(venv, [venv] + sys.argv)
        except Exception:
            pass  # 若重新執行失敗，仍讓原流程繼續（DSEC 會優雅降級為 partial）

_ensure_playwright_interpreter()

import argparse
import datetime
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# ---------- 基礎工具 ----------

def fetch(url, accept=None, timeout=20):
    """回傳 (text, http_code)。失敗回 ('', 0)。"""
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # 嘗試以 utf-8 解碼，失敗用 errors=ignore
            return raw.decode("utf-8", errors="ignore"), resp.getcode()
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        return body, e.code
    except Exception as e:
        return "", 0

def clean(txt):
    if not txt:
        return ""
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"&[a-z]+;", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def norm_date(s):
    """盡量把各種日期格式轉成 YYYY-MM-DD；失敗回 None。"""
    if not s:
        return None
    s = s.strip()
    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{1,2})月(\d{1,2})日", s)
    if m:
        y = datetime.date.today().year
        return f"{y}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None

def in_range(date_str, start, end):
    if not date_str:
        return True  # 無日期不過濾
    try:
        d = datetime.date.fromisoformat(date_str)
        return start <= d <= end
    except Exception:
        return True


def _playwright_html(url, wait="networkidle", extra_wait=2500):
    """用 Playwright 無頭渲染取得整頁 HTML；不可用（未安裝/渲染失敗）回 None。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox"])
            pg = b.new_page()
            pg.goto(url, wait_until=wait, timeout=30000)
            pg.wait_for_timeout(extra_wait)
            h = pg.content()
            b.close()
            return h
    except Exception:
        return None

# ---------- 各來源抓取 ----------

def fetch_zhengpao(week_start, week_end):
    """正報：列表取連結+標題，再抓前 N 筆詳情取日期+摘要。"""
    items = []
    note = ""
    base = "https://www.chengpou.com.mo"
    text, code = fetch(base + "/news.html")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"列表頁 HTTP {code}", "items": []}
    links = re.findall(r'<a[^>]*href="(/dailynews/\d+\.html)"[^>]*>(.*?)</a>', text, re.S)
    seen, top = set(), []
    for href, atxt in links:
        if href in seen:
            continue
        seen.add(href)
        title = clean(atxt)
        if len(title) < 4:
            continue
        top.append((base + href, title))
        if len(top) >= 14:
            break
    # 抓詳情取日期 + 摘要
    for url, title in top:
        date, summary = None, None
        dtext, dcode = fetch(url)
        if dtext:
            # 日期：優先取頁面實際發佈日期欄位（class=daily-news-date，格式 YYYY-MM-DD），
            # 避免內文提及的未來日期（如「11月14日開放報名」）被誤當發佈日。
            dm = re.search(r'class="daily-news-date"[^>]*>(\d{4}-\d{2}-\d{2})<', dtext)
            if dm:
                date = dm.group(1)
            else:
                date = norm_date(
                    re.search(r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日)", dtext).group(1)
                ) if re.search(r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日)", dtext) else None
            # 摘要：第一個較長的 <p> 文字
            paras = re.findall(r"<p[^>]*>(.*?)</p>", dtext, re.S)
            for p in paras:
                c = clean(p)
                if len(c) > 25:
                    summary = c[:160]
                    break
        items.append({
            "source": "正報", "title": title, "url": url,
            "date": date, "summary": summary, "category": None, "extra": {}
        })
    cnt = len(items)
    note = f"列表 {len(top)} 則，詳情抓取 {cnt} 則"
    return {"status": "ok", "count": cnt, "note": note, "items": items}


def fetch_houkong(week_start, week_end):
    """濠江日報：JSON API 取列表，詳情正文改用 instantNews 頁面。

    🔴 2026-11-29：原詳情網址 hkdaily-api.bpprojects.com/v1/section_news/{id}/html
    回傳的內文與標題錯位（實測 5 則全中，如「馬青驊奪魁」配上 2022 疫情社論），
    改為 www.houkongdailynews.com/instantNews/{id} 後正文與標題正確對應。
    API 仍用於取 headline／欄目列表，只替換詳情連結生成。
    """
    items = []
    base = "https://hkdaily-api.bpprojects.com"
    detail_url = lambda aid: f"https://www.houkongdailynews.com/instantNews/{aid}"
    # 1) headline
    text, code = fetch(base + "/v1/section_news/headline", accept="application/json")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"headline API HTTP {code}", "items": []}
    try:
        data = json.loads(text).get("data", [])
    except Exception:
        return {"status": "error", "count": 0, "note": "JSON 解析失敗", "items": []}
    for it in data:
        items.append({
            "source": "濠江日報",
            "title": it.get("title", ""),
            "url": detail_url(it.get("id")),
            "date": norm_date(it.get("published_at", "")[:10]),
            "summary": clean(it.get("subtitle", "")) or None,
            "category": None,
            "extra": {"id": it.get("id"), "views": it.get("views")}
        })
    # 2) 補抓「澳門新聞」欄目（categories 中標題含 澳門 者）
    ctext, _ = fetch(base + "/v1/section_news/categories", accept="application/json")
    try:
        cats = json.loads(ctext).get("data", []) if ctext else []
    except Exception:
        cats = []
    macau_ids = [c.get("id") for c in cats if "澳門" in (c.get("title", "") or "")][:2]
    for sid in macau_ids:
        stext, _ = fetch(f"{base}/v1/section_news?section_id={sid}", accept="application/json")
        try:
            sdata = json.loads(stext).get("data", []) if stext else []
        except Exception:
            sdata = []
        have = {i["extra"].get("id") for i in items}
        for it in sdata:
            if it.get("id") in have:
                continue
            items.append({
                "source": "濠江日報",
                "title": it.get("title", ""),
                "url": detail_url(it.get("id")),
                "date": norm_date(it.get("published_at", "")[:10]),
                "summary": clean(it.get("subtitle", "")) or None,
                "category": None,
                "extra": {"id": it.get("id"), "views": it.get("views")}
            })
    # 3) 補摘要：前 8 則若無 summary，抓詳情頁取首段 <p>
    for it in items[:8]:
        if it.get("summary"):
            continue
        dtext, _ = fetch(it["url"])
        if dtext:
            paras = re.findall(r"<p[^>]*>(.*?)</p>", dtext, re.S)
            for p in paras:
                c = clean(p)
                if len(c) > 25:
                    it["summary"] = c[:160]
                    break
    return {"status": "ok", "count": len(items), "note": f"headline + 澳門欄目共 {len(items)} 則", "items": items}


def fetch_tourism(week_start, week_end):
    """旅遊局：JSON API /api/enf/whatson?lang=zh-hant。"""
    items = []
    url = "https://www.macaotourism.gov.mo/api/enf/whatson?lang=zh-hant"
    text, code = fetch(url, accept="application/json")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"whatson API HTTP {code}", "items": []}
    try:
        data = json.loads(text)
        results = data.get("results", [])
    except Exception:
        return {"status": "error", "count": 0, "note": "JSON 解析失敗", "items": []}
    # 篩選本週有活動的（eventDateRange 與週範圍相交）
    def overlaps(ev):
        rng = ev.get("eventDateRange") or []
        for pair in rng:
            try:
                d0 = datetime.date.fromisoformat(pair[0]); d1 = datetime.date.fromisoformat(pair[1])
            except Exception:
                continue
            if d0 <= week_end and d1 >= week_start:
                return True
        return False
    picked = [r for r in results if overlaps(r)]
    if len(picked) < 8:  # 本週活動太少則退回前 15 筆
        picked = results[:15]
    for it in picked:
        locs = [l.get("name") for l in it.get("location", []) if isinstance(l, dict)]
        items.append({
            "source": "旅遊局",
            "title": it.get("name", ""),
            "url": "https://www.macaotourism.gov.mo/zh-hant/events/whatson",
            "date": None,
            "summary": clean(it.get("shortDesc", ""))[:160] or None,
            "category": "活動/盛事",
            "extra": {
                "showDate": it.get("showDate"),
                "eventDate": it.get("eventDate"),
                "location": locs,
                "types": [t.get("name") for t in it.get("types", []) if isinstance(t, dict)]
            }
        })
    return {"status": "ok", "count": len(items),
            "note": f"whatson 共 {len(results)} 筆，選取 {len(items)} 筆（本週活動優先）", "items": items}


def fetch_dsec(week_start, week_end):
    """DSEC：新聞列表為 JS 動態載入，靜態 HTML 抓不到。
    改用 Playwright 無頭渲染，抽取 #statistic-news-list 下每則
    (.db-statistic-news-cell__title / __content__inner / __period)。
    Playwright 不可用時優雅降級為 partial。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"status": "partial", "count": 0,
                "note": "未安裝 playwright，DSEC 需無頭瀏覽器渲染（pip install playwright && playwright install chromium）",
                "items": []}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox"])
            pg = b.new_page()
            pg.goto("https://www.dsec.gov.mo/zh-MO/Statistic/News",
                    wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(2500)
            nodes = pg.eval_on_selector_all(
                "a.db-statistic-news-cell-link",
                """els => els.map(e => ({
                    title: (e.querySelector('.db-statistic-news-cell__title')||{}).innerText || '',
                    summary: (e.querySelector('.statistic-news-cell__content__inner')||{}).innerText || '',
                    period: (e.querySelector('.db-statistic-news-cell__period')||{}).innerText || ''
                }))"""
            )
            b.close()
    except Exception as e:
        return {"status": "partial", "count": 0, "note": f"Playwright 渲染失敗：{e}", "items": []}

    items = []
    for n in nodes:
        title = clean(n.get("title"))
        summary = clean(n.get("summary"))
        date = norm_date((n.get("period") or "").replace("/", "-"))
        if len(title) < 4:
            continue
        items.append({
            "source": "DSEC",
            "title": title,
            "url": "https://www.dsec.gov.mo/zh-MO/Statistic/News",
            "date": date,
            "summary": (summary[:200] if summary else None),
            "category": "統計發布",
            "extra": {}
        })
    if not items:
        return {"status": "partial", "count": 0,
                "note": "Playwright 渲染後仍無新聞節點（選擇器可能已變動）", "items": []}
    return {"status": "ok", "count": len(items),
            "note": f"Playwright 渲染取得新聞 {len(items)} 筆", "items": items}


def _exmoo_detail(url):
    """抓取單篇力報文章：H1 標題 + 日期(DD/MM/YYYY) + 摘要(og:description)。失敗回 None。"""
    dtext, dcode = fetch(url)
    if not dtext:
        return None
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", dtext, re.S)
    title = clean(h1[0]) if h1 else None
    if not title or len(title) < 4:
        return None
    # 日期：class 含 date 的元素，格式 DD/MM/YYYY
    date = None
    dm = re.search(r'class="[^"]*date[^"]*"[^>]*>(\d{2})/(\d{2})/(\d{4})<', dtext)
    if dm:
        date = f"{int(dm.group(3)):04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
    else:
        ymd = re.search(r"(20\d{2}-\d{2}-\d{2})", dtext)
        date = ymd.group(1) if ymd else None
    # 摘要：og:description
    og = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', dtext)
    if not og:
        og = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', dtext)
    summary = None
    if og:
        s = og.group(1)
        s = s.replace("&ldquo;", "「").replace("&rdquo;", "」").replace("&hellip;", "…")
        s = re.sub(r"&[a-z]+;", " ", s).strip()
        summary = s[:200] if s else None
    return {"source": "力報", "title": title, "url": url, "date": date,
            "summary": summary, "category": None, "extra": {}}


def fetch_exmoo(week_start, week_end):
    """力報 Exmoo：改走日期歸檔 API，逐日取得統計週內稿件（解決「只抓首頁→全是當日」）。

    路徑：/get/exmoo/date?date=YYYY-MM-DD → {"status":1,"id":N} → /read/{id}
          （/read/{id} 需 Playwright 渲染，用 domcontentloaded + 3500ms，
           勿用 networkidle 會 timeout 30s）→ 抽取 /article/<id>.html 連結逐篇取詳情。
    退化：若歸檔 API 整週完全無稿，退回首頁抓取保底（首頁皆當日，視窗過濾後多半為 0）。
    """
    base = "https://www.exmoo.com"
    items, seen = [], set()
    d = week_start
    while d <= week_end:
        day = d.isoformat()
        jt, _ = fetch(f"{base}/get/exmoo/date?date={day}", accept="application/json")
        issue_id = None
        try:
            obj = json.loads(jt)
            if obj.get("status") == 1 and obj.get("id"):
                issue_id = obj["id"]
        except Exception:
            pass
        if issue_id:
            rhtml = _playwright_html(f"{base}/read/{issue_id}", wait="domcontentloaded", extra_wait=3500)
            if rhtml:
                for href in re.findall(r'href="(https?://www\.exmoo\.com/article/\d+\.html)"', rhtml):
                    if href in seen:
                        continue
                    seen.add(href)
                    it = _exmoo_detail(href)
                    if it:
                        items.append(it)
        d += datetime.timedelta(days=1)
    if not items:
        # 退化：首頁抓取（皆當日，視窗過濾後多半為 0，僅保底）
        text, code = fetch(base + "/")
        if code == 200 and text:
            for href in re.findall(r'href="(https?://www\.exmoo\.com/article/\d+\.html)"', text):
                if href in seen:
                    continue
                seen.add(href)
                if len(seen) > 16:
                    break
                it = _exmoo_detail(href)
                if it:
                    items.append(it)
    cnt = len(items)
    note = (f"歸檔 API 逐日抓取 {cnt} 則（視窗 {week_start}~{week_end}）"
            if items else "歸檔無稿，退回首頁")
    return {"status": "ok" if cnt else "error", "count": cnt, "note": note, "items": items}


def fetch_bytes(url, timeout=30):
    """下載二進位（圖片）。回 (bytes, http_code)。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.getcode()
    except urllib.error.HTTPError as e:
        return b"", e.code
    except Exception:
        return b"", 0


def fetch_macaodaily(week_start, week_end, pages_per_day=3, img_root=None):
    """澳門日報：新版面單頁取全報標題＋逐篇抓正文（2026-11-29 重寫）。

    🔴 根因：舊路径 /html/YYYY-MM/DD/node_N.htm 已 404（實測），
       導致本來源長期 status=error、0 則——澳門第一大報卻一期都沒收進來。
       新路径 /column/YYYYMM/{DD}/colA01.html **單頁即含當日全報各版標題**
       （macao-toc-item > h3 版名 + li>a 標題，連結指向 /content/YYYYMM/DD/c{id}.html），
       詳情頁有 <h1> 標題與 <p> 正文，文字層完整可讀。

    策略：逐日抓 colA01 → 解析全部 <li><a> 標題＋連結 → 逐篇抓詳情首段作 summary。
    每天標題數不限；只對前 max_detail 篇抓正文以控制請求量（其餘 summary 留空但標題保留）。
    """
    base = "https://www.macaodaily.com"
    items = []
    days_ok = 0
    details_ok = 0
    MAX_DETAIL_PER_DAY = 12  # 控制請求量：每日只抓前 12 篇正文，其餘保留標題
    d = week_start
    while d <= week_end:
        ym = f"{d:%Y%m}"
        dd = f"{d:%d}"
        day = d.isoformat()
        toc, code = fetch(f"{base}/column/{ym}/{dd}/colA01.html")
        if not toc or code != 200:
            d += datetime.timedelta(days=1)
            continue
        days_ok += 1
        # macao-toc-item > h3 版名；li>a href=../../../content/YYYYMM/DD/c{id}.html
        blocks = re.findall(r'<div class="macao-toc-item".*?</div>', toc, re.S)
        day_items = []
        for blk in blocks:
            hm = re.search(r"<h3>(.*?)</h3>", blk, re.S)
            page_name = clean(hm.group(1)) if hm else ""
            for href, aid, title in re.findall(
                    r'<a href="([^"]*content/[^"]*?c(\d+)\.html)"[^>]*>(.*?)</a>', blk, re.S):
                title = clean(title)
                if not title or len(title) < 4:
                    continue
                # 直接用固定路径（新版面的絕對路徑）；href 僅用於解析 id
                url = base + "/content/" + ym + "/" + dd + "/c" + aid + ".html"
                day_items.append({
                    "source": "澳門日報",
                    "title": title,
                    "url": url,
                    "date": day,
                    "summary": None,
                    "category": page_name or None,
                    "extra": {"sec": page_name, "aid": aid},
                })
        # 去重（同一 id 只留一次）
        uniq = {}
        for it in day_items:
            uniq.setdefault(it["extra"]["aid"], it)
        day_items = list(uniq.values())
        # 逐篇抓正文首段（前 MAX_DETAIL_PER_DAY 篇）
        for it in day_items[:MAX_DETAIL_PER_DAY]:
            dtext, _ = fetch(it["url"])
            if not dtext:
                continue
            paras = re.findall(r"<p[^>]*>(.*?)</p>", dtext, re.S)
            for p in paras:
                c = clean(p)
                if len(c) > 25 and "掃一掃" not in c and "微信" not in c:
                    it["summary"] = c[:180]
                    details_ok += 1
                    break
        items.extend(day_items)
        d += datetime.timedelta(days=1)
    note = (f"新版面單頁取標題：{days_ok} 天，共 {len(items)} 則標題、"
            f"{details_ok} 則抓到正文首段（每日最多 {MAX_DETAIL_PER_DAY} 篇）；"
            "路徑 /column/YYYYMM/DD/colA01.html，舊 /html/.../node_N.htm 已 404")
    return {"status": "ok" if items else "error", "count": len(items), "note": note, "items": items}


# ---------- 主流程 ----------

def compute_week(issue_monday=None, days=None):
    """回傳「抓取視窗」(start, end)。

    - --days N：最近 N 天（end=今天）。
    - --week <出報日(週一)>：該週一出報，統計剛結束的那週 → 視窗 = 出報日-7 ~ 出報日-1（上週一至週日）。
    - 預設（無參數）：上週一至週日（同 SKILL 統計週定義）。
    """
    today = datetime.date.today()
    if days:
        end = today
        start = today - datetime.timedelta(days=days - 1)
        return start, end
    if issue_monday:
        mon = datetime.date.fromisoformat(issue_monday)
    else:
        # 最近一個週一（今天若為週一即今天）
        mon = today - datetime.timedelta(days=today.weekday())
        mon = mon - datetime.timedelta(days=7)  # 上週一
    # 出報週一 → 剛結束的那週
    end = mon - datetime.timedelta(days=1)        # 週日
    start = end - datetime.timedelta(days=6)       # 週一
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="出報日(週一) YYYY-MM-DD")
    ap.add_argument("--days", type=int, help="最近 N 天")
    ap.add_argument("--out", help="輸出 JSON 路徑")
    ap.add_argument("--md-pages", type=int, default=3,
                    help="澳門日報每日下載前 N 版整版圖（預設 2：A01+A02；0=只記錄版次不下載）")
    args = ap.parse_args()

    start, end = compute_week(args.week, args.days)
    label = f"{start.strftime('%Y.%m.%d')} — {end.strftime('%Y.%m.%d')}"

    print(f"▶ 抓取保守範圍：{label}")

    here = os.path.dirname(os.path.abspath(__file__))
    wc = os.path.join(here, "weekly-content")

    # 先決定出報日（檔名以出報日＝週一 命名），以便放置澳門日報圖片
    if args.out:
        out_path = args.out
        issue = os.path.splitext(os.path.basename(args.out))[0]
    else:
        if args.week:
            issue = args.week
        else:
            # 出報日 = 抓取視窗週日 + 1 天（即本週一）
            issue = (end + datetime.timedelta(days=1)).isoformat()
        os.makedirs(wc, exist_ok=True)
        out_path = os.path.join(wc, f"{issue}.sources.json")

    # 澳門日報整版圖存放目錄：weekly-content/<出報日>/macaodaily/<日期>/<SEC>.jpg
    md_img_root = os.path.join(wc, issue, "macaodaily")

    sources = {
        "正報": fetch_zhengpao(start, end),
        "濠江日報": fetch_houkong(start, end),
        "旅遊局": fetch_tourism(start, end),
        "DSEC": fetch_dsec(start, end),
        "力報": fetch_exmoo(start, end),
        "澳門日報": fetch_macaodaily(start, end, pages_per_day=args.md_pages, img_root=md_img_root),
    }

    # 扁平化 + 依日期倒序（無日期排後）
    flat = []
    for name, s in sources.items():
        flat.extend(s["items"])
    # 日期視窗過濾：移除視窗外舊統計（如 DSEC 數月前稿件）與當日新聞
    # （如力報/濠江/正報首頁皆當日，不屬本統計週），避免髒資料混入週報。
    # 旅遊局活動無日期 → in_range 回 True（豁免）。
    before = len(flat)
    flat = [x for x in flat if in_range(x.get("date"), start, end)]
    dropped = before - len(flat)
    def sortkey(x):
        return (x.get("date") or "0000-00-00", x["source"])
    flat.sort(key=sortkey, reverse=True)

    out = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "week_range": {"start": start.isoformat(), "end": end.isoformat(), "label": label},
        "sources": sources,
        "all_items": flat,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 終端摘要
    print("\n=== 抓取結果 ===")
    for name, s in sources.items():
        flag = {"ok": "✅", "partial": "⚠️", "error": "❌"}.get(s["status"], "·")
        print(f"  {flag} {name}: {s['count']} 筆 — {s['note']}")
    print(f"\n總計 {len(flat)} 筆（視窗過濾移除 {dropped} 筆視窗外）→ 已寫入 {out_path}")


if __name__ == "__main__":
    main()

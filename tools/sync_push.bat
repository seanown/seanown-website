@echo off
REM 一鍵上線（備援）：飛書同步 → 重建 → commit → push。
REM 主要是在飛書內「一鍵發布」按鈕之外的備用方式。
cd /d "%~dp0.."
python tools\sync_from_feishu.py --build --push

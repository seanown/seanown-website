@echo off
REM 每日排程用：飛書同步 → 重建文章頁 → git commit（不 push）
REM 由 Windows 工作排程器每日定時呼叫此檔。
cd /d "%~dp0.."
python tools\sync_from_feishu.py --build --commit-only
if errorlevel 1 (
  echo [sync_daily] 同步失敗，請檢查 SYNC_REPORT.txt 與飛書表格。
  exit /b 1
)
echo [sync_daily] 完成（已 commit，尚未 push，等你確認）。

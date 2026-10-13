import subprocess, json, os, sys

SKILL_DIR = "C:/Users/user/.workbuddy/plugins/cache/workbuddy-builtin/tencent-pptx/5.7.7-wb.40774747.g2e8619da.had9031c93ded/skills/tencent-pptx"
FILE_ID = "sid_mv6ewkbr_yal5mbrp"
OUT = "C:/Users/user/WorkBuddy/Seanown.org/miaa/_ppt_dump.json"

def call(tool, **kwargs):
    cmd = ["python3", f"{SKILL_DIR}/scripts/edsdk.py", "call", tool, f"file_id={FILE_ID}"]
    for k, v in kwargs.items():
        cmd.append(f"{k}={v}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return {"__error__": r.stderr.strip()}
    try:
        return json.loads(r.stdout)
    except Exception as e:
        return {"__raw__": r.stdout[:2000], "__err__": str(e)}

all_pages = []
for i in range(38):
    info = call("slide_get_page_info", page_index=i)
    all_pages.append({"page_index": i, "info": info})
    print(f"page {i} done", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(all_pages, f, ensure_ascii=False, indent=1)
print("DONE ->", OUT)

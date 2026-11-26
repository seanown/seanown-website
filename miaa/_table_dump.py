import subprocess, json

SKILL_DIR = "C:/Users/user/.workbuddy/plugins/cache/workbuddy-builtin/tencent-pptx/5.7.7-wb.40774747.g2e8619da.had9031c93ded/skills/tencent-pptx"
FILE_ID = "sid_mv6ewkbr_yal5mbrp"

tables = [
    (3, "0000dd"), (3, "0000de"), (4, "0000e3"),
    (11, "00017a"), (34, "00047c"), (34, "00047e"),
]

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
        return {"__raw__": r.stdout[:1500], "__err__": str(e)}

for page, sid in tables:
    info = call("slide_get_table_info", page_index=page, shape_id=sid)
    print("="*80)
    print(f"PAGE {page} shape {sid}  rows={info.get('row_count')} cols={info.get('col_count')}")
    if "__error__" in info or "__raw__" in info:
        print("  ERR", info)
        continue
    for c in info.get("cells", []):
        if c.get("is_merge_continue"):
            continue
        txt = (c.get("text") or "").replace("\r", " ").replace("\n", " ").strip()
        if txt:
            print(f"  [{c['row']},{c['col']}] {txt}")

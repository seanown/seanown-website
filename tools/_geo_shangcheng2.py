# -*- coding: utf-8 -*-
"""《傷城》第二批：慈幼會孤兒院線 + 1978 年澳門現場"""
import json, time, urllib.parse, urllib.request

UA = "seanown-macau-film/1.0"

QUERIES = [
    ("風順堂上街", "Rua da Prata, Macau"),
    ("風順堂街", "Rua de São Lourenço, Macau"),
    ("聖老楞佐教堂（風順堂）", "Igreja de São Lourenço, Macau"),
    ("慈幼中學（原無原罪孤兒院）", "Instituto Salesiano, Macau"),
    ("慈幼中學", "Colégio Dom Bosco, Macau"),
    ("老人院前地", "Largo da Companhia, Macau"),
    ("高園街（賈尼路街）", "Rua de Dom Belchior Carneiro, Macau"),
    ("婆仔屋（瘋堂斜巷8號）", "Calçada da Igreja de São Lázaro 8, Macau"),
    ("葡京酒店", "Hotel Lisboa, Macau"),
    ("大三巴牌坊", "Ruínas de São Paulo, Macau"),
    ("仁伯爵綜合醫院（山頂醫院）", "Hospital Conde de São Januário, Macau"),
]

def fetch(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 2, "addressdetails": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

out = []
for zh, q in QUERIES:
    try:
        res = fetch(q)
    except Exception as e:
        print(f"[ERR] {zh}: {e}")
        time.sleep(1.2)
        continue
    if not res:
        print(f"[MISS] {zh}  <- {q}")
    for it in res[:2]:
        print(f"[OK] {zh} | {it['lat']},{it['lon']} | {it.get('display_name','')[:85]}")
        out.append({"zh": zh, "q": q, "lat": it["lat"], "lon": it["lon"], "display": it.get("display_name", "")})
    time.sleep(1.2)

with open("_geo_shangcheng2.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n共取得", len(out), "筆")

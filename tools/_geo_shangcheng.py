# -*- coding: utf-8 -*-
"""《傷城》1978 年澳門劇情現場：場地座標查證（OSM Nominatim）"""
import json, time, urllib.parse, urllib.request

UA = "seanown-macau-film/1.0"

QUERIES = [
    ("仁慈堂大樓", "Santa Casa da Misericordia, Largo do Senado, Macau"),
    ("議事亭前地", "Largo do Senado, Macau"),
    ("瘋堂斜巷", "Calçada da Igreja de São Lázaro, Macau"),
    ("婆仔屋（仁慈堂婆仔屋文創空間）", "Rua de Santa Maria, Macau"),
    ("望德堂（聖拉匝祿堂）", "Igreja de São Lázaro, Macau"),
    ("家辣堂街", "Rua de Santa Clara, Macau"),
    ("俾利喇街", "Rua de Francisco Xavier Pereira, Macau"),
    ("高園街", "Rua da Ribeira, Macau"),
    ("澳門主教座堂", "Igreja da Sé, Macau"),
    ("崗頂前地（聖奧斯定教堂）", "Largo de Santo Agostinho, Macau"),
]

def fetch(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 3, "addressdetails": 1}
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
        lat, lon = it["lat"], it["lon"]
        disp = it.get("display_name", "")[:90]
        print(f"[OK] {zh} | {lat},{lon} | {disp}")
        out.append({"zh": zh, "q": q, "lat": lat, "lon": lon, "display": it.get("display_name", "")})
    time.sleep(1.2)

with open("_geo_shangcheng.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n共取得", len(out), "筆")

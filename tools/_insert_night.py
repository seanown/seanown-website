# -*- coding: utf-8 -*-
"""#154 night-comes-for-us-2018 入庫：posts.json 追加條目（movieInfo.macauScenes 三處 ⚠️）。"""
import json

DRAFT = r"C:/Users/user/WorkBuddy/Seanown.org/tools/_draft_night-comes-for-us.md"
POSTS = r"C:/Users/user/WorkBuddy/Seanown.org/data/posts.json"

raw = open(DRAFT, encoding="utf-8").read()
lines = raw.split("\n")
assert lines[0].startswith("副標："), lines[0]
subtitle = lines[0][len("副標："):].strip()
body = "\n".join(lines[1:]).strip()

entry = {
    "num": "154",
    "title": "《嗜人之夜》觀後感",
    "category": "",
    "date": "2026-10-31",
    "location": "澳門",
    "status": "已上線",
    "images": ["assets/og/night-comes-for-us-2018.jpg"],
    "body": body,
    "slug": "night-comes-for-us-2018",
    "series": "macau-film",
    "subtitle": subtitle,
    "filmYear": 2018,
    "movieInfo": {
        "title": "《嗜人之夜》",
        "englishName": "The Night Comes for Us",
        "year": 2018,
        "director": "提莫・塔哈亞托（Timo Tjahjanto）",
        "writer": "提莫・塔哈亞托",
        "genre": "動作 / 犯罪 / 驚悚",
        "releaseDate": "2018-09-22（奇妙電影節首映）、2018-10-19（Netflix 全球上線）",
        "actors": [
            {"name": "喬・塔斯利姆", "role": "伊托 Ito"},
            {"name": "伊科・烏艾斯", "role": "阿里安 Arian"},
            {"name": "茱莉・埃斯特爾", "role": "操控者 The Operator"},
            {"name": "Sunny Pang", "role": "錢武 Chien Wu"},
            {"name": "迪安・薩斯特勞沃德約", "role": "阿爾瑪 Alma"},
            {"name": "漢娜・阿爾・拉希德", "role": "埃琳娜 Elena"},
            {"name": "祖克・李", "role": "博比 Bobby"},
        ],
        "synopsis": "印尼導演提莫・塔哈亞托編劇兼導演，Netflix 第一部印尼原創電影。故事先於二〇一四年與漫畫團體 Glitch Network 畫成圖像小說，四年後拍成電影。東南亞三合會「六海」（enam laut）的執法者伊托（喬・塔斯利姆 飾）奉命屠村，卻在最後關頭反過來救下倖存的小女孩蕾娜，帶她逃回雅加達，成為整個集團的追殺目標；被外派到澳門、替三合會經營俱樂部的昔日兄弟阿里安（伊科・烏艾斯 飾）接到誅殺令，回到雅加達與他上演宿命對決。全片一百二十一分鐘，逾七十分鐘為動作戲，爛番茄新鮮度百分之九十二。",
        "source": "Wikipedia、IMDb（官方劇情摘要與台詞頁）、Rotten Tomatoes、百度百科、英文字幕全本（Springfield! Springfield!）、Cinemateca",
        "scenesLabel": "跟著電影重走《嗜人之夜》",
        "macauScenes": {
            "intro": "《嗜人之夜》的澳門關聯在劇情層面十分明確：英文維基與 IMDb 官方劇情摘要均寫明阿里安被外派到澳門、替三合會經營一間俱樂部，全片唯一的澳門段落就是這間俱樂部與錢武的一通電話。惟俱樂部場景的實拍地，公開資料說法不一——IMDb 拍攝地只登記印尼雅加達，部分資料庫另列澳門。故以下三處均標 ⚠️，屬劇中澳門線的在地參照與歷史對照，不宜當作確認機位。",
            "scenes": [
                {
                    "section": "澳門線同區參照（⚠️ 機位待考）",
                    "places": [
                        {
                            "name": "新口岸／皇朝俱樂部帶（⚠️ 同區參照）",
                            "gps": "22.1901, 113.5502",
                            "map": "https://www.google.com/maps/search/?api=1&query=22.1901, 113.5502",
                            "desc": "新口岸填海區的皇朝一帶，是澳門俱樂部與夜總會最集中的街區，霓虹徹夜不熄。劇中阿里安經營的俱樂部沒有給出地址，畫面裡也沒有任何可辨認的澳門地標；這一帶的街區氣質，與片中「外派職位、用現金結帳」的場所最為貼近。",
                            "camera": "入夜後沿皇朝一帶的街邊走，拍直式霓虹招牌與俱樂部門面的光；深夜車流少，長曝光最出片的夜色。",
                        },
                        {
                            "name": "外港客運碼頭（⚠️ 同區參照）",
                            "gps": "22.1886, 113.5959",
                            "map": "https://www.google.com/maps/search/?api=1&query=22.1886, 113.5959",
                            "desc": "港澳航線的客運碼頭，每天幾十班船進出，是「用船離開、用船回來」的澳門日常。片中蕾娜拿著新護照登船逃往三合會勢力不及的地方，船票是全片真正的出口——這座碼頭正是船票日常化的一面。",
                            "camera": "往海面方向拍船班靠離；傍晚天色轉深、碼頭燈亮起的半小時最飽和。",
                        },
                        {
                            "name": "內港碼頭一帶（⚠️ 歷史對照）",
                            "gps": "22.1948, 113.5354",
                            "map": "https://www.google.com/maps/search/?api=1&query=22.1948, 113.5354",
                            "desc": "火船頭街沿線的內港碼頭區。十九世紀這裡曾是華工出洋（俗稱賣豬仔）的集散地——人從這裡被塞上船，去哪裡由不得自己。片中小女孩自己拿著船票選一個勢力不及的地方，與這段歷史剛好是一個世紀的對照。",
                            "camera": "沿火船頭街由北往南走，拍棧橋、舊倉房與對岸灣仔的水色；下午側光最出層次。",
                        },
                    ],
                }
            ],
        },
    },
}

data = json.load(open(POSTS, encoding="utf-8"))
assert not any(str(p.get("num")) == "154" for p in data["posts"]), "num 154 已存在"
data["posts"].append(entry)
with open(POSTS, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("inserted #154 night-comes-for-us-2018, subtitle =", subtitle)

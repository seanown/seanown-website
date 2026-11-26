# -*- coding: utf-8 -*-
# 為《宮》(num=144) 補上 movieInfo（影片資料＋澳門場景打卡點）
# 對照 bufeng-zhuiying 結構；GPS 套用 geo 閘核證座標（大三巴／路環聖方濟各）
import json, io

P = 'C:/Users/user/WorkBuddy/Seanown.org/data/posts.json'
with io.open(P, encoding='utf-8') as f:
    data = json.load(f)
posts = data['posts']

MI = {
    "title": "《宮》",
    "englishName": "Goong（Princess Hours）",
    "year": 2006,
    "director": "黃仁雷",
    "writer": "仁恩雅",
    "genre": "韓劇（水木劇）／浪漫／宮廷",
    "releaseDate": "2006-01-11（MBC 首播）",
    "actors": [
        {"name": "尹恩惠", "role": "申采靜（平民皇太子妃）"},
        {"name": "朱智勳", "role": "李信（皇太子）"},
        {"name": "金楨勳", "role": "李律（表兄）"},
        {"name": "宋智孝", "role": "閔孝琳"}
    ],
    "synopsis": "《宮》設定在大韓民國仍保留君主制的架空現代，皇太子李信（朱智勳）被迫與平民美術系學生申采靜（尹恩惠）締結政治聯姻，兩人從抗拒、磨合到相愛；全劇大結局讓這對夫妻逃離宮牆，遠走澳門完婚。2006 年 MBC 水木劇，收視峰值近三成，為當年年度冠軍。",
    "source": "MBC、維基百科、IMDb、澳門旅遊局公開資料",
    "scenesLabel": "跟著《宮》遊澳門打卡點",
    "macauScenes": {
        "intro": "二〇〇六年三月二十五至二十七日，五十多人的《宮》劇組來澳拍了三天，澳門旅遊局當時還出面協助。從大三巴到路環的南歐小鎮，這份清單幾乎就是一張澳門旅遊地圖——全劇最關鍵的一場婚禮，就選在路環聖方濟各聖堂。",
        "scenes": [
            {
                "section": "一、澳門半島：城市地標",
                "places": [
                    {
                        "name": "大三巴牌坊",
                        "gps": "22.19746, 113.54086",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.19746, 113.54086",
                        "desc": "劇中澳門場景的門面。這座歷經火災只剩前壁的聖保祿教堂遺址，是澳門最標誌性的地標，也是《宮》把整座城寫進愛情結局的第一個鏡頭。",
                        "camera": "上午逆光拍攝前壁立面最立體；人潮湧入前最能重現劇中清場感。"
                    },
                    {
                        "name": "民政總署大樓",
                        "gps": "22.19380, 113.54220",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.19380, 113.54220",
                        "desc": "位於議事亭前地的葡式政府建築，石柱迴廊與內庭花園洋溢南歐氣息，劇組曾取景其優雅的拱廊與廣場。",
                        "camera": "從議事亭前地廣場仰拍大樓主立面與拱廊；黃昏燈光亮起時最顯葡式風情。"
                    }
                ]
            },
            {
                "section": "二、氹仔：舊城街巷",
                "places": [
                    {
                        "name": "十月初五馬路（氹仔舊城區）",
                        "gps": "22.15360, 113.54970",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.15360, 113.54970",
                        "desc": "氹仔老城區的葡式街道之一，彩色舊樓與石板路保留慢生活氣息，是劇組在離島取景的街景之一。",
                        "camera": "沿路步行跟拍，利用兩側葡式舊樓形成框景；午後光影最能帶出小城氛圍。"
                    }
                ]
            },
            {
                "section": "三、路環：南歐小鎮與海灘",
                "places": [
                    {
                        "name": "路環黑沙海灘",
                        "gps": "22.11800, 113.56100",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.11800, 113.56100",
                        "desc": "路環南岸的黑色沙灘，是全劇少數自然海景場景，開闊的海岸線呼應「遠走他方」的逃離感。",
                        "camera": "黃昏拍海岸線與夕照；沙灘西側礁石可框出劇中開闊感。"
                    },
                    {
                        "name": "竹灣海灘",
                        "gps": "22.12100, 113.56300",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.12100, 113.56300",
                        "desc": "鄰近黑沙的海灣沙灘，背山面海、人跡較少，同屬劇組在路環取景的海岸場景。",
                        "camera": "清晨或傍晚光線柔和時取景；以海灣弧線為引導線拍攝。"
                    },
                    {
                        "name": "恩尼斯總統前地",
                        "gps": "22.11690, 113.55140",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.11690, 113.55140",
                        "desc": "路環村中心的靜謐小廣場，四周葡式建築與老樹成蔭，是劇中漫步談心的南歐小鎮場景。",
                        "camera": "廣場樹蔭下低角度拍攝，捕捉葡式建築立面與行人節奏。"
                    },
                    {
                        "name": "安德魯餅店",
                        "gps": "22.11750, 113.55250",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.11750, 113.55250",
                        "desc": "路環知名的蛋撻老店，劇中角色品嚐澳門地道小吃的場景之一，也是旅遊局協助帶路的地道滋味。",
                        "camera": "店前排隊人潮與葡式街角同框；可拍蛋撻特寫帶出「澳門滋味」。"
                    },
                    {
                        "name": "里斯本地帶餐廳",
                        "gps": "22.11680, 113.55180",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.11680, 113.55180",
                        "desc": "位於路環水鴨街八號的葡國菜餐廳，是劇中角色用餐的南歐風情場景之一。",
                        "camera": "餐廳戶外座位拍葡式街道背景；入夜燈光最顯氛圍。"
                    },
                    {
                        "name": "澳門威斯汀度假酒店",
                        "gps": "22.11980, 113.56480",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.11980, 113.56480",
                        "desc": "位於路環黑沙馬路一九一八號的度假酒店，劇組來澳期間的下榻與部分場景拍攝地。",
                        "camera": "酒店園林與黑沙海灣一帶取景；注意為私人度假設施，拍攝請先徵詢。"
                    },
                    {
                        "name": "路環聖方濟各聖堂",
                        "gps": "22.11690, 113.55150",
                        "map": "https://www.google.com/maps/search/?api=1&query=22.11690, 113.55150",
                        "desc": "全劇最關鍵的一場——李信與采靜在這座米白立面、綠色百葉窗的小教堂舉行婚禮，把澳門的南歐小鎮氣息拍成了童話的終章。",
                        "camera": "教堂前地廣角拍米白立面與鐘樓；午後光線最能重現劇中婚禮的溫柔色溫。"
                    }
                ]
            }
        ],
        "foot": "《宮》大結局篇於二〇〇六年三月在澳門拍攝三天，由澳門旅遊局協助；以上皆為劇中真實出現的澳門實景，多半集中在路環的南歐小鎮與海灘一帶。"
    }
}

for p in posts:
    if p.get('num') == 144:
        p['movieInfo'] = MI
        print('movieInfo set for', p.get('slug'))
        break
else:
    print('ERROR: num=144 not found')

with io.open(P, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('posts.json written')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由結構化資料產生第 43 期（2026-10-19）週報 body HTML。"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "weekly-content" / "2026-10-19.body.html"

C = {n: f"var(--c{n})" for n in range(1, 11)}

# ── PART 01 總覽 ─────────────────────────────────────────────
OVERVIEW_P = (
    "上週澳門以「會議＋文化」雙主線開啟第四季：第十二屆世界旅遊經濟論壇假美獅美高梅開幕，"
    "逾20個國家及地區約1,300名代表來澳，行政長官岑浩輝親臨致辭；第八屆立法會第二會期開鑼，"
    "細則性通過《消費稅規章》修訂法案；琴澳融合再進一步——廣醫一院橫琴醫院加入澳門「電子健康紀錄平台」，"
    "實現琴澳醫療數據跨境共享，澳門大學則與宇樹科技共建智能機器人聯合實驗室落地橫琴大學城。"
    "三展聯動（MIF＋PLPEX＋MFE）10月21日開幕在即，第四屆粵港澳大灣區發展工商大會亦將於10月22至23日在澳舉行，"
    "商貿盛事接力登場。"
)

ANALYSIS = [
    ("澳門社團怎麼看？",
     "本週民生面有兩件事值得社團界盯緊：一是檢察院公佈托兒所負責人涉嫌夥同他人詐騙政府公帑被羈押，涉案屬社福資助體系，"
     "社團作為服務提供者與公帑使用者，必須以更嚴格的內部稽核重建公眾信任；二是社會保障基金提示十月供款月仍有約58%僱主未繳款，"
     "呼籲經「商社通」「一戶通」電子繳納——基層商號與微型企業主恰恰是對線上繳費最不敏感的群體，社團的價值就是把這類「最後一公里」的"
     "行政資訊逐會員送到手。同月，新城A區首個社屋項目東康樓落成、450個家團年底前入住，社團亦應跟進新遷入社區的配套與融入服務。"
     "政府建議：社會文化司轄下社會工作局可聯同教育及青年發展局，就資助機構建立常態化的財務抽查與培訓機制，"
     "並在A區等新社區預先佈點社區服務設施。"),
    ("澳門青年企業家怎麼看？",
     "本週最值得青年創業者研究的是「三展聯動」與「華為ICT師資認證」這兩條線。第31屆MIF連同葡語國家產品展、品牌連鎖加盟展"
     "10月21日起在威尼斯人金光會展舉行，並首設西語國家產業館——這是把葡語市場經驗複製到十億人口西語市場的一次試水，"
     "做電商、品牌代理、文創產品的青年企業家，最直接的動作是拿著貨與方案入場談分銷，把澳門的會展人流轉成訂單。"
     "與此同時，生產力中心與華為推動「ICT師資認證計劃」進中學，意味著三五年內本地AI與網安人才供給將明顯改善，"
     "青年企業家的數位轉型不再只能外包。政府建議：經濟財政司轄下經濟及科技發展局（現正整合消費者委員會及科學技術發展基金職能、"
     "推進重組）可為參展中小企配套「首單獎勵」與跨境電商對接專項，讓展會簽約率轉化為實質出口。"),
    ("澳門文化旅遊業者怎麼看？",
     "世界旅遊經濟論壇本屆重返澳門始創地舉行，加上澳門剛獲西班牙旅行社協會選為2027年「理想旅遊目的地」、"
     "歐洲客源今年首8個月增長逾三成，本地文旅業者面對的是一波明確的「歐洲客」增量。澳門的產品庫其實已經齊備："
     "第29屆葡韻嘉年華與中葡文化藝術節10月23日起接力、青洲出土3.1米古炮帶熱「鑄炮史」深度遊敘事、"
     "創意城市美食之都剛在世界糧食論壇分享經驗——關鍵在於把世遺、節慶與美食打包成國際旅客可線上預約、有明確場次與價格的產品，"
     "而不是等客人碰運氣。政府建議：社會文化司轄下旅遊局可聯同文化局（現正整合體育局及文化發展基金職能、推進重組），"
     "針對歐洲長途客推出「節慶＋深度導賞＋美食體驗」的語種化預約產品，並把國際獎項與論壇成果轉化為海外OTA的合作行銷。"),
]

HIGHLIGHTS = [
    ("180.63億", "澳門元", "9月幸運博彩毛收入（連跌4個月）"),
    ("1,300人", "與會", "第十二屆世界旅遊經濟論壇（逾20國）"),
    ("10間", "醫院", "琴澳醫療數據跨境互通（廣東首間加入eHR）"),
]

# ── 重點議題（★ 星等） ───────────────────────────────────────
KEY_TOPICS = {
    8: [  # 大灣區・橫琴
        (3, "澳大琴研院─宇樹科技聯合實驗室揭牌，落地橫琴大學城", "澳門大學／GCS", "具身智能與機器人產業直接落地琴澳，是大灣區AI硬件賽道上澳門少有的實體佈局。"),
        (3, "琴澳醫療數據跨境開通，廣醫一院橫琴醫院加入澳門 eHR", "橫琴民生事務局／衛生局", "廣東首間，琴澳「規則銜接」從旅遊消費走向民生數據層，跨境服務模式的樣板。"),
        (2, "「琴澳共耕桃花源」民生影像展", "力報", "天沐琴台舉行，以光影回顧深合區五年民生蝶變。"),
    ],
    6: [
        (3, "「我與中華文化」文創大賽10月30日截止報名", "文化局×中國國家博物館", "獎金總額38萬，澳門×文旅部聯合主辦的文創賽道，正是絲綢文創業者可切入的官方平台。"),
    ],
    1: [
        (3, "澳大AI技術助攻肝癌精準治療，成果登上國際頂尖期刊", "澳門大學／GCS", "本地高校AI醫療科研突破，佐證澳門「AI＋醫療」產學研潛力。"),
        (3, "華為ICT大賽澳門站啟動＋攜手多校培育中學資訊科技師資", "生產力中心／華為澳門", "AI與網絡安全人才向下紮根，直接關係未來本地科技企業用人供給。"),
        (3, "澳門電訊率先打造全球首批U6GHz商用場景", "力報", "電信基建升級是數字澳門的底座，對電商與跨境數據業務屬直接利好。"),
    ],
    4: [
        (2, "第十二屆世界旅遊經濟論壇揭幕，主題「危機・韌性・躍升」", "GSEF／GCS", "逾20國約1,300人與會，文旅高層對話回到始創地，國際能見度與商務客流雙收。"),
        (2, "第31屆MIF、2026PLPEX、2026MFE三展聯動10月21日開幕，首設西語國家產業館", "招商投資促進局", "中葡平台＋會展引流，葡西市場新開口。"),
    ],
    5: [
        (2, "金管局聯同銀行公會訪巴西，深化中葡金融服務平台", "金管局", "「精準聯繫人」角色向拉美延伸，跨境金融合作空間擴大。"),
        (2, "第29屆葡韻嘉年華10月23至25日登場，串聯第八屆中葡文化藝術節", "文化局", "中葡文化IP化為可體驗產品，文旅包裝的直接素材。"),
    ],
}

# ── PART 02 數據看板 ──────────────────────────────────────────
DATA_CARDS = [
    ("幸運博彩毛收入", "180.63億", "連跌4個月", "neg", "2026-09 · 博監局", 62, 6),
    ("博彩稅收", "83.92億", "9月", "neu", "2026-09 · 財政局", 30, 6),
    ("入境旅客", "447.81萬", "按年 +6.1%", "pos", "2026-08 · DSEC", 64, 8),
    ("酒店業場所入住率", "93.9%", "8月", "pos", "2026-08 · DSEC", 94, 8),
    ("綜合消費物價指數", "+1.29%", "按年・溫和", "neu", "2026-08 · DSEC", 18, 8),
    ("總體失業率", "2.0%", "低位持平", "pos", "2026-06–08 · DSEC", 20, 8),
    ("就業人口月工作收入中位數", "18,000元", "第2季", "neu", "2026-Q2 · DSEC", 55, 2),
    ("本地生產總值", "1,023.53億", "第2季", "neu", "2026-Q2 · DSEC", 58, 2),
    ("出口貨值", "14.27億", "按年 +11%", "pos", "2026-08 · DSEC", 26, 8),
    ("進口貨值", "115.36億", "按年 +18%", "neu", "2026-08 · DSEC", 70, 8),
    ("外匯儲備", "2,450億", "環比 -0.3%", "neu", "2026-09底 · 金管局", 88, 4),
    ("總人口", "68.65萬", "第2季", "neu", "2026-Q2 · DSEC", 68, 2),
]

SVG_CHART = """<div class="chart-card">
  <h3>2026年8月进出口货值与博彩税收对照（億澳門元）</h3>
  <div class="chart-unit">單位：億澳門元 · 資料期間：2026年8月（博彩為9月）· 來源：DSEC／博監局</div>
  <svg viewBox="0 0 680 300" width="100%" role="img" aria-label="2026年8月进出口货值与博彩税收對照長條圖">
    <line x1="60" y1="250" x2="650" y2="250" stroke="#E0DDD5" stroke-width="1"/>
    <line x1="60" y1="60" x2="650" y2="60" stroke="#E0DDD5" stroke-width="1" stroke-dasharray="3 4"/>
    <text x="52" y="254" text-anchor="end" font-size="11" fill="#888">0</text>
    <text x="52" y="64" text-anchor="end" font-size="11" fill="#888">120</text>
    <rect x="90" y="110" width="80" height="140" fill="#0B3D2E" rx="3"/>
    <text x="130" y="100" text-anchor="middle" font-size="14" font-weight="700" fill="#0B3D2E">14.27</text>
    <text x="130" y="272" text-anchor="middle" font-size="12" fill="#4A4A4A">出口貨值</text>
    <text x="130" y="290" text-anchor="middle" font-size="11" fill="#888">按年+11%</text>
    <rect x="210" y="88" width="80" height="162" fill="#C75B12" rx="3"/>
    <text x="250" y="78" text-anchor="middle" font-size="14" font-weight="700" fill="#C75B12">115.36</text>
    <text x="250" y="272" text-anchor="middle" font-size="12" fill="#4A4A4A">進口貨值</text>
    <text x="250" y="290" text-anchor="middle" font-size="11" fill="#888">按年+18%</text>
    <rect x="330" y="186" width="80" height="64" fill="#1E5F8C" rx="3"/>
    <text x="370" y="176" text-anchor="middle" font-size="14" font-weight="700" fill="#1E5F8C">83.92</text>
    <text x="370" y="272" text-anchor="middle" font-size="12" fill="#4A4A4A">博彩稅收</text>
    <text x="370" y="290" text-anchor="middle" font-size="11" fill="#888">2026年9月</text>
    <rect x="450" y="189" width="80" height="61" fill="#8C1D18" rx="3"/>
    <text x="490" y="179" text-anchor="middle" font-size="14" font-weight="700" fill="#8C1D18">180.63</text>
    <text x="490" y="272" text-anchor="middle" font-size="12" fill="#4A4A4A">博彩毛收入</text>
    <text x="490" y="290" text-anchor="middle" font-size="11" fill="#888">連跌4個月</text>
    <text x="575" y="150" font-size="12" fill="#4A4A4A">逆差</text>
    <text x="575" y="170" font-size="15" font-weight="700" fill="#8C1D18">101.09</text>
    <text x="575" y="190" font-size="11" fill="#888">億澳門元</text>
  </svg>
</div>"""

GDP_NOTE = ("<p><strong>數據解讀：</strong>8月進出口貨值逆差擴大至101.09億澳門元，進口按年增18%反映內需與旅遊消費仍在擴張，"
            "出口增11%則顯示外貿具韌性；博彩毛收入連跌四個月，但同期酒店入住率維持93.9%、入境旅客按年增6.1%，"
            "說明訪澳旅客並未流失，消費結構正在由博彩轉向住宿、餐飲與會展——這正是「換擋期」應有的數據樣貌。</p>")

# ── 分類新聞 ────────────────────────────────────────────────
CATS = [
    (1, "時政與政府政策", [
        ("第八屆立法會第二會期開鑼", "10/16，立法會", "第二次會期首次全體會議舉行，隨後各委員會完成主席及秘書選舉；同場細則性通過《修改〈消費稅規章〉》法案，並通過2027年度立法會本身預算。"),
        ("修改《行政程序法典》展開多場諮詢", "10/13–10/17，法務局", "先後舉行法律界界別專場（逾80人）、部門界別專場（逾140人）及首場公眾諮詢會（逾90人），行政程序現代化立法進入密集聽證階段。"),
        ("2026/2027司法年度開幕", "10/15", "行政長官岑浩輝主禮並對司法機關提出七項要求，強調堅定維護法治、尊重和維護司法獨立，「三五」時期法治是發展建設關鍵。"),
        ("2025年度多繳職業稅10月27日起有序退還", "10/19，財政局", "約5.7萬名納稅人受惠，經銀行轉帳或退稅結算單方式退回；有欠債者的退款11月下旬處理。"),
        ("特區政府撥159.1億元予退休基金會", "力報，10/13", "以2025年度中央預算執行結餘80%注資，應對未來五年約90億元缺口，學者倡博彩稅每年注資30億穩定收入。"),
        ("審計報告與預算執行情況交立法會", "10/16，審計署／財政局", "審計長歐陽瑜介紹《2025年度政府帳目審計報告》；經財司長吳惠嫻介紹2025年度預算執行情況。"),
        ("司警局報案及緊急行動中心氹仔分站啟用", "10/13", "保安司司長陳子勁主禮，離島警務服務佈局進一步優化。"),
    ], "立法會新會期與司法年度同週啟動，行政立法司法三條線同時「開年」；《行政程序法典》修訂諮詢場次密集，顯示公共行政現代化是本屆政府首兩年的制度工程主軸。財政面上，159億注資退休基金會反映人口老化壓力提前入帳規劃，退稅安排則延續還富於民的慣例。"),

    (2, "經濟與民生", [
        ("九月賭收180.63億，連跌四個月", "DSEC／金管局", "9月幸運博彩毛收入180.63億澳門元，博彩稅收83.92億；市場續觀察第四季國際客與大型活動能否扭轉跌勢。"),
        ("8月物業按揭統計", "10/15，金管局", "新批核住宅按揭按月下跌，商用物業貸款回升，未償還貸款總額兩者均按月下跌。"),
        ("新城A區首個社屋項目東康樓落成入伙", "10/16，房屋局", "合資格家團簽約領鑰，預計今年可安排450個家團入住，A區居住人口正式起步。"),
        ("托兒所負責人涉嫌詐騙公帑被羈押", "10/17，檢察院", "三名嫌犯被捕，兩人羈押候審，涉案為政府資助托兒服務。"),
        ("社保供款月：58%僱主未繳", "10/15，社保基金", "截至10月14日約1.45萬名僱主未繳第三季供款，當局籲用「商社通」「一戶通」電子繳款。"),
        ("「雷霆2026」持續行動", "全週，治安警／司警", "每日巡查娛樂場、賓館、酒吧等場所並不定點查車；10/12路氹四間娛樂場巡查截查114人。"),
        ("市署檢出兩款散裝乾螺製品二氧化硫超標", "10/16，市政署", "勒令停售並籲市民停止食用，食安例行監測持續。"),
    ], "賭收連跌四個月是本季經濟最大變數，官方維持2,360億全年預測不變，靠大型會展與國際客補位；樓市按揭轉弱但商用物業回暖，反映資金仍觀望住宅。民生則呈「保障加碼＋執法加壓」並行——社屋入伙、職業稅退還、社保提醒同時，雷霆行動與食安抽查不放鬆。"),

    (3, "社會與文化", [
        ("第一屆「全城有禮」系列活動開幕", "10/17，市政署", "黃少澤主禮，為期兩週、16項共43場次，涵蓋公民教育、親子與社區共融。"),
        ("第三屆澳門國際兒童藝術節落幕", "10/16，文化局", "逾千場活動、吸引超過64萬人次參與，規模創新高。"),
        ("青洲出土3.1米古炮管", "力報，10/16", "繼2020–21年內港及路氹出土四門古炮後再現重器，帶出「大航海時代澳門鑄炮史」深度文化敘事，媒體以系列專題回顧卜加勞炮廠遺產。"),
        ("「城市浪漫——澳門作家作品展」10月21日開放", "10/13，文化局×澳門筆會", "澳門文學館舉行，展現新生代文學創作力量。"),
        ("文化局率演藝業界赴港參與香港演藝博覽", "10/14", "本地委約製作作品設展推介，拓展演藝輸出機會。"),
        ("第七屆澳門人文社會科學研究優秀成果評獎公佈", "10/15，澳門基金會", "390份申請評出58項優秀著述。"),
        ("重陽節防疫與便民安排", "10/14–10/18，衛生局／市政署", "市政墳場延長開放、增開37T免費接駁；當局赴墳場宣傳防控登革熱及基孔肯雅熱「雙熱」，本週通報多宗輸入性個案並進行區域滅蚊。"),
    ], "文化活動密集但焦點分明——兒童藝術節以64萬人次收官證明親子文旅市場體量；古炮出土則為澳門的「海洋史」敘事再添實證，這類考古發現對深度文化旅遊是稀缺素材。衛生面須留意「雙熱」輸入壓力隨秋遊客流上升。"),

    (4, "旅遊、大型活動與會展盛事", [
        ("第十二屆世界旅遊經濟論壇（GTEF）揭幕", "10/15–10/17，美獅美高梅", "主題「危機・韌性・躍升——旅遊經濟重塑全球可持續未來」，逾20個國家及地區約1,300人與會；岑浩輝與聯合國世界旅遊組織秘書長會面；澳旅大承辦「新一代旅遊業領軍人才」研討會。"),
        ("澳門獲選2027年西班牙旅行社協會（CEAV）「理想旅遊目的地」", "10/14，旅遊局", "首8個月歐洲客源增長逾30%、西班牙客升近兩成，深耕市場策略收效。"),
        ("澳門於世界糧食論壇分享美食之都經驗", "10/13，旅遊局", "與UNESCO創意城市網絡合作，以澳門為案例探討創意城市美食之都發展與土生菜承傳。"),
        ("第73屆澳門格蘭披治大賽車11月19至22日舉行", "10/16，體育局", "組委會舉行新聞發佈會公佈賽事及贊助商資訊；東望洋跑道防撞設施16日起安裝，多處道路分階段交管。"),
        ("FIBA三人籃球澳門大師賽大三巴開打", "10/17–10/18，體育局×澳門星娛樂", "世界排名第一的塞爾維亞烏布隊奪冠；同期舉行2026大灣區3×3籃球巡迴賽總決賽。"),
        ("第31屆MIF、PLPEX、MFE三展聯動10月21至24日舉行", "10/15，招商局", "匯聚葡西資源，首設西語國家產業館；郵電局設紀念郵戳櫃台。"),
        ("第四屆粵港澳大灣區發展工商大會10月22至23日在澳舉行", "10/13，招商局", "中貿促、粵、港、澳四方主辦，預計逾1,000人參會。"),
    ], "本週是「盛事季」的排程高峰——GTEF剛落幕，MIF三展、大灣區工商大會、大賽車接連在途，會展業明顯進入檔期紅利期。國際客開拓出現結構性亮點：歐洲線雙位數增長＋CEAV獎項，說明澳門旅遊推廣正從「量」轉向「客源結構」經營。"),

    (5, "中葡商貿合作平台", [
        ("金管局聯同銀行公會訪巴西", "10/16，金管局", "拜會中國駐巴西使領館、巴西央行及主流銀行，推介「中葡金融服務平台」，探討跨境金融合作與「精準聯繫人」角色。"),
        ("第二屆葡語國家仲裁大會在澳開幕", "10/15–10/16", "黃少澤代表行政長官主禮，葡語國家法律服務生態持續在澳集聚。"),
        ("第31屆MIF＋2026PLPEX＋2026MFE三展聯動", "10/21–10/24", "PLPEX聚焦葡語國家產品及服務，首設西語國家產業館拓展葡語平台外延。"),
        ("巴西聖保羅州立大學副教授到訪澳理工", "10/13", "深化澳巴高教、語言文化及新聞傳播交流。"),
        ("澳門「一國兩制」成功實踐歐洲巡展葡萄牙開展", "10/12–10/22，大眾報", "雷利亞、科英布拉、阿爾加維三所大學巡展，以中葡文圖片與影片對外講述澳門故事。"),
    ], "中葡平台本週呈「金融＋法律＋展覽＋外交敘事」四線並進：金管局南美拓點是平台角色最實質的一次延伸，仲裁大會鞏固法治基建，巡展則服務於對外形象。西語館的設立值得持續追蹤——若成常設，澳門平台的腹地將從2.6億葡語人口擴及5億西語市場。"),

    (6, "中華文化交流合作基地", [
        ("第十九屆澳門國際媽祖文化旅遊節", "10/12–10/13", "兩岸四地逾千人聚澳，閩澳文旅招商推介會暨歡迎晚宴舉行；柯嵐出席福建工美供需對接暨工藝美術精品展啟動儀式——工藝美術對接正合本地文創業界所需。"),
        ("第29屆葡韻嘉年華＋第八屆中葡文化藝術節10月23至25日舉行", "文化局", "社區傳統歌舞表演10月24至25日走入社區，展現中華文化為主流、多元文化共存的定位。"),
        ("市政署「國風拾趣工房」十一月工作坊開放報名", "10/16", "紙藝、紮染等民族工藝手作，弘揚中華傳統文化。"),
        ("澳門基金會「澳門記憶」七週年「記憶沙龍」開放報名", "10/12", "10月24日兩場離島主題文史講座。"),
        ("2026年「澳門社區工作者陝西體驗式研修計劃」啟程", "10/14，澳門基金會", "12個社服團體20名學員赴陝研修。"),
    ], "媽祖旅遊節與文創大賽一南一北把「中華文化基地」的兩種路徑講清楚——民俗節慶帶客流，文創賽道帶產業；工美供需對接與文創大賽都是澳門設計者可以直接下場的介面，值得業界把握10月30日的報名截止線。"),

    (7, "社團與社區活動", [
        ("澳門歸僑總會成立58周年聯歡晚會", "10/14", "吳惠嫻代表行政長官出席，強調引僑資助澳門經濟多元發展。"),
        ("澳門社區工作者陝西研修計劃啟程", "10/14–10/24", "工聯、明愛、街坊總會、婦聯、民建聯等12個團體20人參加。"),
        ("司警局「社區禁毒推廣站」巡迴宣教總結", "10/15", "攜手街坊總會、工聯、婦聯、歸僑總會及民建聯，8月中旬起分階段覆蓋社區服務網絡。"),
        ("茨林圍活化座談會", "力報，10/13", "社區營建促進會與關注組邀專家及居民約30人獻策，倡「居民優先、活態保育、漸進更新」。"),
        ("澳門唐家灣同鄉聯誼會慶祝成立29周年", "力報，10/16", "續發揮澳珠交流橋樑作用。"),
        ("「營動全城」健康生活方式大賽首月逾2.2萬居民參與", "10/14，衛生局", "疫苗接種站與社區服務點聯動推廣。"),
    ], "社團界本週呈「對外聯誼＋對內治理」雙軌：僑總、同鄉會慶典強化橋樑敘事，茨林圍座談則顯示社區活化議題開始由居民自發端上檯面；社福資助詐騙案提醒社團治理與公信力是聯誼之外的硬功課。"),

    (8, "大灣區・橫琴", [
        ("2026葡風琴韻嘉年華在橫琴啟幕", "10/16–10/18，橫琴民生事務局×澳門文化局", "葡風美食、文化特展與歌舞串聯琴澳，把澳門中葡文化輸出到橫琴街頭。"),
        ("粵港澳三地「綠色通道專題工作小組」會議在廣州召開", "10/13–10/14，警察總局", "持續優化大灣區跨境應急救援協作機制。"),
        ("廣東省科學技術廳廳長王月琴訪澳大", "10/12", "就粵澳科技合作交流。"),
    ], "本週橫琴新聞的關鍵詞是「制度輸出」——醫療數據跨境是規則銜接的硬突破，聯合實驗室則是澳門科研首次以實體形式進駐大學城核心區；文化輸出（葡風琴韻）反向把澳門IP帶入橫琴，澳琴一體化開始呈現雙向流動。"),
]

CAT9 = [
    ("10/16–18", "ENHYPEN「BLOOD SAGA」巡演", "銀河綜藝館", "K-pop", "kpop"),
    ("10/17–18", "都暻秀（D.O.）", "新濠影匯綜藝館", "K-pop", "kpop"),
    ("10/17", "泳兒（Vincy）", "百老匯舞台", "粵語", "mando"),
    ("10/17", "裴俊英（JACOB）", "銀河 G Box", "K-pop", "kpop"),
    ("10/17", "PerthSanta", "葡京人 H853 娛樂館", "見面會", "event"),
    ("10/18", "金允植、朴時宇雙人見面會", "澳門百老匯", "K-pop", "kpop"),
]

CAT10 = [
    ("Google DeepMind 全球發布 Gemini 4 Argon", "10/13", "以純推理在 ERQA 具身推理基準拿下87%居首，主打機器人全生命周期工作流——Video-to-Sim-to-Real 首次跑通，Apptronik Apollo 人形機器人零樣本連投七球命中；輸入定價每百萬 token 2 美元（優惠期至11/30）。"),
    ("Meta 連發 Muse Spark Open 與 Muse Wonder 系列", "10/13–10/16", "816B 參數開放權重多模態模型（42B 激活、1M 上下文）＋兩款代理任務旗艦，開源與商業代理雙線押注。"),
    ("Anthropic 自研版本控制系統 Scion 替代 git", "10/14", "AI 寫碼量爆增令 git 不堪負荷，五個月完成遷移，日合併量從5月的約2,500次躍至9月的逾30,000次——AI Coding 對基礎設施的反向重塑。"),
    ("Microsoft 發布第三代自研 AI 晶片 Maia 300", "10/13", "每兆瓦 token 輸出較領先 GPU 系統多40%，2027年量產，持續降低對 Nvidia 依賴。"),
    ("DeepSeek 發布 V4.1-Flash-1017（MIT 授權）", "10/18", "推理、編碼、代理任務與視覺基準全面提升，開源賽道節奏未減。"),
]

CAT10_NOTE = "本週全球AI的主敘事是「模型走進物理世界與生產管線」——Google 用 Argon 把機器人教學從數週壓到數小時，Anthropic 乾脆為 AI 寫碼重建了版本控制，Microsoft 則在算力層續拼性價比。對澳門的啟示：具身智能與代理編碼都在快速降門檻，澳大×宇樹實驗室恰在此窗口落地，方向踩得準。"

CAT9_NOTE = "上週末澳門迎來K-pop「多館齊發」——ENHYPEN連唱三場銀河綜藝館，與新濠影匯、百老匯同檔分流，演唱會經濟的館際競爭白熱化；本週末（10/24前後）任賢齊、草蜢、tripleS等接力，10月全月密度屬全年高位。"

MONTH = [
    ("10/3", "劉若英【飛行日】巡演", "銀河綜藝館", "華語", "mando"),
    ("10/4", "TeeTee（陳藝迪）、鄧宇博", "百老匯舞台", "見面會", "event"),
    ("10/4", "Sara Landry", "倫敦人綜藝館", "電音", "event"),
    ("10/9", "After Party（DJ Mustard × 楊和蘇）", "倫敦人綜藝館", "電音／嘻哈", "event"),
    ("10/9–11", "NBA 中國賽", "威尼斯人金光綜藝館", "體育", "event"),
    ("10/9–11", "李燦（DINO）", "新濠影匯綜藝館", "K-pop", "kpop"),
    ("10/10", "張靚穎「追」巡演收官站", "銀河綜藝館", "華語", "mando"),
    ("10/10", "古淖文（German）", "百老匯舞台", "粵語", "mando"),
    ("10/10–11", "NBA 球迷日", "威尼斯人金光綜藝館", "體育", "event"),
    ("10/12–13", "第十九屆澳門國際媽祖文化旅遊節", "澳門", "文化／節慶", "event"),
    ("10/16–18", "ENHYPEN「BLOOD SAGA」巡演", "銀河綜藝館", "K-pop", "kpop"),
    ("10/16–18", "2026 葡風琴韻嘉年華", "橫琴", "文化（琴澳）", "event"),
    ("10/17–31", "第一屆「全城有禮」系列活動（43場次）", "全城社區", "公民教育／免費", "event"),
    ("10/21", "「城市浪漫——澳門作家作品展」開展", "澳門文學館", "展覽", "event"),
    ("10/21–24", "第31屆MIF＋2026 PLPEX＋2026 MFE 三展聯動", "威尼斯人金光會展", "會展", "event"),
    ("10/22–23", "第四屆粵港澳大灣區發展工商大會", "澳門", "會展", "event"),
    ("10/23–25", "第29屆葡韻嘉年華＋第八屆中葡文化藝術節", "龍環葡韻及社區", "文化／免費", "event"),
    ("10/24", "任賢齊「齊跡」演唱會", "銀河綜藝館", "華語", "mando"),
    ("10/24", "蘇志燮", "倫敦人劇場", "韓星見面會", "kpop"),
    ("10/24", "Ian（陳卓賢）", "倫敦人綜藝館", "K-pop", "kpop"),
    ("10/24", "tripleS", "澳門百老匯", "K-pop", "kpop"),
    ("10/24–25", "草蜢「THREE IN LOVE」", "威尼斯人綜藝館", "粵語", "mando"),
    ("10/30", "「我與中華文化・從文創裡看澳門歷史」文創大賽截止報名", "—", "徵件截止", "event"),
    ("10/31", "EPEX", "銀河 G Box", "K-pop", "kpop"),
    ("10/31", "邱鋒澤", "澳門百老匯", "華語", "mando"),
    ("10/31", "AppleMim", "澳門皇冠假日酒店", "見面會", "event"),
    ("10/31–11/1", "PLAVE", "倫敦人綜藝館", "虛擬偶像", "kpop"),
    ("10/31–11/1", "李赫宰（銀赫）", "倫敦人劇場", "K-pop", "kpop"),
]

NEXT_MONTH = [
    ("11/1", "Air Supply", "澳門百老匯", "西洋經典", "event"),
    ("11/4–8", "第二屆橫琴魔術節（HMF2026）", "橫琴", "文化", "event"),
    ("11/7", "周柏豪「綻放之章」（生日限定場）", "威尼斯人綜藝館", "粵語", "mando"),
    ("11/7–8", "金俊秀、金在中（JX）巡演", "倫敦人綜藝館", "K-pop", "kpop"),
    ("11/7–8", "LE SSERAFIM", "銀河綜藝館", "K-pop", "kpop"),
    ("11/7", "孔劉見面會", "新濠影匯綜藝館", "韓星", "kpop"),
    ("11/13–15", "梓渝", "銀河綜藝館", "華語", "mando"),
    ("11/14", "杜德偉《Get Up》2.0", "倫敦人綜藝館", "粵語", "mando"),
    ("11/14", "玉澤演", "上葡京", "K-pop", "kpop"),
    ("11/14–15", "CNBLUE", "新濠影匯", "韓團", "kpop"),
    ("11/14", "AxMxP「X VERSE」", "巴黎人劇場", "樂團", "event"),
    ("11/14", "Yesung", "澳門百老匯", "K-pop", "kpop"),
    ("11/19–22", "第73屆澳門格蘭披治大賽車", "東望洋跑道", "體育盛事", "event"),
    ("11/20–22", "TOMORROW X TOGETHER", "銀河綜藝館", "K-pop", "kpop"),
    ("11/21", "Supper Moment「謝謝你啊世界」澳門限定版", "威尼斯人綜藝館", "粵語", "mando"),
    ("11/21", "陳偉霆", "新濠影匯", "華語", "mando"),
    ("11/21", "岳雲鵺、孫越相聲專場（德雲社30周年）", "倫敦人綜藝館", "華語曲藝", "mando"),
    ("11/27–28", "MC張天賦《E=MC²》", "銀河綜藝館", "粵語", "mando"),
]

SOURCE_ROWS = [
    ("政府新聞局 GCS", "成功", "0", "本週最完整官方稿源"),
    ("統計暨普查局 DSEC", "成功", "0", "博彩收入、旅客、CPI、失業率等主要指標"),
    ("力報 Exmoo", "成功", "0", "159億注資退休基金會、古炮出土、6GHz商用場景"),
    ("澳廣視 TDM", "部分成功", "0", "經 WebSearch 單篇補抓"),
    ("濠江日報", "部分成功", "0", "API 頭條＋澳門欄目"),
    ("大眾報", "部分成功", "0", "「一國兩制」歐洲巡展（新法首次成功）"),
    ("現代澳門日報", "部分成功", "0", "經 WebSearch 索引"),
    ("旅遊局", "部分成功", "0", "CEAV 理想旅遊目的地、美食之都分享"),
    ("正報", "失敗", "2", "圖片型電子報，結構性限制"),
    ("澳門日報", "失敗", "2", "本週未及逐日抓取"),
    ("華僑報", "失敗", "2", "本週未及抓取"),
]

SOURCE_NOTES = [
    "正報為圖片型電子報，WebFetch 無法解析內文，為結構性限制；澳門日報、華僑報本週投入度低，稿源已由 GCS 補足，下週若仍無取得將累計至3週。",
    "本週無來源達「連續3週失敗」門檻，毋須移除或更換提示。",
]


def star(n):
    return "★" * n


def build():
    p = []
    p.append("<!-- ===== 一、本週總覽 ===== -->")
    p.append('  <div class="section" id="overview">')
    p.append('    <div class="section-num">PART 01</div>')
    p.append('    <h2 class="section-title">本週總覽</h2>')
    p.append('    <div class="overview">')
    p.append(f"      <p>{OVERVIEW_P}</p>")
    p.append('      <div class="overview-analysis">')
    p.append('        <div class="analysis-lead">軒哥視角｜澳門三個群體怎麼看</div>')
    p.append('        <div class="analysis-byline">翁振軒（軒哥）· 粵港澳大灣區電子商會會長</div>')
    for tag, body in ANALYSIS:
        p.append('        <div class="analysis-item">')
        p.append(f'          <span class="analysis-tag">{tag}</span>')
        p.append(f"          <p>{body}</p>")
        p.append("        </div>")
    p.append("      </div>")
    p.append('      <div class="overview-highlights">')
    for num, label, desc in HIGHLIGHTS:
        p.append('        <div class="highlight-chip">')
        p.append(f'          <div class="num">{num}</div>')
        p.append(f'          <div class="label">{label}</div>')
        p.append(f'          <div class="desc">{desc}</div>')
        p.append("        </div>")
    p.append("      </div>")
    p.append("    </div>")
    p.append("  </div>")

    p.append("  <!-- ===== 二、一週數據看板 ===== -->")
    p.append('  <div class="section" id="data">')
    p.append('    <div class="section-num">PART 02</div>')
    p.append('    <h2 class="section-title">一週數據看板</h2>')
    p.append('    <div class="data-grid">')
    for label, value, change, kind, period, width, ci in DATA_CARDS:
        p.append('      <div class="data-card">')
        p.append(f'        <div class="label">{label}</div>')
        p.append(f'        <div class="value">{value}</div>')
        p.append(f'        <div class="change {kind}">{change}</div>')
        p.append(f'        <div class="period">{period}</div>')
        p.append(f'        <div class="data-bar"><div class="data-bar-fill" style="width:{width}%;background:{C[ci]}"></div></div>')
        p.append("      </div>")
    p.append("    </div>")
    p.append("    " + SVG_CHART)
    p.append('    <div class="overview" style="margin-top:16px">')
    p.append(f"      {GDP_NOTE}")
    p.append("    </div>")
    p.append("  </div>")

    p.append("  <!-- ===== 三、分類新聞 ===== -->")
    p.append('  <div class="section">')
    for idx, title, items, note in CATS:
        cid = C[idx]
        p.append(f'    <div class="category" id="cat{idx}">')
        p.append(f'      <div class="category-header" style="background:{cid}">')
        p.append(f'        <span class="cat-num">{idx:02d}</span>')
        p.append(f'        <span class="cat-title">{title}</span>')
        p.append(f'        <span class="cat-count">{len(items)} 則</span>')
        p.append("      </div>")
        p.append('      <div class="category-body">')
        # 重點議題（★）先列
        for sn, stitle, ssrc, sdesc in KEY_TOPICS.get(idx, []):
            p.append('        <div class="news-item">')
            p.append(f'          <div class="bullet" style="background:{cid}"></div>')
            p.append('          <div class="content">')
            p.append(f'            <div class="title">{star(sn)} {stitle}</div>')
            p.append(f'            <div class="desc">{sdesc}</div>')
            p.append(f'            <div class="source">{ssrc}</div>')
            p.append("          </div>")
            p.append("        </div>")
        for t, s, d in items:
            if any(t == kt[1] for kt in KEY_TOPICS.get(idx, [])):
                continue
            p.append('        <div class="news-item">')
            p.append(f'          <div class="bullet" style="background:{cid}"></div>')
            p.append('          <div class="content">')
            p.append(f'            <div class="title">{t}</div>')
            p.append(f'            <div class="desc">{d}</div>')
            p.append(f'            <div class="source">{s}</div>')
            p.append("          </div>")
            p.append("        </div>")
        p.append(f'        <div class="category-summary" style="border-color:{cid}">')
        p.append(f"          <strong>本週小結：</strong>{note}")
        p.append("        </div>")
        p.append("      </div>")
        p.append("    </div>")

    # Cat 9
    p.append('    <div class="category" id="cat9">')
    p.append(f'      <div class="category-header" style="background:{C[9]}">')
    p.append('        <span class="cat-num">09</span>')
    p.append('        <span class="cat-title">文化娛樂演唱會</span>')
    p.append('        <span class="cat-count">本週重點＋整月</span>')
    p.append("      </div>")
    p.append('      <div class="category-body">')
    p.append('        <h4 style="font-size:16px;font-weight:600;margin:4px 0 10px;color:var(--brand)">本週重點（10/12–10/18）</h4>')
    p.append('        <table class="concert-table"><thead><tr><th>日期</th><th>活動／藝人</th><th>場地</th><th>類型</th></tr></thead><tbody>')
    for d, name, venue, kind, cls in CAT9:
        p.append(f'          <tr><td>{d}</td><td>{name}</td><td>{venue}</td><td><span class="badge {cls}">{kind}</span></td></tr>')
    p.append("        </tbody></table>")
    p.append('        <h4 style="font-size:16px;font-weight:600;margin:22px 0 10px;color:var(--brand)">2026年10月整月月曆</h4>')
    p.append('        <table class="concert-table"><thead><tr><th>日期</th><th>活動或藝人</th><th>場地</th><th>類型</th></tr></thead><tbody>')
    for d, name, venue, kind, cls in MONTH:
        p.append(f'          <tr><td>{d}</td><td>{name}</td><td>{venue}</td><td><span class="badge {cls}">{kind}</span></td></tr>')
    p.append("        </tbody></table>")
    p.append('        <h4 style="font-size:16px;font-weight:600;margin:22px 0 10px;color:var(--brand)">11月已公佈場次（預告）</h4>')
    p.append('        <table class="concert-table"><thead><tr><th>日期</th><th>活動或藝人</th><th>場地</th><th>類型</th></tr></thead><tbody>')
    for d, name, venue, kind, cls in NEXT_MONTH:
        p.append(f'          <tr><td>{d}</td><td>{name}</td><td>{venue}</td><td><span class="badge {cls}">{kind}</span></td></tr>')
    p.append("        </tbody></table>")
    p.append('        <p style="font-size:12.5px;color:var(--ink-3);margin-top:10px">（票價以官方售票平台為準；場地以主辦方最新公佈為準。）</p>')
    p.append(f'        <div class="category-summary" style="border-color:{C[9]}">')
    p.append(f"          <strong>本週小結：</strong>{CAT9_NOTE}")
    p.append("        </div>")
    p.append("      </div>")
    p.append("    </div>")

    # Cat 10
    p.append('    <div class="category" id="cat10">')
    p.append(f'      <div class="category-header" style="background:{C[10]}">')
    p.append('        <span class="cat-num">10</span>')
    p.append('        <span class="cat-title">全球 AI 領域精選</span>')
    p.append(f'        <span class="cat-count">{len(CAT10)} 條</span>')
    p.append("      </div>")
    p.append('      <div class="category-body">')
    for t, s, d in CAT10:
        p.append('        <div class="news-item">')
        p.append(f'          <div class="bullet" style="background:{C[10]}"></div>')
        p.append('          <div class="content">')
        p.append(f'            <div class="title">{t}</div>')
        p.append(f'            <div class="desc">{d}</div>')
        p.append(f'            <div class="source">{s}</div>')
        p.append("          </div>")
        p.append("        </div>")
    p.append(f'        <div class="category-summary" style="border-color:{C[10]}">')
    p.append(f"          <strong>本週小結：</strong>{CAT10_NOTE}")
    p.append("        </div>")
    p.append("      </div>")
    p.append("    </div>")
    p.append("  </div>")

    # 來源
    p.append("  <!-- ===== 四、來源與備註 ===== -->")
    p.append('  <div class="section" id="sources">')
    p.append('    <div class="section-num">PART 04</div>')
    p.append('    <h2 class="section-title">來源與備註</h2>')
    ok = [r for r in SOURCE_ROWS if r[1] == "成功"]
    part = [r for r in SOURCE_ROWS if r[1] == "部分成功"]
    bad = [r for r in SOURCE_ROWS if r[1] == "失敗"]
    p.append('    <div class="source-grid">')
    p.append('      <div class="source-list">')
    p.append(f'        <h4>成功來源（{len(ok)}）</h4>')
    p.append("        <ul>")
    for name, st, fail, note in ok:
        p.append(f'          <li><span class="dot" style="background:#0B3D2E"></span><span>{name}｜{note}</span></li>')
    p.append("        </ul>")
    p.append("      </div>")
    p.append('      <div class="source-list">')
    p.append(f'        <h4>部分成功（{len(part)}）</h4>')
    p.append("        <ul>")
    for name, st, fail, note in part:
        p.append(f'          <li><span class="dot" style="background:#C75B12"></span><span>{name}｜{note}</span></li>')
    p.append("        </ul>")
    p.append("      </div>")
    p.append('      <div class="source-list">')
    p.append(f'        <h4>失敗來源（{len(bad)}）</h4>')
    p.append("        <ul>")
    for name, st, fail, note in bad:
        p.append(f'          <li><span class="dot" style="background:#8C1D18"></span><span>{name}｜連續失敗 {fail} 週｜{note}</span></li>')
    p.append("        </ul>")
    p.append("      </div>")
    p.append('      <div class="source-list">')
    p.append("        <h4>備註</h4>")
    p.append("        <ul>")
    for n in SOURCE_NOTES:
        p.append(f'          <li><span class="dot" style="background:#1E5F8C"></span><span>{n}</span></li>')
    p.append("        </ul>")
    p.append("      </div>")
    p.append("    </div>")
    p.append('    <div class="overview" style="margin-top:18px">')
    p.append('      <p style="font-size:14px;color:var(--ink-2);line-height:1.8"><strong>編註：</strong>本週報新聞彙整自澳門特區政府新聞局、統計暨普查局（DSEC）、力報、澳廣視 TDM、濠江日報、大眾報、旅遊局等公開來源。所有數據均來自可查證來源，未經查證的訊息不予採用；引用請以官方原始發佈為準。</p>')
    p.append("    </div>")
    p.append("  </div>")

    OUT.write_text("\n".join(p), encoding="utf-8")
    n_items = sum(len(v[2]) + len(KEY_TOPICS.get(v[0], [])) for v in CATS)
    print(f"OK -> {OUT}")
    print(f"分類數 10 / 新聞條數 {n_items} / 數據卡 {len(DATA_CARDS)} / 演唱會本週 {len(CAT9)} + 10月 {len(MONTH)} + 11月 {len(NEXT_MONTH)} / AI {len(CAT10)} / 來源 {len(SOURCE_ROWS)}")


if __name__ == "__main__":
    build()
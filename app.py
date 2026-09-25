"""健身房紀錄頁面（Streamlit + Supabase）

執行：  streamlit run app.py
設定：  .streamlit/secrets.toml 需要
            SUPABASE_URL = "https://xxxx.supabase.co"
            SUPABASE_KEY = "你的 key"
資料表： 先在 Supabase SQL Editor 執行 schema.sql
需求：  Python 3.11+ / requirements.txt
"""

import html
import math
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

# ── 設定 ────────────────────────────────────────────────
# 動作教學內容（已替換為 Unsplash 穩定圖床連結）
TUTORIALS: dict[str, dict] = {
    "機關胸推": {
        "target": "胸大肌、三頭肌、前三角肌",
        "steps": ["調整椅座高度，握把與胸線齊平，背部貼緊椅背", "吐氣將握把往前推出，手肘不完全鎖死", "吸氣緩慢還原，感受胸肌伸展"],
        "mistakes": ["聳肩", "椅座高度沒調好，導致握把與胸口不同高", "推到底時手肘鎖死甩動"],
        "image_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&auto=format&fit=crop",
    },
    "槓鈴臥推": {
        "target": "胸大肌、三頭肌、前三角肌",
        "steps": ["躺平於臥推椅，握距略寬於肩，肩胛骨下壓內收，雙腳踩穩地面", "槓鈴下降至胸口下緣，手肘約呈 45 度角", "用力推起，回到起始位置"],
        "mistakes": ["下背過度拱起", "槓鈴在胸口彈震借力", "手肘外展呈 90 度，增加肩關節壓力"],
        "image_url": "https://images.unsplash.com/photo-1534367507873-d2d7e24c797f?w=800&auto=format&fit=crop",
    },
    "啞鈴臥推": {
        "target": "胸大肌、三頭肌",
        "steps": ["平躺長凳，雙手持啞鈴於胸側，掌心朝前", "向上推起啞鈴至手臂微彎，不完全鎖死", "控制速度下放回起始位置"],
        "mistakes": ["兩側啞鈴高度不對稱", "下放過快、失去控制", "肩胛骨沒有固定夾緊"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop",
    },
    "上斜啞鈴臥推": {
        "target": "上胸、前三角肌",
        "steps": ["將長凳調至約 30–45 度，啞鈴放大腿上再躺下", "推起啞鈴至最高點，手肘不鎖死", "緩慢下放到胸部上緣兩側"],
        "mistakes": ["角度調太高，變成肩推", "下放時肩胛前引", "手肘過度外張"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop",
    },
    "夾胸機": {
        "target": "胸大肌內側",
        "steps": ["坐正，手肘輕靠把手，微彎曲", "水平夾向身體中線，感受胸肌收縮", "緩慢打開還原，不要完全放鬆卸力"],
        "mistakes": ["用力甩動而非穩定夾胸", "聳肩代償", "活動範圍拉太開造成肩關節壓力"],
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&auto=format&fit=crop",
    },
    "雙槓體撐": {
        "target": "下胸、三頭肌",
        "steps": ["雙手撐於握把，身體懸空，手臂伸直", "身體微前傾，手肘彎曲下降至約 90 度", "推起回到起始位置"],
        "mistakes": ["下降過深，造成肩關節壓力", "身體過度前傾或後仰，失去控制"],
        "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&auto=format&fit=crop",
    },
    "滑輪下拉": {
        "target": "闊背肌、二頭肌",
        "steps": ["坐好固定大腿，寬握把手", "向下拉至鎖骨上緣，夾背挺胸", "緩慢回到起始位置，感受背部伸展"],
        "mistakes": ["身體後仰借力甩動", "拉到脖子後方", "聳肩、沒有夾背"],
        "image_url": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=800&auto=format&fit=crop",
    },
    "座姿滑輪划船": {
        "target": "中背、闊背肌、二頭肌",
        "steps": ["坐穩，雙腳踩踏板，膝蓋微彎，手臂伸直握把手", "身體挺直，將把手拉向腹部", "緩慢向前伸展還原"],
        "mistakes": ["身體前後晃動借力", "圓背駝背", "拉到胸口而非腹部"],
        "image_url": "https://images.unsplash.com/photo-1521804906057-1df8fdb718b7?w=800&auto=format&fit=crop",
    },
    "槓鈴划船": {
        "target": "中背、闊背肌",
        "steps": ["屈髖前傾約 45 度，握槓於身前，背部打直", "將槓拉向下腹部，夾緊肩胛骨", "緩慢下放還原"],
        "mistakes": ["腰部拱起或圓背", "用甩動借力", "站姿太直，變成聳肩上提"],
        "image_url": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800&auto=format&fit=crop",
    },
    "單臂啞鈴划船": {
        "target": "中背、闊背肌",
        "steps": ["單膝與單手撐於長凳，另一手持啞鈴", "將啞鈴拉向髖部，手肘貼近身體", "緩慢下放伸展"],
        "mistakes": ["軀幹旋轉借力", "手肘外開，變成側平舉動作"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop",
    },
    "引體向上": {
        "target": "闊背肌、二頭肌",
        "steps": ["寬握單槓，身體懸掛，核心收緊", "拉起身體，直到下巴過槓", "緩慢下放到手臂完全伸直"],
        "mistakes": ["擺盪借力", "只做半程，沒有完全伸展", "聳肩代償"],
        "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&auto=format&fit=crop",
    },
    "反向飛鳥/後三角機": {
        "target": "後三角肌、菱形肌",
        "steps": ["胸部貼靠椅背，握住把手，手臂微彎", "向外向後展開手臂，夾緊肩胛骨", "緩慢回到起始位置"],
        "mistakes": ["用手臂力量而非背部發力", "身體離開椅背借力"],
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&auto=format&fit=crop",
    },
    "機械肩推": {
        "target": "三角肌、三頭肌",
        "steps": ["坐正，調整椅座高度使握把與肩齊", "向上推起至手臂微彎", "緩慢下放回起始位置"],
        "mistakes": ["過度後仰", "推到底時肘部鎖死甩動", "椅座過低，活動範圍不足"],
        "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800&auto=format&fit=crop",
    },
    "啞鈴肩推": {
        "target": "三角肌、三頭肌",
        "steps": ["坐姿或站姿，啞鈴置於肩側，掌心朝前", "向上推起至手臂伸直不鎖死", "控制下放回肩側"],
        "mistakes": ["腰部過度後仰代償", "兩側啞鈴速度不一致"],
        "image_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&auto=format&fit=crop",
    },
    "啞鈴側平舉": {
        "target": "中三角肌",
        "steps": ["站姿，啞鈴置於身側，手肘微彎", "向兩側抬起至與肩同高", "緩慢下放還原"],
        "mistakes": ["聳肩代償", "抬得比肩膀還高", "用甩動借力"],
        "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop",
    },
    "滑輪側平舉": {
        "target": "中三角肌",
        "steps": ["身體側對滑輪機，單手握把", "向外側抬起至肩膀高度", "緩慢控制回到起始位置"],
        "mistakes": ["身體側傾借力", "手肘完全伸直，增加關節壓力"],
        "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop",
    },
    "機械側平舉": {
        "target": "中三角肌",
        "steps": ["坐正，調整椅座使手肘對齊轉軸", "向外推起手臂至肩膀高度", "緩慢還原"],
        "mistakes": ["聳肩代償", "椅座高度沒調好，施力點錯誤"],
        "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop",
    },
    "機械腿推": {
        "target": "股四頭肌、臀大肌、腿後肌",
        "steps": ["坐入機器，雙腳與肩同寬踩於踏板", "彎曲膝蓋至約 90 度", "用力推出，還原時不完全鎖死膝蓋"],
        "mistakes": ["膝蓋內夾", "下背離開椅背", "腳掌位置過高或過低"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop",
    },
    "機械伸腿": {
        "target": "股四頭肌",
        "steps": ["坐正，腳踝置於滾墊下方", "伸直膝蓋，抬起至頂點", "緩慢下放還原"],
        "mistakes": ["甩動借力", "膝蓋鎖死時用力過猛"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop",
    },
    "機械屈腿": {
        "target": "腿後肌",
        "steps": ["俯臥或坐姿，腳踝置於滾墊上方", "彎曲膝蓋，將滾墊拉向臀部", "緩慢伸直還原"],
        "mistakes": ["臀部抬起借力", "動作過快，失去控制"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop",
    },
    "槓鈴深蹲": {
        "target": "股四頭肌、臀大肌、核心",
        "steps": ["槓鈴置於上背，雙腳與肩同寬", "屈髖屈膝下蹲，至大腿與地面平行", "用力站起，回到起始位置"],
        "mistakes": ["膝蓋內夾", "腰部圓背", "腳跟離地"],
        "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop",
    },
    "啞鈴分腿蹲": {
        "target": "股四頭肌、臀大肌",
        "steps": ["後腳置於長凳上，前腳站穩，雙手持啞鈴", "下蹲至前腿大腿與地面平行", "用力站起還原"],
        "mistakes": ["前膝超過腳尖過多", "身體過度前傾", "後腳出力過多，變成後腳主導"],
        "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop",
    },
    "機械臀推": {
        "target": "臀大肌",
        "steps": ["背部靠於椅墊，雙腳踩穩踏板", "用臀部力量向上推起髖部", "緩慢下放還原"],
        "mistakes": ["用下背代償", "頂點沒有夾緊臀部", "腳掌位置過遠或過近"],
        "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop",
    },
    "大腿外展機": {
        "target": "臀中肌",
        "steps": ["坐正，雙腿置於墊片內側", "用力將雙腿向外推開", "緩慢還原"],
        "mistakes": ["上身前傾借力", "動作幅度太快"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop",
    },
    "大腿內收機": {
        "target": "內收肌群",
        "steps": ["坐正，雙腿置於墊片外側", "用力將雙腿向內夾緊", "緩慢還原"],
        "mistakes": ["夾動過快，失去控制", "椅背沒有坐直"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop",
    },
    "啞鈴二頭彎舉": {
        "target": "二頭肌",
        "steps": ["站姿，啞鈴自然垂放身側，掌心朝前", "彎曲手肘，將啞鈴捲起至肩膀", "緩慢下放還原"],
        "mistakes": ["手肘前後晃動借力", "身體後仰甩動"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop",
    },
    "機械二頭彎舉": {
        "target": "二頭肌",
        "steps": ["坐正，手臂置於墊上，握住把手", "彎曲手肘，捲起至頂點", "緩慢下放還原"],
        "mistakes": ["肩膀離開座墊", "動作過快甩動"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop",
    },
    "滑輪三頭下拉": {
        "target": "三頭肌",
        "steps": ["站姿面對滑輪機，握住把手，手肘貼緊身體", "向下推直手臂至完全伸展", "緩慢回到起始位置"],
        "mistakes": ["手肘外開", "身體前傾借力", "只做半程動作"],
        "image_url": "https://images.unsplash.com/photo-1530822847156-5df684618728?w=800&auto=format&fit=crop",
    },
    "機械三頭伸展": {
        "target": "三頭肌",
        "steps": ["坐正，手臂置於墊上，握住把手", "伸直手肘，推起把手", "緩慢彎曲還原"],
        "mistakes": ["肩膀聳起代償", "動作過快甩動"],
        "image_url": "https://images.unsplash.com/photo-1530822847156-5df684618728?w=800&auto=format&fit=crop",
    },
    "機械捲腹": {
        "target": "腹直肌",
        "steps": ["坐正，雙手握把或置於胸前墊片", "收縮腹部，向前捲曲上身", "緩慢回到起始位置"],
        "mistakes": ["用手臂力量拉動", "頸部過度前彎施力"],
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&auto=format&fit=crop",
    },
    "懸垂抬腿": {
        "target": "下腹肌、髖屈肌",
        "steps": ["懸掛於單槓，身體伸直", "收縮腹部，將雙腿抬起至水平或更高", "緩慢放下還原"],
        "mistakes": ["用身體擺盪借力", "只靠髖屈肌，沒有收縮腹部", "下放過快，失去控制"],
        "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&auto=format&fit=crop",
    },
}
TABLE = "workout_logs"
TZ = ZoneInfo("Asia/Taipei")

st.set_page_config(
    page_title="健身紀錄",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── 樣式：大字體、大按鈕（配色取自奧林匹克槓片：深藍 20kg、黃 15kg）──
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&display=swap');
:root { --ink:#14213D; --plate:#F2B705; --line:#E4E7EC; --danger:#B3261E; }

.block-container { max-width: 560px; padding: 1.2rem 1rem 4rem; }

/* 分頁 */
[data-testid="stTabs"] button[role="tab"] {
    font-size: 1.15rem; font-weight: 700; padding: .8rem .3rem;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--plate); height: 3px; }

/* 標籤與下拉選單 */
[data-testid="stWidgetLabel"] p { font-size: 1.15rem; font-weight: 600; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    min-height: 3.6rem; font-size: 1.4rem; font-weight: 600;
}

/* 數字輸入框 */
[data-testid="stNumberInput"] input {
    height: 3.6rem; font-size: 2rem; font-weight: 700; text-align: center;
    font-family: 'Barlow Condensed', sans-serif;
}
[data-testid="stNumberInput"] button { width: 3.2rem; }

/* 休息秒數選擇（水平單選） */
[data-testid="stRadio"] > div { gap: .5rem; }
[data-testid="stRadio"] label {
    border: 2px solid var(--line); border-radius: 10px; padding: .5rem 1rem; font-weight: 600;
}

/* 鍵盤／觸控聚焦時要看得到 */
[data-baseweb="input"]:focus-within,
[data-baseweb="select"]:focus-within { outline: 3px solid var(--ink); outline-offset: 1px; }

/* 主按鈕：完成此組 */
[data-testid="stBaseButton-primary"], button[kind="primary"] {
    min-height: 5rem; border: none; border-radius: 14px; background: var(--plate);
}
[data-testid="stBaseButton-primary"] p, button[kind="primary"] p {
    color: var(--ink); font-size: 1.9rem; font-weight: 800; letter-spacing: .05em;
}

/* 次按鈕（略過休息、取消等） */
[data-testid="stBaseButton-secondary"], button[kind="secondary"] {
    min-height: 3.2rem; border-radius: 12px;
}
[data-testid="stBaseButton-secondary"] p, button[kind="secondary"] p { font-size: 1.1rem; }

/* 今日 / 歷史 清單 */
.exname { font-size: 1.3rem; font-weight: 700; margin: 1.3rem 0 .45rem; }
.exname small { font-size: 1rem; font-weight: 500; opacity: .65; margin-left: .5rem; }
.setrow {
    display: flex; align-items: center; gap: .8rem; margin-bottom: .4rem;
    padding: .7rem 1rem; background: #fff; border-left: 6px solid var(--plate); border-radius: 8px;
}
.setrow.pr { border-left-color: var(--danger); }
.setrow .idx { width: 2rem; font: 700 1.9rem 'Barlow Condensed', sans-serif; flex-shrink: 0; }
.setrow .val { flex: 1; font-size: 1.5rem; font-weight: 700; }
.setrow .val small { font-size: 1rem; font-weight: 500; margin: 0 .15rem; }
.setrow .tm { font-size: 1rem; opacity: .6; flex-shrink: 0; }
.pr-badge {
    font-size: .85rem; font-weight: 700; color: var(--danger);
    border: 1.5px solid var(--danger); border-radius: 999px; padding: .1rem .5rem; margin-right: .2rem;
}
.day-heading {
    font: 700 1.15rem 'Barlow Condensed', sans-serif; font-size: 1.2rem;
    margin: 1.6rem 0 .3rem; padding-bottom: .3rem; border-bottom: 2px solid var(--line);
}

/* 動作教學卡片 */
.tut-image {
    width: 100%; aspect-ratio: 16 / 9; border-radius: 14px; margin-bottom: 1rem;
    display: flex; align-items: center; justify-content: center; flex-direction: column; gap: .3rem;
    background: linear-gradient(135deg, var(--ink), #2A3D66); color: #fff; text-align: center;
}
.tut-image .emoji { font-size: 2.6rem; }
.tut-image .hint { font-size: .85rem; opacity: .75; padding: 0 1.5rem; }
.tut-card {
    background: #fff; border-radius: 14px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    border-left: 6px solid var(--plate);
}
.tut-card h4 { margin: 0 0 .5rem; font-size: 1.1rem; }
.tut-card ol, .tut-card ul { margin: 0; padding-left: 1.3rem; }
.tut-card li { font-size: 1.05rem; line-height: 1.6; margin-bottom: .35rem; }
.tut-card.mistakes { border-left-color: var(--danger); }
.tut-card.mistakes li::marker { color: var(--danger); }
</style>
"""

# ── 休息倒數：純前端 JS，不會讓 Streamlit 每秒重跑 ──────────
TIMER_HTML = """
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&display=swap" rel="stylesheet">
<style>
  body { margin: 0; font-family: -apple-system, 'Noto Sans TC', sans-serif; }
  #box { background: #14213D; color: #fff; border-radius: 14px; padding: 16px 20px 20px; text-align: center; }
  #label { font-size: 18px; font-weight: 600; opacity: .85; }
  #time { font: 700 76px/1.1 'Barlow Condensed', 'Arial Narrow', sans-serif; color: #F2B705; }
  #bar { height: 8px; background: rgba(255,255,255,.2); border-radius: 4px; overflow: hidden; margin-top: 6px; }
  #fill { height: 100%; width: 100%; background: #F2B705; transition: width .25s linear; }
  #box.done { background: #F2B705; color: #14213D; }
  #box.done #time { color: #14213D; }
  #box.done #bar { background: rgba(20,33,61,.2); }
  #box.done #fill { background: #14213D; }
</style>
<div id="box">
  <div id="label">組間休息</div>
  <div id="time">--:--</div>
  <div id="bar"><div id="fill"></div></div>
</div>
<script>
  const TOTAL = __TOTAL__;
  const end = Date.now() + __REMAINING__ * 1000;
  const box = document.getElementById('box');
  const label = document.getElementById('label');
  const timeEl = document.getElementById('time');
  const fill = document.getElementById('fill');
  const pad = n => String(n).padStart(2, '0');

  function tick() {
    const left = Math.max(0, Math.ceil((end - Date.now()) / 1000));
    timeEl.textContent = pad(Math.floor(left / 60)) + ':' + pad(left % 60);
    fill.style.width = (left / TOTAL * 100) + '%';
    if (left <= 0) {
      clearInterval(timer);
      box.classList.add('done');
      label.textContent = '休息結束，開始下一組';
      try { navigator.vibrate && navigator.vibrate([300, 150, 300]); } catch (e) {}
    }
  }
  const timer = setInterval(tick, 250);
  tick();
</script>
"""


def timer_html(remaining: int, total: int) -> str:
	return TIMER_HTML.replace("__TOTAL__", str(total)).replace("__REMAINING__", str(remaining))


# ── Supabase ────────────────────────────────────────────
@st.cache_resource
def get_client() -> Client:
	return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def utc_str(dt: datetime) -> str:
	return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_set(sb: Client, exercise: str, weight: float, reps: int) -> None:
	sb.table(TABLE).insert({"exercise": exercise, "weight_kg": weight, "reps": reps}).execute()


def delete_set(sb: Client, row_id: int) -> None:
	sb.table(TABLE).delete().eq("id", row_id).execute()


def fetch_max_weight(sb: Client, exercise: str) -> float | None:
	res = (
	    sb.table(TABLE)
	    .select("weight_kg")
	    .eq("exercise", exercise)
	    .order("weight_kg", desc=True)
	    .limit(1)
	    .execute()
	)
	return float(res.data[0]["weight_kg"]) if res.data else None


def fetch_today(sb: Client) -> list[dict]:
	start = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
	end = start + timedelta(days=1)
	res = (
	    sb.table(TABLE)
	    .select("id, exercise, weight_kg, reps, created_at")
	    .gte("created_at", utc_str(start))
	    .lt("created_at", utc_str(end))
	    .order("created_at")
	    .execute()
	)
	return res.data or []


def fetch_all(sb: Client) -> list[dict]:
	res = (
	    sb.table(TABLE)
	    .select("id, exercise, weight_kg, reps, created_at")
	    .order("created_at", desc=True)
	    .execute()
	)
	return res.data or []


def to_local(ts: str) -> datetime:
	return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(TZ)


def hhmm(ts: str) -> str:
	return to_local(ts).strftime("%H:%M")


def local_date(ts: str) -> date:
	return to_local(ts).date()


def day_heading(d: date) -> str:
	today = datetime.now(TZ).date()
	if d == today:
		return f"今天・{d.strftime('%m/%d')}"
	if d == today - timedelta(days=1):
		return f"昨天・{d.strftime('%m/%d')}"
	weekday = "一二三四五六日"[d.weekday()]
	return f"{d.strftime('%m/%d')}（週{weekday}）"


GROUP_EMOJI = {
    "胸部 Chest": "🏋️",
    "背部 Back": "🦾",
    "肩部 Shoulders": "🤸",
    "腿部 & 臀部 Legs & Glutes": "🦵",
    "手臂 Arms": "💪",
    "核心 Core": "🔥",
}


def exercise_group(name: str) -> str:
	for group, names in EXERCISE_GROUPS.items():
		if name in names:
			return group
	return ""


# ── 頁面 ────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

try:
	sb = get_client()
except Exception:
	st.error("找不到 Supabase 設定，請在 .streamlit/secrets.toml 加入 SUPABASE_URL 與 SUPABASE_KEY。")
	st.stop()

st.title("健身紀錄")

tab_today, tab_history, tab_progress, tab_tutorial = st.tabs(
    ["今日訓練", "歷史紀錄", "進度圖表", "📚 動作教學"]
)

# ═══════════════════════════════ 今日訓練 ═══════════════════════════════
with tab_today:
	st.caption(datetime.now(TZ).strftime("%Y/%m/%d"))

	muscle_group = st.selectbox("肌群", list(EXERCISE_GROUPS.keys()), key="today_muscle_group")
	exercise = st.selectbox("動作", EXERCISE_GROUPS[muscle_group], key=f"today_exercise_{muscle_group}")

	col_w, col_r = st.columns(2)
	weight = col_w.number_input(
	    "重量 (kg)", min_value=0.0, max_value=1000.0, value=20.0, step=2.5, format="%.1f", key="weight"
	)
	reps = col_r.number_input("次數 (reps)", min_value=1, max_value=200, value=10, step=1, key="reps")

	rest_label = st.radio("休息時間", list(REST_OPTIONS.keys()), index=1, horizontal=True, key="rest_label")

	if st.button("完成此組", type="primary", use_container_width=True):
		try:
			prev_max = fetch_max_weight(sb, exercise)
			log_set(sb, exercise, float(weight), int(reps))
		except Exception as e:
			st.error(f"寫入失敗：{e}")
		else:
			st.session_state["rest_end"] = time.time() + REST_OPTIONS[rest_label]
			st.session_state["rest_total"] = REST_OPTIONS[rest_label]
			st.session_state["just_pr"] = prev_max is None or weight > prev_max

	if st.session_state.get("just_pr"):
		st.balloons()
		st.success("🎉 創下新 PR！這是這個動作目前舉過最重的一次。")
		st.session_state["just_pr"] = False

	# 休息倒數
	rest_end = st.session_state.get("rest_end")
	if rest_end:
		remaining = math.ceil(rest_end - time.time())
		if remaining > 0:
			components.html(timer_html(remaining, st.session_state["rest_total"]), height=150)
			if st.button("略過休息", use_container_width=True):
				st.session_state.pop("rest_end", None)
				st.rerun()
		else:
			st.session_state.pop("rest_end", None)

	st.divider()

	try:
		today_rows = fetch_today(sb)
	except Exception as e:
		st.error(f"讀取失敗：{e}")
		today_rows = []

	if not today_rows:
		st.subheader("今天還沒有紀錄")
		st.caption("選好動作、輸入重量與次數，按「完成此組」開始。")
	else:
		volume = sum(float(r["weight_kg"]) * int(r["reps"]) for r in today_rows)
		st.subheader(f"今天已完成 {len(today_rows)} 組")
		st.caption(f"總訓練量 {volume:,.0f} kg")

		grouped: dict[str, list[dict]] = {}
		for r in today_rows:
			grouped.setdefault(r["exercise"], []).append(r)

		for name, sets in grouped.items():
			parts = [f'<div class="exname">{html.escape(name)}<small>{len(sets)} 組</small></div>']
			for i, r in enumerate(sets, start=1):
				parts.append(
				    f'<div class="setrow"><span class="idx">{i}</span>'
				    f'<span class="val">{float(r["weight_kg"]):g}<small>kg</small>× {int(r["reps"])}</span>'
				    f'<span class="tm">{hhmm(r["created_at"])}</span></div>'
				)
			st.markdown("".join(parts), unsafe_allow_html=True)

# ═══════════════════════════════ 歷史紀錄 ═══════════════════════════════
with tab_history:
	try:
		all_rows = fetch_all(sb)
	except Exception as e:
		st.error(f"讀取失敗：{e}")
		all_rows = []

	if not all_rows:
		st.subheader("還沒有任何歷史紀錄")
		st.caption("在「今日訓練」記錄第一組之後，這裡會顯示所有日期的訓練。")
	else:
		# 每個動作歷史最大重量，用來標記哪一組是 PR
		pr_weight: dict[str, float] = {}
		for r in sorted(all_rows, key=lambda r: r["created_at"]):
			ex = r["exercise"]
			w = float(r["weight_kg"])
			if w >= pr_weight.get(ex, -1):
				pr_weight[ex] = w

		by_day: dict[date, list[dict]] = {}
		for r in all_rows:
			by_day.setdefault(local_date(r["created_at"]), []).append(r)

		for d in sorted(by_day.keys(), reverse=True):
			st.markdown(f'<div class="day-heading">{day_heading(d)}</div>', unsafe_allow_html=True)
			for r in by_day[d]:
				is_pr = float(r["weight_kg"]) == pr_weight.get(r["exercise"]) and float(r["weight_kg"]) > 0
				row_cls = "setrow pr" if is_pr else "setrow"
				badge = '<span class="pr-badge">PR</span>' if is_pr else ""
				col_row, col_btn = st.columns([5, 1])
				with col_row:
					st.markdown(
					    f'<div class="{row_cls}">{badge}'
					    f'<span class="val">{html.escape(r["exercise"])} '
					    f'{float(r["weight_kg"]):g}<small>kg</small>× {int(r["reps"])}</span>'
					    f'<span class="tm">{hhmm(r["created_at"])}</span></div>',
					    unsafe_allow_html=True,
					)
				with col_btn:
					row_id = r["id"]
					if st.session_state.get("confirm_delete") == row_id:
						c1, c2 = st.columns(2)
						if c1.button("✓", key=f"yes_{row_id}", help="確認刪除"):
							try:
								delete_set(sb, row_id)
							except Exception as e:
								st.error(f"刪除失敗：{e}")
							else:
								st.session_state.pop("confirm_delete", None)
								st.rerun()
						if c2.button("✕", key=f"no_{row_id}", help="取消"):
							st.session_state.pop("confirm_delete", None)
							st.rerun()
					else:
						if st.button("刪除", key=f"del_{row_id}"):
							st.session_state["confirm_delete"] = row_id
							st.rerun()

# ═══════════════════════════════ 進度圖表 ═══════════════════════════════
with tab_progress:
	try:
		all_rows_chart = fetch_all(sb)
	except Exception as e:
		st.error(f"讀取失敗：{e}")
		all_rows_chart = []

	known_exercises = sorted({r["exercise"] for r in all_rows_chart} | set(ALL_EXERCISES))
	chart_exercise = st.selectbox("選擇動作", known_exercises, key="chart_exercise")

	rows_for_ex = [r for r in all_rows_chart if r["exercise"] == chart_exercise]

	if not rows_for_ex:
		st.subheader("這個動作還沒有紀錄")
		st.caption("記錄幾組之後，這裡會顯示重量隨時間的變化。")
	else:
		df = pd.DataFrame(rows_for_ex)
		df["date"] = df["created_at"].apply(local_date)
		df["weight_kg"] = df["weight_kg"].astype(float)
		daily_max = df.groupby("date", as_index=False)["weight_kg"].max().sort_values("date")

		latest = daily_max.iloc[-1]["weight_kg"]
		best = daily_max["weight_kg"].max()
		c1, c2 = st.columns(2)
		c1.metric("最近一次最大重量", f"{latest:g} kg")
		c2.metric("歷史最高", f"{best:g} kg")

		fig = px.line(daily_max, x="date", y="weight_kg", markers=True)
		fig.update_traces(line_color="#14213D", marker=dict(size=9, color="#F2B705"))
		fig.update_layout(
		    margin=dict(l=10, r=10, t=10, b=10),
		    xaxis_title=None,
		    yaxis_title="重量 (kg)",
		    plot_bgcolor="white",
		    paper_bgcolor="white",
		    font=dict(size=14),
		)
		fig.update_yaxes(gridcolor="#E4E7EC")
		st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════ 動作教學 ═══════════════════════════════
with tab_tutorial:
	tut_group = st.selectbox("肌群", list(EXERCISE_GROUPS.keys()), key="tutorial_muscle_group")
	tut_exercise = st.selectbox(
	    "動作", EXERCISE_GROUPS[tut_group], key=f"tutorial_exercise_{tut_group}"
	)

	info = TUTORIALS.get(tut_exercise)

	if not info:
		st.info("這個動作還沒有教學內容。")
	else:
		emoji = GROUP_EMOJI.get(exercise_group(tut_exercise), "🏋️")
		if info.get("image_url"):
			st.image(info["image_url"], use_container_width=True, caption=tut_exercise)
		else:
			st.markdown(
			    f'<div class="tut-image"><span class="emoji">{emoji}</span>'
			    f'<span class="hint">尚未設定示範圖片，可在 TUTORIALS 字典中'
			    f'補上「{html.escape(tut_exercise)}」的 image_url</span></div>',
			    unsafe_allow_html=True,
			)

		st.subheader(tut_exercise)
		st.markdown(f"**目標肌群：** {html.escape(info['target'])}")

		steps_html = "".join(f"<li>{html.escape(s)}</li>" for s in info["steps"])
		st.markdown(
		    f'<div class="tut-card"><h4>動作步驟</h4><ol>{steps_html}</ol></div>',
		    unsafe_allow_html=True,
		)

		mistakes_html = "".join(f"<li>{html.escape(m)}</li>" for m in info["mistakes"])
		st.markdown(
		    f'<div class="tut-card mistakes"><h4>關鍵細節 & 常見錯誤</h4><ul>{mistakes_html}</ul></div>',
		    unsafe_allow_html=True,
		)

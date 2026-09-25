import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1. 頁面基本設定與 Custom CSS 美化
# ==========================================
st.set_page_config(
    page_title="ProFit 健身隨身助手",
    page_icon="🏋️‍♂️",
    layout="centered"
)

# 套用客製化 CSS 樣式
st.markdown("""
    <style>
    /* 全域背景與字型優化 */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* 標題與 Header 美化 */
    h1 {
        color: #1e293b;
        font-weight: 800 !important;
        text-align: center;
        padding-bottom: 0.5rem;
    }
    
    /* 卡片式容器樣式 */
    .css-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    /* 完成卡片特別樣式 */
    .finish-card {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
    }
    
    /* 按鈕樣式強化 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        background: linear-gradient(90deg, #2563eb, #1d4ed8);
        border: none;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    
    /* Tabs 標籤頁美化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 6px;
        font-weight: 600;
        color: #475569;
    }

    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #2563eb !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料庫與全域設定
# ==========================================
EXERCISE_GROUPS = {
    "胸部 Chest": ["機關胸推", "槓鈴臥推", "啞鈴臥推", "上斜啞鈴臥推", "夾胸機", "雙槓體撐"],
    "背部 Back": ["滑輪下拉", "座姿滑輪划船", "槓鈴划船", "單臂啞鈴划船", "引體向上", "反向飛鳥/後三角機"],
    "肩膀 Shoulders": ["機械肩推", "啞鈴肩推", "啞鈴側平舉", "滑輪側平舉", "機械側平舉"],
    "腿部 Legs": ["機械腿推", "機械伸腿", "機械屈腿", "槓鈴深蹲", "啞鈴分腿蹲", "機械臀推", "大腿外展機", "大腿內收機"],
    "手臂 Arms": ["啞鈴二頭彎舉", "機械二頭彎舉", "滑輪三頭下拉", "機械三頭伸展"],
    "核心 Core": ["機械捲腹", "懸垂抬腿"]
}

TUTORIALS = {
    "機關胸推": {
        "target": "胸大肌、三頭肌、前三角肌",
        "steps": ["調整椅座高度，握把與胸線齊平，背部貼緊椅背", "吐氣將握把往前推出，手肘不完全鎖死", "吸氣緩慢還原，感受胸肌伸展"],
        "mistakes": ["聳肩", "椅座高度沒調好，導致握把與胸口不同高", "推到底時手肘鎖死甩動"],
        "link": "https://www.youtube.com/results?search_query=坐姿機械胸推+教學"
    },
    "槓鈴臥推": {
        "target": "胸大肌、三頭肌、前三角肌",
        "steps": ["躺平於臥推椅，握距略寬於肩，肩胛骨下壓內收，雙腳踩穩地面", "槓鈴下降至胸口下緣，手肘約呈 45 度角", "用力推起，回到起始位置"],
        "mistakes": ["下背過度拱起", "槓鈴在胸口彈震借力", "手肘外展呈 90 度，增加肩關節壓力"],
        "link": "https://www.youtube.com/results?search_query=槓鈴臥推+教學"
    },
    "啞鈴臥推": {
        "target": "胸大肌、三頭肌",
        "steps": ["平躺長凳，雙手持啞鈴於胸側，掌心朝前", "向上推起啞鈴至手臂微彎，不完全鎖死", "控制速度下放回起始位置"],
        "mistakes": ["兩側啞鈴高度不對稱", "下放過快、失去控制", "肩胛骨沒有固定夾緊"],
        "link": "https://www.youtube.com/results?search_query=啞鈴臥推+教學"
    },
    "上斜啞鈴臥推": {
        "target": "上胸、前三角肌",
        "steps": ["將長凳調至約 30–45 度，啞鈴放大腿上再躺下", "推起啞鈴至最高點，手肘不鎖死", "緩慢下放到胸部上緣兩側"],
        "mistakes": ["角度調太高，變成肩推", "下放時肩胛前引", "手肘過度外張"],
        "link": "https://www.youtube.com/results?search_query=上斜啞鈴臥推+教學"
    },
    "夾胸機": {
        "target": "胸大肌內側",
        "steps": ["坐正，手肘輕靠把手，微彎曲", "水平夾向身體中線，感受胸肌收縮", "緩慢打開還原，不要完全放鬆卸力"],
        "mistakes": ["用力甩動而非穩定夾胸", "聳肩代償", "活動範圍拉太開造成肩關節壓力"],
        "link": "https://www.youtube.com/results?search_query=蝴蝶機夾胸+教學"
    },
    "雙槓體撐": {
        "target": "下胸、三頭肌",
        "steps": ["雙手撐於握把，身體懸空，手臂伸直", "身體微前傾，手肘彎曲下降至約 90 度", "推起回到起始位置"],
        "mistakes": ["下降過深，造成肩關節壓力", "身體過度前傾或後仰，失去控制"],
        "link": "https://www.youtube.com/results?search_query=雙槓體撐+教學"
    },
    "滑輪下拉": {
        "target": "闊背肌、二頭肌",
        "steps": ["坐好固定大腿，寬握把手", "向下拉至鎖骨上緣，夾背挺胸", "緩慢回到起始位置，感受背部伸展"],
        "mistakes": ["身體後仰借力甩動", "拉到脖子後方", "聳肩、沒有夾背"],
        "link": "https://www.youtube.com/results?search_query=滑輪下拉+教學"
    },
    "座姿滑輪划船": {
        "target": "中背、闊背肌、二頭肌",
        "steps": ["坐穩，雙腳踩踏板，膝蓋微彎，手臂伸直握把手", "身體挺直，將把手拉向腹部", "緩慢向前伸展還原"],
        "mistakes": ["身體前後晃動借力", "圓背駝背", "拉到胸口而非腹部"],
        "link": "https://www.youtube.com/results?search_query=坐姿划船+教學"
    },
    "槓鈴划船": {
        "target": "中背、闊背肌",
        "steps": ["屈髖前傾約 45 度，握槓於身前，背部打直", "將槓拉向下腹部，夾緊肩胛骨", "緩慢下放還原"],
        "mistakes": ["腰部拱起或圓背", "用甩動借力", "站姿太直，變成聳肩上提"],
        "link": "https://www.youtube.com/results?search_query=槓鈴划船+教學"
    },
    "單臂啞鈴划船": {
        "target": "中背、闊背肌",
        "steps": ["單膝與單手撐於長凳，另一手持啞鈴", "將啞鈴拉向髖部，手肘貼近身體", "緩慢下放伸展"],
        "mistakes": ["軀幹旋轉借力", "手肘外開，變成側平舉動作"],
        "link": "https://www.youtube.com/results?search_query=單臂啞鈴划船+教學"
    },
    "引體向上": {
        "target": "闊背肌、二頭肌",
        "steps": ["寬握單槓，身體懸掛，核心收緊", "拉起身體，直到下巴過槓", "緩慢下放到手臂完全伸直"],
        "mistakes": ["擺盪借力", "只做半程，沒有完全伸展", "聳肩代償"],
        "link": "https://www.youtube.com/results?search_query=引體向上+教學"
    },
    "反向飛鳥/後三角機": {
        "target": "後三角肌、菱形肌",
        "steps": ["胸部貼靠椅背，握住把手，手臂微彎", "向外向後展開手臂，夾緊肩胛骨", "緩慢回到起始位置"],
        "mistakes": ["用手臂力量而非背部發力", "身體離開椅背借力"],
        "link": "https://www.youtube.com/results?search_query=反向飛鳥+教學"
    },
    "機械肩推": {
        "target": "三角肌、三頭肌",
        "steps": ["坐正，調整椅座高度使握把與肩齊", "向上推起至手臂微彎", "緩慢下放回起始位置"],
        "mistakes": ["過度後仰", "推到底時肘部鎖死甩動", "椅座過低，活動範圍不足"],
        "link": "https://www.youtube.com/results?search_query=坐姿機械肩推+教學"
    },
    "啞鈴肩推": {
        "target": "三角肌、三頭肌",
        "steps": ["坐姿或站姿，啞鈴置於肩側，掌心朝前", "向上推起至手臂伸直不鎖死", "控制下放回肩側"],
        "mistakes": ["腰部過度後仰代償", "兩側啞鈴速度不一致"],
        "link": "https://www.youtube.com/results?search_query=啞鈴肩推+教學"
    },
    "啞鈴側平舉": {
        "target": "中三角肌",
        "steps": ["站姿，啞鈴置於身側，手肘微彎", "向兩側抬起至與肩同高", "緩慢下放還原"],
        "mistakes": ["聳肩代償", "抬得比肩膀還高", "用甩動借力"],
        "link": "https://www.youtube.com/results?search_query=啞鈴側平舉+教學"
    },
    "滑輪側平舉": {
        "target": "中三角肌",
        "steps": ["身體側對滑輪機，單手握把", "向外側抬起至肩膀高度", "緩慢控制回到起始位置"],
        "mistakes": ["身體側傾借力", "手肘完全伸直，增加關節壓力"],
        "link": "https://www.youtube.com/results?search_query=滑輪側平舉+教學"
    },
    "機械側平舉": {
        "target": "中三角肌",
        "steps": ["坐正，調整椅座使手肘對齊轉軸", "向外推起手臂至肩膀高度", "緩慢還原"],
        "mistakes": ["聳肩代償", "椅座高度沒調好，施力點錯誤"],
        "link": "https://www.youtube.com/results?search_query=機械側平舉+教學"
    },
    "機械腿推": {
        "target": "股四頭肌、臀大肌、腿後肌",
        "steps": ["坐入機器，雙腳與肩同寬踩於踏板", "彎曲膝蓋至約 90 度", "用力推出，還原時不完全鎖死膝蓋"],
        "mistakes": ["膝蓋內夾", "下背離開椅背", "腳掌位置過高或過低"],
        "link": "https://www.youtube.com/results?search_query=機械腿推+Leg+Press+教學"
    },
    "機械伸腿": {
        "target": "股四頭肌",
        "steps": ["坐正，腳踝置於滾墊下方", "伸直膝蓋，抬起至頂點", "緩慢下放還原"],
        "mistakes": ["甩動借力", "膝蓋鎖死時用力過猛"],
        "link": "https://www.youtube.com/results?search_query=機械伸腿+Leg+Extension+教學"
    },
    "機械屈腿": {
        "target": "腿後肌",
        "steps": ["俯臥或坐姿，腳踝置於滾墊上方", "彎曲膝蓋，將滾墊拉向臀部", "緩慢伸直還原"],
        "mistakes": ["臀部抬起借力", "動作過快，失去控制"],
        "link": "https://www.youtube.com/results?search_query=機械屈腿+Leg+Curl+教學"
    },
    "槓鈴深蹲": {
        "target": "股四頭肌、臀大肌、核心",
        "steps": ["槓鈴置於上背，雙腳與肩同寬", "屈髖屈膝下蹲，至大腿與地面平行", "用力站起，回到起始位置"],
        "mistakes": ["膝蓋內夾", "腰部圓背", "腳跟離地"],
        "link": "https://www.youtube.com/results?search_query=槓鈴深蹲+教學"
    },
    "啞鈴分腿蹲": {
        "target": "股四頭肌、臀大肌",
        "steps": ["後腳置於長凳上，前腳站穩，雙手持啞鈴", "下蹲至前腿大腿與地面平行", "用力站起還原"],
        "mistakes": ["前膝超過腳尖過多", "身體過度前傾", "後腳出力過多，變成後腳主導"],
        "link": "https://www.youtube.com/results?search_query=保加利亞分腿蹲+教學"
    },
    "機械臀推": {
        "target": "臀大肌",
        "steps": ["背部靠於椅墊，雙腳踩穩踏板", "用臀部力量向上推起髖部", "緩慢下放還原"],
        "mistakes": ["用下背代償", "頂點沒有夾緊臀部", "腳掌位置過遠或過近"],
        "link": "https://www.youtube.com/results?search_query=臀推+Hip+Thrust+教學"
    },
    "大腿外展機": {
        "target": "臀中肌",
        "steps": ["坐正，雙腿置於墊片內側", "用力將雙腿向外推開", "緩慢還原"],
        "mistakes": ["上身前傾借力", "動作幅度太快"],
        "link": "https://www.youtube.com/results?search_query=大腿外展機+教學"
    },
    "大腿內收機": {
        "target": "內收肌群",
        "steps": ["坐正，雙腿置於墊片外側", "用力將雙腿向內夾緊", "緩慢還原"],
        "mistakes": ["夾動過快，失去控制", "椅背沒有坐直"],
        "link": "https://www.youtube.com/results?search_query=大腿內收機+教學"
    },
    "啞鈴二頭彎舉": {
        "target": "二頭肌",
        "steps": ["站姿，啞鈴自然垂放身側，掌心朝前", "彎曲手肘，將啞鈴捲起至肩膀", "緩慢下放還原"],
        "mistakes": ["手肘前後晃動借力", "身體後仰甩動"],
        "link": "https://www.youtube.com/results?search_query=啞鈴二頭彎舉+教學"
    },
    "機械二頭彎舉": {
        "target": "二頭肌",
        "steps": ["坐正，手臂置於墊上，握住把手", "彎曲手肘，捲起至頂點", "緩慢下放還原"],
        "mistakes": ["肩膀離開座墊", "動作過快甩動"],
        "link": "https://www.youtube.com/results?search_query=機械二頭彎舉+教學"
    },
    "滑輪三頭下拉": {
        "target": "三頭肌",
        "steps": ["站姿面對滑輪機，握住把手，手肘貼緊身體", "向下推直手臂至完全伸展", "緩慢回到起始位置"],
        "mistakes": ["手肘外開", "身體前傾借力", "只做半程動作"],
        "link": "https://www.youtube.com/results?search_query=滑輪三頭下拉+教學"
    },
    "機械三頭伸展": {
        "target": "三頭肌",
        "steps": ["坐正，手臂置於墊上，握住把手", "伸直手肘，推起把手", "緩慢彎曲還原"],
        "mistakes": ["肩膀聳起代償", "動作過快甩動"],
        "link": "https://www.youtube.com/results?search_query=機械三頭伸展+教學"
    },
    "機械捲腹": {
        "target": "腹直肌",
        "steps": ["坐正，雙手握把或置於胸前墊片", "收縮腹部，向前捲曲上身", "緩慢回到起始位置"],
        "mistakes": ["用手臂力量拉動", "頸部過度前彎施力"],
        "link": "https://www.youtube.com/results?search_query=機械捲腹+教學"
    },
    "懸垂抬腿": {
        "target": "下腹肌、髖屈肌",
        "steps": ["懸掛於單槓，身體伸直", "收縮腹部，將雙腿抬起至水平或更高", "緩慢放下還原"],
        "mistakes": ["用身體擺盪借力", "只靠髖屈肌，沒有收縮腹部", "下放過快，失去控制"],
        "link": "https://www.youtube.com/results?search_query=懸垂抬腿+教學"
    }
}

if "workout_logs" not in st.session_state:
    st.session_state["workout_logs"] = []

if "finished_dates" not in st.session_state:
    st.session_state["finished_dates"] = set()

# ==========================================
# 3. 頂部 App 標題與數據摘要儀表板
# ==========================================
st.markdown("<h1>🏋️‍♂️ ProFit 健身隨身助手</h1>", unsafe_allow_html=True)

# 頂部快速數據儀表板
logs_count = len(st.session_state["workout_logs"])
unique_exercises = len(set(log["exercise"] for log in st.session_state["workout_logs"])) if logs_count > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("累積紀錄組數", f"{logs_count} 組")
m2.metric("已解鎖動作", f"{unique_exercises} 種")
m3.metric("完成天數", f"{len(st.session_state['finished_dates'])} 天")

st.write("")

# ==========================================
# 4. 主要分頁區塊
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📝 今日訓練", "📜 歷史紀錄", "📊 進度圖表", "📚 動作教學"])

# ------------------------------------------
# Tab 1: 今日訓練
# ------------------------------------------
with tab1:
    today_date = st.date_input("選擇訓練日期", datetime.date.today())
    date_str = str(today_date)
    
    # 篩選出選取日期的紀錄
    today_logs = [log for log in st.session_state["workout_logs"] if log["date"] == date_str]
    
    # 檢查該日期是否已經標記完成
    is_finished = date_str in st.session_state["finished_dates"]
    
    # 若今日已完成，顯示結算榮譽卡片
    if is_finished:
        total_sets = len(today_logs)
        total_volume = sum(log["weight"] * log["reps"] for log in today_logs)
        exercises_done = list(set(log["exercise"] for log in today_logs))
        
        st.markdown(f"""
            <div class="finish-card">
                <h2>🎉 {date_str} 訓練圓滿完成！</h2>
                <p style="font-size: 1.1rem; margin-top: 10px;">今天表現太棒了，好好補充蛋白質與休息！</p>
                <hr style="border-color: rgba(255,255,255,0.3);">
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div><strong>總組數</strong><br><span style="font-size: 1.5rem;">{total_sets} 組</span></div>
                    <div><strong>總訓練量 (Volume)</strong><br><span style="font-size: 1.5rem;">{total_volume:,.0f} kg</span></div>
                    <div><strong>完成動作</strong><br><span style="font-size: 1.5rem;">{len(exercises_done)} 個</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 解除完成狀態（繼續編輯今日訓練）"):
            st.session_state["finished_dates"].remove(date_str)
            st.rerun()

    # 新增組數的卡片區塊
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("➕ 新增訓練組數")
    
    col_g, col_e = st.columns(2)
    with col_g:
        selected_group = st.selectbox("肌群部位", list(EXERCISE_GROUPS.keys()))
    with col_e:
        exercises_in_group = EXERCISE_GROUPS[selected_group]
        selected_exercise = st.selectbox("訓練動作", exercises_in_group)
    
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("負重 (kg)", min_value=0.0, step=2.5)
    with col2:
        reps = st.number_input("完成次數", min_value=1, step=1)
        
    notes = st.text_input("心得 / 筆記 (可選)", "", placeholder="例如：最後一組差點力竭、握距調寬一點")
    
    if st.button("寫入紀錄", type="primary"):
        new_log = {
            "date": date_str,
            "group": selected_group,
            "exercise": selected_exercise,
            "weight": weight,
            "reps": reps,
            "notes": notes
        }
        st.session_state["workout_logs"].append(new_log)
        st.toast(f"✅ 已成功紀錄：{selected_exercise} {weight}kg x {reps}次", icon="💪")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 顯示當天即時訓練小結與「完成訓練」按鈕
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader(f"📋 {date_str} 當日已記錄組數 ({len(today_logs)} 組)")
    
    if today_logs:
        df_today = pd.DataFrame(today_logs)[["group", "exercise", "weight", "reps", "notes"]]
        df_today.columns = ["肌群", "動作", "重量(kg)", "次數", "備註"]
        st.dataframe(df_today, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        # 訓練完成按鈕
        if not is_finished:
            if st.button("🏆 完成今日訓練（結算成果）"):
                st.session_state["finished_dates"].add(date_str)
                st.balloons()  # 慶祝彩色氣球動畫
                st.rerun()
    else:
        st.info("今日尚未新增任何訓練組數，開始第一組吧！")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------
# Tab 2: 歷史紀錄
# ------------------------------------------
with tab2:
    st.subheader("📜 歷史訓練清單")
    if st.session_state["workout_logs"]:
        df = pd.DataFrame(st.session_state["workout_logs"])
        df_display = df.rename(columns={
            "date": "日期",
            "group": "肌群",
            "exercise": "動作",
            "weight": "重量(kg)",
            "reps": "次數",
            "notes": "備註"
        })
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("💡 目前尚無訓練紀錄，快去「今日訓練」新增第一組吧！")

# ------------------------------------------
# Tab 3: 進度圖表
# ------------------------------------------
with tab3:
    st.subheader("📈 重量突破分析")
    if st.session_state["workout_logs"]:
        df = pd.DataFrame(st.session_state["workout_logs"])
        chart_exercise = st.selectbox("請選擇要分析的動作", df["exercise"].unique())
        filtered_df = df[df["exercise"] == chart_exercise]
        
        if not filtered_df.empty:
            st.line_chart(filtered_df.set_index("date")["weight"])
        else:
            st.warning("⚠️ 該動作目前尚無數據可供畫圖")
    else:
        st.info("💡 尚未累積足夠數據，完成訓練後即可檢視趨勢圖！")

# ------------------------------------------
# Tab 4: 動作教學
# ------------------------------------------
with tab4:
    st.subheader("📚 專業健身指南")
    
    col_tg, col_te = st.columns(2)
    with col_tg:
        t_group = st.selectbox("選擇肌群", list(EXERCISE_GROUPS.keys()), key="t_group")
    with col_te:
        t_exercise = st.selectbox("選擇動作", EXERCISE_GROUPS[t_group], key="t_exercise")
    
    if t_exercise in TUTORIALS:
        info = TUTORIALS[t_exercise]
        
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown(f"### 🏋️ {t_exercise}")
        st.markdown(f"**🎯 目標肌群：** `{info['target']}`")
        
        st.markdown("#### 🔹 動作要領")
        for idx, step in enumerate(info["steps"], 1):
            st.write(f"**{idx}.** {step}")
            
        st.markdown("#### ⚠️ 常見錯誤")
        for mistake in info["mistakes"]:
            st.write(f"• {mistake}")
            
        st.markdown("---")
        st.link_button(f"🎥 觀看【{t_exercise}】完整影音教學", info["link"], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🚧 該動作教學準備中...")

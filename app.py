import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1. 資料庫與全域設定
# ==========================================
st.set_page_config(
    page_title="健身紀錄 App",
    page_icon="🏋️",
    layout="centered"
)

# 各肌群對應動作清單
EXERCISE_GROUPS = {
    "胸部 Chest": ["機關胸推", "槓鈴臥推", "啞鈴臥推", "上斜啞鈴臥推", "夾胸機", "雙槓體撐"],
    "背部 Back": ["滑輪下拉", "座姿滑輪划船", "槓鈴划船", "單臂啞鈴划船", "引體向上", "反向飛鳥/後三角機"],
    "肩膀 Shoulders": ["機械肩推", "啞鈴肩推", "啞鈴側平舉", "滑輪側平舉", "機械側平舉"],
    "腿部 Legs": ["機械腿推", "機械伸腿", "機械屈腿", "槓鈴深蹲", "啞鈴分腿蹲", "機械臀推", "大腿外展機", "大腿內收機"],
    "手臂 Arms": ["啞鈴二頭彎舉", "機械二頭彎舉", "滑輪三頭下拉", "機械三頭伸展"],
    "核心 Core": ["機械捲腹", "懸垂抬腿"]
}

# 動作教學內容（採用高穩定度 CDN 圖片連結）
TUTORIALS = {
    "機關胸推": {
        "target": "胸大肌、三頭肌、前三角肌",
        "steps": ["調整椅座高度，握把與胸線齊平，背部貼緊椅背", "吐氣將握把往前推出，手肘不完全鎖死", "吸氣緩慢還原，感受胸肌伸展"],
        "mistakes": ["聳肩", "椅座高度沒調好，導致握把與胸口不同高", "推到底時手肘鎖死甩動"],
        "image_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&auto=format&fit=crop"
    },
    "槓鈴臥推": {
        "target": "胸大肌、三頭肌、前三角肌",
        "steps": ["躺平於臥推椅，握距略寬於肩，肩胛骨下壓內收，雙腳踩穩地面", "槓鈴下降至胸口下緣，手肘約呈 45 度角", "用力推起，回到起始位置"],
        "mistakes": ["下背過度拱起", "槓鈴在胸口彈震借力", "手肘外展呈 90 度，增加肩關節壓力"],
        "image_url": "https://images.unsplash.com/photo-1534367507873-d2d7e24c797f?w=800&auto=format&fit=crop"
    },
    "啞鈴臥推": {
        "target": "胸大肌、三頭肌",
        "steps": ["平躺長凳，雙手持啞鈴於胸側，掌心朝前", "向上推起啞鈴至手臂微彎，不完全鎖死", "控制速度下放回起始位置"],
        "mistakes": ["兩側啞鈴高度不對稱", "下放過快、失去控制", "肩胛骨沒有固定夾緊"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop"
    },
    "上斜啞鈴臥推": {
        "target": "上胸、前三角肌",
        "steps": ["將長凳調至約 30–45 度，啞鈴放大腿上再躺下", "推起啞鈴至最高點，手肘不鎖死", "緩慢下放到胸部上緣兩側"],
        "mistakes": ["角度調太高，變成肩推", "下放時肩胛前引", "手肘過度外張"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop"
    },
    "夾胸機": {
        "target": "胸大肌內側",
        "steps": ["坐正，手肘輕靠把手，微彎曲", "水平夾向身體中線，感受胸肌收縮", "緩慢打開還原，不要完全放鬆卸力"],
        "mistakes": ["用力甩動而非穩定夾胸", "聳肩代償", "活動範圍拉太開造成肩關節壓力"],
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&auto=format&fit=crop"
    },
    "雙槓體撐": {
        "target": "下胸、三頭肌",
        "steps": ["雙手撐於握把，身體懸空，手臂伸直", "身體微前傾，手肘彎曲下降至約 90 度", "推起回到起始位置"],
        "mistakes": ["下降過深，造成肩關節壓力", "身體過度前傾或後仰，失去控制"],
        "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&auto=format&fit=crop"
    },
    "滑輪下拉": {
        "target": "闊背肌、二頭肌",
        "steps": ["坐好固定大腿，寬握把手", "向下拉至鎖骨上緣，夾背挺胸", "緩慢回到起始位置，感受背部伸展"],
        "mistakes": ["身體後仰借力甩動", "拉到脖子後方", "聳肩、沒有夾背"],
        "image_url": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=800&auto=format&fit=crop"
    },
    "座姿滑輪划船": {
        "target": "中背、闊背肌、二頭肌",
        "steps": ["坐穩，雙腳踩踏板，膝蓋微彎，手臂伸直握把手", "身體挺直，將把手拉向腹部", "緩慢向前伸展還原"],
        "mistakes": ["身體前後晃動借力", "圓背駝背", "拉到胸口而非腹部"],
        "image_url": "https://images.unsplash.com/photo-1521804906057-1df8fdb718b7?w=800&auto=format&fit=crop"
    },
    "槓鈴划船": {
        "target": "中背、闊背肌",
        "steps": ["屈髖前傾約 45 度，握槓於身前，背部打直", "將槓拉向下腹部，夾緊肩胛骨", "緩慢下放還原"],
        "mistakes": ["腰部拱起或圓背", "用甩動借力", "站姿太直，變成聳肩上提"],
        "image_url": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800&auto=format&fit=crop"
    },
    "單臂啞鈴划船": {
        "target": "中背、闊背肌",
        "steps": ["單膝與單手撐於長凳，另一手持啞鈴", "將啞鈴拉向髖部，手肘貼近身體", "緩慢下放伸展"],
        "mistakes": ["軀幹旋轉借力", "手肘外開，變成側平舉動作"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop"
    },
    "引體向上": {
        "target": "闊背肌、二頭肌",
        "steps": ["寬握單槓，身體懸掛，核心收緊", "拉起身體，直到下巴過槓", "緩慢下放到手臂完全伸直"],
        "mistakes": ["擺盪借力", "只做半程，沒有完全伸展", "聳肩代償"],
        "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&auto=format&fit=crop"
    },
    "反向飛鳥/後三角機": {
        "target": "後三角肌、菱形肌",
        "steps": ["胸部貼靠椅背，握住把手，手臂微彎", "向外向後展開手臂，夾緊肩胛骨", "緩慢回到起始位置"],
        "mistakes": ["用手臂力量而非背部發力", "身體離開椅背借力"],
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&auto=format&fit=crop"
    },
    "機械肩推": {
        "target": "三角肌、三頭肌",
        "steps": ["坐正，調整椅座高度使握把與肩齊", "向上推起至手臂微彎", "緩慢下放回起始位置"],
        "mistakes": ["過度後仰", "推到底時肘部鎖死甩動", "椅座過低，活動範圍不足"],
        "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800&auto=format&fit=crop"
    },
    "啞鈴肩推": {
        "target": "三角肌、三頭肌",
        "steps": ["坐姿或站姿，啞鈴置於肩側，掌心朝前", "向上推起至手臂伸直不鎖死", "控制下放回肩側"],
        "mistakes": ["腰部過度後仰代償", "兩側啞鈴速度不一致"],
        "image_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&auto=format&fit=crop"
    },
    "啞鈴側平舉": {
        "target": "中三角肌",
        "steps": ["站姿，啞鈴置於身側，手肘微彎", "向兩側抬起至與肩同高", "緩慢下放還原"],
        "mistakes": ["聳肩代償", "抬得比肩膀還高", "用甩動借力"],
        "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop"
    },
    "滑輪側平舉": {
        "target": "中三角肌",
        "steps": ["身體側對滑輪機，單手握把", "向外側抬起至肩膀高度", "緩慢控制回到起始位置"],
        "mistakes": ["身體側傾借力", "手肘完全伸直，增加關節壓力"],
        "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop"
    },
    "機械側平舉": {
        "target": "中三角肌",
        "steps": ["坐正，調整椅座使手肘對齊轉軸", "向外推起手臂至肩膀高度", "緩慢還原"],
        "mistakes": ["聳肩代償", "椅座高度沒調好，施力點錯誤"],
        "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop"
    },
    "機械腿推": {
        "target": "股四頭肌、臀大肌、腿後肌",
        "steps": ["坐入機器，雙腳與肩同寬踩於踏板", "彎曲膝蓋至約 90 度", "用力推出，還原時不完全鎖死膝蓋"],
        "mistakes": ["膝蓋內夾", "下背離開椅背", "腳掌位置過高或過低"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop"
    },
    "機械伸腿": {
        "target": "股四頭肌",
        "steps": ["坐正，腳踝置於滾墊下方", "伸直膝蓋，抬起至頂點", "緩慢下放還原"],
        "mistakes": ["甩動借力", "膝蓋鎖死時用力過猛"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop"
    },
    "機械屈腿": {
        "target": "腿後肌",
        "steps": ["俯臥或坐姿，腳踝置於滾墊上方", "彎曲膝蓋，將滾墊拉向臀部", "緩慢伸直還原"],
        "mistakes": ["臀部抬起借力", "動作過快，失去控制"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop"
    },
    "槓鈴深蹲": {
        "target": "股四頭肌、臀大肌、核心",
        "steps": ["槓鈴置於上背，雙腳與肩同寬", "屈髖屈膝下蹲，至大腿與地面平行", "用力站起，回到起始位置"],
        "mistakes": ["膝蓋內夾", "腰部圓背", "腳跟離地"],
        "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop"
    },
    "啞鈴分腿蹲": {
        "target": "股四頭肌、臀大肌",
        "steps": ["後腳置於長凳上，前腳站穩，雙手持啞鈴", "下蹲至前腿大腿與地面平行", "用力站起還原"],
        "mistakes": ["前膝超過腳尖過多", "身體過度前傾", "後腳出力過多，變成後腳主導"],
        "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop"
    },
    "機械臀推": {
        "target": "臀大肌",
        "steps": ["背部靠於椅墊，雙腳踩穩踏板", "用臀部力量向上推起髖部", "緩慢下放還原"],
        "mistakes": ["用下背代償", "頂點沒有夾緊臀部", "腳掌位置過遠或過近"],
        "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop"
    },
    "大腿外展機": {
        "target": "臀中肌",
        "steps": ["坐正，雙腿置於墊片內側", "用力將雙腿向外推開", "緩慢還原"],
        "mistakes": ["上身前傾借力", "動作幅度太快"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop"
    },
    "大腿內收機": {
        "target": "內收肌群",
        "steps": ["坐正，雙腿置於墊片外側", "用力將雙腿向內夾緊", "緩慢還原"],
        "mistakes": ["夾動過快，失去控制", "椅背沒有坐直"],
        "image_url": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=800&auto=format&fit=crop"
    },
    "啞鈴二頭彎舉": {
        "target": "二頭肌",
        "steps": ["站姿，啞鈴自然垂放身側，掌心朝前", "彎曲手肘，將啞鈴捲起至肩膀", "緩慢下放還原"],
        "mistakes": ["手肘前後晃動借力", "身體後仰甩動"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop"
    },
    "機械二頭彎舉": {
        "target": "二頭肌",
        "steps": ["坐正，手臂置於墊上，握住把手", "彎曲手肘，捲起至頂點", "緩慢下放還原"],
        "mistakes": ["肩膀離開座墊", "動作過快甩動"],
        "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop"
    },
    "滑輪三頭下拉": {
        "target": "三頭肌",
        "steps": ["站姿面對滑輪機，握住把手，手肘貼緊身體", "向下推直手臂至完全伸展", "緩慢回到起始位置"],
        "mistakes": ["手肘外開", "身體前傾借力", "只做半程動作"],
        "image_url": "https://images.unsplash.com/photo-1530822847156-5df684618728?w=800&auto=format&fit=crop"
    },
    "機械三頭伸展": {
        "target": "三頭肌",
        "steps": ["坐正，手臂置於墊上，握住把手", "伸直手肘，推起把手", "緩慢彎曲還原"],
        "mistakes": ["肩膀聳起代償", "動作過快甩動"],
        "image_url": "https://images.unsplash.com/photo-1530822847156-5df684618728?w=800&auto=format&fit=crop"
    },
    "機械捲腹": {
        "target": "腹直肌",
        "steps": ["坐正，雙手握把或置於胸前墊片", "收縮腹部，向前捲曲上身", "緩慢回到起始位置"],
        "mistakes": ["用手臂力量拉動", "頸部過度前彎施力"],
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&auto=format&fit=crop"
    },
    "懸垂抬腿": {
        "target": "下腹肌、髖屈肌",
        "steps": ["懸掛於單槓，身體伸直", "收縮腹部，將雙腿抬起至水平或更高", "緩慢放下還原"],
        "mistakes": ["用身體擺盪借力", "只靠髖屈肌，沒有收縮腹部", "下放過快，失去控制"],
        "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=800&auto=format&fit=crop"
    }
}

# 初始化 Session State
if "workout_logs" not in st.session_state:
    st.session_state["workout_logs"] = []

# ==========================================
# 2. 頁面標題與分頁標籤
# ==========================================
st.title("🏋️ 健身紀錄")

tab1, tab2, tab3, tab4 = st.tabs(["今日訓練", "歷史紀錄", "進度圖表", "📚 動作教學"])

# ==========================================
# Tab 1: 今日訓練
# ==========================================
with tab1:
    today_date = st.date_input("日期", datetime.date.today())
    
    selected_group = st.selectbox("肌群", list(EXERCISE_GROUPS.keys()))
    exercises_in_group = EXERCISE_GROUPS[selected_group]
    selected_exercise = st.selectbox("動作", exercises_in_group)
    
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("重量 (kg)", min_value=0.0, step=2.5)
    with col2:
        reps = st.number_input("次數", min_value=1, step=1)
        
    notes = st.text_input("備註 (可選)", "")
    
    if st.button("新增紀錄", type="primary"):
        new_log = {
            "date": str(today_date),
            "group": selected_group,
            "exercise": selected_exercise,
            "weight": weight,
            "reps": reps,
            "notes": notes
        }
        st.session_state["workout_logs"].append(new_log)
        st.success(f"已新增：{selected_exercise} - {weight} kg x {reps} 次")

# ==========================================
# Tab 2: 歷史紀錄
# ==========================================
with tab2:
    st.subheader("歷史記錄清單")
    if st.session_state["workout_logs"]:
        df = pd.DataFrame(st.session_state["workout_logs"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前尚無訓練紀錄，請在「今日訓練」標籤頁中新增！")

# ==========================================
# Tab 3: 進度圖表
# ==========================================
with tab3:
    st.subheader("訓練趨勢")
    if st.session_state["workout_logs"]:
        df = pd.DataFrame(st.session_state["workout_logs"])
        chart_exercise = st.selectbox("選擇要檢視的動作", df["exercise"].unique())
        filtered_df = df[df["exercise"] == chart_exercise]
        
        if not filtered_df.empty:
            st.line_chart(filtered_df.set_index("date")["weight"])
        else:
            st.warning("該動作無歷史數據")
    else:
        st.info("尚無數據可提供分析")

# ==========================================
# Tab 4: 動作教學
# ==========================================
with tab4:
    st.subheader("動作教學庫")
    
    t_group = st.selectbox("選擇肌群分類", list(EXERCISE_GROUPS.keys()), key="t_group")
    t_exercise = st.selectbox("選擇動作", EXERCISE_GROUPS[t_group], key="t_exercise")
    
    if t_exercise in TUTORIALS:
        info = TUTORIALS[t_exercise]
        
        st.markdown(f"### {t_exercise}")
        st.write(f"**目標肌群：** {info['target']}")
        
        st.write("**動作步驟：**")
        for idx, step in enumerate(info["steps"], 1):
            st.write(f"{idx}. {step}")
            
        st.write("**常見錯誤：**")
        for mistake in info["mistakes"]:
            st.write(f"- {mistake}")
            
        try:
            st.image(info["image_url"], caption=f"【{t_exercise}】動作示意圖", use_container_width=True)
        except Exception:
            st.info("📷 圖片載入中或暫無示意圖")
    else:
        st.info("該動作教學準備中...")

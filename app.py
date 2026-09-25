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
# 想增減動作、或調整分肌群方式，直接改這個字典即可
EXERCISE_GROUPS: dict[str, list[str]] = {
    "胸部 Chest": [
        "機關胸推", "槓鈴臥推", "啞鈴臥推", "上斜啞鈴臥推", "夾胸機", "雙槓體撐",
    ],
    "背部 Back": [
        "滑輪下拉", "座姿滑輪划船", "槓鈴划船", "單臂啞鈴划船", "引體向上", "反向飛鳥/後三角機",
    ],
    "肩部 Shoulders": [
        "機械肩推", "啞鈴肩推", "啞鈴側平舉", "滑輪側平舉", "機械側平舉",
    ],
    "腿部 & 臀部 Legs & Glutes": [
        "機械腿推", "機械伸腿", "機械屈腿", "槓鈴深蹲", "啞鈴分腿蹲",
        "機械臀推", "大腿外展機", "大腿內收機",
    ],
    "手臂 Arms": [
        "啞鈴二頭彎舉", "機械二頭彎舉", "滑輪三頭下拉", "機械三頭伸展",
    ],
    "核心 Core": [
        "機械捲腹", "懸垂抬腿",
    ],
}
ALL_EXERCISES = [ex for group in EXERCISE_GROUPS.values() for ex in group]
REST_OPTIONS = {"60 秒": 60, "90 秒": 90, "120 秒": 120}
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


# ── 頁面 ────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

try:
    sb = get_client()
except Exception:
    st.error("找不到 Supabase 設定，請在 .streamlit/secrets.toml 加入 SUPABASE_URL 與 SUPABASE_KEY。")
    st.stop()

st.title("健身紀錄")

tab_today, tab_history, tab_progress = st.tabs(["今日訓練", "歷史紀錄", "進度圖表"])

# ═══════════════════════════════ 今日訓練 ═══════════════════════════════
with tab_today:
    st.caption(datetime.now(TZ).strftime("%Y/%m/%d"))

    muscle_group = st.selectbox("肌群", list(EXERCISE_GROUPS.keys()), key="muscle_group")
    exercise = st.selectbox("動作", EXERCISE_GROUPS[muscle_group], key=f"exercise_{muscle_group}")

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

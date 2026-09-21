"""健身房紀錄頁面（Streamlit + Supabase）

執行：  streamlit run app.py
設定：  .streamlit/secrets.toml 需要
            SUPABASE_URL = "https://xxxx.supabase.co"
            SUPABASE_KEY = "你的 key"
資料表： 先在 Supabase SQL Editor 執行 schema.sql
需求：  Python 3.11+
"""

import html
import math
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

# ── 設定 ────────────────────────────────────────────────
EXERCISES = ["機關胸推", "滑輪下拉", "腿推機", "槓鈴深蹲"]  # 想加動作直接加在這裡
REST_SECONDS = 90
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
:root { --ink:#14213D; --plate:#F2B705; }

.block-container { max-width: 560px; padding: 1.5rem 1rem 4rem; }

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

/* 次按鈕：略過休息 */
[data-testid="stBaseButton-secondary"], button[kind="secondary"] {
    min-height: 3.2rem; border-radius: 12px;
}
[data-testid="stBaseButton-secondary"] p, button[kind="secondary"] p { font-size: 1.1rem; }

/* 今日清單 */
.exname { font-size: 1.3rem; font-weight: 700; margin: 1.3rem 0 .45rem; }
.exname small { font-size: 1rem; font-weight: 500; opacity: .65; margin-left: .5rem; }
.setrow {
    display: flex; align-items: baseline; gap: 1rem; margin-bottom: .4rem;
    padding: .7rem 1rem; background: #fff; border-left: 6px solid var(--plate); border-radius: 8px;
}
.setrow .idx { width: 2rem; font: 700 1.9rem 'Barlow Condensed', sans-serif; }
.setrow .val { flex: 1; font-size: 1.5rem; font-weight: 700; }
.setrow .val small { font-size: 1rem; font-weight: 500; margin: 0 .15rem; }
.setrow .tm { font-size: 1rem; opacity: .6; }
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


def timer_html(remaining: int) -> str:
    return TIMER_HTML.replace("__TOTAL__", str(REST_SECONDS)).replace("__REMAINING__", str(remaining))


# ── Supabase ────────────────────────────────────────────
@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def utc_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_set(sb: Client, exercise: str, weight: float, reps: int) -> None:
    sb.table(TABLE).insert({"exercise": exercise, "weight_kg": weight, "reps": reps}).execute()


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


def hhmm(ts: str) -> str:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(TZ).strftime("%H:%M")


# ── 頁面 ────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

try:
    sb = get_client()
except Exception:
    st.error("找不到 Supabase 設定，請在 .streamlit/secrets.toml 加入 SUPABASE_URL 與 SUPABASE_KEY。")
    st.stop()

st.title("今日訓練")
st.caption(datetime.now(TZ).strftime("%Y/%m/%d"))

exercise = st.selectbox("動作", EXERCISES)

col_w, col_r = st.columns(2)
weight = col_w.number_input(
    "重量 (kg)", min_value=0.0, max_value=1000.0, value=20.0, step=2.5, format="%.1f", key="weight"
)
reps = col_r.number_input("次數 (reps)", min_value=1, max_value=200, value=10, step=1, key="reps")

if st.button("完成此組", type="primary", use_container_width=True):
    try:
        log_set(sb, exercise, float(weight), int(reps))
    except Exception as e:
        st.error(f"寫入失敗：{e}")
    else:
        st.session_state["rest_end"] = time.time() + REST_SECONDS

# 休息倒數（按下按鈕後 90 秒）
rest_end = st.session_state.get("rest_end")
if rest_end:
    remaining = math.ceil(rest_end - time.time())
    if remaining > 0:
        components.html(timer_html(remaining), height=150)
        if st.button("略過休息", use_container_width=True):
            st.session_state.pop("rest_end", None)
            st.rerun()
    else:
        st.session_state.pop("rest_end", None)

# 今天已記錄的組數（在按鈕之後才查詢，所以剛存的那一組會立刻出現）
st.divider()
try:
    rows = fetch_today(sb)
except Exception as e:
    st.error(f"讀取失敗：{e}")
    rows = []

if not rows:
    st.subheader("今天還沒有紀錄")
    st.caption("選好動作、輸入重量與次數，按「完成此組」開始。")
else:
    volume = sum(float(r["weight_kg"]) * int(r["reps"]) for r in rows)
    st.subheader(f"今天已完成 {len(rows)} 組")
    st.caption(f"總訓練量 {volume:,.0f} kg")

    grouped: dict[str, list[dict]] = {}
    for r in rows:
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

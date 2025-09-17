# water.py
import streamlit as st
import json, os
from datetime import date, timedelta
import plotly.express as px
import bcrypt
from twilio.rest import Client
from streamlit_lottie import st_lottie
import requests
import pandas as pd
from streamlit.components.v1 import html as st_html

# ------------------------------------
# Basic config
# ------------------------------------
st.set_page_config(page_title="HydraCoach", page_icon="💧", layout="centered")

def _rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# ------------------------------------
# Styling (creative colors + subtle animation)
# ------------------------------------
st.markdown("""
<style>
.big-title { font-size: 2.2rem; font-weight: 800;
  background: linear-gradient(90deg, #00d4ff, #6a00f4, #00ffa3);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtle { color: #a8b0b9; }
.bounce { display:inline-block; animation: bounce 1.2s infinite; }
@keyframes bounce { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-6px) } }
.card {
  padding: 1rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(106,0,244,0.10));
}
.pill {
  display:inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
  background: linear-gradient(90deg, #00ffa3, #00d4ff);
  color: #002b36; font-weight: 600; font-size: 0.8rem; margin-left: 6px;
}
.small { font-size: 0.9rem; color: #e9f7ff; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">HydraCoach <span class="bounce">💧</span></div>', unsafe_allow_html=True)
st.caption("Colorful hydration tracker with friendly coaching and WhatsApp reminders")

# ------------------------------------
# Constants: Climate options and tips
# ------------------------------------
CLIMATE_OPTIONS = [
    "Hot & Humid 🌴",
    "Hot & Dry 🏜️",
    "Temperate 🌤️",
    "Cold & Dry ❄️",
    "High Altitude ⛰️",
]

CLIMATE_TIPS = {
    "Hot & Humid 🌴": "Sweat loss is higher—try small, frequent sips 💦",
    "Hot & Dry 🏜️": "Evaporation is quick—keep your bottle within reach 🧴",
    "Temperate 🌤️": "Steady sipping through the day works best 👍",
    "Cold & Dry ❄️": "Thirst cues dip in cold—set gentle reminders 🕒",
    "High Altitude ⛰️": "Altitude increases fluid needs—sip regularly 🚶",
}

# ------------------------------------
# Helpers: DB + Security + Utils
# ------------------------------------
DB_PATH = "users_db.json"

def load_db():
    if not os.path.exists(DB_PATH):
        return {"users": {}}
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False

def today_key():
    return date.today().isoformat()

def last_7_days():
    return [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

def ensure_user(db, username):
    return db["users"].get(username)

def create_user(db, username, password, phone, goal, climate="Temperate 🌤️"):
    if username in db["users"]:
        return False, "Username already exists."
    if not username.isalnum():
        return False, "Username must be alphanumeric."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not phone.startswith("+"):
        return False, "Phone must include country code, e.g., +14155551212."
    try:
        goal = float(goal)
        if goal <= 0:
            raise ValueError()
    except Exception:
        return False, "Goal must be a positive number (liters)."

    db["users"][username] = {
        "password_hash": hash_pw(password),
        "phone": phone,
        "goal_liters": float(goal),
        "history": {},              # date -> total liters
        "reminder_opt_in": True,
        "climate": climate,
    }
    save_db(db)
    return True, "Account created successfully! Please log in."

def authenticate(db, username, password):
    user = db["users"].get(username)
    if not user:
        return False
    return verify_pw(password, user["password_hash"])

def add_intake(db, username, liters):
    try:
        liters = float(liters)
        if liters <= 0:
            return False, "Please enter a positive amount."
    except Exception:
        return False, "Invalid number."

    user = db["users"][username]
    hist = user.setdefault("history", {})
    k = today_key()
    hist[k] = round(hist.get(k, 0.0) + liters, 3)
    save_db(db)
    return True, hist[k]

def adjust_today_total(db, username, delta):
    # Adjust today's total by +/- delta (used for undo)
    user = db["users"][username]
    hist = user.setdefault("history", {})
    k = today_key()
    new_total = round(max(0.0, hist.get(k, 0.0) + float(delta)), 3)
    hist[k] = new_total
    save_db(db)
    return new_total

def get_today_intake(user):
    return float(user.get("history", {}).get(today_key(), 0.0))

def get_week_series(user):
    hist = user.get("history", {})
    days = last_7_days()
    values = [float(hist.get(d, 0.0)) for d in days]
    return days, values

def weekly_success_counts(user):
    days, values = get_week_series(user)
    goal = float(user.get("goal_liters", 3.0))
    success = sum(1 for v in values if v >= goal)
    return success, 7 - success

def compute_progress(intake, goal):
    # For donut segments
    if intake <= goal:
        consumed = intake
        remaining = max(goal - intake, 0.0)
        over = 0.0
    else:
        consumed = goal
        remaining = 0.0
        over = intake - goal

    # Friendly message
    if intake == 0:
        msg = "💧 Let’s start with a refreshing sip now!"
    elif intake < 0.5 * goal:
        msg = "💧 Good start! Try a glass each hour to stay refreshed."
    elif intake < goal:
        msg = "🚰 Nice pace! You’re getting close—keep sipping."
    elif abs(intake - goal) < 1e-6:
        msg = "🎉 Great job! You’ve hit your hydration goal today. Keep it up!"
    else:
        msg = "🚰 Excellent! You’re well-hydrated. Balance is key—no need to overdo it."

    pct = 0 if goal <= 0 else min(1.25, intake / goal)  # cap 125% for display
    return consumed, remaining, over, pct, msg

def send_whatsapp(to_phone, body):
    # Requires .streamlit/secrets.toml with TWILIO_* keys
    try:
        sid = st.secrets["TWILIO_ACCOUNT_SID"]
        token = st.secrets["TWILIO_AUTH_TOKEN"]
        sender = st.secrets["TWILIO_WHATSAPP_FROM"]  # e.g., whatsapp:+14155238886
    except Exception:
        st.error("Twilio secrets missing. Add them in .streamlit/secrets.toml")
        return False

    try:
        client = Client(sid, token)
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"
        client.messages.create(from_=sender, to=to_phone, body=body)
        return True
    except Exception as e:
        st.error(f"WhatsApp send failed: {e}")
        return False

def lottie_from_url(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# ------------------------------------
# Animated water bottle component (safe string replacement, no f-strings)
# ------------------------------------
def animated_bottle(fill_pct: float, over_pct: float, user_key: str, height_px: int = 420):
    # Bottle shows "Consumed" only: 0..100; over_pct shows extra amount above goal
    fill_pct = max(0.0, min(100.0, float(fill_pct)))
    over_pct = max(0.0, float(over_pct))
    safe_user_key = str(user_key).replace('"', '_').replace("'", "_")

    html = '''
<div id="bottle-wrap" style="display:flex;justify-content:center;align-items:center;">
  <style>
    .bottle {
      position: relative; width: 180px; height: 360px;
      border: 4px solid #6a00f4;
      border-radius: 40px 40px 30px 30px / 70px 70px 30px 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,.15), inset 0 0 0 6px rgba(255,255,255,.06);
      overflow: hidden; background: linear-gradient(135deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
    }
    .cap {
      position: absolute; top: -28px; left: 50%; transform: translateX(-50%);
      width: 90px; height: 30px; background: #6a00f4; border-radius: 12px;
      box-shadow: 0 4px 0 #4b00b3;
    }
    .water {
      position: absolute; left: 0; bottom: 0; width: 100%;
      height: 0%;
      background: linear-gradient(180deg, #00d4ff 0%, #00a6ff 70%);
      transition: height 900ms ease;
      box-shadow: inset 0 8px 20px rgba(0,0,0,.1);
    }
    .wave {
      position: absolute; left: 0; width: 200%; height: 20px;
      background: radial-gradient(circle at 10px 10px, rgba(255,255,255,.9) 20%, rgba(255,255,255,0) 21%) 0 0/40px 20px repeat-x;
      animation: drift 4s linear infinite; opacity: .6;
      bottom: 0;
      pointer-events: none;
    }
    @keyframes drift { from { transform: translateX(0);} to { transform: translateX(-40px);} }
    .bubbles { position:absolute; left:0; bottom:0; width:100%; height:100%; pointer-events:none; overflow:hidden; }
    .bubbles span {
      position:absolute; bottom:0; width:8px; height:8px; background:#e6faff; border-radius:50%;
      opacity:.7; animation: rise calc(3s + var(--d,0s)) ease-in infinite;
      left: var(--x, 50%);
    }
    @keyframes rise {
      0% { transform: translateY(0) scale(1); opacity:.8; }
      100% { transform: translateY(-260px) scale(.6); opacity:0; }
    }
    .label {
      position:absolute; top:12px; right:12px;
      background: linear-gradient(90deg,#00ffa3,#00d4ff); color:#012;
      padding:4px 10px; border-radius:999px; font-weight:700; font-size:14px;
      box-shadow: 0 2px 10px rgba(0,212,255,.4);
    }
    .over-badge {
      position:absolute; top:50px; right:12px; padding:4px 8px; border-radius:10px;
      background:#ff7aa2; color:white; font-weight:700; animation:pulse 1.2s infinite; display:none;
    }
    @keyframes pulse { 0%{transform:scale(1)} 50%{transform:scale(1.06)} 100%{transform:scale(1)} }
  </style>

  <div class="bottle" id="bottle">
    <div class="cap"></div>
    <div class="label" id="label">0%</div>
    <div class="over-badge" id="over">+0%</div>
    <div class="water" id="water"></div>
    <div class="wave" id="wave"></div>
    <div class="bubbles" id="bubbles"></div>
  </div>
</div>

<script>
(function() {
  const target = __FILL__;   // 0..100 (% of goal consumed)
  const over = __OVER__;     // >0 if intake is above goal
  const userKey = "__USER_KEY__".replaceAll('"','_').replaceAll("'", "_");
  const storageKey = "hydracoach_prev_" + userKey;

  const water = document.getElementById('water');
  const wave = document.getElementById('wave');
  const label = document.getElementById('label');
  const overBadge = document.getElementById('over');
  const bubbles = document.getElementById('bubbles');

  let prev = 0;
  try { prev = parseFloat(localStorage.getItem(storageKey) || '0'); } catch(e) {}
  if (isNaN(prev)) prev = 0;

  water.style.height = prev + "%";
  label.textContent = Math.round(target) + "%";
  function setWave(level) {
    wave.style.bottom = "calc(" + Math.min(level, 100) + "% - 10px)";
  }
  setWave(prev);

  requestAnimationFrame(() => {
    water.style.height = target + "%";
    setWave(target);
    try { localStorage.setItem(storageKey, String(target)); } catch(e) {}
  });

  if (over > 0) {
    overBadge.style.display = 'inline-block';
    overBadge.textContent = "+" + Math.round(over) + "%";
  }

  for (let i=0; i<12; i++) {
    const s = document.createElement('span');
    s.style.setProperty('--x', (10 + Math.random()*80) + '%');
    s.style.setProperty('--d', (Math.random()*2).toFixed(2) + 's');
    bubbles.appendChild(s);
  }
})();
</script>
'''
    html = (
        html.replace('__FILL__', f'{fill_pct:.2f}')
            .replace('__OVER__', f'{over_pct:.2f}')
            .replace('__USER_KEY__', safe_user_key)
    )
    st_html(html, height=height_px)

# ------------------------------------
# Session init
# ------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "add_stack" not in st.session_state:
    # Stack of additions (floats) in this session for Undo
    st.session_state.add_stack = []

db = load_db()

# ------------------------------------
# Auth Pages: Login / Sign up
# ------------------------------------
if not st.session_state.user:
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("#### Welcome back! <span class='pill'>Hydrate</span>", unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in 🚀")
            if submitted:
                if authenticate(db, username, password):
                    st.session_state.user = username
                    st.session_state.add_stack = []  # reset undo stack on login
                    st.success("Logged in successfully!")
                    _rerun()
                else:
                    st.error("Invalid username or password.")

    with tab_signup:
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("#### Create your account <span class='pill'>Free</span>", unsafe_allow_html=True)
            new_username = st.text_input("Choose a username (letters/numbers only)")
            new_password = st.text_input("Choose a password (min 6 chars)", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            phone = st.text_input("Mobile number for WhatsApp (with country code, e.g., +14155551212)")
            goal = st.number_input("Daily hydration goal (liters)", min_value=0.5, max_value=10.0, value=3.0, step=0.1)
            climate_choice = st.selectbox("Your climate", CLIMATE_OPTIONS, index=2)
            create = st.form_submit_button("Sign up ✨")
            if create:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = create_user(db, new_username, new_password, phone, goal, climate_choice)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.stop()

# ------------------------------------
# Logged-in area
# ------------------------------------
user = st.session_state.user
u = ensure_user(db, user)

with st.sidebar:
    st.markdown("### Hi, " + user + " 👋")
    page = st.radio("Navigate", ["Dashboard", "Reports", "Settings", "Logout"])

# ------------------------------------
# DASHBOARD
# ------------------------------------
if page == "Dashboard":
    # Climate tip banner
    climate_label = u.get("climate", "Temperate 🌤️")
    tip = CLIMATE_TIPS.get(climate_label, "")
    st.markdown(f"<div class='card'><b>Climate:</b> {climate_label} • {tip}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1,1])

    with colA:
        st.markdown("#### Today’s hydration")
        lottie = lottie_from_url("https://assets7.lottiefiles.com/packages/lf20_2szgfs.json")
        if lottie:
            st_lottie(lottie, height=180, key="water_anim")
        else:
            st.markdown("<div class='card'>💧💧💧</div>", unsafe_allow_html=True)

        # Add water form
        with st.form("add_water", clear_on_submit=True):
            add_l = st.number_input("Add water (liters)", min_value=0.1, max_value=5.0, value=0.25, step=0.05)
            add_btn = st.form_submit_button("Log intake ➕")
            if add_btn:
                ok, new_total = add_intake(db, user, add_l)
                if ok:
                    # push to session stack for Undo
                    st.session_state.add_stack.append(float(add_l))
                    st.success(f"Added {add_l:.2f} L! Today’s total: {new_total:.2f} L")
                    _rerun()
                else:
                    st.error(new_total)  # 'new_total' contains error message in this branch

        # Undo last addition (outside the form)
        if st.session_state.add_stack:
            last = st.session_state.add_stack[-1]
            st.info(f"Last added: {last:.2f} L")
            if st.button("Undo last ⤺"):
                popped = st.session_state.add_stack.pop()
                new_total = adjust_today_total(db, user, -popped)
                st.success(f"Undid {popped:.2f} L. Today’s total: {new_total:.2f} L")
                _rerun()
        else:
            st.caption("No additions to undo in this session.")

    with colB:
        today_intake = get_today_intake(u)
        goal = float(u.get("goal_liters", 3.0))
        consumed, remaining, over, pct, friendly_msg = compute_progress(today_intake, goal)

        # Donut pie (Consumed / Remaining / Over)
        labels = []
        values = []
        if consumed > 0:
            labels.append("Consumed")
            values.append(consumed)
        if remaining > 0:
            labels.append("Remaining")
            values.append(remaining)
        if over > 0:
            labels.append("Over")
            values.append(over)

        if not values:
            labels = ["Goal"]
            values = [goal]

        fig = px.pie(
            names=labels, values=values, hole=0.6,
            color=labels,
            color_discrete_map={
                "Consumed": "#00d4ff",
                "Remaining": "#6a00f4",
                "Over": "#00ffa3",
                "Goal": "#6a00f4"
            }
        )
        fig.update_traces(textinfo="label+percent", textfont_size=12)
        fig.update_layout(
            showlegend=False,
            annotations=[dict(text=f"{int(min(125, pct*100))}%", x=0.5, y=0.5, font_size=28, showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div class='card'><b>{friendly_msg}</b></div>", unsafe_allow_html=True)

        # Animated bottle (fills exactly to the Consumed slice of the pie)
        # Consumed is min(intake, goal) so bottle fills 0..100%, over shows as +X%
        fill_pct = 0.0 if goal <= 0 else (consumed / goal) * 100.0
        over_pct = 0.0 if goal <= 0 else (over / goal) * 100.0
        st.markdown("#### Animated bottle 💧")
        animated_bottle(fill_pct, over_pct, user_key=user)

        # WhatsApp reminder button (if behind)
        if today_intake < goal:
            if u.get("reminder_opt_in", True):
                if st.button("Send WhatsApp reminder now 📲"):
                    remaining_l = max(goal - today_intake, 0.0)
                    body = (
                        f"💧 HydraCoach reminder!\n"
                        f"Hi {user}, you’ve logged {today_intake:.2f}L today.\n"
                        f"Goal: {goal:.2f}L • Remaining: {remaining_l:.2f}L.\n"
                        f"Try a quick glass now to stay refreshed! 🚰"
                    )
                    ok = send_whatsapp(u.get("phone", ""), body)
                    if ok:
                        st.success("Reminder sent via WhatsApp!")
            else:
                st.info("WhatsApp reminders are turned off in Settings.")

# ------------------------------------
# REPORTS
# ------------------------------------
elif page == "Reports":
    st.markdown("#### Weekly overview 📈")

    days, vals = get_week_series(u)
    goal = float(u.get("goal_liters", 3.0))
    df = pd.DataFrame({"Date": days, "Intake (L)": vals, "Goal": [goal]*len(days)})

    # Weekly success pie (on-target days vs others)
    success, not_success = weekly_success_counts(u)
    pie2 = px.pie(
        names=["On target", "Below target"],
        values=[success, not_success],
        hole=0.5,
        color=["On target", "Below target"],
        color_discrete_map={"On target": "#00ffa3", "Below target": "#ff7aa2"}
    )
    pie2.update_layout(showlegend=True, legend_title="")
    st.plotly_chart(pie2, use_container_width=True)

    # Weekly intake vs goal
    bar = px.bar(df, x="Date", y="Intake (L)", color="Intake (L)",
                 color_continuous_scale=["#6a00f4", "#00d4ff"])
    bar.add_scatter(x=df["Date"], y=df["Goal"], mode="lines", name="Goal", line=dict(color="#00ffa3", width=3))
    st.plotly_chart(bar, use_container_width=True)

    # Daily hydration report (text + download)
    st.markdown("#### Daily hydration report 🧾")
    today_intake = get_today_intake(u)
    consumed, remaining, over, pct, friendly_msg = compute_progress(today_intake, goal)

    report_text = (
        f"HydraCoach Daily Report\n"
        f"Date: {today_key()}\n"
        f"User: {user}\n"
        f"Climate: {u.get('climate','Temperate 🌤️')}\n"
        f"Daily intake: {today_intake:.2f} L\n"
        f"Goal: {goal:.2f} L\n"
        f"Progress: {min(125, int(pct*100))}%\n"
        f"Summary: {friendly_msg}\n"
        f"Weekly (on-target days): {success}/7\n"
    )
    st.text_area("Preview", value=report_text, height=200)
    st.download_button("Download report (.txt) ⬇️", data=report_text.encode("utf-8"),
                       file_name=f"hydracoach_{today_key()}.txt", mime="text/plain")

# ------------------------------------
# SETTINGS
# ------------------------------------
elif page == "Settings":
    st.markdown("#### Personalize your plan 🎨")

    climate_val = u.get("climate", "Temperate 🌤️")
    default_index = next((i for i, opt in enumerate(CLIMATE_OPTIONS) if opt == climate_val), 2)

    with st.form("settings_form"):
        new_goal = st.number_input("Daily goal (liters)", min_value=0.5, max_value=10.0,
                                   value=float(u.get("goal_liters", 3.0)), step=0.1)
        new_phone = st.text_input("Mobile for WhatsApp (+countrycode...)", value=u.get("phone", ""))
        opt_in = st.checkbox("Enable WhatsApp reminders", value=u.get("reminder_opt_in", True))
        new_climate = st.selectbox("Your climate", CLIMATE_OPTIONS, index=default_index)
        submitted = st.form_submit_button("Save changes 💾")
        if submitted:
            try:
                u["goal_liters"] = float(new_goal)
                u["phone"] = new_phone
                u["reminder_opt_in"] = bool(opt_in)
                u["climate"] = new_climate
                db["users"][user] = u
                save_db(db)
                st.success("Settings updated!")
            except Exception as e:
                st.error(f"Could not save settings: {e}")

# ------------------------------------
# LOGOUT
# ------------------------------------
elif page == "Logout":
    if st.button("Confirm logout 🔒"):
        st.session_state.user = None
        st.session_state.add_stack = []  # clear undo stack
        st.success("Logged out.")
        _rerun()
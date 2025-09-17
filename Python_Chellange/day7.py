import streamlit as st
import pandas as pd
import datetime
import os

# --- Neon and Fun Streamlit Config ---
st.set_page_config(page_title="Gym Workout Logger 🏋", page_icon="💥", layout="wide")
st.markdown("""
    <style>
        body { background: linear-gradient(120deg, #222be7 0%, #fa37a3 100%); }
        .css-1d391kg { color: #fff; }
        .big-bubble {
            border-radius: 30px;
            background:rgba(43,15,136,0.85);
            box-shadow: 0 8px 40px #fa37a3a0;
            padding: 1.2em;
            margin-bottom: 2em;
            font-size: 1.1em;
            color: #fff;
        }
        .rainbow-title {
            font-family: Comic Sans MS, Comic Sans, cursive;
            font-size:2.8em;
            background: linear-gradient(90deg,#ffef37 10%, #23ffe8 40%, #fd36a7 80%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            letter-spacing:1.5px;
        }
        .glassy {
            background:rgba(255,255,255,.18);backdrop-filter:blur(8px);
            border-radius:25px;
            padding:1.4em;
            box-shadow:0 4px 32px #fc44ff99;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="rainbow-title">🏋️‍♂️ Gym Workout Logger</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- Load or create DataFrame, always parse 'date' as datetime ---
HIST_CSV = "workout_history.csv"
if os.path.exists(HIST_CSV):
    df = pd.read_csv(HIST_CSV)
else:
    df = pd.DataFrame(columns=["date", "exercise", "sets", "reps", "weight"])

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# --- Entry Form with unique keys ---
with st.container():
    st.markdown('<div class="big-bubble">', unsafe_allow_html=True)
    st.subheader("🔥 Log a New Workout!", anchor=False)
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        exercise = st.selectbox("Exercise 💪",
            ["Bench Press", "Squat", "Deadlift", "Bicep Curl", "Pull Up", "Other"],
            key="exercise_select"
        )
    with c2:
        sets = st.slider("Sets🥚", 1, 7, 3, key="sets_slider")
        reps = st.slider("Reps🔥", 1, 20, 10, key="reps_slider")
    with c3:
        weight = st.number_input("Weight (kg) 🏋️", min_value=0, max_value=400, value=50, step=1, key="weight_input")
        date = st.date_input("Workout Date 🎯", datetime.date.today(), key="date_input")

    if st.button("💾 Save Workout", help="Add this set to your Power-Up history!", key="save_button"):
        new_entry = pd.DataFrame([{
            "date": date, "exercise": exercise, "sets": sets, "reps": reps, "weight": weight
        }])
        df = pd.concat([df, new_entry], ignore_index=True)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")  # Ensure date type
        df.to_csv(HIST_CSV, index=False)
        st.success(f"Boom! Logged {sets}x{reps} {exercise} @ {weight}kg 🚀", icon="🎉")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Display Workout History ---
st.markdown('<div class="glassy"><h4>👾 Workout History</h4>', unsafe_allow_html=True)
if not df.empty:
    history_df = df.sort_values(by="date", ascending=False).tail(25)
    st.dataframe(
        history_df.style.set_properties(**{'background-color': '#fff0','color': '#fc44ff','border-radius': '10px'}),
        hide_index=True, use_container_width=True
    )
else:
    st.markdown("No workouts yet! Complete your first quest above. 🌈")
st.markdown('</div>', unsafe_allow_html=True)

# --- Weekly Progress with fixed aggregation ---
show_confetti = False
if not df.empty:
    df["week"] = df["date"].dt.isocalendar().week
    weekly = df.groupby("week", as_index=False).agg(
        total_weight=pd.NamedAgg(column="sets", aggfunc=lambda s: 0)  # placeholder
    )
    weekly["total_weight"] = df.groupby("week").apply(
        lambda x: (x["sets"] * x["reps"] * x["weight"]).sum()
    ).values

    st.markdown('<div class="glassy"><h4>🌈 Weekly Progress Power-Up</h4>', unsafe_allow_html=True)
    st.area_chart(
        weekly, x="week", y="total_weight",
        use_container_width=True,
        height=330,
    )
    if not weekly["total_weight"].empty and weekly["total_weight"].iloc[-1] > weekly["total_weight"].iloc[:-1].max():
        show_confetti = True
    st.markdown('</div>', unsafe_allow_html=True)

if show_confetti:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎊 YOU'VE HIT A NEW RECORD! 🎊", unsafe_allow_html=True)
    st.snow()

# --- Footer ---
st.markdown(
    '<div style="text-align:center;font-family:Comic Sans MS,Comic Sans,cursive;color:#fff;font-size:1.2em;margin-top:30px;">'
    '💥 Let every set be your superhero origin story! 💥'
    '</div>',
    unsafe_allow_html=True,
)

import streamlit as st
import random
import time

# --- CONFIG ---
st.set_page_config(page_title="Neon Rock Paper Scissors", layout="centered", initial_sidebar_state="collapsed")

# --- STYLES: dark neon purple theme with black text + animations ---
NEON_CSS = """
<style>
@keyframes pulseGlow {
  0% { box-shadow: 0 0 6px rgba(200,100,255,0.18); transform: translateY(0px); }
  50% { box-shadow: 0 0 30px rgba(200,100,255,0.35); transform: translateY(-6px); }
  100% { box-shadow: 0 0 6px rgba(200,100,255,0.18); transform: translateY(0px); }
}
@keyframes slideIn {
  0% { transform: translateY(20px) scale(0.96); opacity: 0 }
  60% { transform: translateY(-6px) scale(1.02); opacity: 1 }
  100% { transform: translateY(0px) scale(1); opacity: 1 }
}
body {
    background: linear-gradient(135deg, #1a0033 0%, #2e005c 40%, #4b0082 100%);
    color: #000000;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height:100vh;
}
.main .block-container{
    padding: 2rem 3rem;
}
.neon-card{
    background: rgba(40,0,70,0.5);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 8px 40px rgba(200,100,255,0.12), inset 0 0 40px rgba(140,0,255,0.06);
    border: 1px solid rgba(200,100,255,0.18);
}
.title-neon{
    font-size: 36px;
    font-weight: 800;
    letter-spacing: 1px;
    color: #000000;
    text-shadow: none;
}
.subtle {
    color: #000000cc !important;
}
.choice-box{
    background: linear-gradient(180deg, rgba(40,0,70,0.6), rgba(60,0,100,0.45));
    border-radius: 12px;
    padding: 12px;
    text-align:center;
    border: 1px solid rgba(180,100,255,0.12);
    color: #000000 !important;
}
.move-name{
    font-weight:700;
    font-size:18px;
    color: #000000 !important;
}
.result-winner, .result-loser, .result-tie{
    font-size:20px;
    font-weight:700;
    color: #000000 !important;
}
.anim-left { animation: slideIn 0.9s cubic-bezier(.2,.9,.2,1) both; }
.anim-right { animation: slideIn 0.9s cubic-bezier(.2,.9,.2,1) both; }
.pulse { animation: pulseGlow 1.6s ease-in-out infinite; }
</style>
"""

st.markdown(NEON_CSS, unsafe_allow_html=True)

# --- Session state for scores and animations ---
if "user_score" not in st.session_state:
    st.session_state.user_score = 0
if "computer_score" not in st.session_state:
    st.session_state.computer_score = 0

MOVES = ["Rock", "Paper", "Scissors"]

# ---- Layout header ----
with st.container():
    st.markdown("<div class='neon-card'> <div style='display:flex; justify-content:space-between; align-items:center;'> <div> <div class='title-neon'>Rock • Paper • Scissors</div> <div class='subtle'>User vs Computer — Neon Arena</div> </div> </div></div>", unsafe_allow_html=True)

# --- Main body ---
center_col = st.container()

with center_col:
    st.markdown("<div class='neon-card'>", unsafe_allow_html=True)

    choice = st.radio("Choose your move:", MOVES, horizontal=True)

    col1, col2 = st.columns([1,1])
    with col1:
        play = st.button("Play Round", key="play", help="Click to play against the robot")
    with col2:
        reset = st.button("Reset Game", key="reset", help="Reset the scores to zero")

    if reset:
        st.session_state.user_score = 0
        st.session_state.computer_score = 0
        st.rerun()

    st.markdown(f"<div style='margin-top:10px; display:flex; justify-content:space-between;'><div class='subtle'>User Score: <strong>{st.session_state.user_score}</strong></div><div class='subtle'>Computer Score: <strong>{st.session_state.computer_score}</strong></div></div>", unsafe_allow_html=True)

    result_area = st.empty()
    steps_area = st.empty()

    st.markdown("</div>", unsafe_allow_html=True)

def cot_reasoning(user, comp):
    steps = []
    steps.append(f"Step 1: User chose {user}, Computer chose {comp}.")
    if user == comp:
        steps.append(f"Step 2: Both chose {user}. It's a tie.")
        winner = "tie"
    elif (user == "Rock" and comp == "Scissors"):
        steps.append("Step 2: Rock crushes Scissors.")
        steps.append("Step 3: User wins the round.")
        winner = "user"
    elif (user == "Paper" and comp == "Rock"):
        steps.append("Step 2: Paper covers Rock.")
        steps.append("Step 3: User wins the round.")
        winner = "user"
    elif (user == "Scissors" and comp == "Paper"):
        steps.append("Step 2: Scissors cut Paper.")
        steps.append("Step 3: User wins the round.")
        winner = "user"
    else:
        if comp == "Rock" and user == "Scissors":
            steps.append("Step 2: Rock crushes Scissors.")
        elif comp == "Paper" and user == "Rock":
            steps.append("Step 2: Paper covers Rock.")
        elif comp == "Scissors" and user == "Paper":
            steps.append("Step 2: Scissors cut Paper.")
        steps.append("Step 3: Computer wins the round.")
        winner = "computer"
    return steps, winner

if play:
    computer_choice = random.choice(MOVES)

    # Countdown with animated prompt
    for i in range(3, 0, -1):
        result_area.markdown(f"<div style='text-align:center; font-size:28px; font-weight:700; color:#000000;'>Get ready... {i}</div>", unsafe_allow_html=True)
        time.sleep(0.55)

    # Show animated selection boxes
    left_html = f"<div class='choice-box anim-left pulse' style='display:inline-block; margin-right:24px;'><div class='move-name'>You</div><div style='font-size:22px; margin-top:6px;'>🔷 {choice}</div></div>"
    right_html = f"<div class='choice-box anim-right pulse' style='display:inline-block; margin-left:24px;'><div class='move-name'>Robot</div><div style='font-size:22px; margin-top:6px;'>🤖 {computer_choice}</div></div>"
    result_area.markdown(f"<div style='text-align:center; margin-top:10px;'>" + left_html + right_html + "</div>", unsafe_allow_html=True)

    steps, winner = cot_reasoning(choice, computer_choice)
    steps_area.empty()
    with steps_area.container():
        for s in steps:
            st.markdown(f"<div style='padding:8px; border-radius:8px; margin-top:8px; background:linear-gradient(90deg, rgba(60,0,100,0.45), rgba(40,0,70,0.4)); border:1px solid rgba(200,100,255,0.12); color:#000000;'>{s}</div>", unsafe_allow_html=True)
            time.sleep(0.45)

    # Show result
    if winner == "user":
        st.session_state.user_score += 1
        msg = "<div class='result-winner' style='text-align:center; margin-top:12px;'>You win this round! 🎉</div>"
    elif winner == "computer":
        st.session_state.computer_score += 1
        msg = "<div class='result-loser' style='text-align:center; margin-top:12px;'>Robot takes this round 🤖</div>"
    else:
        msg = "<div class='result-tie' style='text-align:center; margin-top:12px;'>It's a tie — great minds think alike ✨</div>"

    result_area.markdown(msg, unsafe_allow_html=True)

    try:
        st.balloons()
    except Exception:
        pass

    # Keep result for 5 seconds then clear
    time.sleep(5)
    result_area.empty()
    steps_area.empty()

    st.rerun()
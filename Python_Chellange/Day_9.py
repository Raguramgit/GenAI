# company_quiz_game_dark.py
import streamlit as st
import random
import time
from datetime import timedelta

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(page_title="🎮 Company Quiz Game", layout="centered", initial_sidebar_state="collapsed")

# ------------------------------
# Dark Theme Custom CSS (buttons unified to dark blue, all text white)
# and a logic-color reset button style
# ------------------------------
st.markdown(
    """
    <style>
      :root{
        --bg: #0f1419;
        --bg-gradient: linear-gradient(135deg, #0f1419 0%, #1e293b 50%, #0f172a 100%);
        --card: #1a1f2e;
        --card-hover: #242b3d;
        --text: #ffffff;              /* force white text */
        --text-muted: #b6c2df;
        --accent: #6366f1;
        --accent-hover: #4f46e5;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
        --border: #334155;

        /* unified dark-blue for all primary buttons */
        --btn-blue: #0b3d91;
        --btn-blue-hover: #123f9f;
        --btn-text: #ffffff;

        /* logic game color (used for Reset) */
        --logic-color: #e17055;
        --logic-color-hover: #ff7f5b;
      }

      /* Force white for page text for readability */
      .stApp, .stApp * {
        color: var(--text) !important;
      }

      .stApp { background: var(--bg-gradient); }

      /* Titles */
      .title { color: var(--accent); font-size: 42px; font-weight: 800; }
      .subtitle { color: var(--text-muted); }

      /* Question and text colors */
      .question-text { color: #ffffff; font-weight: 700; }
      .accent-text { color: var(--accent); font-weight: 700; }
      .success-text { color: var(--success); font-weight: 700; }
      .danger-text { color: var(--danger); font-weight: 700; }
      .muted-text { color: var(--text-muted); }

      /* Temporary notification styling (auto-hide) */
      .temp-notif {
        display: block;
        max-width: 900px;
        margin: 12px auto;
        padding: 12px 18px;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 10px 30px rgba(2,6,23,0.6);
        border: 1px solid rgba(255,255,255,0.04);
        opacity: 1;
        transform: translateY(0);
        transition: opacity 0.45s ease, transform 0.45s ease;
        z-index: 9999;
      }
      .temp-notif.success {
        background: linear-gradient(90deg, rgba(16,185,129,0.06), rgba(99,102,241,0.03));
        color: var(--success);
        border-color: rgba(16,185,129,0.18);
      }
      .temp-notif.error {
        background: linear-gradient(90deg, rgba(239,68,68,0.06), rgba(15, 23, 42, 0.02));
        color: var(--danger);
        border-color: rgba(239,68,68,0.18);
      }

      /* Card */
      .card { background: var(--card); border-radius: 16px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 1px solid var(--border); margin: 10px 0; }

      /* Category buttons (dark blue) */
      .category-button {
        display:inline-block;
        padding: 18px 14px;
        margin:8px;
        border-radius:12px;
        background: var(--btn-blue);
        color: var(--btn-text);
        font-weight:800;
        border: 1px solid rgba(255,255,255,0.04);
        cursor:pointer;
        text-align:center;
        transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
        box-shadow: 0 10px 25px rgba(11,61,145,0.18);
      }
      .category-button:hover {
        transform: translateY(-6px) scale(1.02);
        background: var(--btn-blue-hover);
        box-shadow: 0 18px 40px rgba(11,61,145,0.26);
      }

      /* Answer buttons (dark blue) */
      .ans-btn {
        width:100%;
        padding:16px;
        border-radius:12px;
        background: var(--btn-blue);
        color: var(--btn-text);
        border: 1px solid rgba(255,255,255,0.04);
        font-weight:800;
        cursor:pointer;
        margin:10px 0;
        transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
        box-shadow: 0 10px 25px rgba(11,61,145,0.14);
        text-align:left;
      }
      .ans-btn:hover {
        transform: translateY(-4px);
        background: var(--btn-blue-hover);
        box-shadow: 0 18px 40px rgba(11,61,145,0.24);
      }

      /* Streamlit native button override (dark-blue) */
      .stButton > button {
        background: var(--btn-blue) !important;
        color: var(--btn-text) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        padding: 10px 14px !important;
        box-shadow: 0 8px 22px rgba(11,61,145,0.18) !important;
        transition: transform 0.18s ease, background 0.18s ease !important;
      }
      .stButton > button:hover {
        background: var(--btn-blue-hover) !important;
        transform: translateY(-3px) !important;
      }

      div.stButton > button[disabled] {
        opacity: 0.6;
        cursor: not-allowed;
      }

      /* pulse */
      .pulse { display:inline-block; width:120px; height:120px; border-radius:50%; background: radial-gradient(circle at 30% 30%, rgba(16,185,129,0.18), rgba(16,185,129,0.06)); animation: pulse 0.8s ease-out; margin: 10px auto; box-shadow: 0 0 30px rgba(16,185,129,0.3); }
      @keyframes pulse { 0% { transform: scale(0.8); opacity: 0;} 50% { transform: scale(1.2); opacity: 1;} 100% { transform: scale(1.0); opacity: 0;} }

      /* small helpers */
      .muted-text { color: var(--text-muted); }

      /* progress bar */
      .progress-bar { width:100%; height:12px; background: var(--border); border-radius:8px; overflow:hidden; margin:10px 0; }
      .progress-fill { height:100%; background: linear-gradient(90deg,var(--accent), #8b5cf6); width:0%; transition: width 0.3s ease; }

      /* Quick Rules moved bottom style */
      .quick-rules {
        max-width: 1100px;
        margin: 20px auto;
        padding: 18px;
        border-radius: 12px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.03);
      }

      /* Logic-colored Reset (HTML button) */
      .logic-reset {
        display:inline-block;
        background: var(--logic-color);
        color: #ffffff;
        padding: 10px 14px;
        border-radius: 10px;
        font-weight: 800;
        text-decoration: none;
        border: none;
        cursor: pointer;
        box-shadow: 0 8px 22px rgba(225, 100, 85, 0.18);
      }
      .logic-reset:hover {
        background: var(--logic-color-hover);
        transform: translateY(-3px);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Hardcoded Expanded Question Bank
# ------------------------------
QUIZ_QUESTIONS = {
    "Hidden Object Game": [
        {"q": "🔎 In a picture full of books, which small item is most likely hidden between the pages?",
         "options": ["Bookmark", "Pen", "Coin", "Glasses"], "answer": "Bookmark"},
        {"q": "🔎 In a cluttered tea tray scene, which small item would be easiest to hide?",
         "options": ["Sugar cube", "Teabag label", "Spoon", "Napkin"], "answer": "Sugar cube"},
        {"q": "🔎 On a seaside shelf, which tiny object might hide behind shells?",
         "options": ["Key", "Bottle cap", "Toy car", "Button"], "answer": "Bottle cap"},
        {"q": "🔎 In an office drawer, which item often hides beneath papers?",
         "options": ["Staple remover", "USB stick", "Ruler", "Calculator"], "answer": "USB stick"},
        {"q": "🔎 In a kitchen scene, what small item often hides near the spice rack?",
         "options": ["Thimble", "Paper clip", "Bottle opener", "Coin"], "answer": "Thimble"},
        {"q": "🔎 In a garden shed, which tiny tool is most likely hidden behind larger ones?",
         "options": ["Small screwdriver", "Hammer", "Saw", "Wrench"], "answer": "Small screwdriver"},
    ],
    "Brain Game": [
        {"q": "🧠 What is the next number in the series: 2, 4, 8, 16, ?",
         "options": ["18", "24", "32", "64"], "answer": "32"},
        {"q": "🧠 If x + 3 = 10, what is 2x ?",
         "options": ["14", "12", "16", "10"], "answer": "14"},
        {"q": "🧠 Which shape is the odd one out: square, rectangle, circle, rhombus?",
         "options": ["Square", "Rectangle", "Circle", "Rhombus"], "answer": "Circle"},
        {"q": "🧠 Find the missing letter: A, C, F, J, O, ?",
         "options": ["T", "U", "S", "V"], "answer": "U"},
        {"q": "🧠 What comes next: 1, 1, 2, 3, 5, 8, ?",
         "options": ["11", "13", "15", "12"], "answer": "13"},
        {"q": "🧠 If 3x - 5 = 16, what is x?",
         "options": ["7", "6", "8", "5"], "answer": "7"},
    ],
    "Logic Game": [
        {"q": "🔐 If A > B and B > C, then A ? C",
         "options": [">", "<", "=", "?"], "answer": ">"},
        {"q": "🔐 All roses are flowers. Some flowers fade quickly. Do all roses fade quickly?",
         "options": ["Yes", "No", "Sometimes", "Cannot tell"], "answer": "No"},
        {"q": "🔐 If today is Tuesday, what day will be 9 days from now?",
         "options": ["Wednesday", "Thursday", "Friday", "Monday"], "answer": "Thursday"},
        {"q": "🔐 True or false: 'If it rains, the ground gets wet; the ground is wet, therefore it rained.'",
         "options": ["True", "False", "Sometimes", "Cannot say"], "answer": "False"},
        {"q": "🔐 In a group of 20 people, 12 like coffee, 8 like tea. How many like both if everyone likes at least one?",
         "options": ["0", "4", "8", "Cannot determine"], "answer": "Cannot determine"},
        {"q": "🔐 If all Blorps are Glorps, and some Glorps are Snorps, can we conclude some Blorps are Snorps?",
         "options": ["Yes", "No", "Maybe", "Need more info"], "answer": "No"},
    ],
    "Intelligence Game": [
        {"q": "🧩 Which word is the odd one out: run, jump, think, fly?",
         "options": ["Run", "Jump", "Think", "Fly"], "answer": "Think"},
        {"q": "🧩 Rearrange 'LISTEN' to make another meaningful word.",
         "options": ["Tinsel", "Silent", "Enlist", "All of these"], "answer": "All of these"},
        {"q": "🧩 If 'CAT' = 24, 'DOG' = 26, what is 'BAT' ? (A=1...Z=26)",
         "options": ["25", "27", "23", "24"], "answer": "25"},
        {"q": "🧩 Which completes analogy: Bird : Fly :: Fish : ?",
         "options": ["Swim", "Walk", "Dance", "Dive"], "answer": "Swim"},
        {"q": "🧩 What's the next in sequence: J, F, M, A, M, J, ?",
         "options": ["J", "A", "S", "N"], "answer": "J"},
        {"q": "🧩 If you rearrange the letters of 'NEW DOOR', you get?",
         "options": ["One word", "Two words", "Three words", "No valid words"], "answer": "One word"},
    ],
    "Funny Game": [
        {"q": "😂 Why did the math book look sad?",
         "options": ["It had problems", "It lost a page", "It was cooked", "It was tired"], "answer": "It had problems"},
        {"q": "😂 Why don't scientists trust atoms?",
         "options": ["They make up everything", "They are small", "They split", "They are old"], "answer": "They make up everything"},
        {"q": "😂 What do you call fake spaghetti?",
         "options": ["An impasta", "Noodles", "No pasta", "Spag-fake"], "answer": "An impasta"},
        {"q": "😂 Why did the scarecrow win an award?",
         "options": ["For standing out", "Best in field", "Scaring birds", "He looked good"], "answer": "Best in field"},
        {"q": "😂 What do you call a bear with no teeth?",
         "options": ["A gummy bear", "A sad bear", "A soft bear", "A quiet bear"], "answer": "A gummy bear"},
        {"q": "😂 Why don't eggs tell jokes?",
         "options": ["They'd crack each other up", "They're too shell-fish", "They're scrambled", "They're hard-boiled"], "answer": "They'd crack each other up"},
    ],
}

# ------------------------------
# Session State Defaults
# ------------------------------
for key, default in {
    "category": None, "questions": [], "current_q": 0, "score": 0,
    "start_time": None, "paused": False, "pause_started_at": None,
    "pause_accum": 0.0, "quiz_over": False, "mix_categories": False,
    "remind_30": False, "show_review": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Answer storage
for i in range(0, 100):
    k = f"answer_{i}"
    if k not in st.session_state:
        st.session_state[k] = None

TOTAL_QUESTIONS = 15
TOTAL_SECONDS = 180  # 3 minutes

# ------------------------------
# Utility Functions
# ------------------------------
def prepare_questions(category_name, mix=False):
    pool = []
    if mix:
        for cat_questions in QUIZ_QUESTIONS.values():
            pool.extend(cat_questions)
    else:
        pool = list(QUIZ_QUESTIONS.get(category_name, []))
    if len(pool) >= TOTAL_QUESTIONS:
        return random.sample(pool, TOTAL_QUESTIONS)
    else:
        chosen = pool.copy()
        while len(chosen) < TOTAL_QUESTIONS:
            chosen.append(random.choice(pool))
        random.shuffle(chosen)
        return chosen

def now_ts():
    return time.time()

def start_timer():
    st.session_state.start_time = now_ts()
    st.session_state.pause_accum = 0.0
    st.session_state.pause_started_at = None
    st.session_state.paused = False

def pause_timer():
    if not st.session_state.paused:
        st.session_state.paused = True
        st.session_state.pause_started_at = now_ts()

def resume_timer():
    if st.session_state.paused and st.session_state.pause_started_at:
        st.session_state.pause_accum += now_ts() - st.session_state.pause_started_at
        st.session_state.pause_started_at = None
        st.session_state.paused = False

def seconds_left():
    if not st.session_state.start_time:
        return TOTAL_SECONDS
    if st.session_state.paused:
        elapsed = st.session_state.pause_started_at - st.session_state.start_time - st.session_state.pause_accum
    else:
        elapsed = now_ts() - st.session_state.start_time - st.session_state.pause_accum
    remaining = int(TOTAL_SECONDS - elapsed)
    return max(0, remaining)

def render_enhanced_clock(remaining_seconds):
    fraction = remaining_seconds / TOTAL_SECONDS
    angle_deg = fraction * 360
    major_ticks = ""
    for i in range(12):
        major_ticks += f'<div class="clock-tick" style="transform: rotate({i * 30}deg);"></div>'
    if remaining_seconds <= 30:
        hand_color = "#ef4444"
    elif remaining_seconds <= 60:
        hand_color = "#f59e0b"
    else:
        hand_color = "#ef4444"
    clock_html = f'''
    <div class="animated-clock">
        <div class="clock-face">
            {major_ticks}
            <div class="clock-hand minute-hand" style="transform: translate(-50%, -100%) rotate({-angle_deg}deg); background: linear-gradient(to top, {hand_color}, #ff6b6b);"></div>
            <div class="clock-center"></div>
        </div>
    </div>
    '''
    return clock_html

def reset_quiz():
    st.session_state.category = None
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.start_time = None
    st.session_state.paused = False
    st.session_state.pause_started_at = None
    st.session_state.pause_accum = 0.0
    st.session_state.quiz_over = False
    st.session_state.mix_categories = False
    st.session_state.remind_30 = False
    st.session_state.show_review = False
    for i in range(TOTAL_QUESTIONS):
        st.session_state[f"answer_{i}"] = None

# ------------------------------
# Temporary notification HTML (auto-hide)
# ------------------------------
def show_temporary_notification(message_html: str, kind: str = "error", timeout_ms: int = 1400):
    uid = f"notif_{int(time.time()*1000)}"
    html = (
        f"<div id='{uid}' class='temp-notif {kind}'>"
        f"{message_html}"
        "</div>"
        "<script>"
        "setTimeout(function(){"
        "  var el = document.getElementById('" + uid + "');"
        "  if(!el) return;"
        "  el.style.opacity = '0'; el.style.transform = 'translateY(-10px)';"
        "  setTimeout(function(){ if(el && el.parentNode) el.parentNode.removeChild(el); }, 450);"
        "}, " + str(int(timeout_ms)) + ");"
        "</script>"
    )
    st.markdown(html, unsafe_allow_html=True)

# ------------------------------
# Handle reset query param (HTML button uses ?reset=1)
# ------------------------------
params = st.experimental_get_query_params()
if "reset" in params:
    # perform reset and clear query params
    reset_quiz()
    st.experimental_set_query_params()  # clears params
    st.rerun()

# ------------------------------
# UI: Header + Reset Button + Category Selection
# ------------------------------
st.markdown(
    '<div style="text-align:center; padding:12px 10px;"><div class="title">🎮 Quiz Game</div>'
    '<div class="subtitle">Dark Mode · Playful & Professional — 15 questions · 3 minutes</div></div>',
    unsafe_allow_html=True
)

# Top controls: left for categories, right for Reset button (HTML styled in logic color)
left_col, right_col = st.columns([3, 1])

with right_col:
    # Use an HTML button styled to logic game color. Clicking it reloads page with ?reset=1 handled above.
    reset_button_html = """
    <div style="display:flex; justify-content:flex-end;">
      <a class="logic-reset" href="?reset=1">Reset Quiz</a>
    </div>
    """
    st.markdown(reset_button_html, unsafe_allow_html=True)
    # small spacer
    st.write("")

with left_col:
    if not st.session_state.category:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Choose Your Challenge")
        cols = st.columns(3)
        cat_list = list(QUIZ_QUESTIONS.keys())
        emoji_map = {
            "Hidden Object Game": "🔎", "Brain Game": "🧠",
            "Logic Game": "🔐", "Intelligence Game": "🧩", "Funny Game": "😂"
        }
        mix_checked = st.checkbox("🔀 Mix categories (random)", value=st.session_state.mix_categories)
        st.session_state.mix_categories = mix_checked

        for i, cat in enumerate(cat_list):
            col = cols[i % 3]
            with col:
                btn_html = (
                    "<div class='category-button'>"
                    f"<div style='font-size:28px;margin-bottom:6px'>{emoji_map.get(cat,'🎮')}</div>"
                    f"<div style='font-weight:800;color:var(--btn-text);'>{cat}</div>"
                    "</div>"
                )
                st.markdown(btn_html, unsafe_allow_html=True)
                if st.button(f"Start {cat}", key=f"btn_{cat}"):
                    st.session_state.category = cat
                    st.session_state.mix_categories = mix_checked
                    st.session_state.questions = prepare_questions(cat, mix=mix_checked)
                    st.session_state.current_q = 0
                    start_timer()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# Quiz Running UI
# ------------------------------
if st.session_state.category and not st.session_state.quiz_over:
    remaining = seconds_left()
    mins = remaining // 60
    secs = remaining % 60
    pct_done = min(1.0, (st.session_state.current_q) / TOTAL_QUESTIONS)

    t1, t2, t3 = st.columns([2, 6, 2])

    with t1:
        clock_html = render_enhanced_clock(remaining)
        st.markdown(clock_html, unsafe_allow_html=True)
        status_text = "<span class='muted-text'>⏸️ Paused</span>" if st.session_state.paused else f"<span class='muted-text'>⏳ {mins}:{secs:02d}</span>"
        st.markdown(f"<div style='text-align:center;margin-top:8px'>{status_text}</div>", unsafe_allow_html=True)

    with t2:
        progress_html = f'''
        <div style="margin: 20px 0;">
            <div class="progress-bar">
                <div class="progress-fill" style="width:{int(pct_done*100)}%"></div>
            </div>
            <div style="display:flex; justify-content:space-between; color:var(--text-muted); font-size:14px; font-weight:600;">
                <span>Question {st.session_state.current_q + 1} / {TOTAL_QUESTIONS}</span>
                <span class="accent-text">{st.session_state.category if not st.session_state.mix_categories else "Mixed Categories"}</span>
            </div>
        </div>
        '''
        st.markdown(progress_html, unsafe_allow_html=True)

    with t3:
        if st.session_state.paused:
            if st.button("▶️ Resume"):
                resume_timer()
                st.rerun()
        else:
            if st.button("⏸️ Pause"):
                pause_timer()
                st.rerun()
        if st.button("🔔 30s Alert"):
            st.success("✅ Reminder enabled (will warn at 30s).")
            st.session_state.remind_30 = True

    if remaining <= 30 and remaining > 0 and st.session_state.remind_30:
        st.markdown('<div class="warning-banner">⏰ URGENT: Only 30 seconds remaining!</div>', unsafe_allow_html=True)

    if remaining <= 0:
        st.session_state.quiz_over = True
        st.rerun()

    q_idx = st.session_state.current_q
    if not st.session_state.questions:
        st.session_state.questions = prepare_questions(st.session_state.category, mix=st.session_state.mix_categories)
    if q_idx >= TOTAL_QUESTIONS:
        st.session_state.quiz_over = True
        st.rerun()
    question = st.session_state.questions[q_idx]

    st.markdown("<div class='card' style='margin-top:20px'>", unsafe_allow_html=True)
    st.markdown(f"<div class='question-text'>Q{q_idx+1}. {question['q']}</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)

    # Answer buttons: 2x2 grid (only one interactive button per option)
    ans_cols = st.columns(2)
    for i, opt in enumerate(question["options"]):
        col = ans_cols[i % 2]
        with col:
            if st.button(opt, key=f"ans_{q_idx}_{i}", use_container_width=True):
                st.session_state[f"answer_{q_idx}"] = opt
                correct = question["answer"]
                if opt == correct:
                    st.session_state.score += 1
                    show_temporary_notification("<span class='success-text'>✅ Excellent! That's correct.</span>", kind="success", timeout_ms=1200)
                    st.markdown("<div style='text-align:center;margin:10px 0'><div class='pulse'></div></div>", unsafe_allow_html=True)
                    st.balloons()
                else:
                    correct_html = f"<strong>{correct}</strong>"
                    show_temporary_notification(f"<span class='danger-text'>❌ Not quite right. The correct answer is: {correct_html}</span>", kind="error", timeout_ms=1400)
                st.session_state.current_q += 1
                time.sleep(0.7)
                st.rerun()

    st.markdown("<div class='hint'>💡 <strong>Pro Tip:</strong> Use Pause if you need a short break. Quick answers boost speed!</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Live score and metrics
    st.markdown("---")
    score_cols = st.columns(4)
    with score_cols[0]:
        accuracy = int((st.session_state.score / max(1, st.session_state.current_q)) * 100) if st.session_state.current_q > 0 else 100
        st.metric("🎯 Score", f"{st.session_state.score}/{TOTAL_QUESTIONS}", delta=f"{accuracy}% accuracy")
    with score_cols[1]:
        elapsed_sec = TOTAL_SECONDS - remaining
        st.metric("⏱️ Elapsed", str(timedelta(seconds=int(elapsed_sec))))
    with score_cols[2]:
        avg_time = elapsed_sec / max(1, st.session_state.current_q) if st.session_state.current_q > 0 else 0
        st.metric("⚡ Avg/Question", f"{avg_time:.1f}s")
    with score_cols[3]:
        remaining_qs = TOTAL_QUESTIONS - st.session_state.current_q
        st.metric("📋 Remaining", f"{remaining_qs} questions")

    if not st.session_state.paused:
        time.sleep(0.6)
        st.rerun()

# ------------------------------
# Final Results
# ------------------------------
if st.session_state.quiz_over:
    final_score = st.session_state.score
    percentage = int((final_score / TOTAL_QUESTIONS) * 100)
    if percentage >= 90:
        performance_level = "🌟 OUTSTANDING"
        feedback = "You're a quiz master!"
        st.balloons()
    elif percentage >= 75:
        performance_level = "🏆 EXCELLENT"
        feedback = "Fantastic work!"
    elif percentage >= 60:
        performance_level = "👍 GOOD"
        feedback = "Nice job!"
    elif percentage >= 40:
        performance_level = "📚 FAIR"
        feedback = "Good effort!"
    else:
        performance_level = "💪 KEEP TRYING"
        feedback = "Practice makes perfect!"

    final_html = f'''
    <div class="final-score-container">
        <div class="final-score-title accent-text">🎊 Quiz Complete!</div>
        <div class="final-score-value" style="font-size:48px;font-weight:900">{final_score} / {TOTAL_QUESTIONS}</div>
        <div style="font-size:20px;color:var(--text-muted);margin-top:6px">{feedback}</div>
        <div style="font-size:28px;color:var(--accent);margin-top:8px">{percentage}%</div>
    </div>
    '''
    st.markdown(final_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Play Again"):
            reset_quiz()
            st.rerun()
    with col2:
        if st.button("📊 View Results"):
            st.session_state.show_review = True

    if st.session_state.show_review:
        st.markdown("---")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📋 Detailed Review")
        for i, q in enumerate(st.session_state.questions[:TOTAL_QUESTIONS]):
            chosen = st.session_state.get(f"answer_{i}", "—")
            correct = q["answer"]
            is_correct = (chosen == correct)
            status_icon = "✅" if is_correct else "❌"
            status_color = "var(--success)" if is_correct else "var(--danger)"
            review_html = f'''
            <div style="border-left: 4px solid {status_color}; padding: 12px; margin: 8px 0; background: rgba(255,255,255,0.01); border-radius:6px;">
              <div style="font-weight:700; margin-bottom:6px;">{status_icon} Question {i+1}: <span style="color:var(--text-muted)">{q['q']}</span></div>
              <div style="color:var(--text-muted)"><strong>Your answer:</strong> {chosen} &nbsp; | &nbsp; <strong>Correct:</strong> {correct}</div>
            </div>
            '''
            st.markdown(review_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📈 Performance Insights")
        correct_answers = sum(1 for i in range(TOTAL_QUESTIONS) if st.session_state.get(f"answer_{i}") == st.session_state.questions[i]["answer"])
        wrong_answers = TOTAL_QUESTIONS - correct_answers
        total_time = TOTAL_SECONDS - seconds_left() if st.session_state.start_time else 0
        insights_cols = st.columns(3)
        with insights_cols[0]:
            st.metric("✅ Correct Answers", correct_answers)
        with insights_cols[1]:
            st.metric("❌ Wrong Answers", wrong_answers)
        with insights_cols[2]:
            st.metric("⏱️ Total Time", f"{total_time//60}:{total_time%60:02d}")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# Quick Rules (moved to bottom)
# ------------------------------
st.markdown("<div class='quick-rules card'>", unsafe_allow_html=True)
st.markdown("**⚡ Quick Rules**", unsafe_allow_html=True)
st.markdown("- 15 questions total\n- 3 minutes to finish\n- Pause/Resume available (Stop-Clock)\n- Score tracked live\n- Use the Reset button to restart anytime", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<div style="text-align:center;color:var(--text-muted);padding:14px">Made with ❤️ — Dark Mode Edition</div>', unsafe_allow_html=True)
# ------------------------------
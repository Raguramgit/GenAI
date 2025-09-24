# Stopwatch Trainer Streamlit App
# Save this file as `stopwatch_trainer_streamlit.py` and run with:
#    streamlit run stopwatch_trainer_streamlit.py

import time
import streamlit as st

# --- App configuration ---
st.set_page_config(page_title="Stopwatch Trainer", page_icon="⏱️", layout="centered")

# --- Helper functions ---

def format_time(seconds: float) -> str:
    """Format seconds as MM:SS.ms"""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    millis = int((seconds - int(seconds)) * 100)
    return f"{minutes:02d}:{secs:02d}.{millis:02d}"


def ensure_session_state():
    """Initialize keys used in the app."""
    if "running" not in st.session_state:
        st.session_state.running = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "paused_elapsed" not in st.session_state:
        st.session_state.paused_elapsed = 0.0
    if "elapsed" not in st.session_state:
        st.session_state.elapsed = 0.0
    if "message" not in st.session_state:
        st.session_state.message = "Ready."
    if "last_action" not in st.session_state:
        st.session_state.last_action = None


ensure_session_state()

# --- Layout ---
st.title("⏱️ Stopwatch — Trainer Edition")
st.markdown(
    """
A simple, reliable stopwatch for coaching sessions. Use **Start**, **Stop**, and **Reset** to manage sets, rests, and intervals.

Helpful for HIIT, strength training, circuits, and cooldowns.
"""
)

col1, col2 = st.columns([2, 1])

with col1:
    display = st.empty()  # Where the timer will be shown
    subtitle = st.empty()

with col2:
    st.write("**Controls**")
    start_btn = st.button("Start", key="start")
    stop_btn = st.button("Stop", key="stop")
    reset_btn = st.button("Reset", key="reset")

# Quick presets for common use-cases (informational only)
preset_expander = st.expander("Quick presets (informational)")
with preset_expander:
    st.write("Examples you can use while timing: ")
    st.write("- 40s plank → Start and hold 40s")
    st.write("- 30s rest → Stop when rest ends or Start when rest timer begins")
    st.write("- Reset between circuits to start fresh")

# --- Button logic ---
if start_btn:
    # If starting from a paused state, keep paused_elapsed
    if not st.session_state.running:
        # If starting fresh or after reset
        if st.session_state.start_time is None:
            st.session_state.start_time = time.monotonic()
            st.session_state.paused_elapsed = 0.0
        else:
            # Resume from pause
            st.session_state.start_time = time.monotonic()
        st.session_state.running = True
        st.session_state.message = "Timer started. Push hard!"
        st.session_state.last_action = "start"

if stop_btn:
    if st.session_state.running:
        # Calculate elapsed until this stop
        now = time.monotonic()
        st.session_state.paused_elapsed += now - st.session_state.start_time
        st.session_state.start_time = None
        st.session_state.running = False
        st.session_state.message = "Rest time stopped. Back to training!"
        st.session_state.last_action = "stop"
    else:
        # If not running, just show message
        st.session_state.message = "Timer is already stopped."

if reset_btn:
    st.session_state.running = False
    st.session_state.start_time = None
    st.session_state.paused_elapsed = 0.0
    st.session_state.elapsed = 0.0
    st.session_state.message = "Timer reset. Ready for the next round!"
    st.session_state.last_action = "reset"

# --- Display and live update ---
# Compute elapsed based on state
if st.session_state.running:
    # When running, compute elapsed dynamically
    now = time.monotonic()
    st.session_state.elapsed = st.session_state.paused_elapsed + (now - st.session_state.start_time)
else:
    st.session_state.elapsed = st.session_state.paused_elapsed

# Show main timer
minutes = int(st.session_state.elapsed) // 60
seconds = int(st.session_state.elapsed) % 60
milliseconds = int((st.session_state.elapsed - int(st.session_state.elapsed)) * 100)

display.markdown(f"# {minutes:02d}:{seconds:02d}.{milliseconds:02d}")

# Show secondary info and message
subtitle.write(f"**Status:** {'Running' if st.session_state.running else 'Stopped'}")
st.write(f"**{st.session_state.message}**")

# Small activity log
with st.expander("Activity log"):
    st.write(f"Last action: {st.session_state.last_action}")
    st.write(f"Elapsed (s): {st.session_state.elapsed:.2f}")

# --- Auto-refresh while running to give a live timer ---
# The pattern below forces the app to re-run frequently while the timer is running,
# which keeps the timer updating on the page but still allows button clicks to be registered.
if st.session_state.running:
    # short sleep to avoid hogging CPU, then re-run the script to update display
    time.sleep(0.08)
    st.rerun()

# --- Footer with tips and keyboard accessibility hint ---
st.markdown("---")
st.caption(
    "Tips: Use Start to begin a set, Stop for short interruptions or end of a rep/rest, and Reset when you want a fresh timer.\n\nFor quick intervals, use the presets above as a reminder. Keep focus — the timer's job is to reduce distraction so you can coach."
)

# Optionally show a compact stopwatch for mobile layout
if st.checkbox("Show compact view", value=False):
    st.write(f"Compact: {format_time(st.session_state.elapsed)}")

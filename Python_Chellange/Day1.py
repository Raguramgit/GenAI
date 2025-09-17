import streamlit as st
from datetime import datetime

# Try to import pyautogui safely
try:
    import pyautogui
    PYA_AVAILABLE = True
except Exception:
    PYA_AVAILABLE = False

st.set_page_config(page_title="Good Morning Greeting", layout="centered")
st.title("🌞 Good Morning Greeting App")

st.markdown("Fill out the form below and get your personalized **Good Morning** greeting!")

# --- Form ---
with st.form(key="greet_form"):
    name = st.text_input("Enter your name", value="")
    age = st.slider("Select your age", min_value=1, max_value=100, value=25)
    use_pyautogui = st.checkbox("Type greeting into active window using pyautogui", value=False)
    submit = st.form_submit_button("Get Greeting")

# --- Greeting logic ---
def build_greeting(name: str, age: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    if name.strip():
        return f"🌞 Good Morning {name.strip()}! You are {age} years old today. ({today})"
    else:
        return f"🌞 Good Morning! You are {age} years old today. ({today})"

if submit:
    greeting = build_greeting(name, age)
    st.success(greeting)

    # Optional: pyautogui typing
    if use_pyautogui:
        if not PYA_AVAILABLE:
            st.error("⚠ pyautogui is not installed. Run `pip install pyautogui` and restart.")
        else:
            st.info("pyautogui will type the greeting in 3 seconds. Switch to a text box (e.g., Notepad)!")
            import time
            time.sleep(3)  # give user time to switch window
            try:
                pyautogui.write(greeting, interval=0.05)
                pyautogui.press("enter")
                st.success("Greeting typed successfully into the active window! ✅")
            except Exception as e:
                st.error(f"pyautogui failed: {e}")

# --- Notes ---
st.markdown("---")
st.caption(
    "💡 Notes:\n"
    "- The greeting always starts with **Good Morning**.\n"
    "- If pyautogui is enabled, make sure a text editor (like Notepad) is active.\n"
    "- Works only on local environments (not on hosted Streamlit Cloud).\n"
)

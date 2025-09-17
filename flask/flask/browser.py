from flask import Flask, jsonify, render_template_string
import threading
import time
import os
import platform
import pyautogui

app = Flask(__name__)

# --- Configuration: adjust these for your screen ---
SEARCH_QUERY = "Gen AI Leatest News"
# Example click coordinates for your screen (change these)
CLICK_X = 246
CLICK_Y = 671
# -------------------------------------------------

# Simple HTML page with a button to trigger the script
INDEX_HTML = """
<!doctype html>
<title>Run PyAutoGUI Task</title>
<h2>Run PyAutoGUI Task</h2>
<p>This will run a small GUI automation on this machine (open browser, search, click).</p>
<form action="/run" method="post">
  <button type="submit">Run</button>
</form>
"""

def open_browser():
    """Open Chrome (cross-platform attempt)."""
    system = platform.system()
    try:
        if system == "Windows":
            # 'start' is a shell builtin; use os.system as in your original script
            os.system("start chrome")
        elif system == "Darwin":
            # macOS
            os.system("open -a 'Google Chrome'")
        else:
            # Linux: try google-chrome, chromium, or xdg-open
            if os.system("which google-chrome") == 0:
                os.system("google-chrome &")
            elif os.system("which chromium") == 0:
                os.system("chromium &")
            else:
                # fallback: xdg-open will open default browser but may not be Chrome
                os.system("xdg-open 'about:blank' &")
    except Exception as e:
        print("Could not open browser:", e)

def automation_task():
    """The pyautogui automation that mimics your original script."""
    try:
        # Safety: give user a short time to move mouse to top-left to abort if needed
        pyautogui.FAILSAFE = True  # moving mouse to top-left (0,0) will raise exception
        print("Opening browser...")
        open_browser()
        time.sleep(3)  # wait for browser to open

        # Type search and press enter
        pyautogui.write(SEARCH_QUERY, interval=0.1)
        pyautogui.press("enter")
        time.sleep(5)  # wait for results to load

        # Move and click first link - coordinates MUST be adjusted for your screen
        pyautogui.moveTo(CLICK_X, CLICK_Y, duration=1)
        pyautogui.click()
        print("Automation finished.")
    except pyautogui.FailSafeException:
        print("PyAutoGUI fail-safe triggered. Aborting automation.")
    except Exception as e:
        print("Error during automation:", e)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML)

@app.route("/run", methods=["POST", "GET" , "PUT"])
def run():
    """
    Start the automation in a separate thread and return immediately.
    (Using GET is OK for quick tests; in production prefer POST.)
    """
    t = threading.Thread(target=automation_task, daemon=True)
    t.start()
    return jsonify({"status": "started", "message": "Automation started in background thread."})

if __name__ == "__main__":
    # Run in debug=False when running actual automation to avoid multiple reloads/threads
    app.run(host="127.0.0.1", port=5000, debug=True)
import pyautogui
import time
import os

# Step 1: Open browser (Windows example for Chrome)
os.system("start chrome")   # On Mac: os.system("open -a 'Google Chrome'")
time.sleep(3)  # Wait for browser to open

# Step 2: Type search query
pyautogui.write("Pro Kabaddi score", interval=0.1)
pyautogui.press("enter")
time.sleep(5)  # Wait for search results to load

# Step 3: Move to first link and click
# You may need to adjust coordinates for your screen
# Tip: Run pyautogui.position() in an interactive script to find x,y
pyautogui.moveTo(379, 831, duration=1)  # Example position
pyautogui.click()

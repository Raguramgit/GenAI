import pyautogui
import time
import os

source_path = "C:\Ragu\AI\AI- Study\RPA\pyautogui\source.txt"
destination_path = "C:\Ragu\AI\AI- Study\RPA\pyautogui\destination.txt"

# Create content for the source file.
content = [
    "Thala Ajith (Ajith Kumar) is an Indian actor and a passionate motorcycling enthusiast.\n",
]
# Open Notepad
pyautogui.hotkey("win", "r")
time.sleep(2)
pyautogui.write("notepad")
time.sleep(2)
pyautogui.press("enter")
time.sleep(2)

# Type the content
for line in content:
    pyautogui.write(line)
    time.sleep(2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(2)

# Save as -> full path
pyautogui.hotkey("ctrl", "s")
time.sleep(2)
pyautogui.write(source_path)   # full path here
time.sleep(2)
pyautogui.press("enter")
time.sleep(2)
pyautogui.hotkey("alt", "f4")
time.sleep(2)

# Copy the file from source to destination
pyautogui.hotkey("win", "r")
time.sleep(2)
pyautogui.write("notepad")
time.sleep(2)
pyautogui.press("enter")
time.sleep(2)
pyautogui.hotkey("ctrl","v")
time.sleep(2)
pyautogui.hotkey("ctrl", "s")
time.sleep(2)
pyautogui.write(destination_path)
time.sleep(2)
pyautogui.press("enter")
time.sleep(2)
pyautogui.hotkey("alt", "f4")
time.sleep(2)





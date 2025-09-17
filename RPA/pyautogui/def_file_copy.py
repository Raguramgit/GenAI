import time
import os
import pyautogui

# Define source and destination file paths

SRC_PATH = "C:\Ragu\AI\AI_Study\RPA\pyautogui\source.txt"
DST_PATH = "C:\Ragu\AI\AI_Study\RPA\pyautogui\destination.txt"

# Content to write to the source file
LINES = [
    "Thala Ajith (Ajith Kumar) is an Indian actor and a passionate motorcycling enthusiast.\n",
]

# create blank notepad file
def create_notepad_file():
    pyautogui.hotkey("win", "r")
    time.sleep(2)
    pyautogui.write("notepad")
    time.sleep(2)
    pyautogui.press("enter")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "n")
    time.sleep(2)

# Write content to the source file
def write_to_source_file():
    create_notepad_file()
    for line in LINES:
        pyautogui.write(line)
        time.sleep(2)
        pyautogui.hotkey("ctrl", "s")
        time.sleep(2)
        pyautogui.write(SRC_PATH)
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(2)
        pyautogui.hotkey("alt", "f4")
        time.sleep(2)  
        print(f"Source file created at {SRC_PATH}")

# Copy content from source to destination file
def copy_dest_file():
    create_notepad_file()
    time.sleep(2)
    pyautogui.hotkey("ctrl", "o")
    time.sleep(2)
    pyautogui.write(SRC_PATH)
    time.sleep(2)
    pyautogui.press("enter")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "n")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(2)
    pyautogui.hotkey("ctrl", "s")
    time.sleep(2)
    pyautogui.write(DST_PATH)
    time.sleep(2)
    pyautogui.press("enter")
    time.sleep(2)
    pyautogui.hotkey("alt", "f4")
    time.sleep(2)  
    print(f"Destination file created at {DST_PATH}")
        

def main():
    write_to_source_file()
    copy_dest_file()
    print("File copy operation completed.")
if __name__ == "__main__":
    main()
    
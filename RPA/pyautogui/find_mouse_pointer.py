import pyautogui
import time
time.sleep(5)
# Get the current mouse position
x,y = pyautogui.position()
print(f'X: {x} Y: {y}')
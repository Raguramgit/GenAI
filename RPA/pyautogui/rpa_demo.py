import  pyautogui
import time
print ("Hello from RPA with Python")

#Mouse operations using pyautogui
''' pyautogui.click(100, 100)
time.sleep(3)
pyautogui.rightClick(100, 100)'''
time.sleep(3)
pyautogui.click(146, 356)


#Keyboard operations using pyautogui
time.sleep(3)
pyautogui.write("Hello from RPA with Python")
pyautogui.hotkey("ctrl", "s")

import pyautogui
import time

print("Coloca el mouse donde desees capturar la coordenada...")
time.sleep(5)
x, y = pyautogui.position()
print(f"Coordenadas capturadas: ({x}, {y})")

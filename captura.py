#import pyautogui
#import time

#print("Coloca el mouse donde desees capturar la coordenada...")
#time.sleep(5)
#x, y = pyautogui.position()
#print(f"Coordenadas capturadas: ({x}, {y})")

from pywinauto import Application, timings
import os
import time

# Ruta del archivo .scl o similar que deseas abrir con Sonel Analysis
archivo_sonel = f"/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm/9. Catiglata T 1225 C 0100234196.pqm702"  # Cambia la ruta a tu archivo real

# Ruta del ejecutable de Sonel Analysis (ajusta si es necesario)
ruta_exe = f"D:/Wolfly/Sonel/SonelAnalysis.exe"

# Verificar que el archivo existe
if not os.path.exists(archivo_sonel):
    print("El archivo no existe.")
    exit()

# Iniciar la aplicación con el archivo
app = Application(backend="uia").start(f'"{ruta_exe}" "{archivo_sonel}"')

# Esperar más tiempo para que se cargue bien
time.sleep(10)

try:
    print("[🪟 Ventanas detectadas por pywinauto]:")
    for w in app.windows():
        print("-", w.window_text())

    # Intentar capturar la ventana principal activa
    main_window = app.top_window()
    main_window.set_focus()
    main_window.maximize()

    # Imprimir controles accesibles
    print("\n[🔍 Controles detectados]\n")
    main_window.print_control_identifiers()

except Exception as e:
    print("❌ Error:", e)


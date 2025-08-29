import sys
from PyQt5.QtWidgets import QApplication
from gui.window.application import SonelDataExtractorGUI

def main():
    app = QApplication(sys.argv)
    
    # Configurar la aplicación
    app.setApplicationName("Sonel Data Extractor")
    app.setApplicationVersion("1.2.0")
    
    # Crear ventana principal
    window = SonelDataExtractorGUI()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
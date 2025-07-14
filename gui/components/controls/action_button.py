from PyQt5.QtWidgets import QPushButton

class ActionButton(QPushButton):
    """Botón de acción personalizado"""
    def __init__(self, text, icon="", button_type="primary", parent=None):
        super().__init__(f"{icon} {text}" if icon else text, parent)
        self.button_type = button_type
        self.setMinimumHeight(44)
        self.setObjectName(f"ActionButton_{button_type}")
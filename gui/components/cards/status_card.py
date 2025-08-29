from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel

class StatusCard(QFrame):
    """Tarjeta de estado con métricas"""
    def __init__(self, icon, title, value, color="#2196F3", parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedHeight(100)
        self.setObjectName("StatusCard")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icono
        icon_label = QLabel(icon)
        icon_label.setObjectName("StatusIcon")
        icon_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Contenido
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setObjectName("StatusTitle")
        
        self.value_label = QLabel(value)  # ⬅️ se convierte en atributo de instancia
        self.value_label.setObjectName("StatusValue")
        self.value_label.setStyleSheet(f"font-size: 20px; color: {color}; font-weight: 700;")
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(self.value_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(content_layout)
        layout.addStretch()

    def update_value(self, new_value: str):
        """Actualizar el valor mostrado en la tarjeta"""
        self.value_label.setText(new_value)

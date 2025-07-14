from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QToolButton

class HeaderPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("HeaderFrame")
        self.setFixedHeight(120)
        self.init_ui()
        
    def init_ui(self):
        header_layout = QHBoxLayout(self)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        # Lado izquierdo - Título y descripción
        left_layout = QVBoxLayout()
        
        # Título principal
        title_label = QLabel("Sonel Data Extractor")
        title_label.setObjectName("MainTitle")
        
        # Subtítulo
        subtitle_label = QLabel("Sistema ETL para análisis de datos eléctricos empresariales")
        subtitle_label.setObjectName("Subtitle")
        
        # Descripción
        desc_label = QLabel("Procesamiento automatizado de archivos PQM • Integración PostgreSQL • Análisis en tiempo real")
        desc_label.setObjectName("Description")
        
        left_layout.addWidget(title_label)
        left_layout.addWidget(subtitle_label)
        left_layout.addWidget(desc_label)
        left_layout.addStretch()
        
        # Lado derecho - Controles
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        
        # Botón cambiar tema
        self.theme_btn = QToolButton()
        self.theme_btn.setText("🌙 Modo Oscuro")
        self.theme_btn.setObjectName("ThemeButton")
        self.theme_btn.setFixedSize(120, 35)
        self.theme_btn.clicked.connect(self.parent_app.toggle_theme)
        
        # Estado de conexión
        self.connection_status = QLabel("🔗 PostgreSQL Conectado")
        self.connection_status.setObjectName("ConnectionStatus")
        self.connection_status.setFixedSize(180, 35)
        self.connection_status.setAlignment(Qt.AlignCenter)
        
        right_layout.addWidget(self.theme_btn)
        right_layout.addWidget(self.connection_status)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        header_layout.addLayout(right_layout)
        
    def update_theme_button_text(self, text):
        self.theme_btn.setText(text)
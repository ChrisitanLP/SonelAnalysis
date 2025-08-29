import datetime
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel

class FooterPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("FooterFrame")
        self.setFixedHeight(50)
        self.init_ui()
        
    def init_ui(self):
        footer_layout = QHBoxLayout(self)
        footer_layout.setContentsMargins(20, 12, 20, 12)
        
        # Información del sistema
        system_info = QLabel("Python 3.9.7 • PostgreSQL 13.8 • Sonel Analysis 4.6.6 • ETL Framework v2.1")
        system_info.setObjectName("SystemInfo")
        
        # Versión y timestamp
        version_info = QLabel(f"v1.2.0 - Build {datetime.datetime.now().strftime('%Y%m%d')} • Última actualización: {datetime.datetime.now().strftime('%H:%M:%S')}")
        version_info.setObjectName("VersionInfo")
        
        footer_layout.addWidget(system_info)
        footer_layout.addStretch()
        footer_layout.addWidget(version_info)
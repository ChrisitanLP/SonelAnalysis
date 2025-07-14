from PyQt5.QtCore import Qt
from components.cards.modern_card import ModernCard
from components.controls.action_button import ActionButton
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from utils.ui_helper import UIHelpers

class ControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("ControlPanel")
        self.init_ui()
        
    def init_ui(self):
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(20)
        
        # Selección de archivos
        file_card = ModernCard("Selección de Archivos")
        file_content = QWidget()
        file_layout = QVBoxLayout(file_content)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(12)
        
        # Info de carpeta
        self.folder_info = QLabel("📂 Ninguna carpeta seleccionada")
        self.folder_info.setObjectName("FolderInfo")
        self.folder_info.setMinimumHeight(60)
        self.folder_info.setAlignment(Qt.AlignCenter)
        self.folder_info.setWordWrap(True)
        
        # Botón seleccionar
        self.select_folder_btn = ActionButton("Seleccionar Carpeta PQM", "📁", "secondary")
        self.select_folder_btn.clicked.connect(self.parent_app.select_folder)
        
        file_layout.addWidget(self.folder_info)
        file_layout.addWidget(self.select_folder_btn)
        
        file_card.layout().addWidget(file_content)
        
        # Acciones principales
        actions_card = ModernCard("Acciones Principales")
        actions_content = QWidget()
        actions_layout = QVBoxLayout(actions_content)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)
        
        # Botones de acción
        self.csv_btn = ActionButton("Generar Archivos CSV", "📊", "secondary")
        self.csv_btn.clicked.connect(self.parent_app.generate_csv)
        self.csv_btn.clicked.connect(self.confirm_generate_csv)
        
        self.upload_btn = ActionButton("Subir a Base de Datos", "🗄️", "secondary")
        self.upload_btn.clicked.connect(self.parent_app.upload_to_db)
        self.upload_btn.clicked.connect(self.confirm_upload_db)
        
        self.execute_all_btn = ActionButton("Ejecutar Proceso Completo", "⚡", "primary")
        self.execute_all_btn.setMinimumHeight(52)
        self.execute_all_btn.clicked.connect(self.parent_app.execute_all)
        
        actions_layout.addWidget(self.csv_btn)
        actions_layout.addWidget(self.upload_btn)
        actions_layout.addSpacing(8)
        actions_layout.addWidget(self.execute_all_btn)
        
        actions_card.layout().addWidget(actions_content)
        
        # Progreso
        progress_card = ModernCard("Progreso del Proceso")
        progress_content = QWidget()
        progress_layout = QVBoxLayout(progress_content)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        
        self.progress_label = QLabel("🔄 Extracción de archivos PQM en progreso...")
        self.progress_label.setObjectName("ProgressLabel")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(12)
        self.progress_bar.setValue(72)
        self.progress_bar.setObjectName("ProgressBar")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        progress_card.layout().addWidget(progress_content)
        
        # Agregar tarjetas al panel
        panel_layout.addWidget(file_card)
        panel_layout.addWidget(actions_card)
        panel_layout.addWidget(progress_card)
        panel_layout.addStretch()
        
    def update_folder_info(self, text):
        self.folder_info.setText(text)
        
    def get_progress_value(self):
        return self.progress_bar.value()
        
    def set_progress_value(self, value):
        self.progress_bar.setValue(value)
        
    def update_progress_label(self, text):
        self.progress_label.setText(text)

    def confirm_generate_csv(self):
        """Pide confirmación antes de generar CSV."""
        ok = UIHelpers.show_confirmation_dialog(
            self,
            title="Confirmar generación de CSV",
            message="¿Seguro que deseas generar los archivos CSV?",
            details="Esta operación puede sobrescribir archivos existentes."
        )
        if ok:
            self.parent_app.generate_csv()

    def confirm_upload_db(self):
        """Pide confirmación antes de subir a la base de datos."""
        ok = UIHelpers.show_confirmation_dialog(
            self,
            title="Confirmar subida a la base de datos",
            message="¿Seguro que deseas subir los datos a la BD?",
            details="Asegúrate de que la conexión esté disponible y las tablas preparadas."
        )
        if ok:
            self.parent_app.upload_to_db()
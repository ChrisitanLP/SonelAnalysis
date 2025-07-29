from PyQt5.QtCore import Qt
from gui.components.cards.modern_card import ModernCard
from gui.components.controls.action_button import ActionButton
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from gui.utils.ui_helper import UIHelpers

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
        self.csv_btn.clicked.connect(self.confirm_generate_csv)
        
        self.upload_btn = ActionButton("Subir a Base de Datos", "🗄️", "secondary")
        self.upload_btn.clicked.connect(self.confirm_upload_db)
        
        self.execute_all_btn = ActionButton("Ejecutar Proceso Completo", "⚡", "primary")
        self.execute_all_btn.setMinimumHeight(52)
        self.execute_all_btn.clicked.connect(self.confirm_complete_process)
        
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

        self.progress_label = QLabel("Sistema listo para procesar...")
        self.progress_label.setObjectName("ProgressLabel")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(12)
        self.progress_bar.setValue(0)  # Cambiar de 72 a 0
        self.progress_bar.setObjectName("ProgressBar")

        # Aplicar estilo inicial (sin progreso)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-weight: normal;
                padding: 8px;
                border-left: 4px solid #E0E0E0;
                background-color: rgba(224, 224, 224, 0.1);
                border-radius: 4px;
            }
        """)

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
        """Establecer valor del progreso con validación"""
        # Asegurar que el valor esté en rango válido
        value = max(0, min(100, value))
        self.progress_bar.setValue(value)
        
        # Cambiar color de la barra según el progreso
        if value == 0:
            # Sin progreso - estilo neutral
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #E0E0E0;
                    border-radius: 8px;
                    background-color: rgba(224, 224, 224, 0.1);
                    text-align: center;
                    color: #666666;
                    font-weight: normal;
                }
                QProgressBar::chunk {
                    background-color: #E0E0E0;
                    border-radius: 6px;
                }
            """)
        elif value == 100:
            # Verde para completado
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    background-color: rgba(76, 175, 80, 0.1);
                    text-align: center;
                    color: #2E7D32;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #4CAF50, stop: 1 #66BB6A);
                    border-radius: 6px;
                }
            """)
        elif value > 0:
            # Azul para en progreso
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                    background-color: rgba(33, 150, 243, 0.1);
                    text-align: center;
                    color: #1565C0;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #2196F3, stop: 1 #42A5F5);
                    border-radius: 6px;
                }
            """)
        
    def update_progress_label(self, text):
        """Actualizar etiqueta de progreso con emoji dinámico"""
        self.progress_label.setText(text)
        
        # NUEVO: Agregar efecto visual según el tipo de mensaje
        if "✅" in text or "completado" in text.lower() or "finalizada" in text.lower():
            # Estilo para completado
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #2E7D32;
                    font-weight: bold;
                    padding: 8px;
                    border-left: 4px solid #4CAF50;
                    background-color: rgba(76, 175, 80, 0.1);
                    border-radius: 4px;
                }
            """)
        elif "❌" in text or "error" in text.lower() or "fallido" in text.lower():
            # Estilo para error
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #C62828;
                    font-weight: bold;
                    padding: 8px;
                    border-left: 4px solid #F44336;
                    background-color: rgba(244, 67, 54, 0.1);
                    border-radius: 4px;
                }
            """)
        elif "⚠️" in text or "advertencia" in text.lower():
            # Estilo para advertencia
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #F57C00;
                    font-weight: bold;
                    padding: 8px;
                    border-left: 4px solid #FF9800;
                    background-color: rgba(255, 152, 0, 0.1);
                    border-radius: 4px;
                }
            """)
        else:
            # Estilo para procesando
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #1565C0;
                    font-weight: bold;
                    padding: 8px;
                    border-left: 4px solid #2196F3;
                    background-color: rgba(33, 150, 243, 0.1);
                    border-radius: 4px;
                }
            """)

    def reset_progress(self):
        """Resetear la barra de progreso y etiqueta al estado inicial"""
        self.set_progress_value(0)
        self.update_progress_label("Sistema listo para procesar...")
        
    # NUEVO MÉTODO: Mostrar progreso detallado
    def update_detailed_progress(self, current: int, total: int, operation: str = ""):
        """Actualizar progreso con información detallada"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.set_progress_value(percentage)
            
            if operation:
                self.update_progress_label(f"{operation} ({current}/{total}) - {percentage}%")
            else:
                self.update_progress_label(f"Procesando... ({current}/{total}) - {percentage}%")

    def confirm_generate_csv(self):
        """Solicita confirmación antes de generar los archivos CSV."""
        ok = UIHelpers.show_confirmation_dialog(
            self,
            title="Confirmar generación de archivos CSV",
            message="¿Deseas continuar con la generación de los archivos CSV?",
            details="Este proceso puede sobrescribir archivos existentes en el directorio de salida."
        )
        if ok:
            self.parent_app.generate_csv()

    def confirm_upload_db(self):
        """Solicita confirmación antes de subir los datos a la base de datos."""
        ok = UIHelpers.show_confirmation_dialog(
            self,
            title="Confirmar carga a base de datos",
            message="¿Deseas cargar los datos procesados en la base de datos?",
            details="Verifica que la conexión esté activa y las tablas necesarias se encuentren configuradas."
        )
        if ok:
            self.parent_app.upload_to_db()

    def confirm_complete_process(self):
        """Solicita confirmación antes de ejecutar el proceso completo."""
        ok = UIHelpers.show_confirmation_dialog(
            self,
            title="Confirmar ejecución completa del proceso",
            message="¿Deseas ejecutar el proceso completo de extracción, transformación y carga?",
            details="Esta operación ejecutará todas las etapas del flujo (ETL) en una sola ejecución y actualizará los paneles con los resultados obtenidos."
        )
        if ok:
            self.parent_app.execute_all()

    def start_progress(self, initial_message="🔄 Iniciando proceso..."):
        """Iniciar el progreso con un mensaje inicial"""
        self.set_progress_value(0)
        self.update_progress_label(initial_message)
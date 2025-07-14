import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QGroupBox, QProgressBar, QTextEdit, QFileDialog,
                             QFrame, QSizePolicy, QSpacerItem, QToolButton, 
                             QMenu, QAction, QSplitter, QTabWidget, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
import datetime

class ModernCard(QFrame):
    """Widget personalizado para crear tarjetas modernas"""
    def __init__(self, title="", content_widget=None, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("ModernCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            layout.addWidget(title_label)
        
        if content_widget:
            layout.addWidget(content_widget)

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
        
        value_label = QLabel(value)
        value_label.setObjectName("StatusValue")
        value_label.setStyleSheet(f"font-size: 20px; color: {color}; font-weight: 700;")
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(value_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(content_layout)
        layout.addStretch()

class ActionButton(QPushButton):
    """Botón de acción personalizado"""
    def __init__(self, text, icon="", button_type="primary", parent=None):
        super().__init__(f"{icon} {text}" if icon else text, parent)
        self.button_type = button_type
        self.setMinimumHeight(44)
        self.setObjectName(f"ActionButton_{button_type}")

class SonelDataExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_folder = ""
        self.is_dark_mode = False
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Sonel Data Extractor - Sistema ETL Empresarial")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header
        self.create_header(main_layout)
        
        # Contenido principal
        self.create_main_content(main_layout)
        
        # Footer
        self.create_footer(main_layout)
        
        # Aplicar tema inicial
        self.apply_theme()
        
        # Inicializar datos estáticos
        self.update_static_data()
        
    def create_header(self, layout):
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setFixedHeight(120)
        
        header_layout = QHBoxLayout(header_frame)
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
        self.theme_btn.clicked.connect(self.toggle_theme)
        
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
        
        layout.addWidget(header_frame)
        
    def create_main_content(self, layout):
        # Crear contenedor principal
        content_frame = QFrame()
        content_frame.setObjectName("ContentFrame")
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        
        # Panel izquierdo - Controles
        left_panel = self.create_control_panel()
        left_panel.setMaximumWidth(450)
        left_panel.setMinimumWidth(400)
        
        # Panel derecho - Estado y métricas
        right_panel = self.create_status_panel()
        right_panel.setMinimumWidth(600)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        
        # Configurar stretch factors
        content_layout.setStretchFactor(left_panel, 0)
        content_layout.setStretchFactor(right_panel, 1)
        
        layout.addWidget(content_frame)
        
    def create_control_panel(self):
        # Panel principal
        panel = QWidget()
        panel.setObjectName("ControlPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(20)
        
        # Selección de archivos
        file_card = ModernCard("📁 Selección de Archivos")
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
        self.select_folder_btn.clicked.connect(self.select_folder)
        
        file_layout.addWidget(self.folder_info)
        file_layout.addWidget(self.select_folder_btn)
        
        file_card.layout().addWidget(file_content)
        
        # Acciones principales
        actions_card = ModernCard("🚀 Acciones Principales")
        actions_content = QWidget()
        actions_layout = QVBoxLayout(actions_content)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)
        
        # Botones de acción
        self.csv_btn = ActionButton("Generar Archivos CSV", "📊", "secondary")
        self.csv_btn.clicked.connect(self.generate_csv)
        
        self.upload_btn = ActionButton("Subir a Base de Datos", "🗄️", "secondary")
        self.upload_btn.clicked.connect(self.upload_to_db)
        
        self.execute_all_btn = ActionButton("Ejecutar Proceso Completo", "⚡", "primary")
        self.execute_all_btn.setMinimumHeight(52)
        self.execute_all_btn.clicked.connect(self.execute_all)
        
        actions_layout.addWidget(self.csv_btn)
        actions_layout.addWidget(self.upload_btn)
        actions_layout.addSpacing(8)
        actions_layout.addWidget(self.execute_all_btn)
        
        actions_card.layout().addWidget(actions_content)
        
        # Progreso
        progress_card = ModernCard("📈 Progreso del Proceso")
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
        
        return panel
        
    def create_status_panel(self):
        # Panel principal
        panel = QWidget()
        panel.setObjectName("StatusPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(20)
        
        # Métricas en grid
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        metrics_layout.setSpacing(16)
        
        # Datos de métricas
        self.status_cards = []
        metrics_data = [
            ("📁", "Archivos Procesados", "28 / 32", "#4CAF50"),
            ("⚠️", "Advertencias", "3", "#FF9800"),
            ("❌", "Errores", "1", "#F44336"),
            ("⏱️", "Tiempo Restante", "2:15 min", "#2196F3"),
            ("📊", "Registros", "18,542", "#9C27B0"),
            ("🗄️", "Estado BD", "Sincronizado", "#4CAF50")
        ]
        
        for i, (icon, title, value, color) in enumerate(metrics_data):
            row = i // 3
            col = i % 3
            status_card = StatusCard(icon, title, value, color)
            self.status_cards.append(status_card)
            metrics_layout.addWidget(status_card, row, col)
        
        # Log de actividad
        log_card = ModernCard("📝 Log de Actividad en Tiempo Real")
        log_content = QWidget()
        log_layout = QVBoxLayout(log_content)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(220)
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("LogText")
        
        # Contenido del log
        log_content_text = """[15:42:18] ✅ Conexión PostgreSQL establecida exitosamente
[15:42:19] 📁 Escaneando directorio: ./data/sonel_files/
[15:42:20] 📊 Detectados 32 archivos .pqm702 válidos
[15:42:21] 🔄 Iniciando procesamiento: medicion_20240301.pqm702
[15:42:22] ✅ Archivo procesado: 847 registros extraídos
[15:42:23] 🔄 Procesando: medicion_20240302.pqm702
[15:42:25] ✅ Archivo procesado: 823 registros extraídos
[15:42:26] 🔄 Procesando: medicion_20240303.pqm702
[15:42:27] ❌ Error: Archivo corrupto - omitiendo
[15:42:28] 📊 Generando CSV consolidado: output_20240710.csv
[15:42:29] 🗄️ Insertando batch 1/3 en tabla measurements
[15:42:30] 🗄️ Insertando batch 2/3 en tabla measurements
[15:42:31] ✅ Proceso 87% completado - 28/32 archivos"""
        
        self.log_text.setPlainText(log_content_text)
        log_layout.addWidget(self.log_text)
        log_card.layout().addWidget(log_content)
        
        # Resumen ejecutivo
        summary_card = ModernCard("📋 Resumen Ejecutivo")
        summary_content = QWidget()
        summary_layout = QVBoxLayout(summary_content)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        
        self.summary_label = QLabel()
        self.summary_label.setObjectName("SummaryLabel")
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)
        summary_card.layout().addWidget(summary_content)
        
        # Agregar elementos al panel
        panel_layout.addWidget(metrics_widget)
        panel_layout.addWidget(log_card)
        panel_layout.addWidget(summary_card)
        
        return panel
        
    def create_footer(self, layout):
        footer_frame = QFrame()
        footer_frame.setObjectName("FooterFrame")
        footer_frame.setFixedHeight(50)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 12, 20, 12)
        
        # Información del sistema
        system_info = QLabel("🔧 Python 3.9.7 • PostgreSQL 13.8 • Sonel Analysis 4.6.6 • ETL Framework v2.1")
        system_info.setObjectName("SystemInfo")
        
        # Versión y timestamp
        version_info = QLabel(f"v1.2.0 - Build {datetime.datetime.now().strftime('%Y%m%d')} • Última actualización: {datetime.datetime.now().strftime('%H:%M:%S')}")
        version_info.setObjectName("VersionInfo")
        
        footer_layout.addWidget(system_info)
        footer_layout.addStretch()
        footer_layout.addWidget(version_info)
        
        layout.addWidget(footer_frame)
        
    def update_static_data(self):
        # Actualizar resumen ejecutivo
        summary_text = f"""
<b>Estado General:</b> En progreso (87% completado)<br>
<b>Archivos Detectados:</b> 32 archivos .pqm702<br>
<b>Procesados Exitosamente:</b> 28 archivos<br>
<b>Con Advertencias:</b> 3 archivos (datos fuera de rango)<br>
<b>Con Errores:</b> 1 archivo (corrupción de datos)<br><br>
<b>Métricas de Datos:</b><br>
• Registros de voltaje extraídos: 18,542<br>
• Registros de corriente: 18,542<br>
• Registros de frecuencia: 18,542<br><br>
<b>Performance:</b><br>
• Tiempo de procesamiento: 4:12 min<br>
• Velocidad promedio: 6.7 archivos/min<br>
• Tiempo estimado restante: 2:15 min<br><br>
<b>Última Sincronización:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        self.summary_label.setText(summary_text)
        
    def toggle_theme(self):
        """Cambiar entre modo claro y oscuro"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        
        # Actualizar texto del botón
        if self.is_dark_mode:
            self.theme_btn.setText("☀️ Modo Claro")
        else:
            self.theme_btn.setText("🌙 Modo Oscuro")
        
    def apply_theme(self):
        """Aplicar tema claro u oscuro"""
        if self.is_dark_mode:
            # Tema oscuro
            stylesheet = """
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QWidget {
                    color: #ffffff;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QFrame#HeaderFrame {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 16px;
                }
                
                QFrame#ContentFrame {
                    background-color: transparent;
                }
                
                QFrame#FooterFrame {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QWidget#ControlPanel {
                    background-color: transparent;
                }
                
                QWidget#StatusPanel {
                    background-color: transparent;
                }
                
                QFrame#ModernCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QFrame#StatusCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QLabel#MainTitle {
                    font-size: 28px;
                    font-weight: 700;
                    color: #ffffff;
                    margin-bottom: -8px;
                }
                
                QLabel#Subtitle {
                    font-size: 14px;
                    color: #b0b0b0;
                    font-weight: 400;
                }
                
                QLabel#Description {
                    font-size: 12px;
                    color: #888888;
                    margin-top: 8px;
                }
                
                QLabel#CardTitle {
                    font-size: 16px;
                    font-weight: 600;
                    color: #ffffff;
                }
                
                QLabel#StatusTitle {
                    font-size: 12px;
                    color: #b0b0b0;
                    font-weight: 500;
                }
                
                QLabel#FolderInfo {
                    font-size: 13px;
                    color: #b0b0b0;
                    padding: 12px;
                    background-color: #3d3d3d;
                    border: 1px solid #505050;
                    border-radius: 8px;
                }
                
                QLabel#ProgressLabel {
                    font-size: 13px;
                    color: #b0b0b0;
                    font-weight: 500;
                }
                
                QLabel#SummaryLabel {
                    font-size: 12px;
                    line-height: 1.5;
                    color: #ffffff;
                }
                
                QLabel#SystemInfo, QLabel#VersionInfo {
                    color: #888888;
                    font-size: 11px;
                    font-weight: 500;
                }
                
                QLabel#ConnectionStatus {
                    color: #4CAF50;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 10px 18px;
                    background-color: rgba(76, 175, 80, 0.15);
                    border-radius: 6px;
                }
                
                QToolButton#ThemeButton {
                    background-color: transparent;
                    color: #ffffff;
                    border: 2px solid #505050;
                    border-radius: 8px;
                    padding: 1px 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                QToolButton#ThemeButton:hover {
                    background-color: #3d3d3d;
                    border-color: #1976D2;
                }
                
                QPushButton#ActionButton_primary {
                    background-color: #1976D2;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_primary:hover {
                    background-color: #1565C0;
                }
                
                QPushButton#ActionButton_secondary {
                    background-color: transparent;
                    color: #ffffff;
                    border: 2px solid #505050;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_secondary:hover {
                    background-color: #3d3d3d;
                    border-color: #1976D2;
                }
                
                QProgressBar#ProgressBar {
                    background-color: #3d3d3d;
                    border: none;
                    border-radius: 6px;
                    text-align: center;
                    color: #ffffff;
                }
                
                QProgressBar#ProgressBar::chunk {
                    background-color: #1976D2;
                    border-radius: 6px;
                }
                
                QTextEdit#LogText {
                    background-color: #2d2d2d;
                    border: 1px solid #505050;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    color: #ffffff;
                }
            """
        else:
            # Tema claro
            stylesheet = """
                QMainWindow {
                    background-color: #f5f6f7;
                    color: #212121;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QWidget {
                    color: #212121;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QFrame#HeaderFrame {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 16px;
                }
                
                QFrame#ContentFrame {
                    background-color: transparent;
                }
                
                QFrame#FooterFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QWidget#ControlPanel {
                    background-color: transparent;
                }
                
                QWidget#StatusPanel {
                    background-color: transparent;
                }
                
                QFrame#ModernCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QFrame#StatusCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QLabel#MainTitle {
                    font-size: 28px;
                    font-weight: 700;
                    color: #212121;
                    margin-bottom: -8px;
                }
                
                QLabel#Subtitle {
                    font-size: 14px;
                    color: #666666;
                    font-weight: 400;
                }
                
                QLabel#Description {
                    font-size: 12px;
                    color: #9e9e9e;
                    margin-top: 8px;
                }
                
                QLabel#CardTitle {
                    font-size: 16px;
                    font-weight: 600;
                    color: #212121;
                }
                
                QLabel#StatusTitle {
                    font-size: 12px;
                    color: #666666;
                    font-weight: 500;
                }
                
                QLabel#FolderInfo {
                    font-size: 13px;
                    color: #666666;
                    padding: 12px;
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                }
                
                QLabel#ProgressLabel {
                    font-size: 13px;
                    color: #666666;
                    font-weight: 500;
                }
                
                QLabel#SummaryLabel {
                    font-size: 12px;
                    line-height: 1.5;
                    color: #212121;
                }
                
                QLabel#SystemInfo, QLabel#VersionInfo {
                    color: #9e9e9e;
                    font-size: 11px;
                    font-weight: 500;
                }
                
                QLabel#ConnectionStatus {
                    color: #4CAF50;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 10px 18px;
                    background-color: rgba(76, 175, 80, 0.1);
                    border-radius: 6px;
                }
                
                QToolButton#ThemeButton {
                    background-color: transparent;
                    color: #212121;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 1px 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                QToolButton#ThemeButton:hover {
                    background-color: #f5f5f5;
                    border-color: #1976D2;
                }
                
                QPushButton#ActionButton_primary {
                    background-color: #1976D2;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_primary:hover {
                    background-color: #1565C0;
                }
                
                QPushButton#ActionButton_secondary {
                    background-color: transparent;
                    color: #212121;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_secondary:hover {
                    background-color: #f5f5f5;
                    border-color: #1976D2;
                }
                
                QProgressBar#ProgressBar {
                    background-color: #f0f0f0;
                    border: none;
                    border-radius: 6px;
                    text-align: center;
                    color: #212121;
                }
                
                QProgressBar#ProgressBar::chunk {
                    background-color: #1976D2;
                    border-radius: 6px;
                }
                
                QTextEdit#LogText {
                    background-color: #fafafa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    color: #212121;
                }
            """
        
        self.setStyleSheet(stylesheet)
        
    def select_folder(self):
        """Seleccionar carpeta de archivos"""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con archivos .pqm")
        if folder:
            self.selected_folder = folder
            self.folder_info.setText(f"📂 Carpeta seleccionada:\n{folder}")
            # Simular detección de archivos
            self.folder_info.setText(f"📂 Carpeta seleccionada:\n{folder}\n\n✅ 32 archivos .pqm702 detectados")
            
    def generate_csv(self):
        """Generar archivos CSV"""
        if not self.selected_folder:
            self.folder_info.setText("⚠️ Selecciona una carpeta primero")
            return
            
        self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando generación de CSV...")
        self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📊 Procesando archivos en: {self.selected_folder}")
        
    def upload_to_db(self):
        """Subir archivos a base de datos"""
        if not self.selected_folder:
            self.folder_info.setText("⚠️ Selecciona una carpeta primero")
            return
            
        self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🗄️ Iniciando subida a base de datos...")
        self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔗 Conectando con PostgreSQL...")
        
    def execute_all(self):
        """Ejecutar proceso completo"""
        if not self.selected_folder:
            self.folder_info.setText("⚠️ Selecciona una carpeta primero")
            return
            
        self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚡ Iniciando proceso completo...")
        self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📁 Escaneando archivos...")
        
        # Simular animación de progreso
        self.animate_progress()
        
    def animate_progress(self):
        """Animar barra de progreso"""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(200)  # Actualizar cada 200ms
        
    def update_progress(self):
        """Actualizar progreso"""
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 1)
            
            # Actualizar etiqueta de progreso
            if current_value < 30:
                self.progress_label.setText("🔍 Escaneando archivos...")
            elif current_value < 60:
                self.progress_label.setText("📊 Extrayendo datos...")
            elif current_value < 90:
                self.progress_label.setText("🗄️ Subiendo a base de datos...")
            else:
                self.progress_label.setText("✅ Proceso completado")
        else:
            self.progress_timer.stop()
            self.log_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Proceso completado exitosamente")


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
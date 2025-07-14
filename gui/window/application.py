import os
import sys
import datetime
from PyQt5.QtCore import QTimer
from utils.ui_helper import UIHelpers
from styles.themes import ThemeManager
from components.panels.status_panel import StatusPanel
from components.panels.footer_panel import FooterPanel
from components.panels.header_panel import HeaderPanel
from components.panels.control_panel import ControlPanel
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QFileDialog)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

class SonelDataExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_folder = ""
        self.is_dark_mode = False
        self.theme_manager = ThemeManager()
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
        
        # Crear paneles
        self.header_panel = HeaderPanel(self)
        self.control_panel = ControlPanel(self)
        self.status_panel = StatusPanel(self)
        self.footer_panel = FooterPanel(self)
        
        # Contenido principal
        self.create_main_content(main_layout)
        
        # Aplicar tema inicial
        self.apply_theme()
        
        # Inicializar datos estáticos
        self.update_static_data()

        # Mostrar resumen general por defecto
        QTimer.singleShot(1000, self.update_general_summary)
        
    def create_main_content(self, layout):
        # Header
        layout.addWidget(self.header_panel)
        
        # Crear contenedor principal
        content_frame = QWidget()
        content_frame.setObjectName("ContentFrame")
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        
        # Panel izquierdo - Controles
        self.control_panel.setMaximumWidth(450)
        self.control_panel.setMinimumWidth(400)
        
        # Panel derecho - Estado y métricas
        self.status_panel.setMinimumWidth(600)
        
        content_layout.addWidget(self.control_panel)
        content_layout.addWidget(self.status_panel)
        
        # Configurar stretch factors
        content_layout.setStretchFactor(self.control_panel, 0)
        content_layout.setStretchFactor(self.status_panel, 1)
        
        layout.addWidget(content_frame)
        
        # Footer
        layout.addWidget(self.footer_panel)
        
    def update_static_data(self):
        # Actualizar resumen ejecutivo
        summary_text = f"""
<b>Estado General:</b> En progreso (87% completado)<br>
<b>Archivos Detectados:</b> 32 archivos .pqm702<br>
<b>Procesados Exitosamente:</b> 28 archivos<br>
<b>Con Advertencias:</b> 3 archivos (datos fuera de rango)<br>
<b>Con Errores:</b> 1 archivo (corrupción de datos)<br><br>
<b>Métricas de Datos:</b><br>
- Registros de voltaje extraídos: 18,542<br>
- Registros de corriente: 18,542<br>
- Registros de frecuencia: 18,542<br><br>
<b>Performance:</b><br>
- Tiempo de procesamiento: 4:12 min<br>
- Velocidad promedio: 6.7 archivos/min<br>
- Tiempo estimado restante: 2:15 min<br><br>
<b>Última Sincronización:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        self.status_panel.update_summary(summary_text)
        
    def toggle_theme(self):
        """Cambiar entre modo claro y oscuro"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        
        # Actualizar texto del botón
        if self.is_dark_mode:
            self.header_panel.update_theme_button_text("☀️ Modo Claro")
        else:
            self.header_panel.update_theme_button_text("🌙 Modo Oscuro")
        
    def apply_theme(self):
        """Aplicar tema claro u oscuro"""
        stylesheet = self.theme_manager.get_stylesheet(self.is_dark_mode)
        self.setStyleSheet(stylesheet)
        
    def select_folder(self):
        """Seleccionar carpeta de archivos"""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con archivos .pqm")
        if folder:
            self.selected_folder = folder
            self.control_panel.update_folder_info(f"📂 Carpeta seleccionada:\n{folder}")
            # Simular detección de archivos
            self.control_panel.update_folder_info(f"📂 Carpeta seleccionada:\n{folder}\n\n✅ 32 archivos .pqm702 detectados")
            
    def generate_csv(self):
        """Generar archivos CSV"""
        if not self.selected_folder:
            self.control_panel.update_folder_info("⚠️ Selecciona una carpeta primero")
            UIHelpers.warn_select_folder(self)
            return
            
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando generación de CSV...")
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📊 Procesando archivos en: {self.selected_folder}")
        
        # Simular datos de resultado de extracción CSV
        csv_results = {
            'status': 'success',
            'total_files': 32,
            'processed_files': 30,
            'errors': 2,
            'total_records': 18542,
            'execution_time': '4:12',
            'avg_speed': '6.7 archivos/min',
            'files': [
                {
                    'filename': 'medicion_20240301.pqm702',
                    'status': '✅ Exitoso',
                    'records': 847,
                    'size': '2.3 MB',
                    'message': 'Procesado correctamente'
                },
                {
                    'filename': 'medicion_20240302.pqm702',
                    'status': '✅ Exitoso',
                    'records': 823,
                    'size': '2.1 MB',
                    'message': 'Procesado correctamente'
                },
                {
                    'filename': 'medicion_20240303.pqm702',
                    'status': '❌ Error',
                    'records': 0,
                    'size': '1.8 MB',
                    'message': 'Archivo corrupto'
                },
                {
                    'filename': 'medicion_20240304.pqm702',
                    'status': '⚠️ Advertencia',
                    'records': 765,
                    'size': '2.0 MB',
                    'message': 'Datos fuera de rango'
                }
            ]
        }
        
        # Actualizar panel de resultados
        self.status_panel.update_csv_results(csv_results)
        
    # 2. Modificar el método upload_to_db():
    def upload_to_db(self):
        """Subir archivos a base de datos"""
        if not self.selected_folder:
            self.control_panel.update_folder_info("⚠️ Selecciona una carpeta primero")
            UIHelpers.warn_select_folder(self)
            return
            
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🗄️ Iniciando subida a base de datos...")
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔗 Conectando con PostgreSQL...")
        
        # Simular datos de resultado de subida a BD
        db_results = {
            'status': 'success',
            'uploaded_files': 28,
            'failed_uploads': 2,
            'inserted_records': 18542,
            'conflicts': 3,
            'connection_status': 'Conectado',
            'files': [
                {
                    'filename': 'output_20240301.csv',
                    'status': '✅ Subido',
                    'records': 847,
                    'table': 'measurements',
                    'time': '00:15',
                    'error': ''
                },
                {
                    'filename': 'output_20240302.csv',
                    'status': '✅ Subido',
                    'records': 823,
                    'table': 'measurements',
                    'time': '00:14',
                    'error': ''
                },
                {
                    'filename': 'output_20240303.csv',
                    'status': '❌ Error',
                    'records': 0,
                    'table': 'measurements',
                    'time': '00:02',
                    'error': 'Constraint violation'
                }
            ]
        }
        
        # Actualizar panel de resultados
        self.status_panel.update_db_results(db_results)

    # 3. Modificar el método execute_all():
    def execute_all(self):
        """Ejecutar proceso completo"""
        if not self.selected_folder:
            self.control_panel.update_folder_info("⚠️ Selecciona una carpeta primero")
            UIHelpers.warn_select_folder(self)
            return
            
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚡ Iniciando proceso completo...")
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📁 Escaneando archivos...")
        
        # Simular animación de progreso
        self.animate_progress()
        
        # Simular datos de resultado de ejecución completa
        complete_results = {
            'overall_status': 'success',
            'total_execution_time': '6:27',
            'total_records': 18542,
            'efficiency': 87,
            'start_time': '2024-07-10 15:42:18',
            'end_time': '2024-07-10 15:48:45',
            'csv_phase': {
                'status': 'success',
                'execution_time': '4:12',
                'processed_files': 30
            },
            'db_phase': {
                'status': 'success',
                'execution_time': '2:15',
                'uploaded_files': 28,
                'inserted_records': 18542
            },
            'observations': 'Proceso ejecutado exitosamente con 2 archivos omitidos por corrupción.'
        }
        
        # Actualizar panel de resultados después de completar
        QTimer.singleShot(5000, lambda: self.status_panel.update_complete_results(complete_results))

    def update_general_summary(self):
        """Actualizar resumen general con datos históricos mejorados"""
        general_data = {
            'total_processed': 156,
            'total_time': '28:45',
            'successful': 142,
            'failed': 14,
            'history': """
    <b>📊 Estadísticas Generales:</b><br>
    • Total de ejecuciones: 23<br>
    • Archivos procesados: 156<br>
    • Tasa de éxito: 91.0%<br>
    • Tiempo promedio por ejecución: 5:45 min<br><br>
    <b>🕒 Últimas Ejecuciones:</b><br>
    • 2024-07-10 15:42 - ✅ Completo (30 archivos, 6:27 min)<br>
    • 2024-07-09 14:20 - ⚠️ Parcial (28 archivos, 5:12 min)<br>
    • 2024-07-08 09:15 - ✅ Completo (32 archivos, 7:03 min)<br>
    • 2024-07-07 16:30 - ❌ Fallido (error conexión BD)<br>
    • 2024-07-06 11:45 - ✅ Completo (29 archivos, 4:58 min)<br><br>
    <b>📈 Tendencias del Mes:</b><br>
    • Promedio diario: 7.8 archivos<br>
    • Pico de rendimiento: 32 archivos (2024-07-08)<br>
    • Eficiencia en aumento: +12% vs mes anterior<br>
    • Downtime total: 0.3% (mantenimiento programado)
            """
        }
        
        self.status_panel.update_general_results(general_data)

    def animate_progress(self):
        """Animar barra de progreso"""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(200)  # Actualizar cada 200ms
        
    def update_progress(self):
        """Actualizar progreso"""
        current_value = self.control_panel.get_progress_value()
        if current_value < 100:
            self.control_panel.set_progress_value(current_value + 1)
            
            # Actualizar etiqueta de progreso
            if current_value < 30:
                self.control_panel.update_progress_label("🔍 Escaneando archivos...")
            elif current_value < 60:
                self.control_panel.update_progress_label("📊 Extrayendo datos...")
            elif current_value < 90:
                self.control_panel.update_progress_label("🗄️ Subiendo a base de datos...")
            else:
                self.control_panel.update_progress_label("✅ Proceso completado")
        else:
            self.progress_timer.stop()
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Proceso completado exitosamente")
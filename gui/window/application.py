import os
import sys
import json
import datetime
import traceback
from PyQt5.QtCore import QTimer
from gui.utils.ui_helper import UIHelpers
from gui.styles.themes import ThemeManager
from gui.components.panels.status_panel import StatusPanel
from gui.components.panels.footer_panel import FooterPanel
from gui.components.panels.header_panel import HeaderPanel
from gui.components.panels.control_panel import ControlPanel
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QFileDialog)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from core.controller.sonel_controller import SonelController

class SonelDataExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_folder = ""
        self.is_dark_mode = False
        self.theme_manager = ThemeManager()

        try:
            self.controller = SonelController()
        except Exception as e:
            print(f"⚠️ Error inicializando controlador: {e}")
            self.controller = None

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

         # Esto permite que execute_all acceda a los tabs individuales
        self.setup_tab_references()
        
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


    def setup_tab_references(self):
        """Configurar referencias a los tabs para actualizaciones directas"""
        try:
            # Verificar si el status_panel tiene execution_summary_panel
            if hasattr(self.status_panel, 'execution_summary_panel'):
                panel = self.status_panel.execution_summary_panel
                
                # Verificar si tiene tab_widget (no 'tabs')
                if hasattr(panel, 'tab_widget'):
                    # Obtener referencias a cada tab
                    for i in range(panel.tab_widget.count()):
                        tab_widget = panel.tab_widget.widget(i)
                        tab_text = panel.tab_widget.tabText(i)
                        
                        # Asignar referencias basadas en el nombre del tab
                        if "General" in tab_text:
                            if hasattr(tab_widget, 'refresh_data'):
                                panel.general_tab_ref = tab_widget
                            # Verificar si tiene el nuevo método de actualización CSV
                            if hasattr(tab_widget, 'update_after_csv_processing'):
                                panel.general_tab_csv_update_ref = tab_widget
                        elif "CSV" in tab_text and hasattr(tab_widget, 'refresh_data'):
                            panel.csv_tab_ref = tab_widget
                        elif "Base de Datos" in tab_text and hasattr(tab_widget, 'refresh_data'):
                            panel.db_tab_ref = tab_widget
            
            print("Referencias a tabs configuradas correctamente (incluyendo actualización CSV)")
        
        except Exception as e:
            print(f"Error configurando referencias a tabs: {e}")

    def load_summary_data(self):
        """Cargar datos de resumen desde archivos JSON"""
        csv_data = self.load_json_file("data/archivos_csv/resumen_csv.json")
        etl_data = self.load_json_file("data/archivos_csv/resumen_etl.json")
        return csv_data, etl_data

    def load_json_file(self, file_path):
        """Cargar archivo JSON de forma segura"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                print(f"Archivo no encontrado: {file_path}")
                return {}
        except Exception as e:
            print(f"Error al cargar {file_path}: {e}")
            return {}
        
    def update_static_data(self):
        """Actualizar datos estáticos desde archivos JSON"""
        
        # Cargar datos reales
        csv_data, etl_data = self.load_summary_data()
        
        # Obtener resúmenes
        csv_summary = csv_data.get('csv_summary', {})
        etl_summary = etl_data.get('overall_summary', {})
        
        # Si hay datos reales, usarlos; si no, mostrar estado inicial
        if csv_summary.get('total_files', 0) > 0 or etl_summary.get('total_files', 0) > 0:
            # Calcular porcentaje de completado
            total_files = max(csv_summary.get('total_files', 0), etl_summary.get('total_files', 0))
            processed_files = csv_summary.get('processed_files', 0)
            completion_percentage = (processed_files / total_files) * 100 if total_files > 0 else 0
            
            # Obtener timestamp de generación
            metadata = etl_data.get('metadata', {})
            generated_at = metadata.get('generated_at', datetime.datetime.now().isoformat())
            
            try:
                # Convertir timestamp ISO a formato legible
                dt = datetime.datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Actualizar resumen ejecutivo con datos reales
            summary_text = f"""
                <b>Estado General:</b> {etl_summary.get('overall_status', 'Procesando')} ({completion_percentage:.1f}% completado)<br>
                <b>Archivos Detectados:</b> {total_files} archivos .pqm<br>
                <b>Procesados Exitosamente:</b> {processed_files} archivos<br>
                <b>Con Advertencias:</b> {csv_summary.get('warnings', 0)} archivos<br>
                <b>Con Errores:</b> {csv_summary.get('errors', 0)} archivos<br><br>
                <b>Performance:</b><br>
                - Tiempo extracción CSV: {csv_summary.get('execution_time', '0:00')}<br>
                - Tiempo carga BD: {etl_summary.get('total_time', '0:00')}<br>
                - Velocidad promedio: {csv_summary.get('avg_speed', '0 archivos/min')}<br>
                - Registros procesados: {etl_summary.get('data_processed', 0):,}<br><br>
                <b>Base de Datos:</b><br>
                - Estado conexión: {etl_summary.get('connection_status', 'Desconectado')}<br>
                - Tamaño procesado: {etl_summary.get('data_size', '0 MB')}<br><br>
                <b>Última Actualización:</b> {formatted_time}
            """
        else:
            # Datos iniciales cuando no hay procesamiento previo
            summary_text = f"""
                <b>Estado General:</b> Sistema listo<br>
                <b>Archivos Detectados:</b> 0 archivos .pqm<br>
                <b>Procesados Exitosamente:</b> 0 archivos<br>
                <b>Con Advertencias:</b> 0 archivos<br>
                <b>Con Errores:</b> 0 archivos<br><br>
                <b>Performance:</b><br>
                - Tiempo de procesamiento: 0:00 min<br>
                - Velocidad promedio: 0 archivos/min<br>
                - Tiempo estimado restante: 0:00 min<br><br>
                <b>Última Sincronización:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
                    
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

    def generate_csv(self):
        """Generar archivos CSV usando el controlador"""
        
        # Verificar que el controlador esté disponible
        if not self.controller:
            self.control_panel.update_folder_info("❌ Error: Controlador no disponible")
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error: Controlador no inicializado")
            
            UIHelpers.show_error_message(
                self,
                "Controlador No Disponible",
                "El sistema de procesamiento no está disponible.",
                "Reinicia la aplicación e intenta nuevamente."
            )
            return
        
        self.control_panel.start_progress("Iniciando generación de CSV...")
        
        # Actualizar el directorio de entrada del controlador
        try:
            self.controller.rutas["input_directory"] = self.selected_folder
        except Exception as e:
            error_msg = f"Error configurando ruta: {str(e)}"
            self.control_panel.update_folder_info(f"❌ Error configurando ruta: {str(e)}")
            
            UIHelpers.show_error_message(
                self,
                "Error de Configuración",
                "No se pudo configurar la ruta de procesamiento.",
                f"Detalles: {error_msg}\n\nSelecciona nuevamente la carpeta de archivos."
            )
            return
        
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Iniciando generación de CSV...")
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Procesando archivos en: {self.selected_folder}")
        
        # Ejecutar extracción usando el controlador
        try:
            success, extraction_summary = self.controller.run_pywinauto_extraction()
        
            # Verificar que extraction_summary es un diccionario
            if not isinstance(extraction_summary, dict):
                raise ValueError(f"El controlador devolvió un tipo inválido: {type(extraction_summary)}")
            
            # Extraer datos del resumen
            extracted_files = extraction_summary.get('extracted_files', 0)
            
            if success:
                # Generar resultados basados en el resultado real
                csv_results = {
                    'status': 'success' if extracted_files > 0 else 'completed',
                    'total_files': extraction_summary.get('total_files', 0),
                    'processed_files': extraction_summary.get('processed_files', 0),
                    'errors': extraction_summary.get('errors', 0),
                    'warnings': extraction_summary.get('warnings', 0),
                    'csv_files_generated': extraction_summary.get('csv_files_generated', 0),
                    'total_records': extraction_summary.get('csv_files_generated', 0) * 3278,
                    'execution_time': extraction_summary.get('execution_time', '0:00'),
                    'avg_speed': '6.7 archivos/min' if extracted_files > 0 else '0 archivos/min',
                    'files': extraction_summary.get('files_detail', [])
                }
                
                self.control_panel.set_progress_value(100)
                
                if extracted_files > 0:
                    self.control_panel.update_progress_label(" Archivos nuevos procesados exitosamente")
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Extracción completada: {extracted_files} archivos nuevos procesados")
                else:
                    self.control_panel.update_progress_label(" Archivos procesados exitosamente")
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Todos los archivos ya estaban procesados")

                UIHelpers.show_success_message(
                    self,
                    "Extracción CSV Completada",
                    f"Se procesaron exitosamente los archivos nuevos.",
                    f"Los archivos están listos para ser cargados a la base de datos."
                )
            else:
                error_message = extraction_summary.get('error_message', 'Error desconocido')
                csv_results = {
                    'status': 'error',
                    'total_files': extraction_summary.get('total_files', 0),
                    'processed_files': 0,
                    'errors': extraction_summary.get('errors', 1),
                    'warnings': 0,
                    'csv_files_generated': 0,
                    'total_records': 0,
                    'execution_time': '0:00',
                    'avg_speed': '0 archivos/min',
                    'files': []
                }
                
                self.control_panel.reset_progress()
                self.control_panel.update_progress_label(f"❌ Error: {error_message}")
                self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error en la extracción: {error_message}")
            
                UIHelpers.show_error_message(
                    self,
                    "Error en la Extracción CSV",
                    "No se pudo completar la extracción de archivos CSV.",
                    f"Motivo: {error_message}\n\nRevisa los archivos de entrada y vuelve a intentar."
                )

            # Actualizar panel de resultados
            self.status_panel.update_csv_results(csv_results)

            # === Actualizar tab general después del procesamiento CSV ===
            try:
                if success and hasattr(self.status_panel, 'execution_summary_panel'):
                    # Obtener referencia al tab general
                    execution_panel = self.status_panel.execution_summary_panel
                    
                    # Verificar si tiene tab_widget y encontrar el tab general
                    if hasattr(execution_panel, 'tab_widget'):
                        for i in range(execution_panel.tab_widget.count()):
                            tab_widget = execution_panel.tab_widget.widget(i)
                            tab_text = execution_panel.tab_widget.tabText(i)
                            
                            # Si es el tab general, actualizarlo
                            if "General" in tab_text and hasattr(tab_widget, 'update_after_csv_processing'):
                                # Preparar datos para actualización del tab general
                                csv_update_data = {
                                    'processed_files': csv_results.get('processed_files', 0),
                                    'total_files': csv_results.get('total_files', 0),
                                    'errors': csv_results.get('errors', 0),
                                    'warnings': csv_results.get('warnings', 0),
                                    'execution_time': csv_results.get('execution_time', '0:00'),
                                    'status': csv_results.get('status', 'unknown'),
                                    'extracted_files': extraction_summary.get('extracted_files', 0)
                                }
                                
                                # Actualizar el tab general con los datos CSV
                                tab_widget.update_after_csv_processing(csv_update_data)
                                
                                # Log de la actualización
                                self.status_panel.add_log_entry(
                                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                                    f"📊 Tab General actualizado con datos CSV"
                                )
                                break
                                
                # También actualizar los datos estáticos generales
                self.update_static_data()
                
            except Exception as update_error:
                # Error no crítico - solo log
                self.status_panel.add_log_entry(
                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                    f"⚠️ Error actualizando tab general: {str(update_error)}"
                )
                print(f"Error actualizando tab general después de CSV: {update_error}")
            
        except Exception as e:
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)}")
            self.control_panel.reset_progress()
            self.control_panel.update_progress_label("❌ Error crítico")
            print(f"Error en generate_csv: {e}")
            traceback.print_exc()
        
    def _generate_file_details(self, extracted_files):
        """Genera detalles simulados de archivos para compatibilidad con la GUI"""
        files_details = []
        
        # Si no hay archivos extraídos, generar datos de ejemplo
        if extracted_files <= 0:
            return files_details
        
        for i in range(extracted_files):
            files_details.append({
                "filename": f"archivo_{i+1:03d}.pqm702",
                "status": "✅ Exitoso",
                "records": f"{3278 + (i * 50)}",  # Registros variables
                "size": f"{2.1 + (i * 0.1):.1f} MB",
                "message": "Procesado correctamente"
            })
        
        return files_details

    # 2. Modificar el método upload_to_db():
    def upload_to_db(self):
        """Subir archivos a base de datos usando el controlador"""
        
        # Verificar que el controlador esté disponible
        if not self.controller:
            self.control_panel.update_folder_info("❌ Error: Controlador no disponible")
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error: Controlador no inicializado")
            
            UIHelpers.show_error_message(
                self,
                "Controlador No Disponible",
                "El sistema de procesamiento no está disponible.",
                "Reinicia la aplicación e intenta nuevamente."
            )
            return
        
        self.control_panel.start_progress("Iniciando subida a base de datos...")

        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Iniciando subida a base de datos...")
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Conectando con PostgreSQL...")
        
        try:
            # Ejecutar procesamiento ETL usando el controlador
            success, summary_data = self.controller.run_etl_processing(force_reprocess=False)

               # Verificar que summary_data es un diccionario
            if not isinstance(summary_data, dict):
                raise ValueError(f"El controlador devolvió un tipo inválido: {type(summary_data)}")
            
            uploaded_files = summary_data.get('uploaded_files', 0)
            failed_uploads = summary_data.get('failed_uploads', 0)
            
            if success:
                self.control_panel.set_progress_value(100)

                if uploaded_files > 0:
                    self.control_panel.update_progress_label(" Archivos nuevos procesados exitosamente")
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}]  Procesamiento completado: {uploaded_files} archivos nuevos subidos")
                else:
                    self.control_panel.update_progress_label(" Archivos procesados exitosamente")
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Todos los archivos ya estaban en la base de datos")
                
                UIHelpers.show_success_message(
                    self,
                    "Carga a Base de Datos Exitosa",
                    f"Se subieron exitosamente los archivos a la base de datos.",
                    f"Los datos están disponibles para consulta."
                )

                # Convertir el resumen del controlador al formato GUI
                db_results = self._convert_summary_to_db_format(summary_data)
                self.status_panel.update_db_results(db_results)

                # === Actualizar tab general después del procesamiento DB ===
                try:
                    if success and hasattr(self.status_panel, 'execution_summary_panel'):
                        # Obtener referencia al tab general
                        execution_panel = self.status_panel.execution_summary_panel
                        
                        # Verificar si tiene tab_widget y encontrar el tab general
                        if hasattr(execution_panel, 'tab_widget'):
                            for i in range(execution_panel.tab_widget.count()):
                                tab_widget = execution_panel.tab_widget.widget(i)
                                tab_text = execution_panel.tab_widget.tabText(i)
                                
                                # Si es el tab general, actualizarlo
                                if "General" in tab_text and hasattr(tab_widget, 'update_after_db_processing'):
                                    # Preparar datos para actualización del tab general
                                    db_update_data = {
                                        'uploaded_files': db_results.get('uploaded_files', 0),
                                        'failed_uploads': db_results.get('failed_uploads', 0),
                                        'inserted_records': db_results.get('inserted_records', 0),
                                        'upload_time': db_results.get('upload_time', '0:00'),
                                        'connection_status': db_results.get('connection_status', 'Desconocido'),
                                        'data_size': db_results.get('data_size', '0 MB'),
                                        'success_rate': db_results.get('success_rate', 0),
                                        'status': db_results.get('status', 'unknown'),
                                        'total_files': summary_data.get('total_files', 0)
                                    }
                                    
                                    # Actualizar el tab general con los datos DB
                                    tab_widget.update_after_db_processing(db_update_data)
                                    
                                    # Log de la actualización
                                    self.status_panel.add_log_entry(
                                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                                        f"📊 Tab General actualizado con datos de BD"
                                    )
                                    break
                                    
                    # También actualizar los datos estáticos generales
                    self.update_static_data()
                    
                except Exception as update_error:
                    # Error no crítico - solo log
                    self.status_panel.add_log_entry(
                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                        f"⚠️ Error actualizando tab general: {str(update_error)}"
                    )
                    print(f"Error actualizando tab general después de DB: {update_error}")

            else:
                error_message = summary_data.get('error_message', 'Error desconocido en el procesamiento')
            
                self.control_panel.reset_progress()
                self.control_panel.update_progress_label(f"❌ Error: {error_message}")
                self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error en el procesamiento: {error_message}")
                
                UIHelpers.show_error_message(
                    self,
                    "Error en la Carga a Base de Datos",
                    "No se pudo completar la carga de datos a la base de datos.",
                    f"Motivo: {error_message}\n\nVerifica la conexión a la base de datos y vuelve a intentar."
                )

                # Mostrar error en la GUI
                error_data = {
                    'status': 'error',
                    'uploaded_files': 0,
                    'failed_uploads': failed_uploads if failed_uploads > 0 else 1,
                    'inserted_records': 0,
                    'conflicts': 0,
                    'connection_status': 'Error',
                    'files': [],
                    'upload_time': '0:00',
                    'success_rate': 0
                }
                self.status_panel.update_db_results(error_data)
                
        except Exception as e:
            error_msg = str(e)
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error crítico: {error_msg}")
            
            self.control_panel.reset_progress()
            self.control_panel.update_progress_label(f"❌ Error crítico: {error_msg}")

            UIHelpers.show_error_message(
                self,
                "Error Crítico en Base de Datos",
                "Ocurrió un error inesperado durante la carga a la base de datos.",
                f"Detalles técnicos: {error_msg}\n\nContacta al administrador de la base de datos."
            )
            
            # Mostrar error crítico en la GUI
            error_data = {
                'status': 'error',
                'uploaded_files': 0,
                'failed_uploads': 1,
                'inserted_records': 0,
                'conflicts': 0,
                'connection_status': 'Error crítico',
                'files': [],
                'upload_time': '0:00',
                'success_rate': 0
            }
            self.status_panel.update_db_results(error_data)
            
            print(f"Error en upload_to_db: {e}")
            traceback.print_exc()

    def _convert_summary_to_db_format(self, summary_data):
        """Convertir el formato del core al formato que espera la GUI"""
        return {
            'status': 'success' if summary_data.get('overall_status') == '✅ Completado' else 'partial',
            'uploaded_files': summary_data.get('db_uploaded', 0),
            'failed_uploads': summary_data.get('total_errors', 0),
            'inserted_records': summary_data.get('data_processed', 0),
            'conflicts': 0,  # Puedes extraer esto de los archivos con status específico si lo necesitas
            'connection_status': summary_data.get('connection_status', 'Desconocido'),
            'upload_time': summary_data.get('total_time', '0:00'),
            'success_rate': summary_data.get('success_rate', 0),
            'data_size': summary_data.get('data_size', '0 bytes'),
            'files': summary_data.get('files', [])
        }

    # 3. Modificar el método execute_all():
    def execute_all(self):
        """Ejecutar proceso completo usando el controlador"""
        
        # Verificar que el controlador esté disponible
        if not self.controller:
            self.control_panel.update_folder_info("❌ Error: Controlador no disponible")
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error: Controlador no inicializado")
            
            UIHelpers.show_error_message(
                self,
                "Controlador No Disponible",
                "El sistema de procesamiento no está disponible.",
                "Reinicia la aplicación e intenta nuevamente."
            )
            return
        
        self.control_panel.start_progress("Iniciando proceso completo...")
        
        # Actualizar el directorio de entrada del controlador
        try:
            self.controller.rutas["input_directory"] = self.selected_folder
        except Exception as e:
            self.control_panel.update_folder_info(f"❌ Error configurando ruta: {str(e)}")
            return
        
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando proceso completo...")
        self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📂 Procesando archivos en: {self.selected_folder}")
        
        # Simular animación de progreso
        self.animate_progress()
        
        try:
            # Ejecutar workflow completo usando el controlador
            success, complete_summary = self.controller.run_complete_workflow(
                force_reprocess=False,
                skip_gui=False,
                skip_etl=False
            )
            
            # Verificar que complete_summary es un diccionario
            if not isinstance(complete_summary, dict):
                raise ValueError(f"El controlador devolvió un tipo inválido: {type(complete_summary)}")
            
            # Detener animación de progreso
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()
            
            # Actualizar progreso al 100%
            self.control_panel.set_progress_value(100)
            
            # NUEVA LLAMADA UNIFICADA - Reemplaza todo el código de actualización anterior
            self.status_panel.update_complete_workflow_results(complete_summary)
            
            # Logs y mensajes finales
            extraction_summary = complete_summary.get('extraction_summary', {})
            db_summary = complete_summary.get('db_summary', {})
            
            # === ACTUALIZAR LOGS ===
            if success:
                extracted_files = extraction_summary.get('csv_files_generated', 0)
                uploaded_files = db_summary.get('uploaded_files', 0)
                
                if extracted_files > 0:
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Extracción CSV: {extracted_files} archivos procesados")
                else:
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Extracción CSV: Todos los archivos ya procesados")
                
                if uploaded_files > 0:
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Base de datos: {uploaded_files} archivos subidos")
                else:
                    self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Base de datos: Todos los archivos ya estaban procesados")
                
                self.control_panel.update_progress_label("Proceso completo exitoso")
                self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Proceso completo finalizado exitosamente")
            else:
                self.control_panel.update_progress_label("Proceso completado con advertencias")
                self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Proceso completado con advertencias")
                
            # Actualizar datos estáticos y resumen general
            self.update_static_data()
            
            # === REFRESCAR TODOS LOS TABS DESDE JSON (DATOS MÁS ACTUALES) ===
            # Esto asegura que los tabs muestren los datos más recientes desde los archivos JSON
            QTimer.singleShot(2000, self._refresh_all_tabs_after_complete)
            
        except Exception as e:
            # Detener animación en caso de error
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()
                
            error_time = datetime.datetime.now().strftime('%H:%M:%S')
            error_msg = str(e)
            
            self.status_panel.add_log_entry(f"[{error_time}] ❌ Error durante la ejecución: {error_msg}")
            self.control_panel.reset_progress()
            self.control_panel.update_progress_label(f"❌ Error: {error_msg}")
            
            # Mostrar error en los paneles
            error_csv_data = {
                'status': 'error',
                'total_files': 0,
                'processed_files': 0,
                'errors': 1,
                'warnings': 0,
                'csv_files_generated': 0,
                'total_records': 0,
                'execution_time': '0:00',
                'avg_speed': '0 archivos/min',
                'files': []
            }
            
            error_db_data = {
                'status': 'error',
                'uploaded_files': 0,
                'failed_uploads': 1,
                'inserted_records': 0,
                'conflicts': 0,
                'connection_status': 'Error crítico',
                'files': [],
                'upload_time': '0:00',
                'success_rate': 0
            }
            
            self.status_panel.update_csv_results(error_csv_data)
            self.status_panel.update_db_results(error_db_data)
            
            # Actualizar tabs con datos de error
            if hasattr(self.status_panel, 'execution_summary_panel') and hasattr(self.status_panel.execution_summary_panel, 'update_csv_summary'):
                self.status_panel.update_csv_results(error_csv_data)
            
            if hasattr(self.status_panel, 'execution_summary_panel') and hasattr(self.status_panel.execution_summary_panel, 'update_db_summary'):
                self.status_panel.update_db_results(error_db_data)
            
            print(f"Error en execute_all: {e}")
            traceback.print_exc()

    def _refresh_all_tabs_after_complete(self):
        """Refrescar todos los tabs después del proceso completo"""
        try:
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔄 Actualizando información de tabs...")
            
            # Refrescar CSV Tab
            if hasattr(self.status_panel, 'execution_summary_panel') and hasattr(self.status_panel.execution_summary_panel, 'refresh_all_tabs'):
                self.status_panel.execution_summary_panel.refresh_all_tabs()
                print("CSV Tab actualizado")
            
            # Refrescar DB Tab  
            if hasattr(self.status_panel, 'execution_summary_panel') and hasattr(self.status_panel.execution_summary_panel, 'refresh_all_tabs'):
                self.status_panel.execution_summary_panel.refresh_all_tabs()
                print("DB Tab actualizado")
                
            # Refrescar General Tab con método específico para proceso completo
            if hasattr(self.status_panel, 'execution_summary_panel'):
                if hasattr(self.status_panel.execution_summary_panel, 'refresh_data_after_complete_process'):
                    self.status_panel.execution_summary_panel.refresh_data_after_complete_process()
                elif hasattr(self.status_panel.execution_summary_panel, 'refresh_data'):
                    self.status_panel.execution_summary_panel.refresh_all_tabs()
                print("General Tab actualizado")
            
            # Actualizar datos estáticos generales también  
            self.update_static_data()
            
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Información de tabs actualizada")
            
        except Exception as refresh_error:
            print(f"Error refrescando tabs después del proceso completo: {refresh_error}")
            self.status_panel.add_log_entry(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Error actualizando información de tabs")

    def update_general_summary(self):
        """Actualizar resumen general con datos reales desde JSON"""
        
        # Cargar datos reales
        csv_data, etl_data = self.load_summary_data()
        
        # Obtener resúmenes
        csv_summary = csv_data.get('csv_summary', {})
        etl_summary = etl_data.get('overall_summary', {})
        db_summary = etl_data.get('database_summary', {})
        
        # Preparar datos para el status panel
        general_data = {
            'total_processed': f"{csv_summary.get('processed_files', 0)} / {csv_summary.get('total_files', 0)}",
            'total_time': csv_summary.get('warnings', 0),
            'successful': csv_summary.get('errors', 0),
            'failed': f"{etl_summary.get('db_uploaded', 0)} / {etl_summary.get('total_files', 0)}",
            'history': self._generate_history_text(etl_data)
        }
        
        self.status_panel.update_general_results(general_data)

    def animate_progress(self):
        """Animar barra de progreso"""
        # Asegurar que comience desde 1% para mostrar que está activo
        if self.control_panel.get_progress_value() == 0:
            self.control_panel.set_progress_value(1)
        
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(200)  # Actualizar cada 200ms

    def _generate_history_text(self, etl_data):
        """Generar texto de historial basado en datos ETL"""
        
        failed_files = etl_data.get('failed_files_list', [])
        successful_files = etl_data.get('database_summary', {}).get('uploaded_files', 0)
        
        if not failed_files and successful_files > 0:
            return "<b>✅ Todos los archivos procesados exitosamente</b>"
        elif failed_files:
            history_text = f"""
                <b>Últimos Archivos Procesados:</b><br>
                - Exitosos: {successful_files}<br>
                - Con errores: {len(failed_files)}<br><br>
                <b>Archivos con Problemas:</b><br>
                {', '.join(failed_files[:3])}{'...' if len(failed_files) > 3 else ''}
            """
            return history_text
        else:
            return "<b>ℹ️ No hay historial de procesamiento disponible</b>"

    # 6. Agregar método para refrescar datos desde JSON
    def refresh_all_data(self):
        """Refrescar todos los datos desde archivos JSON"""
        self.update_static_data()
        self.update_general_summary()
        
        # También refrescar datos en el status panel si tiene tabs
        if hasattr(self.status_panel, 'refresh_tabs_data'):
            self.status_panel.refresh_tabs_data()

        
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

    def closeEvent(self, event):
        """Manejar cierre de la aplicación - limpiar recursos"""
        try:
            # Limpiar el analyzer de carpetas
            if hasattr(self.control_panel, 'cleanup_folder_analyzer'):
                self.control_panel.cleanup_folder_analyzer()
            
            # Limpiar otros recursos si existen
            if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
                self.progress_timer.stop()
                
            print("Aplicación cerrada correctamente")
            event.accept()
            
        except Exception as e:
            print(f"Error al cerrar aplicación: {e}")
            event.accept()
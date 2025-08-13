import os
import json
import traceback
from PyQt5.QtCore import Qt
from gui.utils.ui_helper import UIHelpers
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard
from core.controller.sonel_controller import SonelController
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton

class CsvTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("CsvTab")
        self.csv_data = self.load_csv_summary()

        try:
            self.controller = SonelController()
        except Exception as e:
            print(f"⚠️ Error inicializando controlador: {e}")
            self.controller = None

        self.init_ui()
        
    def init_ui(self):
        """Crear tab de extracción CSV con información del JSON"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES EN CARDS ===
        csv_metrics_widget = QWidget()
        csv_metrics_layout = QGridLayout(csv_metrics_widget)
        csv_metrics_layout.setSpacing(16)
        
        # Obtener datos del JSON cargado
        summary = self.csv_data.get('csv_summary', {})

        # Formatear tiempo de ejecución
        execution_time_raw = summary.get('execution_time', '0:00')
        execution_time_formatted = self.format_execution_time(execution_time_raw)
        
        # Crear tarjetas de métricas CSV con datos reales
        self.csv_cards = []
        csv_metrics_data = [
            ("📁", "Archivos Procesados", f"{summary.get('processed_files', 0)} / {summary.get('total_files', 0)}", "#4CAF50"),
            ("⚠️", "Advertencias", str(summary.get('warnings', 0)), "#FF9800"),
            ("❌", "Errores", str(summary.get('errors', 0)), "#F44336"),
            ("📄", "CSVs Generados", str(summary.get('csv_files_generated', 0)), "#3F51B5"),
            ("⏱️", "Tiempo Extracción", execution_time_formatted, "#9C27B0"),
            ("🔗", "Conexión", 'Estable', "#607D8B"),
        ]
        
        for i, (icon, title, value, color) in enumerate(csv_metrics_data):
            row = i // 3
            col = i % 3
            status_card = StatusCard(icon, title, value, color)
            self.csv_cards.append(status_card)
            csv_metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(csv_metrics_widget)

        # === BOTÓN DE REPROCESAR SI HAY ERRORES ===
        if summary.get('errors', 0) > 0:
            self.reprocess_button = QPushButton("🔁 Reprocesar archivos")
            self.reprocess_button.setStyleSheet("padding: 8px; background-color: #F44336; color: white; border-radius: 6px;")
            self.reprocess_button.clicked.connect(self.confirm_reprocess_errors)
            layout.addWidget(self.reprocess_button, alignment=Qt.AlignLeft)
        
        # === TABLA DE ARCHIVOS PROCESADOS ===
        files_card = ModernCard("Detalle de Archivos Procesados")
        self.csv_files_table = QTableWidget()
        self.csv_files_table.setObjectName("FilesTable")
        self.setup_files_table(self.csv_files_table)
        
        # Poblar con datos del JSON
        files_data = self.csv_data.get('files_processed', [])
        self.populate_files_table(self.csv_files_table, files_data)
        
        files_card.layout().addWidget(self.csv_files_table)
        layout.addWidget(files_card)

    def load_csv_summary(self):
        """Cargar datos del resumen CSV desde el archivo JSON"""
        json_path = "data/archivos_csv/resumen_csv.json"
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                print(f"Archivo no encontrado: {json_path}")
                return self.get_default_data()
        except Exception as e:
            print(f"Error al cargar {json_path}: {e}")
            return self.get_default_data()
        
    def get_default_data(self):
        """Datos por defecto si no se puede cargar el JSON"""
        return {
            "csv_summary": {
                "processed_files": 0,
                "total_files": 0,
                "errors": 0,
                "warnings": 0,
                "csv_files_generated": 0,
                "execution_time": "0:00",
                "avg_speed": "0 archivos/min",
                "success_rate": 0.0,
                "total_records": 0
            },
            "files_processed": []
        }
    
    def refresh_data(self):
        """Refrescar datos desde el archivo JSON"""
        self.csv_data = self.load_csv_summary()
        
        # Actualizar métricas
        summary = self.csv_data.get('csv_summary', {})

        # Formatear tiempo de ejecución
        execution_time_raw = summary.get('execution_time', '0:00')
        execution_time_formatted = self.format_execution_time(execution_time_raw)

        metrics_values = [
            f"{summary.get('processed_files', 0)} / {summary.get('total_files', 0)}",
            str(summary.get('warnings', 0)),
            str(summary.get('errors', 0)),
            str(summary.get('csv_files_generated', 0)),
            execution_time_formatted
        ]
        
        # Actualizar cards
        for i, value in enumerate(metrics_values):
            if i < len(self.csv_cards):
                self.csv_cards[i].update_value(value)
        
        # Actualizar tabla
        files_data = self.csv_data.get('files_processed', [])
        self.populate_files_table(self.csv_files_table, files_data)
                
    def setup_files_table(self, table):
        """Configurar tabla de archivos CSV"""
        headers = ["#", "Archivo", "Estado", "Tiempo", "Archivo CSV", "Mensaje"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)     # "#" - mínimo necesario
        header.setSectionResizeMode(1, QHeaderView.Stretch)              # "Archivo"
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)     # "Estado"
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)     # "Tiempo"
        header.setSectionResizeMode(4, QHeaderView.Stretch)              # "Archivo csv"
        header.setSectionResizeMode(5, QHeaderView.Stretch)    
        
    def populate_files_table(self, table, files_data):
        """Poblar tabla de archivos CSV con validación mejorada"""
        if not isinstance(files_data, list):
            print(f"Warning: files_data no es una lista: {type(files_data)}")
            return
            
        try:
            table.setRowCount(len(files_data))
            for row, file_data in enumerate(files_data):
                if not isinstance(file_data, dict):
                    continue
                    
                # Extraer datos de forma segura
                index = file_data.get('index', row + 1)
                filename = file_data.get('filename', file_data.get('file_name', ''))
                status = file_data.get('status', '')
                records = file_data.get('records', file_data.get('duration', '0'))
                csv_output = file_data.get('filename_csv', file_data.get('csv_output', ''))
                message = file_data.get('message', '')
                
                # Poblar tabla
                table.setItem(row, 0, QTableWidgetItem(str(index)))
                table.setItem(row, 1, QTableWidgetItem(str(filename)))
                table.setItem(row, 2, QTableWidgetItem(str(status)))
                table.setItem(row, 3, QTableWidgetItem(str(records)))
                table.setItem(row, 4, QTableWidgetItem(str(csv_output)))
                table.setItem(row, 5, QTableWidgetItem(str(message)))
                
        except Exception as e:
            print(f"Error poblando tabla de archivos: {e}")
            # Limpiar tabla en caso de error
            table.setRowCount(0)

    def update_csv_summary(self, summary_data):
        """Actualizar resumen de extracción CSV con validación robusta"""
        if not summary_data or not isinstance(summary_data, dict):
            print("Warning: summary_data inválido en CSV tab")
            return
        
        # Actualizar cards de métricas con validación
        if hasattr(self, 'csv_cards') and len(self.csv_cards) >= 5:
            try:
                # Extraer valores de forma segura
                processed_files = int(summary_data.get('processed_files', 0))
                total_files = int(summary_data.get('total_files', processed_files))
                warnings = int(summary_data.get('warnings', 0))
                errors = int(summary_data.get('errors', 0))
                csv_files_generated = int(summary_data.get('csv_files_generated', processed_files))
                
                # Formatear tiempo de ejecución
                execution_time_raw = summary_data.get('execution_time', '0:00')
                execution_time = self.format_execution_time(execution_time_raw)
                
                metrics_values = [
                    f"{processed_files} / {total_files}",  # Archivos Procesados
                    str(warnings),                         # Advertencias
                    str(errors),                          # Errores
                    str(csv_files_generated),             # CSVs Generados
                    execution_time,                       # Tiempo Extracción
                ]
                
                # Actualizar cada card de forma segura
                for i, value in enumerate(metrics_values):
                    if i < len(self.csv_cards) and hasattr(self.csv_cards[i], 'update_value'):
                        self.csv_cards[i].update_value(str(value))
                        
                print(f"✅ CSV Cards actualizadas: {metrics_values}")
                            
            except Exception as e:
                print(f"Error actualizando métricas CSV: {e}")
        
        # CORRECCIÓN: Mejor manejo de archivos con múltiples fuentes
        try:
            files_data = []
            
            # Prioridad 1: 'files_detail' (formato del controlador)
            if 'files_detail' in summary_data:
                files_data = summary_data['files_detail']
            # Prioridad 2: 'files' (formato estándar)
            elif 'files' in summary_data:
                files_data = summary_data['files']
            
            # Validar que sea una lista
            if isinstance(files_data, list) and files_data:
                self.populate_files_table(self.csv_files_table, files_data)
                print(f"✅ Tabla CSV actualizada con {len(files_data)} archivos")
            else:
                print("ℹ️ No hay datos de archivos para mostrar en CSV tab")
                # Limpiar tabla si no hay datos
                if hasattr(self, 'csv_files_table'):
                    self.csv_files_table.setRowCount(0)
                
        except Exception as e:
            print(f"Error actualizando tabla de archivos CSV: {e}")
            # Limpiar tabla en caso de error
            if hasattr(self, 'csv_files_table'):
                self.csv_files_table.setRowCount(0)

    def on_reprocess_errors_clicked(self):
        """Acción al hacer clic en el botón de reprocesar archivos con error"""
        print("🔁 Reprocesando archivos con error...")

        try:
            # Llamar al controlador para ejecutar la extracción con coordenadas
            success, extraction_summary = self.controller.run_pyguiauto_extraction()

            # Validar que el resumen es un diccionario
            if not isinstance(extraction_summary, dict):
                raise ValueError(f"El controlador devolvió un tipo inválido: {type(extraction_summary)}")

            extracted_files = extraction_summary.get('procesados_exitosos', 0)

            if success:
                csv_results = {
                    'status': 'success' if extracted_files > 0 else 'completed',
                    'total_files': extraction_summary.get('total_files', 0),
                    'processed_files': extraction_summary.get('procesados_exitosos', 0),
                    'errors': extraction_summary.get('procesados_fallidos', 0),
                    'warnings': extraction_summary.get('warnings', 0),
                    'csv_files_generated': extraction_summary.get('csvs_verificados', 0),
                    'total_records': extraction_summary.get('csvs_verificados', 0) * 3278,
                    'execution_time': extraction_summary.get('execution_time', '0:00'),
                    'avg_speed': '6.7 archivos/min' if extracted_files > 0 else '0 archivos/min',
                    'files': extraction_summary.get('files_detail', [])
                }

                UIHelpers.show_success_message(
                    self,
                    "Reprocesamiento Completado",
                    "Los archivos con error han sido reprocesados exitosamente.",
                    "Los CSV generados están listos para ser cargados."
                )

            else:
                error_message = extraction_summary.get('mensaje_error', 'Error desconocido')
                csv_results = {
                    'status': 'error',
                    'total_files': extraction_summary.get('total_files', 0),
                    'processed_files': 0,
                    'errors': extraction_summary.get('procesados_fallidos', 1),
                    'warnings': 0,
                    'csv_files_generated': 0,
                    'total_records': 0,
                    'execution_time': '0:00',
                    'avg_speed': '0 archivos/min',
                    'files': []
                }

                UIHelpers.show_error_message(
                    self,
                    "Error en el Reprocesamiento",
                    "No se pudo completar la recuperación de archivos con coordenadas.",
                    f"Motivo: {error_message}\n\nRevisa los archivos y vuelve a intentar."
                )

        except Exception as e:
            print(f"Error en on_reprocess_errors_clicked: {e}")
            traceback.print_exc()

    def confirm_reprocess_errors(self):
        """Solicita confirmación antes de reprocesar archivos con error."""
        ok = UIHelpers.show_confirmation_dialog(
            self,
            title="Confirmar reprocesamiento",
            message="¿Deseas reprocesar los archivos que tienen errores?",
            details="Este proceso intentará nuevamente analizar los archivos marcados con error."
        )
        if ok:
            self.on_reprocess_errors_clicked()

    def format_execution_time(self, time_str):
        """
        Formatear tiempo de ejecución para mostrar:
        - Segundos si < 60s (ej: "45.2s")
        - Minutos:segundos si >= 60s y < 1h (ej: "1:30")
        - Horas:minutos:segundos si >= 1h (ej: "1:01:05")
        """
        try:
            if not time_str or time_str in ['0:00', '0', '']:
                return "0s"
            
            # Si ya viene en formato numérico
            if isinstance(time_str, (int, float)):
                total_seconds = float(time_str)
            else:
                # Convertir string a segundos
                time_str = str(time_str).strip()
                
                # Si contiene ":", es formato H:MM:SS o M:SS
                if ':' in time_str:
                    # Separar microsegundos si existen
                    if '.' in time_str:
                        time_part, _ = time_str.split('.', 1)
                    else:
                        time_part = time_str
                    
                    parts = [int(p) for p in time_part.split(':')]
                    
                    if len(parts) == 3:  # H:M:S
                        hours, minutes, seconds = parts
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                    elif len(parts) == 2:  # M:S
                        minutes, seconds = parts
                        total_seconds = minutes * 60 + seconds
                    else:
                        total_seconds = float(time_str.replace(':', ''))
                else:
                    # Es un número directo (segundos)
                    total_seconds = float(time_str)
            
            # Formatear según la duración
            if total_seconds < 60:
                return f"{int(total_seconds)}s" if total_seconds.is_integer() else f"{total_seconds:.1f}s"
            elif total_seconds < 3600:
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)
                return f"{minutes}:{seconds:02d}"
            else:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                return f"{hours}:{minutes:02d}:{seconds:02d}"
                
        except (ValueError, TypeError) as e:
            print(f"Error formateando tiempo '{time_str}': {e}")
            return str(time_str)
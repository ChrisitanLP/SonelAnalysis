import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard


class CsvTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("CsvTab")
        self.csv_data = self.load_csv_summary()
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
        
        # Crear tarjetas de métricas CSV con datos reales
        self.csv_cards = []
        csv_metrics_data = [
            ("📁", "Archivos Procesados", f"{summary.get('processed_files', 0)} / {summary.get('total_files', 0)}", "#4CAF50"),
            ("⚠️", "Advertencias", str(summary.get('warnings', 0)), "#FF9800"),
            ("❌", "Errores", str(summary.get('errors', 0)), "#F44336"),
            ("📄", "CSVs Generados", str(summary.get('csv_files_generated', 0)), "#3F51B5"),
            ("⏱️", "Tiempo Extracción", summary.get('execution_time', '0:00'), "#9C27B0"),
            ("🔗", "Conexión", 'Estable', "#607D8B"),
        ]
        
        for i, (icon, title, value, color) in enumerate(csv_metrics_data):
            row = i // 3
            col = i % 3
            status_card = StatusCard(icon, title, value, color)
            self.csv_cards.append(status_card)
            csv_metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(csv_metrics_widget)
        
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
        metrics_values = [
            f"{summary.get('processed_files', 0)} / {summary.get('total_files', 0)}",
            str(summary.get('warnings', 0)),
            str(summary.get('errors', 0)),
            str(summary.get('csv_files_generated', 0)),
            summary.get('execution_time', '0:00')
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
        """Actualizar resumen de extracción CSV"""
        if not summary_data or not isinstance(summary_data, dict):
            return
        
        # Actualizar cards de métricas
        if hasattr(self, 'csv_cards') and len(self.csv_cards) >= 6:
            try:
                # Valores seguros con validación de tipos
                processed_files = summary_data.get('processed_files', 0)
                total_files = summary_data.get('total_files', 0)
                warnings = summary_data.get('warnings', 0)
                errors = summary_data.get('errors', 0)
                csv_files_generated = summary_data.get('csv_files_generated', 0)
                execution_time = summary_data.get('execution_time', '0:00')
                
                # Asegurar que son tipos correctos
                if not isinstance(processed_files, int):
                    processed_files = 0
                if not isinstance(total_files, int):
                    total_files = 0
                if not isinstance(warnings, int):
                    warnings = 0
                if not isinstance(errors, int):
                    errors = 0
                if not isinstance(csv_files_generated, int):
                    csv_files_generated = 0
                if not isinstance(execution_time, str):
                    execution_time = '0:00'
                
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
                        
            except Exception as e:
                print(f"Error actualizando métricas CSV: {e}")
        
        # Actualizar tabla de archivos
        try:
            files_data = summary_data.get('files', [])
            if isinstance(files_data, list) and files_data:
                self.populate_files_table(self.csv_files_table, files_data)
            elif hasattr(summary_data, 'get') and 'files_detail' in summary_data:
                # Alternativa si los datos están en files_detail
                files_detail = summary_data.get('files_detail', [])
                if isinstance(files_detail, list):
                    self.populate_files_table(self.csv_files_table, files_detail)
        except Exception as e:
            print(f"Error actualizando tabla de archivos CSV: {e}")
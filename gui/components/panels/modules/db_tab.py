import os
import json
from PyQt5.QtCore import Qt
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView

class DbTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("DbTab")
        self.json_file_path = ".\\data\\archivos_csv\\resumen_etl.json"
        self.init_ui()
        
    def init_ui(self):
        """Crear tab de subida a BD con información dinámica desde JSON"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Cargar datos del JSON
        json_data = self.load_json_data()
        
        # === MÉTRICAS PRINCIPALES EN CARDS ===
        db_metrics_widget = QWidget()
        db_metrics_layout = QGridLayout(db_metrics_widget)
        db_metrics_layout.setSpacing(16)
        
        # Crear tarjetas de métricas BD con datos dinámicos
        self.db_cards = []
        db_metrics_data = self.get_db_metrics_from_json(json_data)
        
        for i, (icon, title, value, color) in enumerate(db_metrics_data):
            row = i // 3
            col = i % 3
            status_card = StatusCard(icon, title, value, color)
            self.db_cards.append(status_card)
            db_metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(db_metrics_widget)
        
        # === TABLA DE ARCHIVOS SUBIDOS ===
        uploads_card = ModernCard("Detalle de Operaciones de Subida")
        self.db_files_table = QTableWidget()
        self.db_files_table.setObjectName("FilesTable")
        self.setup_db_table(self.db_files_table)
        
        # Poblar con datos dinámicos desde JSON
        files_data = self.get_files_data_from_json(json_data)
        self.populate_db_table(self.db_files_table, files_data)
        
        uploads_card.layout().addWidget(self.db_files_table)
        layout.addWidget(uploads_card)

    def refresh_data(self):
        """Método para refrescar los datos desde el JSON"""
        json_data = self.load_json_data()
        
        # Actualizar métricas
        db_metrics_data = self.get_db_metrics_from_json(json_data)
        for i, (_, _, value, color) in enumerate(db_metrics_data):
            if i < len(self.db_cards):
                self.db_cards[i].update_value(value)
                # Si StatusCard tiene método para actualizar color, descomenta la siguiente línea
                # self.db_cards[i].update_color(color)
        
        # Actualizar tabla
        files_data = self.get_files_data_from_json(json_data)
        self.populate_db_table(self.db_files_table, files_data)
    
    def set_json_path(self, path):
        """Permitir cambiar la ruta del archivo JSON"""
        self.json_file_path = path
        self.refresh_data()
        
    def setup_db_table(self, table):
        """Configurar tabla de subidas a BD"""
        headers = ["#", "Archivo", "Estado", "Registros", "Tabla", "Tiempo", "Mensaje"]
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
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)     # "Registros"
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)     # "Tabla"
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)     # "Tiempo"
        header.setSectionResizeMode(6, QHeaderView.Stretch)     
        
    def populate_db_table(self, table, files_data):
        """Poblar tabla de subidas a BD"""
        table.setRowCount(len(files_data))
        for row, file_data in enumerate(files_data):
            table.setItem(row, 0, QTableWidgetItem(str(row + 1))) 
            table.setItem(row, 1, QTableWidgetItem(file_data.get('filename', '')))
            table.setItem(row, 2, QTableWidgetItem(file_data.get('status', '')))
            table.setItem(row, 3, QTableWidgetItem(str(file_data.get('records', 0))))
            table.setItem(row, 4, QTableWidgetItem(file_data.get('table', '')))
            table.setItem(row, 5, QTableWidgetItem(file_data.get('time', '')))
            table.setItem(row, 6, QTableWidgetItem(file_data.get('message', '')))
            
    def update_db_summary(self, summary_data):
        """Actualizar resumen de subida a BD con validación robusta"""
        if not summary_data or not isinstance(summary_data, dict):
            print("Warning: summary_data inválido en DB tab")
            return
        
        # Actualizar cards de métricas con validación
        if hasattr(self, 'db_cards') and len(self.db_cards) >= 6:
            try:
                # Extraer valores de forma segura
                uploaded_files = int(summary_data.get('uploaded_files', 0))
                failed_uploads = int(summary_data.get('failed_uploads', 0))
                
                # CORRECCIÓN: Calcular total_files de forma más robusta
                total_files = int(summary_data.get('total_files', 0))
                if total_files == 0:
                    # Si no viene total_files, calcularlo
                    total_files = uploaded_files + failed_uploads
                    if total_files == 0 and uploaded_files > 0:
                        total_files = uploaded_files  # Al menos los subidos exitosamente
                
                conflicts = int(summary_data.get('conflicts', 0))
                inserted_records = int(summary_data.get('inserted_records', 0))

                # Formatear tiempo de ejecución
                upload_time_raw = summary_data.get('upload_time', '0:00')
                upload_time = self.format_execution_time(upload_time_raw)

                connection_status = str(summary_data.get('connection_status', 'Desconocido'))
                
                metrics_values = [
                    f"{uploaded_files} / {total_files}",  # Archivos Subidos
                    str(conflicts),                       # Advertencias/Conflictos
                    str(failed_uploads),                  # Errores
                    f"{inserted_records:,}",              # Registros Insertados
                    upload_time,                          # Tiempo Subida
                    connection_status                     # Conexión
                ]
                
                # Actualizar cada card de forma segura
                for i, value in enumerate(metrics_values):
                    if i < len(self.db_cards) and hasattr(self.db_cards[i], 'update_value'):
                        self.db_cards[i].update_value(str(value))
                        
                print(f"✅ DB Cards actualizadas: {metrics_values}")
                            
            except Exception as e:
                print(f"Error actualizando métricas DB: {e}")
        
        # Actualizar tabla de archivos
        try:
            files_data = summary_data.get('files', [])
            if isinstance(files_data, list) and files_data:
                self.populate_db_table(self.db_files_table, files_data)
                print(f"✅ Tabla DB actualizada con {len(files_data)} archivos")
            else:
                print("ℹ️ No hay datos de archivos para mostrar en DB tab")
                
        except Exception as e:
            print(f"Error actualizando tabla de archivos DB: {e}")
            # Limpiar tabla en caso de error
            if hasattr(self, 'db_files_table'):
                self.db_files_table.setRowCount(0)

    def get_files_data_from_json(self, json_data):
        """Extraer datos de archivos desde el JSON"""
        if not json_data:
            return []
        
        # Primero intentar desde overall_summary.files
        files_data = json_data.get('overall_summary', {}).get('files', [])
        
        # Si no hay datos ahí, intentar desde files_processed
        if not files_data:
            files_data = json_data.get('files_processed', [])
        
        # Si aún no hay datos, crear desde successful_files_detail
        if not files_data:
            successful_files = json_data.get('successful_files_detail', [])
            files_data = []
            for file_info in successful_files:
                files_data.append({
                    'filename': file_info.get('filename', ''),
                    'status': '✅ Subido' if file_info.get('status') == 'SUCCESS' else '❌ Error',
                    'records': str(file_info.get('rows_processed', 0)),
                    'table': 'mediciones_planas',  # Valor por defecto
                    'time': f"{file_info.get('processing_time_seconds', 0):.1f}s",
                    'message': ''
                })
        
        return files_data
    
    def load_json_data(self):
        """Cargar datos del archivo JSON"""
        try:
            if os.path.exists(self.json_file_path):
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Archivo JSON no encontrado: {self.json_file_path}")
                return None
        except Exception as e:
            print(f"Error al cargar archivo JSON: {e}")
            return None
    
    def get_db_metrics_from_json(self, json_data):
        """Extraer métricas de BD desde el JSON"""
        if not json_data:
            # Datos por defecto si no hay JSON
            return [
                ("🗄️", "Archivos Subidos", "0 / 0", "#4CAF50"),
                ("⚠️", "Advertencias", "0", "#FF9800"),
                ("❌", "Errores", "0", "#F44336"),
                ("📊", "Registros Insertados", "0", "#2196F3"),
                ("⏱️", "Tiempo Subida", "0:00", "#9C27B0"),
                ("🔗", "Conexión", "Desconocido", "#4CAF50")
            ]
        
        db_summary = json_data.get('database_summary', {})
        overall_summary = json_data.get('overall_summary', {})
        
        # Determinar color de conexión
        connection_status = db_summary.get('connection_status', 'Desconocido')
        connection_color = "#4CAF50" if connection_status == "Estable" else "#FF9800"
        
        # Determinar color de archivos subidos basado en tasa de éxito
        success_rate = db_summary.get('success_rate', 0)
        files_color = "#4CAF50" if success_rate >= 90 else "#FF9800" if success_rate >= 70 else "#F44336"
        
        # Formatear tiempo de ejecución
        upload_time = db_summary.get('upload_time', '0:00')
        upload_time_formatted = self.format_execution_time(upload_time)
        
        return [
            ("🗄️", "Archivos Subidos", f"{db_summary.get('uploaded_files', 0)} / {db_summary.get('total_files', 0)}", files_color),
            ("⚠️", "Advertencias", str(db_summary.get('conflicts', 0)), "#FF9800"),
            ("❌", "Errores", str(db_summary.get('failed_uploads', 0)), "#F44336"),
            ("📊", "Registros Insertados", f"{db_summary.get('inserted_records', 0):,}", "#2196F3"),
            ("⏱️", "Tiempo Subida", upload_time_formatted, "#9C27B0"),
            ("🔗", "Conexión", connection_status, connection_color)
        ]
    
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
                if isinstance(total_seconds, float):
                    return f"{int(total_seconds)}s" if total_seconds.is_integer() else f"{total_seconds:.1f}s"
                else: 
                    return f"{total_seconds}s"
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
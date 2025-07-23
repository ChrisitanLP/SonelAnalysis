from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard


class CsvTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("CsvTab")
        self.init_ui()
        
    def init_ui(self):
        """Crear tab de extracción CSV con información estática profesional"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES EN CARDS ===
        csv_metrics_widget = QWidget()
        csv_metrics_layout = QGridLayout(csv_metrics_widget)
        csv_metrics_layout.setSpacing(16)
        
        # Crear tarjetas de métricas CSV
        self.csv_cards = []
        csv_metrics_data = [
            ("📁", "Archivos Procesados", "30 / 32", "#4CAF50"),
            ("⚠️", "Advertencias", "3", "#FF9800"),
            ("❌", "Errores", "2", "#F44336"),
            ("📄", "CSVs Generados", "30", "#3F51B5"),
            ("⏱️", "Tiempo Extracción", "4:12", "#9C27B0"),
            ("💾", "Tamaño Procesado", "67.8 MB", "#607D8B"),
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
        
        # Poblar con datos estáticos
        sample_files = [
            ("medicion_20240301.pqm702", "✅ Exitoso", "01:30", "2.3 MB", "medicion_20240301.csv", "Procesado correctamente"),
            ("medicion_20240302.pqm702", "✅ Exitoso", "01:30", "2.1 MB", "medicion_20240302.csv", "Procesado correctamente"),
            ("medicion_20240303.pqm702", "❌ Error", "00:00", "1.8 MB", "medicion_20240303.csv", "Archivo corrupto - CRC inválido"),
            ("medicion_20240304.pqm702", "⚠️ Advertencia", "01:30", "2.0 MB", "medicion_20240304.csv", "Datos fuera de rango detectados"),
            ("medicion_20240305.pqm702", "✅ Exitoso", "01:30", "2.4 MB", "medicion_20240305.csv", "Procesado correctamente")
        ]
        self.populate_files_table(self.csv_files_table, [
            {"filename": f[0], "status": f[1], "records": f[2], "size": f[3], "filename_csv": f[4], "message": f[5]}
            for f in sample_files
        ])
        
        files_card.layout().addWidget(self.csv_files_table)
        layout.addWidget(files_card)
        
    def setup_files_table(self, table):
        """Configurar tabla de archivos CSV"""
        headers = ["Archivo", "Estado", "Tiempo", "Tamaño", "Archivo CSV", "Mensaje"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
    def populate_files_table(self, table, files_data):
        """Poblar tabla de archivos CSV"""
        table.setRowCount(len(files_data))
        for row, file_data in enumerate(files_data):
            table.setItem(row, 0, QTableWidgetItem(file_data.get('filename', '')))
            table.setItem(row, 1, QTableWidgetItem(file_data.get('status', '')))
            table.setItem(row, 2, QTableWidgetItem(str(file_data.get('records', 0))))
            table.setItem(row, 3, QTableWidgetItem(file_data.get('size', '')))
            table.setItem(row, 4, QTableWidgetItem(file_data.get('filename_csv', '')))
            table.setItem(row, 5, QTableWidgetItem(file_data.get('message', '')))
            
    def update_csv_summary(self, summary_data):
        """Actualizar resumen de extracción CSV"""
        if not summary_data:
            return
        
        # Actualizar cards de métricas
        if hasattr(self, 'csv_cards'):
            metrics_values = [
                f"{summary_data.get('processed_files', 0)} / {summary_data.get('total_files', 0)}",
                f"{summary_data.get('total_records', 0):,}",
                str(summary_data.get('errors', 0)),
                summary_data.get('execution_time', '0:00'),
                summary_data.get('avg_speed', 'N/A'),
                f"{summary_data.get('success_rate', 0):.1f}%",
                summary_data.get('total_size', 'N/A'),
                str(summary_data.get('csv_files_generated', 0))
            ]
            
            for i, value in enumerate(metrics_values):
                if i < len(self.csv_cards):
                    self.csv_cards[i].update_value(value)
        
        # Actualizar tabla
        files_data = summary_data.get('files', [])
        if files_data:
            self.populate_files_table(self.csv_files_table, files_data)
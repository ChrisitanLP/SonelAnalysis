from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore import Qt
from gui.components.panels.modules.general_tab import GeneralTab
from gui.components.panels.modules.csv_tab import CsvTab
from gui.components.panels.modules.db_tab import DbTab

class ExecutionSummaryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("ExecutionSummaryPanel")
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # Título del panel
        title_label = QLabel("Resumen de Ejecución")
        title_label.setObjectName("CardTitle")
        main_layout.addWidget(title_label)
        
        # Crear tabs para diferentes tipos de resumen
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("SummaryTabs")
        
        # Crear instancias de las pestañas
        self.general_tab = GeneralTab(self.parent_app)
        self.csv_tab = CsvTab(self.parent_app)
        self.db_tab = DbTab(self.parent_app)
        
        # Agregar tabs al widget
        self.tab_widget.addTab(self.general_tab, "Resumen General")
        self.tab_widget.addTab(self.csv_tab, "Extracción CSV")
        self.tab_widget.addTab(self.db_tab, "Subida a BD")
        
        main_layout.addWidget(self.tab_widget)
        
    def set_active_tab(self, tab_name):
        """Cambiar a un tab específico"""
        tab_map = {
            'general': 0,
            'csv': 1,
            'db': 2,
        }
        if tab_name in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name])

    def add_log_entry(self, text):
        """Agregar entrada al log de actividad"""
        self.general_tab.add_log_entry(text)

    def update_summary(self, text):
        """Actualizar resumen ejecutivo"""
        self.general_tab.update_summary(text)

    def update_status_card(self, index, new_value):
        """Actualizar una tarjeta de estado específica"""
        self.general_tab.update_status_card(index, new_value)
        
    def update_csv_summary(self, summary_data):
        """Actualizar resumen de extracción CSV"""
        self.csv_tab.update_csv_summary(summary_data)
        
    def update_db_summary(self, summary_data):
        """Actualizar resumen de subida a BD"""
        self.db_tab.update_db_summary(summary_data)
        
    def update_general_summary(self, summary_data):
        """Actualizar resumen general"""
        self.general_tab.update_general_summary(summary_data)

    def update_complete_summary(self, results_data):
        """Actualizar resumen de ejecución completa"""
        # Actualizar el tab general con el resumen completo
        self.general_tab.update_complete_execution_summary(results_data)
        
        # También actualizar los tabs específicos si hay datos
        if 'csv_phase' in results_data:
            csv_data = {
                'status': results_data['csv_phase']['status'],
                'processed_files': results_data['csv_phase']['processed_files'],
                'execution_time': results_data['csv_phase']['execution_time'],
                'total_files': results_data.get('total_records', 0) // 3278 if results_data.get('total_records', 0) > 0 else 0,
                'csv_files_generated': results_data['csv_phase']['processed_files'],
                'errors': 1 if results_data['csv_phase']['status'] == 'error' else 0,
                'warnings': 0,
                'total_records': results_data.get('total_records', 0),
                'avg_speed': '6.7 archivos/min' if results_data['csv_phase']['processed_files'] > 0 else '0 archivos/min',
                'files': []
            }
            self.csv_tab.update_csv_summary(csv_data)
        
        if 'db_phase' in results_data:
            db_data = {
                'status': results_data['db_phase']['status'],
                'uploaded_files': results_data['db_phase']['uploaded_files'],
                'inserted_records': results_data['db_phase']['inserted_records'],
                'upload_time': results_data['db_phase']['execution_time'],
                'failed_uploads': 1 if results_data['db_phase']['status'] == 'error' else 0,
                'conflicts': 0,
                'connection_status': 'Conectado' if results_data['db_phase']['status'] == 'success' else 'Error',
                'success_rate': 100 if results_data['db_phase']['status'] == 'success' else 0,
                'data_size': f"{results_data.get('total_records', 0) * 0.5:.1f} MB",
                'files': []
            }
            self.db_tab.update_db_summary(db_data)

    def refresh_all_tabs(self):
        """Refrescar datos en todos los tabs desde archivos JSON"""
        # Refrescar tab general
        if hasattr(self.general_tab, 'refresh_data'):
            self.general_tab.refresh_data()
        
        # Refrescar tab CSV
        if hasattr(self.csv_tab, 'refresh_data'):
            self.csv_tab.refresh_data()
        
        # Refrescar tab DB
        if hasattr(self.db_tab, 'refresh_data'):
            self.db_tab.refresh_data()
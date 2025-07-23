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
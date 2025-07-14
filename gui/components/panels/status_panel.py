from PyQt5.QtWidgets import QWidget, QVBoxLayout
from components.panels.global_panel import ExecutionSummaryPanel

class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("StatusPanel")
        self.init_ui()
        
    def init_ui(self):
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(20)

        # Panel de resumen de ejecución (ahora es el principal)
        self.execution_summary_panel = ExecutionSummaryPanel(self.parent_app)
        self.execution_summary_panel.show()  # Mostrar por defecto
        panel_layout.addWidget(self.execution_summary_panel)
        
    def update_summary(self, text):
        self.execution_summary_panel.update_summary(text)
        
    def add_log_entry(self, text):
        self.execution_summary_panel.add_log_entry(text)

    # Agregar estos métodos nuevos a la clase StatusPanel:
    def show_execution_summary(self, summary_type='general'):
        """Mostrar el panel de resumen de ejecución"""
        self.execution_summary_panel.show()
        self.execution_summary_panel.set_active_tab(summary_type)
        
    def hide_execution_summary(self):
        """Ocultar el panel de resumen de ejecución"""
        self.execution_summary_panel.hide()
        
    def update_csv_results(self, results_data):
        """Actualizar resultados de extracción CSV"""
        self.execution_summary_panel.update_csv_summary(results_data)
        self.show_execution_summary('csv')
        
    def update_db_results(self, results_data):
        """Actualizar resultados de subida a BD"""
        self.execution_summary_panel.update_db_summary(results_data)
        self.show_execution_summary('db')
        
    def update_complete_results(self, results_data):
        """Actualizar resultados de ejecución completa"""
        self.execution_summary_panel.update_complete_summary(results_data)
        self.show_execution_summary('complete')
        
    def update_general_results(self, results_data):
        """Actualizar resumen general"""
        self.execution_summary_panel.update_general_summary(results_data)
        self.show_execution_summary('general')
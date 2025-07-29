from PyQt5.QtWidgets import QWidget, QVBoxLayout
from gui.components.panels.global_panel import ExecutionSummaryPanel

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

    def refresh_tabs_data(self):
        """Refrescar datos en todos los tabs después de ejecución completa"""
        if hasattr(self.execution_summary_panel, 'refresh_all_tabs'):
            self.execution_summary_panel.refresh_all_tabs()

    def update_complete_workflow_results(self, complete_summary):
        """
        Método específico para actualizar desde complete_summary del controlador
        """
        if not complete_summary or not isinstance(complete_summary, dict):
            print("Warning: complete_summary es inválido")
            return
        
        # Extraer resúmenes específicos
        extraction_summary = complete_summary.get('extraction_summary', {})
        db_summary = complete_summary.get('db_summary', {})
        gui_success = complete_summary.get('gui_success', False)
        etl_success = complete_summary.get('etl_success', False)
        
        # Actualizar CSV con datos de extraction_summary
        if extraction_summary:
            csv_results = {
                'status': 'success' if gui_success else 'error',
                'total_files': extraction_summary.get('total_files', 0),
                'processed_files': extraction_summary.get('processed_files', 0),
                'errors': extraction_summary.get('errors', 0),
                'warnings': extraction_summary.get('warnings', 0),
                'csv_files_generated': extraction_summary.get('csv_files_generated', 0),
                'execution_time': extraction_summary.get('execution_time', '0:00'),
                'files': extraction_summary.get('files_detail', [])
            }
            self.execution_summary_panel.update_csv_summary(csv_results)
        
        # Actualizar DB con datos de db_summary
        if db_summary:
            db_results = {
                'status': 'success' if etl_success else 'error',
                'uploaded_files': db_summary.get('uploaded_files', 0),
                'failed_uploads': db_summary.get('failed_uploads', 0),
                'inserted_records': db_summary.get('inserted_records', 0),
                'connection_status': db_summary.get('connection_status', 'Desconocido'),
                'upload_time': db_summary.get('upload_time', '0:00'),
                'success_rate': db_summary.get('success_rate', 0),
                'files': db_summary.get('files', [])
            }
            self.execution_summary_panel.update_db_summary(db_results)
        
        # Preparar datos para el resumen general
        complete_results = {
            'overall_status': 'success' if (gui_success and etl_success) else 'partial',
            'total_execution_time': complete_summary.get('total_time', '0:00'),
            'total_records': complete_summary.get('data_processed', 0),
            'efficiency': complete_summary.get('success_rate', 0),
            'csv_phase': {
                'status': 'success' if gui_success else 'error',
                'execution_time': extraction_summary.get('execution_time', '0:00'),
                'processed_files': extraction_summary.get('csv_files_generated', 0)
            },
            'db_phase': {
                'status': 'success' if etl_success else 'error',
                'execution_time': db_summary.get('upload_time', '0:00'),
                'uploaded_files': db_summary.get('uploaded_files', 0),
                'inserted_records': db_summary.get('inserted_records', 0)
            }
        }
        
        self.execution_summary_panel.update_complete_summary(complete_results)
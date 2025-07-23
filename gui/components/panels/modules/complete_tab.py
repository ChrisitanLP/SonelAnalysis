from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard


class CompleteTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("CompleteTab")
        self.init_ui()
        
    def init_ui(self):
        """Crear tab de ejecución completa con información estática profesional"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES EN CARDS ===
        complete_metrics_widget = QWidget()
        complete_metrics_layout = QGridLayout(complete_metrics_widget)
        complete_metrics_layout.setSpacing(16)
        
        # Crear tarjetas de métricas completas
        self.complete_cards = []
        complete_metrics_data = [
            ("⏱️", "Tiempo Total", "6:27", "#2196F3"),
            ("📁", "Archivos Procesados", "30 / 32", "#4CAF50"),
            ("🗄️", "Subidos a BD", "28 / 30", "#4CAF50"),
            ("📊", "Registros Totales", "18,542", "#9C27B0"),
            ("🎯", "Eficiencia General", "87.5%", "#4CAF50"),
            ("🚀", "Throughput", "2,876 reg/min", "#FF9800"),
            ("💾", "Memoria Máxima", "156 MB", "#607D8B"),
            ("🔧", "CPU Promedio", "34%", "#795548")
        ]
        
        for i, (icon, title, value, color) in enumerate(complete_metrics_data):
            row = i // 4
            col = i % 4
            status_card = StatusCard(icon, title, value, color)
            self.complete_cards.append(status_card)
            complete_metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(complete_metrics_widget)
        
        # === ANÁLISIS POR FASES ===
        phases_card = ModernCard("Análisis Detallado por Fases")
        phases_content = QWidget()
        phases_layout = QVBoxLayout(phases_content)
        phases_layout.setContentsMargins(0, 0, 0, 0)

        self.phases_analysis_label = QLabel()
        self.phases_analysis_label.setObjectName("DetailedInfoLabel")
        self.phases_analysis_label.setWordWrap(True)

        # Análisis detallado por fases - DISEÑO HORIZONTAL
        phases_text = """
                <b>FASE 1: Análisis y Escaneo</b><br>
                • <b>Duración:</b> 0:23 (5.9%)<br>
                • <b>Archivos detectados:</b> 32 .pqm702<br>
                • <b>Archivos válidos:</b> 30 (93.75%)<br>
                • <b>Archivos corruptos:</b> 2<br>
                • <b>Validación:</b> 100% completada<br>
                • <b>Estimación:</b> 67.8 MB<br><br>

                <b>FASE 2: Extracción y Procesamiento</b><br>
                • <b>Duración:</b> 4:12 (65.1%)<br>
                • <b>Procesados:</b> 30 archivos<br>
                • <b>Registros:</b> 18,542 (100%)<br>
                • <b>Velocidad:</b> 6.7 archivos/min<br>
                • <b>Throughput:</b> 2,876 reg/min<br>
                • <b>Errores:</b> 0 | <b>Advertencias:</b> 3<br><br>

                <b>FASE 3: Carga y Sincronización</b><br>
                • <b>Duración:</b> 2:15 (28.9%)<br>
                • <b>Insertados:</b> 18,542 (100%)<br>
                • <b>Conflictos resueltos:</b> 15<br>
                • <b>Transacciones:</b> 96.4% éxito<br>
                • <b>Índices:</b> 4 actualizados<br>
                • <b>Backup:</b> Ejecutado exitosamente
        """

        self.phases_analysis_label.setText(phases_text)
        phases_layout.addWidget(self.phases_analysis_label)
        phases_card.layout().addWidget(phases_content)
        layout.addWidget(phases_card)
        
    def update_complete_summary(self, summary_data):
        """Actualizar resumen de ejecución completa"""
        if not summary_data:
            return

        # === Actualizar tarjetas de métricas ===
        if hasattr(self, 'complete_cards'):
            metrics_values = [
                summary_data.get('total_time', '0:00'),
                f"{summary_data.get('processed_files', 0)} / {summary_data.get('detected_files', 0)}",
                f"{summary_data.get('uploaded_records', 0)} / {summary_data.get('valid_files', 0)}",
                f"{summary_data.get('total_records', 0):,}",
                f"{summary_data.get('efficiency', 0):.1f}%",
                summary_data.get('throughput', '0 reg/min'),
                summary_data.get('max_memory', '0 MB'),
                f"{summary_data.get('avg_cpu', 0)}%"
            ]

            for i, value in enumerate(metrics_values):
                if i < len(self.complete_cards):
                    self.complete_cards[i].update_value(value)

        # === Actualizar análisis por fases ===
        if hasattr(self, 'phases_analysis_label'):
            phases_text = f"""
                    <b>FASE 1: Análisis y Escaneo</b><br>
                    • Duración: {summary_data.get('phase1_duration', '0:00')}<br>
                    • Archivos detectados: {summary_data.get('detected_files', 0)} archivos .pqm702<br>
                    • Archivos válidos: {summary_data.get('valid_files', 0)}<br>
                    • Archivos corruptos: {summary_data.get('corrupted_files', 0)}<br>
                    • Validación: {summary_data.get('integrity_check', 'N/A')}<br>
                    • Estimación: {summary_data.get('estimated_size', 'N/A')}<br><br>

                    <b>FASE 2: Extracción y Procesamiento</b><br>
                    • Duración: {summary_data.get('phase2_duration', '0:00')}<br>
                    • Procesados: {summary_data.get('processed_files', 0)}<br>
                    • Registros: {summary_data.get('total_records', 0):,}<br>
                    • Velocidad: {summary_data.get('avg_file_speed', 'N/A')}<br>
                    • Throughput: {summary_data.get('throughput', 'N/A')}<br>
                    • Errores: {summary_data.get('processing_errors', 0)}<br>
                    • Advertencias: {summary_data.get('warnings', 0)}<br><br>

                    <b>FASE 3: Carga y Sincronización</b><br>
                    • Duración: {summary_data.get('phase3_duration', '0:00')}<br>
                    • Insertados: {summary_data.get('uploaded_records', 0):,}<br>
                    • Conflictos: {summary_data.get('conflicts', 0)}<br>
                    • Transacciones: {summary_data.get('success_tx_rate', 'N/A')}<br>
                    • Índices: {summary_data.get('updated_indexes', 'N/A')}<br>
                    • Integridad: {summary_data.get('referential_integrity', 'N/A')}<br>
                    • Backup: {summary_data.get('backup_status', 'N/A')}<br><br>

            """
            self.phases_analysis_label.setText(phases_text)
        
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard
import datetime


class GeneralTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("GeneralTab")
        self.init_ui()
        
    def init_ui(self):
        """Crear tab de resumen general con información integrada de status"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES (anteriormente en status_panel) ===
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        metrics_layout.setSpacing(16)
        
        # Crear tarjetas de métricas principales
        self.general_cards = []
        metrics_data = [
            ("📁", "Archivos Procesados", "28 / 32", "#4CAF50"),
            ("⚠️", "Advertencias", "3", "#FF9800"),
            ("❌", "Errores", "1", "#F44336"),
            ("🗄️", "Archivos Subidos", "28 / 30", "#4CAF50"),
            ("📊", "Registros Totales", "18,542", "#9C27B0"),
            ("💾", "Memoria Máxima", "156 MB", "#607D8B"),
        ]
        
        for i, (icon, title, value, color) in enumerate(metrics_data):
            row = i // 3
            col = i % 3
            status_card = StatusCard(icon, title, value, color)
            self.general_cards.append(status_card)
            metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(metrics_widget)
        
        # === RESUMEN EJECUTIVO ===
        summary_card = ModernCard("Resumen Ejecutivo")
        summary_content = QWidget()
        summary_layout = QVBoxLayout(summary_content)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        
        self.summary_label = QLabel()
        self.summary_label.setObjectName("SummaryLabel")
        self.summary_label.setWordWrap(True)

        self.general_history_label = QLabel()  
        self.general_history_label.setObjectName("SummaryLabel")
        self.general_history_label.setWordWrap(True)

        summary_layout.addWidget(self.summary_label)
        summary_layout.addWidget(self.general_history_label) 

        summary_card.layout().addWidget(summary_content)
        layout.addWidget(summary_card)

        # Contenido del resumen ejecutivo con información estática profesional
        summary_text = f"""
            <b>Estado General:</b> En progreso (87% completado)<br>
            <b>Archivos Detectados:</b> 32 archivos .pqm702<br>
            <b>Procesados Exitosamente:</b> 28 archivos<br>
            <b>Con Advertencias:</b> 3 archivos (datos fuera de rango)<br>
            <b>Con Errores:</b> 1 archivo (corrupción de datos)<br><br>
            <b>Métricas de Datos:</b><br>
            - Registros de voltaje extraídos: 18,542<br>
            - Registros de corriente: 18,542<br>
            - Registros de frecuencia: 18,542<br><br>
            <b>Performance:</b><br>
            - Tiempo de procesamiento: 4:12 min<br>
            - Velocidad promedio: 6.7 archivos/min<br>
            - Tiempo estimado restante: 2:15 min<br><br>
            <b>Última Sincronización:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.summary_label.setText(summary_text)
        
    def add_log_entry(self, text):
        """Agregar entrada al log de actividad"""
        if hasattr(self, 'log_text'):
            self.log_text.append(text)

    def update_summary(self, text):
        """Actualizar resumen ejecutivo"""
        if hasattr(self, 'summary_label'):
            self.summary_label.setText(text)

    def update_status_card(self, index, new_value):
        """Actualizar una tarjeta de estado específica"""
        if hasattr(self, 'general_cards') and 0 <= index < len(self.general_cards):
            self.general_cards[index].update_value(new_value)
            
    def update_general_summary(self, summary_data):
        """Actualizar resumen general"""
        if not summary_data:
            return
            
        # Actualizar métricas generales
        total_processed = summary_data.get('total_processed', 0)
        total_time = summary_data.get('total_time', '0:00')
        successful = summary_data.get('successful', 0)
        failed = summary_data.get('failed', 0)
        
        metrics_data = [
            (total_processed, "#4CAF50"),
            (total_time, "#2196F3"),
            (successful, "#4CAF50"),
            (failed, "#F44336")
        ]
        
        for i, (value, color) in enumerate(metrics_data):
            if i < len(self.general_cards):
                self.general_cards[i].update_value(str(value))
                
        # Actualizar historial
        history_text = summary_data.get('history', 'No hay historial disponible')
        self.general_history_label.setText(history_text)
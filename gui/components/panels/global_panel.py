from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QScrollArea, QFrame, QGridLayout, QTextEdit)
from PyQt5.QtCore import Qt
from components.cards.modern_card import ModernCard
from components.cards.status_card import StatusCard
import datetime


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
        
        # Tab 1: Resumen General
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, "Resumen General")
        
        # Tab 2: Extracción CSV
        self.csv_tab = self.create_csv_tab()
        self.tab_widget.addTab(self.csv_tab, "Extracción CSV")
        
        # Tab 3: Subida a BD
        self.db_tab = self.create_db_tab()
        self.tab_widget.addTab(self.db_tab, "Subida a BD")
        
        # Tab 4: Ejecución Completa
        self.complete_tab = self.create_complete_tab()
        self.tab_widget.addTab(self.complete_tab, "Ejecución Completa")
        
        main_layout.addWidget(self.tab_widget)
        
    def create_general_tab(self):
        """Crear tab de resumen general con información integrada de status"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
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
            ("⏱️", "Tiempo Restante", "2:15 min", "#2196F3"),
            ("📊", "Registros", "18,542", "#9C27B0"),
            ("🗄️", "Estado BD", "Sincronizado", "#4CAF50")
        ]
        
        for i, (icon, title, value, color) in enumerate(metrics_data):
            row = i // 3
            col = i % 3
            status_card = StatusCard(icon, title, value, color)
            self.general_cards.append(status_card)
            metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(metrics_widget)
        
        # === LOG DE ACTIVIDAD EN TIEMPO REAL ===
        log_card = ModernCard("Log de Actividad en Tiempo Real")
        log_content = QWidget()
        log_layout = QVBoxLayout(log_content)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(220)
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("LogText")
        
        # Contenido del log con información estática profesional
        log_content_text = """
            [15:42:18] ✅ Conexión PostgreSQL establecida exitosamente
            [15:42:19] 📁 Escaneando directorio: ./data/sonel_files/
            [15:42:20] 📊 Detectados 32 archivos .pqm702 válidos
            [15:42:21] 🔄 Iniciando procesamiento: medicion_20240301.pqm702
            [15:42:22] ✅ Archivo procesado: 847 registros extraídos
            [15:42:23] 🔄 Procesando: medicion_20240302.pqm702
            [15:42:25] ✅ Archivo procesado: 823 registros extraídos
            [15:42:26] 🔄 Procesando: medicion_20240303.pqm702
            [15:42:27] ❌ Error: Archivo corrupto - omitiendo
            [15:42:28] 📊 Generando CSV consolidado: output_20240710.csv
            [15:42:29] 🗄️ Insertando batch 1/3 en tabla measurements
            [15:42:30] 🗄️ Insertando batch 2/3 en tabla measurements
            [15:42:31] ✅ Proceso 87% completado - 28/32 archivos
        """
        
        self.log_text.setPlainText(log_content_text)
        log_layout.addWidget(self.log_text)
        log_card.layout().addWidget(log_content)
        layout.addWidget(log_card)
        
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
        summary_layout.addWidget(self.summary_label)
        summary_card.layout().addWidget(summary_content)
        layout.addWidget(summary_card)
        
        return tab
        
    def create_csv_tab(self):
        """Crear tab de extracción CSV con información estática profesional"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES EN CARDS ===
        csv_metrics_widget = QWidget()
        csv_metrics_layout = QGridLayout(csv_metrics_widget)
        csv_metrics_layout.setSpacing(16)
        
        # Crear tarjetas de métricas CSV
        self.csv_cards = []
        csv_metrics_data = [
            ("📁", "Archivos Procesados", "30 / 32", "#4CAF50"),
            ("📊", "Registros Extraídos", "18,542", "#2196F3"),
            ("❌", "Errores", "2", "#F44336"),
            ("⏱️", "Tiempo Total", "4:12", "#FF9800"),
            ("🚀", "Velocidad Promedio", "6.7 arch/min", "#9C27B0"),
            ("✅", "Tasa de Éxito", "93.75%", "#4CAF50"),
            ("💾", "Tamaño Procesado", "67.8 MB", "#607D8B"),
            ("📄", "CSVs Generados", "30", "#3F51B5")
        ]
        
        for i, (icon, title, value, color) in enumerate(csv_metrics_data):
            row = i // 4
            col = i % 4
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
            ("medicion_20240301.pqm702", "✅ Exitoso", "847", "2.3 MB", "Procesado correctamente"),
            ("medicion_20240302.pqm702", "✅ Exitoso", "823", "2.1 MB", "Procesado correctamente"),
            ("medicion_20240303.pqm702", "❌ Error", "0", "1.8 MB", "Archivo corrupto - CRC inválido"),
            ("medicion_20240304.pqm702", "⚠️ Advertencia", "765", "2.0 MB", "Datos fuera de rango detectados"),
            ("medicion_20240305.pqm702", "✅ Exitoso", "892", "2.4 MB", "Procesado correctamente")
        ]
        self.populate_files_table(self.csv_files_table, [
            {"filename": f[0], "status": f[1], "records": f[2], "size": f[3], "message": f[4]}
            for f in sample_files
        ])
        
        files_card.layout().addWidget(self.csv_files_table)
        layout.addWidget(files_card)
        
        return tab
        
    def create_db_tab(self):
        """Crear tab de subida a BD con información estática profesional"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES EN CARDS ===
        db_metrics_widget = QWidget()
        db_metrics_layout = QGridLayout(db_metrics_widget)
        db_metrics_layout.setSpacing(16)
        
        # Crear tarjetas de métricas BD
        self.db_cards = []
        db_metrics_data = [
            ("🗄️", "Archivos Subidos", "28 / 30", "#4CAF50"),
            ("📊", "Registros Insertados", "18,542", "#2196F3"),
            ("❌", "Fallos", "2", "#F44336"),
            ("⚠️", "Conflictos", "15", "#FF9800"),
            ("⏱️", "Tiempo Subida", "2:15", "#9C27B0"),
            ("✅", "Transacciones OK", "96.4%", "#4CAF50"),
            ("🔄", "Índices Actualizados", "4", "#607D8B"),
            ("🔗", "Conexión", "Estable", "#4CAF50")
        ]
        
        for i, (icon, title, value, color) in enumerate(db_metrics_data):
            row = i // 4
            col = i % 4
            status_card = StatusCard(icon, title, value, color)
            self.db_cards.append(status_card)
            db_metrics_layout.addWidget(status_card, row, col)
        
        layout.addWidget(db_metrics_widget)
        
        # === TABLA DE ARCHIVOS SUBIDOS ===
        uploads_card = ModernCard("Detalle de Operaciones de Subida")
        self.db_files_table = QTableWidget()
        self.db_files_table.setObjectName("FilesTable")
        self.setup_db_table(self.db_files_table)
        
        # Poblar con datos estáticos
        sample_uploads = [
            ("output_20240301.csv", "✅ Subido", "847", "measurements", "00:15", ""),
            ("output_20240302.csv", "✅ Subido", "823", "measurements", "00:14", ""),
            ("output_20240303.csv", "❌ Error", "0", "measurements", "00:02", "Constraint violation: invalid timestamp"),
            ("output_20240304.csv", "⚠️ Parcial", "765", "measurements", "00:18", "15 duplicates resolved via UPSERT"),
            ("output_20240305.csv", "✅ Subido", "892", "measurements", "00:16", "")
        ]
        self.populate_db_table(self.db_files_table, [
            {"filename": f[0], "status": f[1], "records": f[2], "table": f[3], "time": f[4], "error": f[5]}
            for f in sample_uploads
        ])
        
        uploads_card.layout().addWidget(self.db_files_table)
        layout.addWidget(uploads_card)
        
        return tab
        
    def create_complete_tab(self):
        """Crear tab de ejecución completa con información estática profesional"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
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
        
        return tab
        
    def setup_files_table(self, table):
        """Configurar tabla de archivos CSV"""
        headers = ["Archivo", "Estado", "Registros", "Tamaño", "Mensaje"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
    def setup_db_table(self, table):
        """Configurar tabla de subidas a BD"""
        headers = ["Archivo", "Estado", "Registros", "Tabla", "Tiempo", "Error"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
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
        
    def update_db_summary(self, summary_data):
        """Actualizar resumen de subida a BD"""
        if not summary_data:
            return
        
        # Actualizar cards de métricas
        if hasattr(self, 'db_cards'):
            metrics_values = [
                f"{summary_data.get('uploaded_files', 0)} / {summary_data.get('total_files', 0)}",
                f"{summary_data.get('inserted_records', 0):,}",
                str(summary_data.get('failed_uploads', 0)),
                str(summary_data.get('conflicts', 0)),
                summary_data.get('upload_time', '0:00'),
                f"{summary_data.get('success_rate', 0):.1f}%",
                str(summary_data.get('updated_indexes', 0)),
                summary_data.get('connection_status', 'Desconocido')
            ]
            
            for i, value in enumerate(metrics_values):
                if i < len(self.db_cards):
                    self.db_cards[i].update_value(value)
        
        # Actualizar tabla
        files_data = summary_data.get('files', [])
        if files_data:
            self.populate_db_table(self.db_files_table, files_data)
        
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
        
    def populate_files_table(self, table, files_data):
        """Poblar tabla de archivos CSV"""
        table.setRowCount(len(files_data))
        for row, file_data in enumerate(files_data):
            table.setItem(row, 0, QTableWidgetItem(file_data.get('filename', '')))
            table.setItem(row, 1, QTableWidgetItem(file_data.get('status', '')))
            table.setItem(row, 2, QTableWidgetItem(str(file_data.get('records', 0))))
            table.setItem(row, 3, QTableWidgetItem(file_data.get('size', '')))
            table.setItem(row, 4, QTableWidgetItem(file_data.get('message', '')))
            
    def populate_db_table(self, table, files_data):
        """Poblar tabla de subidas a BD"""
        table.setRowCount(len(files_data))
        for row, file_data in enumerate(files_data):
            table.setItem(row, 0, QTableWidgetItem(file_data.get('filename', '')))
            table.setItem(row, 1, QTableWidgetItem(file_data.get('status', '')))
            table.setItem(row, 2, QTableWidgetItem(str(file_data.get('records', 0))))
            table.setItem(row, 3, QTableWidgetItem(file_data.get('table', '')))
            table.setItem(row, 4, QTableWidgetItem(file_data.get('time', '')))
            table.setItem(row, 5, QTableWidgetItem(file_data.get('error', '')))
            
    def set_active_tab(self, tab_name):
        """Cambiar a un tab específico"""
        tab_map = {
            'general': 0,
            'csv': 1,
            'db': 2,
            'complete': 3
        }
        if tab_name in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name])

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
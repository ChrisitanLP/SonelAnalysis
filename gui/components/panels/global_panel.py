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
        log_content_text = """[15:42:18] ✅ Conexión PostgreSQL establecida exitosamente
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
    [15:42:31] ✅ Proceso 87% completado - 28/32 archivos"""
        
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
    <b>Última Sincronización:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
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
        
        # Estado del proceso
        self.csv_status_label = QLabel("Estado: Completado Exitosamente")
        self.csv_status_label.setObjectName("CardTitle")
        layout.addWidget(self.csv_status_label)
        
        # Métricas CSV
        csv_metrics_card = ModernCard("Métricas de Extracción")
        csv_metrics_text = """
    <b>Archivos Procesados:</b> 30 de 32<br>
    <b>Registros Extraídos:</b> 18,542<br>
    <b>Errores:</b> 2<br>
    <b>Tiempo de Ejecución:</b> 4:12<br>
    <b>Velocidad Promedio:</b> 6.7 archivos/min<br>
    <b>Tamaño Total Procesado:</b> 67.8 MB<br>
    <b>Archivos CSV Generados:</b> 30<br>
    <b>Tasa de Éxito:</b> 93.75%<br>
    <b>Fecha:</b> 2024-07-10 15:42:18
        """
        self.csv_metrics_label = QLabel(csv_metrics_text)
        self.csv_metrics_label.setObjectName("SummaryLabel")
        self.csv_metrics_label.setWordWrap(True)
        csv_metrics_card.layout().addWidget(self.csv_metrics_label)
        layout.addWidget(csv_metrics_card)
        
        # Tabla de archivos procesados
        files_card = ModernCard("Detalle de Archivos")
        self.csv_files_table = QTableWidget()
        self.csv_files_table.setObjectName("FilesTable")
        self.setup_files_table(self.csv_files_table)
        
        # Poblar con datos estáticos
        sample_files = [
            ("medicion_20240301.pqm702", "✅ Exitoso", "847", "2.3 MB", "Procesado correctamente"),
            ("medicion_20240302.pqm702", "✅ Exitoso", "823", "2.1 MB", "Procesado correctamente"),
            ("medicion_20240303.pqm702", "❌ Error", "0", "1.8 MB", "Archivo corrupto"),
            ("medicion_20240304.pqm702", "⚠️ Advertencia", "765", "2.0 MB", "Datos fuera de rango"),
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
        
        # Estado del proceso
        self.db_status_label = QLabel("Estado: Sincronización Completa")
        self.db_status_label.setObjectName("CardTitle")
        layout.addWidget(self.db_status_label)
        
        # Métricas BD
        db_metrics_card = ModernCard("Métricas de Base de Datos")
        db_metrics_text = """
    <b>Archivos Subidos:</b> 28 de 30<br>
    <b>Registros Insertados:</b> 18,542<br>
    <b>Fallos de Subida:</b> 2<br>
    <b>Conflictos Resueltos:</b> 15<br>
    <b>Tiempo de Subida:</b> 2:15<br>
    <b>Conexión BD:</b> PostgreSQL 13.7 - Estable<br>
    <b>Tabla Destino:</b> measurements<br>
    <b>Índices Actualizados:</b> 4<br>
    <b>Transacciones Exitosas:</b> 96.4%<br>
    <b>Fecha:</b> 2024-07-10 15:48:33
        """
        self.db_metrics_label = QLabel(db_metrics_text)
        self.db_metrics_label.setObjectName("SummaryLabel")
        self.db_metrics_label.setWordWrap(True)
        db_metrics_card.layout().addWidget(self.db_metrics_label)
        layout.addWidget(db_metrics_card)
        
        # Tabla de archivos subidos
        uploads_card = ModernCard("Detalle de Subidas")
        self.db_files_table = QTableWidget()
        self.db_files_table.setObjectName("FilesTable")
        self.setup_db_table(self.db_files_table)
        
        # Poblar con datos estáticos
        sample_uploads = [
            ("output_20240301.csv", "✅ Subido", "847", "measurements", "00:15", ""),
            ("output_20240302.csv", "✅ Subido", "823", "measurements", "00:14", ""),
            ("output_20240303.csv", "❌ Error", "0", "measurements", "00:02", "Constraint violation"),
            ("output_20240304.csv", "⚠️ Parcial", "765", "measurements", "00:18", "Duplicates found"),
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
        
        # Estado general
        self.complete_status_label = QLabel("Estado: Ejecución Completada Exitosamente")
        self.complete_status_label.setObjectName("CardTitle")
        layout.addWidget(self.complete_status_label)
        
        # Métricas combinadas
        combined_metrics_card = ModernCard("Métricas del Proceso Completo")
        combined_metrics_text = """
    <b>Tiempo Total de Ejecución:</b> 6:27<br>
    <b>Archivos Procesados:</b> 30 de 32<br>
    <b>Archivos Subidos a BD:</b> 28 de 30<br>
    <b>Registros Totales Procesados:</b> 18,542<br>
    <b>Eficiencia General:</b> 87.5%<br>
    <b>Throughput Promedio:</b> 2,876 registros/min<br>
    <b>Consumo de Memoria Máximo:</b> 156 MB<br>
    <b>CPU Utilización Promedio:</b> 34%<br>
    <b>Fecha Inicio:</b> 2024-07-10 15:42:18<br>
    <b>Fecha Finalización:</b> 2024-07-10 15:48:45
        """
        self.complete_metrics_label = QLabel(combined_metrics_text)
        self.complete_metrics_label.setObjectName("SummaryLabel")
        self.complete_metrics_label.setWordWrap(True)
        combined_metrics_card.layout().addWidget(self.complete_metrics_label)
        layout.addWidget(combined_metrics_card)
        
        # Resumen por fases
        phases_card = ModernCard("Resumen por Fases")
        phases_text = """
    <b>📊 Fase 1: Análisis y Escaneo</b><br>
    - Duración: 0:23<br>
    - Archivos detectados: 32<br>
    - Archivos válidos: 30<br>
    - Archivos corruptos: 2<br><br>
    <b>📁 Fase 2: Extracción de Datos</b><br>
    - Duración: 4:12<br>
    - Archivos procesados: 30<br>
    - Registros extraídos: 18,542<br>
    - Tasa de éxito: 93.75%<br><br>
    <b>🗄️ Fase 3: Carga en Base de Datos</b><br>
    - Duración: 2:15<br>
    - Registros insertados: 18,542<br>
    - Conflictos resueltos: 15<br>
    - Integridad verificada: ✅<br><br>
    <b>📋 Observaciones:</b><br>
    • Proceso ejecutado dentro de los parámetros normales<br>
    • 2 archivos omitidos por corrupción de datos<br>
    • Rendimiento superior al promedio histórico<br>
    • Todas las validaciones de integridad pasaron exitosamente
        """
        self.phases_label = QLabel(phases_text)
        self.phases_label.setObjectName("SummaryLabel")
        self.phases_label.setWordWrap(True)
        phases_card.layout().addWidget(self.phases_label)
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
            
        # Actualizar estado
        status = summary_data.get('status', 'unknown')
        status_icons = {
            'success': '✅ Exitoso',
            'failed': '❌ Fallido',
            'partial': '⚠️ Parcial'
        }
        self.csv_status_label.setText(f"Estado: {status_icons.get(status, '❓ Desconocido')}")
        
        # Actualizar métricas
        total_files = summary_data.get('total_files', 0)
        processed_files = summary_data.get('processed_files', 0)
        errors = summary_data.get('errors', 0)
        total_records = summary_data.get('total_records', 0)
        execution_time = summary_data.get('execution_time', '0:00')
        
        metrics_text = f"""
<b>Archivos Procesados:</b> {processed_files} de {total_files}<br>
<b>Registros Extraídos:</b> {total_records:,}<br>
<b>Errores:</b> {errors}<br>
<b>Tiempo de Ejecución:</b> {execution_time}<br>
<b>Velocidad Promedio:</b> {summary_data.get('avg_speed', 'N/A')}<br>
<b>Fecha:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.csv_metrics_label.setText(metrics_text)
        
        # Actualizar tabla
        files_data = summary_data.get('files', [])
        self.populate_files_table(self.csv_files_table, files_data)
        
    def update_db_summary(self, summary_data):
        """Actualizar resumen de subida a BD"""
        if not summary_data:
            return
            
        # Actualizar estado
        status = summary_data.get('status', 'unknown')
        status_icons = {
            'success': '✅ Exitoso',
            'failed': '❌ Fallido',
            'partial': '⚠️ Parcial'
        }
        self.db_status_label.setText(f"Estado: {status_icons.get(status, '❓ Desconocido')}")
        
        # Actualizar métricas
        uploaded_files = summary_data.get('uploaded_files', 0)
        failed_uploads = summary_data.get('failed_uploads', 0)
        total_records = summary_data.get('inserted_records', 0)
        conflicts = summary_data.get('conflicts', 0)
        
        metrics_text = f"""
<b>Archivos Subidos:</b> {uploaded_files}<br>
<b>Registros Insertados:</b> {total_records:,}<br>
<b>Fallos de Subida:</b> {failed_uploads}<br>
<b>Conflictos:</b> {conflicts}<br>
<b>Conexión BD:</b> {summary_data.get('connection_status', 'Desconocido')}<br>
<b>Fecha:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.db_metrics_label.setText(metrics_text)
        
        # Actualizar tabla
        files_data = summary_data.get('files', [])
        self.populate_db_table(self.db_files_table, files_data)
        
    def update_complete_summary(self, summary_data):
        """Actualizar resumen de ejecución completa"""
        if not summary_data:
            return
            
        # Actualizar estado general
        status = summary_data.get('overall_status', 'unknown')
        status_icons = {
            'success': '✅ Completado Exitosamente',
            'failed': '❌ Falló',
            'partial': '⚠️ Completado Parcialmente'
        }
        self.complete_status_label.setText(f"Estado: {status_icons.get(status, '❓ Desconocido')}")
        
        # Métricas combinadas
        total_time = summary_data.get('total_execution_time', '0:00')
        csv_phase = summary_data.get('csv_phase', {})
        db_phase = summary_data.get('db_phase', {})
        
        metrics_text = f"""
<b>Tiempo Total:</b> {total_time}<br>
<b>Archivos Procesados:</b> {csv_phase.get('processed_files', 0)}<br>
<b>Archivos Subidos:</b> {db_phase.get('uploaded_files', 0)}<br>
<b>Registros Totales:</b> {summary_data.get('total_records', 0):,}<br>
<b>Eficiencia:</b> {summary_data.get('efficiency', 'N/A')}%<br>
<b>Fecha Inicio:</b> {summary_data.get('start_time', 'N/A')}<br>
<b>Fecha Fin:</b> {summary_data.get('end_time', 'N/A')}
        """
        self.complete_metrics_label.setText(metrics_text)
        
        # Resumen por fases
        phases_text = f"""
<b>📊 Fase de Extracción CSV:</b><br>
  - Estado: {csv_phase.get('status', 'N/A')}<br>
  - Tiempo: {csv_phase.get('execution_time', 'N/A')}<br>
  - Archivos: {csv_phase.get('processed_files', 0)}<br><br>
<b>🗄️ Fase de Subida a BD:</b><br>
  - Estado: {db_phase.get('status', 'N/A')}<br>
  - Tiempo: {db_phase.get('execution_time', 'N/A')}<br>
  - Registros: {db_phase.get('inserted_records', 0):,}<br><br>
<b>📋 Observaciones:</b><br>
{summary_data.get('observations', 'Sin observaciones')}
        """
        self.phases_label.setText(phases_text)
        
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
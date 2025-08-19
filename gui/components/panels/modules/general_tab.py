import os
import json
from PyQt5.QtCore import Qt
from datetime import datetime
from gui.components.cards.modern_card import ModernCard
from gui.components.cards.status_card import StatusCard
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QTextEdit

class GeneralTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setObjectName("GeneralTab")
        self.csv_data = self.load_csv_data()
        self.etl_data = self.load_etl_data()
        self.init_ui()
        
    def init_ui(self):
        """Crear tab de resumen general con información integrada de status"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # === MÉTRICAS PRINCIPALES ===
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        metrics_layout.setSpacing(16)
        
        # Obtener datos de ambos JSON
        csv_summary = self.csv_data.get('csv_summary', {})
        etl_summary = self.etl_data.get('overall_summary', {})
        db_summary = self.etl_data.get('database_summary', {})
        
        # Crear tarjetas de métricas principales con datos reales
        self.general_cards = []
        metrics_data = [
            ("📁", "Archivos Procesados", f"{csv_summary.get('processed_files', 0)} / {csv_summary.get('total_files', 0)}", "#4CAF50"),
            ("⚠️", "Advertencias", str(csv_summary.get('warnings', 0)), "#FF9800"),
            ("❌", "Errores", str(csv_summary.get('errors', 0)), "#F44336"),
            ("🗄️", "Archivos Subidos", f"{etl_summary.get('db_uploaded', 0)} / {etl_summary.get('total_files', 0)}", "#3F51B5"),
            ("📊", "Registros Totales", f"{db_summary.get('inserted_records', 0):,}", "#9C27B0"),
            ("💾", "Tamaño Procesado", etl_summary.get('data_size', '0 MB'), "#607D8B"),
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

        # Generar contenido del resumen ejecutivo con datos reales
        self.update_summary_content()
        
    def load_csv_data(self):
        """Cargar datos del resumen CSV desde el archivo JSON"""
        json_path = "exports/resumen_csv.json"
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                print(f"Archivo no encontrado: {json_path}")
                return self.get_default_csv_data()
        except Exception as e:
            print(f"Error al cargar {json_path}: {e}")
            return self.get_default_csv_data()

    def load_etl_data(self):
        """Cargar datos del resumen ETL desde el archivo JSON"""
        json_path = "exports/resumen_etl.json"
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                print(f"Archivo no encontrado: {json_path}")
                return self.get_default_etl_data()
        except Exception as e:
            print(f"Error al cargar {json_path}: {e}")
            return self.get_default_etl_data()

    # 4. Agregar métodos para datos por defecto
    def get_default_csv_data(self):
        """Datos por defecto para CSV si no se puede cargar el JSON"""
        return {
            "csv_summary": {
                "processed_files": 0,
                "total_files": 0,
                "errors": 0,
                "warnings": 0,
                "csv_files_generated": 0,
                "execution_time": "0:00",
                "total_records": 0,
                "total_size": "0 MB"
            }
        }

    def get_default_etl_data(self):
        """Datos por defecto para ETL si no se puede cargar el JSON"""
        return {
            "overall_summary": {
                "total_files": 0,
                "db_uploaded": 0,
                "total_errors": 0,
                "data_processed": 0,
                "data_size": "0 MB",
                "connection_status": "Desconectado"
            },
            "database_summary": {
                "inserted_records": 0
            }
        }
    
    def add_log_entry(self, text):
        """Agregar entrada al log de actividad"""
        if hasattr(self, 'log_text'):
            self.log_text.append(text)

    def update_summary(self, text):
        """Actualizar resumen ejecutivo"""
        if hasattr(self, 'summary_label'):
            self.summary_label.setText(text)

    def update_general_summary(self, summary_data):
        """Actualizar resumen general - mejorado para manejar datos completos"""
        if not summary_data:
            return
        
        # Caso 1: Datos simples (formato original)
        if 'total_processed' in summary_data:
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
            if hasattr(self, 'general_history_label'):
                self.general_history_label.setText(history_text)
        
        # Caso 2: Datos de proceso completo (nuevo formato)
        elif 'csv_phase' in summary_data and 'db_phase' in summary_data:
            self.update_complete_execution_summary(summary_data)
        
        # Caso 3: Fallback - refrescar desde JSON
        else:
            print("Formato de summary_data no reconocido, refrescando desde JSON")
            self.refresh_data()

    def update_summary_content(self):
        """Actualizar el contenido del resumen ejecutivo con datos reales"""
        csv_summary = self.csv_data.get('csv_summary', {})
        etl_summary = self.etl_data.get('overall_summary', {})
        
        # Calcular porcentaje de completado
        total_files = csv_summary.get('total_files', 1)
        processed_files = csv_summary.get('processed_files', 0)
        completion_percentage = (processed_files / total_files) * 100 if total_files > 0 else 0
        
        # Obtener timestamp de generación
        metadata = self.etl_data.get('metadata', {})
        generated_at = metadata.get('generated_at', datetime.now().isoformat())
        
        try:
            # Convertir timestamp ISO a formato legible
            dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary_text = f"""
            <b>Estado General:</b> {etl_summary.get('overall_status', 'Sin datos')} ({completion_percentage:.1f}% completado)<br>
            <b>Archivos Detectados:</b> {total_files} archivos .pqm702<br>
            <b>Procesados Exitosamente:</b> {processed_files} archivos<br>
            <b>Con Advertencias:</b> {csv_summary.get('warnings', 0)} archivos<br>
            <b>Con Errores:</b> {etl_summary.get('total_errors', 0)} archivos<br><br>
            <b>Performance:</b><br>
            - Tiempo extracción CSV: {csv_summary.get('execution_time', '0:00')}<br>
            - Tiempo carga BD: {etl_summary.get('total_time', '0:00')}<br>
            - Velocidad promedio: {csv_summary.get('avg_speed', '0 archivos/min')}<br>
            - Registros procesados: {etl_summary.get('data_processed', 0):,}<br><br>
            <b>Base de Datos:</b><br>
            - Estado conexión: {etl_summary.get('connection_status', 'Desconectado')}<br>
            - Tamaño procesado: {etl_summary.get('data_size', '0 MB')}<br><br>
            <b>Última Actualización:</b> {formatted_time}
        """
        
        self.summary_label.setText(summary_text)
        
        # Agregar información del historial si hay archivos fallidos
        failed_files = self.etl_data.get('failed_files_list', [])
        if failed_files:
            history_text = f"""
                <b>Archivos con Problemas ({len(failed_files)}):</b><br>
                {', '.join(failed_files[:5])}{'...' if len(failed_files) > 5 else ''}
            """
            self.general_history_label.setText(history_text)
        else:
            self.general_history_label.setText("<b>✅ Todos los archivos procesados exitosamente</b>")

    def refresh_data(self):
        """Refrescar datos desde ambos archivos JSON"""
        self.csv_data = self.load_csv_data()
        self.etl_data = self.load_etl_data()
        
        # Actualizar métricas
        csv_summary = self.csv_data.get('csv_summary', {})
        etl_summary = self.etl_data.get('overall_summary', {})
        db_summary = self.etl_data.get('database_summary', {})
        
        metrics_values = [
            f"{csv_summary.get('processed_files', 0)} / {csv_summary.get('total_files', 0)}",
            str(csv_summary.get('warnings', 0)),
            str(etl_summary.get('total_errors', 0)),
            f"{etl_summary.get('db_uploaded', 0)} / {etl_summary.get('total_files', 0)}",
            f"{db_summary.get('inserted_records', 0):,}",
            etl_summary.get('data_size', '0 MB')
        ]
        
        # Actualizar cards
        for i, value in enumerate(metrics_values):
            if i < len(self.general_cards):
                self.general_cards[i].update_value(value)
        
        # Actualizar resumen
        self.update_summary_content()

    def update_complete_execution_summary(self, results_data):
        """Actualizar resumen cuando se ejecuta el proceso completo"""
        if not results_data:
            return
        
        # Actualizar métricas generales con datos del proceso completo
        csv_phase = results_data.get('csv_phase', {})
        db_phase = results_data.get('db_phase', {})
        
        # Determinar valores para las cards
        processed_files = csv_phase.get('processed_files', 0)
        total_files = processed_files  # Asumimos que todos los procesados son el total
        uploaded_files = db_phase.get('uploaded_files', 0)
        inserted_records = db_phase.get('inserted_records', 0)
        
        # Calcular errores basado en el estado de cada fase
        total_errors = 0
        if csv_phase.get('status') == 'error':
            total_errors += 1
        if db_phase.get('status') == 'error':
            total_errors += 1
        
        # Estimar tamaño de datos procesados (aproximación)
        estimated_size = f"{inserted_records * 0.0005:.1f} MB" if inserted_records > 0 else "0 MB"
        
        # Actualizar cards con datos del proceso completo
        metrics_values = [
            f"{processed_files} / {max(total_files, processed_files)}",  # Archivos Procesados
            "0",  # Advertencias (por defecto, podría mejorarse)
            str(total_errors),  # Errores basados en el estado de las fases
            f"{uploaded_files} / {max(processed_files, uploaded_files)}",  # Archivos Subidos  
            f"{inserted_records:,}",  # Registros Totales
            estimated_size  # Tamaño aproximado
        ]
        
        # Actualizar cards de forma segura
        for i, value in enumerate(metrics_values):
            if i < len(self.general_cards) and hasattr(self.general_cards[i], 'update_value'):
                try:
                    self.general_cards[i].update_value(value)
                except Exception as e:
                    print(f"Error actualizando card {i}: {e}")
        
        # Generar resumen ejecutivo para proceso completo
        overall_status = results_data.get('overall_status', 'partial')
        status_text = "✅ Completado" if overall_status == 'success' else "⚠️ Completado con advertencias"
        efficiency = results_data.get('efficiency', 0)
        total_execution_time = results_data.get('total_execution_time', '0:00')
        
        # Construir resumen detallado
        complete_summary_text = f"""
            <b>Estado General:</b> {status_text}<br>
            <b>Archivos Procesados:</b> {processed_files} archivos .pqm<br>  
            <b>Registros Insertados:</b> {inserted_records:,} registros<br>
            <b>Eficiencia General:</b> {efficiency}%<br><br>
            <b>Fase CSV:</b><br>
            - Estado: {'✅ Exitoso' if csv_phase.get('status') == 'success' else '❌ Error'}<br>
            - Tiempo: {csv_phase.get('execution_time', '0:00')}<br>
            - Archivos: {csv_phase.get('processed_files', 0)}<br><br>
            <b>Fase Base de Datos:</b><br>
            - Estado: {'✅ Exitoso' if db_phase.get('status') == 'success' else '❌ Error'}<br>
            - Tiempo: {db_phase.get('execution_time', '0:00')}<br>
            - Subidos: {db_phase.get('uploaded_files', 0)}<br>
            - Registros: {db_phase.get('inserted_records', 0):,}<br><br>
            <b>Tiempo Total:</b> {total_execution_time}<br>
            <b>Observaciones:</b> {results_data.get('observations', 'Proceso completado.')}
        """
        
        # Actualizar el resumen principal
        if hasattr(self, 'summary_label'):
            self.summary_label.setText(complete_summary_text)
        
        # Actualizar historial con información del proceso completo
        history_text = f"""
            <b>✅ Proceso completo ejecutado</b><br>
            <b>Iniciado:</b> {results_data.get('start_time', 'N/A')}<br>
            <b>Finalizado:</b> {results_data.get('end_time', 'N/A')}<br>
            <b>Estado Final:</b> {status_text}<br>
            <b>Archivos procesados:</b> {processed_files}<br>
            <b>Subidos a BD:</b> {uploaded_files}
        """
        
        if hasattr(self, 'general_history_label'):
            self.general_history_label.setText(history_text)

    def refresh_data_after_complete_process(self):
        """Método específico para refrescar después de proceso completo"""
        try:
            # Recargar datos de ambos JSON
            self.csv_data = self.load_csv_data()
            self.etl_data = self.load_etl_data()
            
            # Si hay datos frescos, actualizar con ellos
            csv_summary = self.csv_data.get('csv_summary', {})
            etl_summary = self.etl_data.get('overall_summary', {})
            
            if csv_summary.get('processed_files', 0) > 0 or etl_summary.get('db_uploaded', 0) > 0:
                # Usar datos del JSON que son más actuales
                self.refresh_data()
            
        except Exception as e:
            print(f"Error en refresh_data_after_complete_process: {e}")

    def update_after_csv_processing(self, csv_data):
        """Actualizar tab general después del procesamiento de CSV"""
        try:
            if not csv_data:
                return
            
            # Actualizar cards con datos del procesamiento CSV
            processed_files = csv_data.get('processed_files', 0)
            total_files = csv_data.get('total_files', 0)
            errors = csv_data.get('errors', 0)
            warnings = csv_data.get('warnings', 0)
            extracted_files = csv_data.get('extracted_files', 0)
            
            # Actualizar los primeros 3 cards (Archivos Procesados, Advertencias, Errores)
            if len(self.general_cards) >= 3:
                # Card 0: Archivos Procesados
                self.general_cards[0].update_value(f"{processed_files} / {total_files}")
                
                # Card 1: Advertencias  
                self.general_cards[1].update_value(str(warnings))
                
                # Card 2: Errores
                self.general_cards[2].update_value(str(errors))
            
            # Actualizar resumen ejecutivo con información CSV
            self._update_executive_summary_after_csv(csv_data)
            
            # Log interno
            print(f"Tab General actualizado: {processed_files}/{total_files} archivos, "
                f"{errors} errores, {warnings} advertencias")
                
        except Exception as e:
            print(f"Error en update_after_csv_processing: {e}")

    def _update_executive_summary_after_csv(self, csv_data):
        """Actualizar resumen ejecutivo con datos frescos de CSV"""
        try:
            # Recargar datos JSON para obtener información más reciente
            self.csv_data = self.load_csv_data()
            self.etl_data = self.load_etl_data()
            
            # Obtener datos combinados (JSON + datos recientes de CSV)
            csv_summary = self.csv_data.get('csv_summary', {})
            etl_summary = self.etl_data.get('overall_summary', {})
            
            # Usar datos más recientes si están disponibles
            processed_files = max(csv_data.get('processed_files', 0), 
                                csv_summary.get('processed_files', 0))
            total_files = max(csv_data.get('total_files', 0), 
                            csv_summary.get('total_files', 0))
            errors = max(csv_data.get('errors', 0), 
                        csv_summary.get('errors', 0))
            warnings = max(csv_data.get('warnings', 0), 
                        csv_summary.get('warnings', 0))
            execution_time = csv_data.get('execution_time', 
                                        csv_summary.get('execution_time', '0:00'))
            
            # Calcular porcentaje de completado
            completion_percentage = (processed_files / total_files * 100) if total_files > 0 else 0
            
            # Determinar estado basado en errores
            if errors > 0:
                status_text = "⚠️ Completado con errores"
            elif warnings > 0:
                status_text = "⚠️ Completado con advertencias"
            elif processed_files > 0:
                status_text = "✅ Procesamiento exitoso"
            else:
                status_text = "ℹ️ Sin cambios"
            
            # Generar resumen actualizado
            updated_summary = f"""
                <b>Estado General:</b> {status_text} ({completion_percentage:.1f}% completado)<br>
                <b>Archivos Detectados:</b> {total_files} archivos .pqm<br>
                <b>Procesados Exitosamente:</b> {processed_files} archivos<br>
                <b>Con Advertencias:</b> {warnings} archivos<br>
                <b>Con Errores:</b> {errors} archivos<br><br>
                <b>Performance CSV:</b><br>
                - Tiempo extracción: {execution_time}<br>
                - Archivos nuevos: {csv_data.get('extracted_files', 0)}<br>
                - Estado: {'✅ Completado' if csv_data.get('status') == 'success' else '⚠️ Con problemas'}<br><br>
                <b>Base de Datos:</b><br>
                - Estado conexión: {etl_summary.get('connection_status', 'Pendiente')}<br>
                - Tamaño procesado: {etl_summary.get('data_size', 'Pendiente')}<br><br>
                <b>Última Actualización CSV:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # Actualizar label de resumen
            if hasattr(self, 'summary_label'):
                self.summary_label.setText(updated_summary)
            
            # Actualizar historial con info del procesamiento CSV
            if csv_data.get('extracted_files', 0) > 0:
                history_text = f"""
                    <b>✅ Procesamiento CSV completado</b><br>
                    <b>Archivos nuevos procesados:</b> {csv_data.get('extracted_files', 0)}<br>
                    <b>Total acumulado:</b> {processed_files}/{total_files}<br>
                    <b>Tiempo de procesamiento:</b> {execution_time}<br>
                    <b>Estado:</b> {status_text}
                """
            else:
                history_text = f"""
                    <b>ℹ️ Procesamiento CSV verificado</b><br>
                    <b>Archivos ya procesados:</b> {processed_files}<br>
                    <b>Sin archivos nuevos para procesar</b><br>
                    <b>Estado:</b> Sistema actualizado
                """
            
            if hasattr(self, 'general_history_label'):
                self.general_history_label.setText(history_text)
                
        except Exception as e:
            print(f"Error actualizando resumen ejecutivo después de CSV: {e}")

    def update_after_db_processing(self, db_data):
        """Actualizar tab general después del procesamiento de base de datos"""
        try:
            if not db_data:
                return
            
            # Actualizar cards con datos del procesamiento DB
            uploaded_files = db_data.get('uploaded_files', 0)
            total_files = db_data.get('total_files', uploaded_files)  # Usar uploaded como fallback
            inserted_records = db_data.get('inserted_records', 0)
            failed_uploads = db_data.get('failed_uploads', 0)
            data_size = db_data.get('data_size', '0 MB')
            
            # Actualizar cards específicas de BD (cards 3, 4 y 5)
            if len(self.general_cards) >= 6:
                # Card 3: Archivos Subidos (🗄️)
                self.general_cards[3].update_value(f"{uploaded_files} / {max(total_files, uploaded_files)}")
                
                # Card 4: Registros Totales (📊) 
                self.general_cards[4].update_value(f"{inserted_records:,}")
                
                # Card 5: Tamaño Procesado (💾)
                self.general_cards[5].update_value(data_size)
            
            # Actualizar resumen ejecutivo con información DB
            self._update_executive_summary_after_db(db_data)
            
            # Log interno
            print(f"Tab General actualizado después de DB: {uploaded_files} archivos subidos, "
                f"{inserted_records:,} registros, {data_size}")
                
        except Exception as e:
            print(f"Error en update_after_db_processing: {e}")

    def _update_executive_summary_after_db(self, db_data):
        """Actualizar resumen ejecutivo con datos frescos de BD"""
        try:
            # Recargar datos JSON para obtener información más reciente
            self.csv_data = self.load_csv_data()
            self.etl_data = self.load_etl_data()
            
            # Obtener datos combinados (JSON + datos recientes de DB)
            csv_summary = self.csv_data.get('csv_summary', {})
            etl_summary = self.etl_data.get('overall_summary', {})
            
            # Usar datos más recientes si están disponibles
            uploaded_files = max(db_data.get('uploaded_files', 0), 
                            etl_summary.get('db_uploaded', 0))
            inserted_records = max(db_data.get('inserted_records', 0), 
                                etl_summary.get('data_processed', 0))
            connection_status = db_data.get('connection_status', 
                                        etl_summary.get('connection_status', 'Desconocido'))
            data_size = db_data.get('data_size', etl_summary.get('data_size', '0 MB'))
            upload_time = db_data.get('upload_time', etl_summary.get('total_time', '0:00'))
            success_rate = db_data.get('success_rate', 0)
            
            # Datos CSV para mantener contexto completo
            processed_files = csv_summary.get('processed_files', 0)
            total_files = csv_summary.get('total_files', 0)
            csv_errors = csv_summary.get('errors', 0)
            csv_warnings = csv_summary.get('warnings', 0)
            csv_time = csv_summary.get('execution_time', '0:00')
            
            # Calcular porcentaje de completado total
            completion_percentage = (processed_files / total_files * 100) if total_files > 0 else 100
            
            # Determinar estado basado en el procesamiento DB
            db_errors = db_data.get('failed_uploads', 0)
            if db_errors > 0:
                status_text = "⚠️ BD completada con errores"
            elif uploaded_files > 0:
                status_text = "✅ BD actualizada exitosamente"
            elif success_rate >= 100:
                status_text = "ℹ️ BD sin cambios (ya actualizada)"
            else:
                status_text = "⚠️ BD con problemas"
            
            # Generar resumen actualizado que incluya ambas fases
            updated_summary = f"""
                <b>Estado General:</b> {status_text} ({completion_percentage:.1f}% completado)<br>
                <b>Archivos Detectados:</b> {total_files} archivos .pqm<br>
                <b>Procesados Exitosamente:</b> {processed_files} archivos<br>
                <b>Con Advertencias CSV:</b> {csv_warnings} archivos<br>
                <b>Con Errores:</b> {csv_errors + db_errors} archivos<br><br>
                <b>Performance:</b><br>
                - Tiempo extracción CSV: {csv_time}<br>
                - Tiempo carga BD: {upload_time}<br>
                - Velocidad promedio: {csv_summary.get('avg_speed', '0 archivos/min')}<br>
                - Registros procesados: {inserted_records:,}<br><br>
                <b>Base de Datos:</b><br>
                - Estado conexión: {connection_status}<br>
                - Archivos subidos: {uploaded_files}<br>
                - Tamaño procesado: {data_size}<br>
                - Tasa de éxito: {success_rate}%<br><br>
                <b>Última Actualización BD:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # Actualizar label de resumen
            if hasattr(self, 'summary_label'):
                self.summary_label.setText(updated_summary)
            
            # Actualizar historial con info del procesamiento BD
            if uploaded_files > 0:
                history_text = f"""
                    <b>✅ Procesamiento BD completado</b><br>
                    <b>Archivos subidos:</b> {uploaded_files}<br>
                    <b>Registros insertados:</b> {inserted_records:,}<br>
                    <b>Tiempo de carga:</b> {upload_time}<br>
                    <b>Tasa de éxito:</b> {success_rate}%<br>
                    <b>Estado conexión:</b> {connection_status}
                """
            else:
                history_text = f"""
                    <b>ℹ️ Procesamiento BD verificado</b><br>
                    <b>Sin archivos nuevos para subir</b><br>
                    <b>Base de datos actualizada</b><br>
                    <b>Estado conexión:</b> {connection_status}<br>
                    <b>Sistema sincronizado</b>
                """
            
            if hasattr(self, 'general_history_label'):
                self.general_history_label.setText(history_text)
                
        except Exception as e:
            print(f"Error actualizando resumen ejecutivo después de BD: {e}")
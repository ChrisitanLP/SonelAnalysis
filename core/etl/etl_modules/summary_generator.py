# ============================================
# core/etl/reporting/summary_generator.py
# ============================================
import os
import json
from datetime import datetime
from config.logger import logger
from core.utils.processing_registry import ProcessingStatus

class SummaryGenerator:
    """Generador de resúmenes y reportes del ETL"""
    
    def __init__(self, registry, config):
        self.registry = registry
        self.config = config
    
    def print_processing_summary(self):
        """Imprime un resumen del estado del procesamiento"""
        stats = self.registry.get_processing_stats()
        
        logger.info("📊 === RESUMEN DE PROCESAMIENTO ===")
        logger.info(f"Total de archivos registrados: {stats['total_files']}")
        logger.info(f"Procesados exitosamente: {stats['successful']}")
        logger.info(f"Con errores: {stats['errors']}")
        logger.info(f"Pendientes: {stats['pending']}")
        
        # Mostrar archivos con errores recientes si los hay
        if stats['errors'] > 0:
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            logger.info(f"❌ Archivos con errores recientes ({min(3, len(error_files))} de {len(error_files)}):")
            for file_path in error_files[:3]:
                file_data = self.registry.registry_data["files"][file_path]
                error_msg = file_data.get("error_message", "Sin mensaje")[:100]
    
    def get_processing_report(self):
        """Obtiene un reporte detallado del procesamiento"""
        stats = self.registry.get_processing_stats()
        
        error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
        pending_files = self.registry.get_files_by_status(ProcessingStatus.PENDING)
        
        report = {
            "statistics": stats,
            "error_files": [
                {
                    "file": os.path.basename(f),
                    "error": self.registry.registry_data["files"][f].get("error_message", "Sin mensaje")
                } for f in error_files[:10]
            ],
            "pending_files": [os.path.basename(f) for f in pending_files[:10]],
            "registry_file": self.registry.registry_file
        }
        
        return report
    
    def get_db_summary_for_gui(self):
        """Genera un resumen estructurado para la GUI después del procesamiento ETL"""
        try:
            stats = self.registry.get_processing_stats()
            
            successful_files = self.registry.get_files_by_status(ProcessingStatus.SUCCESS)
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            
            # Calcular métricas
            total_files = stats['total_files']
            uploaded_files = stats['successful']
            failed_uploads = stats['errors']
            conflicts = 0
            
            # Calcular registros totales insertados y tiempo total
            inserted_records = 0
            upload_time_seconds = 0
            total_file_size = 0
            files_data = []
            
            # Procesar archivos exitosos
            for file_path in successful_files:
                file_data = self.registry.registry_data["files"][file_path]
                additional_info = file_data.get("additional_info", {})
                
                rows_processed = additional_info.get("rows_processed", 0)
                inserted_records += rows_processed
                
                file_processing_time = additional_info.get("processing_time_seconds", 0)
                upload_time_seconds += file_processing_time
                
                file_size = additional_info.get("file_size_bytes", 0)
                total_file_size += file_size
                
                files_data.append({
                    'filename': os.path.basename(file_path),
                    'status': '✅ Subido',
                    'records': str(rows_processed),
                    'table': 'mediciones_planas',
                    'time': f"{file_processing_time:.1f}s" if file_processing_time > 0 else '0.0s',
                    'message': ''
                })
            
            # Procesar archivos con errores
            for file_path in error_files:
                file_data = self.registry.registry_data["files"][file_path]
                error_message = file_data.get("error_message", "Error desconocido")
                
                additional_info = file_data.get("additional_info", {})
                file_processing_time = additional_info.get("processing_time_seconds", 0)
                upload_time_seconds += file_processing_time
                
                # Verificar si es un conflicto
                if any(keyword in error_message.lower() for keyword in ['duplicate', 'constraint', 'conflict', 'unique']):
                    conflicts += 1
                    status = '⚠️ Conflicto'
                else:
                    status = '❌ Error'
                
                files_data.append({
                    'filename': os.path.basename(file_path),
                    'status': status,
                    'records': '0',
                    'table': 'mediciones_planas',
                    'time': f"{file_processing_time:.1f}s" if file_processing_time > 0 else '0.0s',
                    'message': error_message[:100] + '...' if len(error_message) > 100 else error_message
                })
            
            # Usar tiempo total real del batch si está disponible
            batch_time = self.registry.get_batch_processing_time()
            if batch_time and batch_time > 0:
                upload_time_seconds = batch_time
            
            # Calcular tasa de éxito
            success_rate = (uploaded_files / total_files * 100) if total_files > 0 else 0
            
            # Formatear tiempo total
            upload_time_str = self._format_time(upload_time_seconds)
            
            # Formatear tamaño total de datos
            data_size_str = self._format_file_size(total_file_size)
            
            # Determinar estado de conexión
            connection_status = "Estable"  # Valor por defecto
            
            return {
                'total_files': total_files,
                'uploaded_files': uploaded_files,
                'failed_uploads': failed_uploads,
                'conflicts': conflicts,
                'inserted_records': inserted_records,
                'success_rate': success_rate,
                'upload_time': upload_time_str,
                'processing_time_seconds': upload_time_seconds,
                'data_size': data_size_str,
                'updated_indexes': 4,  # Valor estático por ahora
                'connection_status': connection_status,
                'files': files_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando resumen BD: {e}")
            return self._get_default_db_summary()

    def get_csv_summary_for_gui(self):
        """Genera un resumen estructurado para CSV/extracción GUI"""
        try:
            stats = self.registry.get_processing_stats()
            
            successful_files = self.registry.get_files_by_status(ProcessingStatus.SUCCESS)
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            
            total_extracted = len(successful_files)
            total_errors = len(error_files)
            
            # Calcular tamaño total
            total_size = 0
            for file_path in successful_files:
                try:
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                except:
                    pass
            
            size_str = self._format_file_size(total_size)
            
            # Calcular tasa de éxito
            total_files = stats['total_files']
            success_rate = (total_extracted / total_files * 100) if total_files > 0 else 0
            
            return {
                'total_files': total_files,
                'extracted_files': total_extracted,
                'failed_extractions': total_errors,
                'duplicates': 0,  # Valor por defecto
                'extraction_time': '0:00',  # Valor por defecto
                'success_rate': success_rate,
                'data_size': size_str,
                'source_app': 'Sonel Analysis'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando resumen CSV: {e}")
            return self._get_default_csv_summary()

    def get_complete_summary_for_gui(self):
        """Genera un resumen completo combinando CSV y BD"""
        try:
            db_summary = self.get_db_summary_for_gui()
            csv_summary = self.get_csv_summary_for_gui()
            
            total_time_seconds = db_summary.get('processing_time_seconds', 0)
            total_time_str = self._format_time(total_time_seconds)
            
            # Determinar estado general
            if db_summary['failed_uploads'] == 0 and csv_summary['failed_extractions'] == 0:
                overall_status = "✅ Completado"
            elif db_summary['uploaded_files'] > 0 or csv_summary['extracted_files'] > 0:
                overall_status = "⚠️ Parcial"
            else:
                overall_status = "❌ Fallido"
            
            return {
                'overall_status': overall_status,
                'total_files': db_summary['total_files'],
                'csv_extracted': csv_summary['extracted_files'],
                'db_uploaded': db_summary['uploaded_files'],
                'total_errors': db_summary['failed_uploads'],
                'total_time': total_time_str,
                'success_rate': db_summary['success_rate'],
                'data_processed': db_summary['inserted_records'],
                'connection_status': db_summary['connection_status'],
                'files': db_summary['files'],
                'data_size': db_summary['data_size'],
                'source_app': csv_summary['source_app'],
                'processing_time_seconds': total_time_seconds
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando resumen completo: {e}")
            return self._get_default_complete_summary()

    def save_processing_summary_to_file(self, output_file=None, include_files_detail=True):
        """Guarda un resumen completo del procesamiento ETL en un archivo JSON"""
        try:
            # Definir archivo de salida por defecto
            if output_file is None:
                export_dir = self.config['PATHS']['export_dir']
                output_file = os.path.join(export_dir, f"resumen_etl.json")
                
            # Obtener resúmenes
            complete_summary = self.get_complete_summary_for_gui()
            db_summary = self.get_db_summary_for_gui()
            csv_summary = self.get_csv_summary_for_gui()
            stats = self.registry.get_processing_stats()
            
            # Obtener archivos fallidos
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            
            # Crear estructura de datos completa
            summary_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat() + 'Z',
                    "etl_version": "1.0",
                    "config_file": getattr(self, 'config_file', 'config.ini'),
                    "registry_file": self.registry.registry_file
                },
                "overall_summary": complete_summary,
                "database_summary": self._extract_db_summary_data(db_summary),
                "csv_summary": csv_summary,
                "processing_statistics": stats,
                "files_processed": [],
                "failed_files_count": len(error_files),
                "failed_files_list": [os.path.basename(f) for f in error_files]
            }
            
            # Agregar detalle de archivos si se solicita
            if include_files_detail and 'files' in db_summary:
                summary_data["files_processed"] = db_summary['files']
            
            # Agregar información adicional del registro
            self._add_detailed_file_info(summary_data)
            
            # Agregar tiempo total del batch si está disponible
            self._add_batch_info(summary_data)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Guardar archivo JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error guardando resumen ETL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _format_time(self, time_seconds):
        """Formatea tiempo en segundos a formato legible"""
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds % 1) * 1000)
        time_str = f"{minutes}:{seconds:02d}"
        if milliseconds > 0:
            time_str += f".{milliseconds:03d}"
        return time_str
    
    def _format_file_size(self, size_bytes):
        """Formatea tamaño de archivo en bytes a formato legible"""
        if size_bytes > 1024 * 1024:  # MB
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes > 1024:  # KB
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes} bytes"
    
    def _get_default_db_summary(self):
        """Retorna estructura básica en caso de error"""
        return {
            'total_files': 0,
            'uploaded_files': 0,
            'failed_uploads': 0,
            'conflicts': 0,
            'inserted_records': 0,
            'success_rate': 0,
            'upload_time': '0:00',
            'processing_time_seconds': 0,
            'data_size': '0 bytes',
            'updated_indexes': 0,
            'connection_status': 'Error',
            'files': []
        }
    
    def _get_default_csv_summary(self):
        """Retorna estructura CSV básica en caso de error"""
        return {
            'total_files': 0,
            'extracted_files': 0,
            'failed_extractions': 0,
            'duplicates': 0,
            'extraction_time': '0:00',
            'success_rate': 0,
            'data_size': '0 bytes',
            'source_app': 'Sonel Analysis'
        }
    
    def _get_default_complete_summary(self):
        """Retorna estructura completa básica en caso de error"""
        return {
            'overall_status': '❌ Error',
            'total_files': 0,
            'csv_extracted': 0,
            'db_uploaded': 0,
            'total_errors': 1,
            'total_time': '0:00',
            'success_rate': 0,
            'data_processed': 0,
            'connection_status': 'Error',
            'files': [],
            'data_size': '0 bytes',
            'source_app': 'Sonel Analysis',
            'processing_time_seconds': 0
        }
    
    def _extract_db_summary_data(self, db_summary):
        """Extrae datos relevantes del resumen de BD"""
        return {
            "total_files": db_summary['total_files'],
            "uploaded_files": db_summary['uploaded_files'],
            "failed_uploads": db_summary['failed_uploads'],
            "conflicts": db_summary['conflicts'],
            "inserted_records": db_summary['inserted_records'],
            "success_rate": db_summary['success_rate'],
            "upload_time": db_summary['upload_time'],
            "processing_time_seconds": db_summary['processing_time_seconds'],
            "data_size": db_summary['data_size'],
            "connection_status": db_summary['connection_status']
        }
    
    def _add_detailed_file_info(self, summary_data):
        """Agrega información detallada de archivos al resumen"""
        successful_files = self.registry.get_files_by_status(ProcessingStatus.SUCCESS)
        error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
        
        # Agregar archivos exitosos con más detalles
        summary_data["successful_files_detail"] = []
        for file_path in successful_files:
            file_data = self.registry.registry_data["files"][file_path]
            additional_info = file_data.get("additional_info", {})
            
            file_detail = {
                "filename": os.path.basename(file_path),
                "full_path": file_path,
                "client_code": additional_info.get("client_code", "N/A"),
                "rows_processed": additional_info.get("rows_processed", 0),
                "processing_time_seconds": additional_info.get("processing_time_seconds", 0),
                "file_size_bytes": additional_info.get("file_size_bytes", 0),
                "processed_at": file_data.get("processed_at", "N/A"),
                "status": "SUCCESS"
            }
            summary_data["successful_files_detail"].append(file_detail)
        
        # Agregar archivos con errores con más detalles
        summary_data["error_files_detail"] = []
        for file_path in error_files:
            file_data = self.registry.registry_data["files"][file_path]
            additional_info = file_data.get("additional_info", {})
            
            file_detail = {
                "filename": os.path.basename(file_path),
                "full_path": file_path,
                "error_message": file_data.get("error_message", "Error desconocido"),
                "processing_time_seconds": additional_info.get("processing_time_seconds", 0),
                "file_size_bytes": additional_info.get("file_size_bytes", 0),
                "processed_at": file_data.get("processed_at", "N/A"),
                "status": "ERROR"
            }
            summary_data["error_files_detail"].append(file_detail)
        
        # Agregar resumen de conteos
        summary_data["processing_summary"] = {
            "total_successful": len(successful_files),
            "total_errors": len(error_files),
            "total_processed": len(successful_files) + len(error_files)
        }
    
    def _add_batch_info(self, summary_data):
        """Agrega información del batch al resumen"""
        batch_time = self.registry.get_batch_processing_time()
        if batch_time:
            summary_data["batch_processing"] = {
                "total_time_seconds": batch_time,
                "batch_start": self.registry.registry_data.get("batch_start_time", "N/A"),
                "batch_end": self.registry.registry_data.get("batch_end_time", "N/A")
            }
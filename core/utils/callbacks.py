# core/utils/callbacks.py
"""
Sistema de callbacks para actualizaciones en tiempo real del procesamiento
"""
import os
import time
import json
from enum import Enum
from datetime import datetime
from config.logger import logger
from dataclasses import dataclass, asdict
from typing import Dict, Any, Callable, Optional, List

class ProcessingEventType(Enum):
    """Tipos de eventos del procesamiento"""
    PROCESS_STARTED = "process_started"
    FILE_STARTED = "file_started"
    FILE_COMPLETED = "file_completed"
    FILES_DISCOVERED = "files_discovered"
    FILE_FAILED = "file_failed"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PROGRESS_UPDATE = "progress_update"
    PROCESS_COMPLETED = "process_completed"
    PROCESS_FAILED = "process_failed"

@dataclass
class ProcessingEvent:
    """Evento de procesamiento"""
    event_type: ProcessingEventType
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario"""
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }

@dataclass
class ProcessingSummary:
    """Resumen completo del procesamiento"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_seconds: float
    
    # Estadísticas generales
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    skipped_files: int
    
    # Fases del procesamiento
    phases: Dict[str, Dict[str, Any]]
    
    # Archivos procesados
    files_details: List[Dict[str, Any]]
    
    # Errores y advertencias
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    
    # Métricas de rendimiento
    success_rate: float
    average_file_time: float
    total_records_processed: int
    
    # Información adicional
    configuration: Dict[str, Any]
    system_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resumen a diccionario"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration_seconds': self.total_duration_seconds,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'skipped_files': self.skipped_files,
            'phases': self.phases,
            'files_details': self.files_details,
            'errors': self.errors,
            'warnings': self.warnings,
            'success_rate': self.success_rate,
            'average_file_time': self.average_file_time,
            'total_records_processed': self.total_records_processed,
            'configuration': self.configuration,
            'system_info': self.system_info
        }

class ProcessingCallbackManager:
    """Gestor de callbacks para procesamiento en tiempo real"""
    
    def __init__(self, summary_file_path: str = None):
        """
        Inicializa el gestor de callbacks
        
        Args:
            summary_file_path: Ruta donde guardar el archivo de resumen
        """
        self.callbacks: List[Callable[[ProcessingEvent], None]] = []
        self.summary_file_path = summary_file_path or "processing_summary.json"
        self.events_history: List[ProcessingEvent] = []
        
        # Estado del procesamiento
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = None
        self.end_time = None
        self.current_phase = None
        self.current_phase = None
        self.files_processed = 0
        self.total_files = 0
        self.phase_start_time = None
        
        # Contadores
        self.total_files = 0
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.skipped_files = 0
        
        # Fases y archivos
        self.phases = {}
        self.files_details = []
        self.errors = []
        self.warnings = []
        
        # Métricas
        self.total_records_processed = 0
        
    def register_callback(self, callback: Callable[[ProcessingEvent], None]):
        """Registra un callback para recibir eventos"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[ProcessingEvent], None]):
        """Desregistra un callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def emit_event(self, event_type: ProcessingEventType, data: Dict[str, Any]):
        """Emite un evento a todos los callbacks registrados"""
        event = ProcessingEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data
        )
        
        # Guardar evento en historial
        self.events_history.append(event)
        
        # Actualizar estado interno
        self._update_internal_state(event)
        
        # Notificar a todos los callbacks
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    def _update_internal_state(self, event: ProcessingEvent):
        """Actualiza el estado interno basado en el evento"""
        event_type = event.event_type
        data = event.data
        
        if event_type == ProcessingEventType.PROCESS_STARTED:
            self.start_time = event.timestamp
            self.total_files = data.get('total_files', 0)
            
        elif event_type == ProcessingEventType.FILE_COMPLETED:
            self.processed_files += 1
            self.successful_files += 1
            self.total_records_processed += data.get('records_processed', 0)
            self.files_details.append({
                'filename': data.get('filename'),
                'status': 'success',
                'processing_time': data.get('processing_time', 0),
                'records': data.get('records_processed', 0),
                'timestamp': event.timestamp.isoformat()
            })
            
        elif event_type == ProcessingEventType.FILE_FAILED:
            self.processed_files += 1
            self.failed_files += 1
            error_info = {
                'filename': data.get('filename'),
                'error': data.get('error_message'),
                'timestamp': event.timestamp.isoformat()
            }
            self.errors.append(error_info)
            self.files_details.append({
                'filename': data.get('filename'),
                'status': 'failed',
                'processing_time': data.get('processing_time', 0),
                'records': 0,
                'error': data.get('error_message'),
                'timestamp': event.timestamp.isoformat()
            })
            
        elif event_type == ProcessingEventType.PHASE_STARTED:
            phase_name = data.get('phase_name')
            self.current_phase = phase_name
            self.phases[phase_name] = {
                'start_time': event.timestamp.isoformat(),
                'end_time': None,
                'duration': 0,
                'status': 'running',
                'files_processed': 0
            }
            
        elif event_type == ProcessingEventType.PHASE_COMPLETED:
            phase_name = data.get('phase_name')
            if phase_name in self.phases:
                self.phases[phase_name]['end_time'] = event.timestamp.isoformat()
                start_time = datetime.fromisoformat(self.phases[phase_name]['start_time'])
                self.phases[phase_name]['duration'] = (event.timestamp - start_time).total_seconds()
                self.phases[phase_name]['status'] = 'completed'
                self.phases[phase_name]['files_processed'] = data.get('files_processed', 0)
                
        elif event_type == ProcessingEventType.PROCESS_COMPLETED:
            self.end_time = event.timestamp
            self._generate_summary_file()
    
    def _generate_summary_file(self):
        """Genera el archivo de resumen final"""
        try:
            # Calcular métricas
            total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
            success_rate = (self.successful_files / max(self.total_files, 1)) * 100
            avg_file_time = total_duration / max(self.processed_files, 1) if self.processed_files > 0 else 0
            
            # Crear resumen
            summary = ProcessingSummary(
                session_id=self.session_id,
                start_time=self.start_time,
                end_time=self.end_time,
                total_duration_seconds=total_duration,
                total_files=self.total_files,
                processed_files=self.processed_files,
                successful_files=self.successful_files,
                failed_files=self.failed_files,
                skipped_files=self.skipped_files,
                phases=self.phases,
                files_details=self.files_details,
                errors=self.errors,
                warnings=self.warnings,
                success_rate=success_rate,
                average_file_time=avg_file_time,
                total_records_processed=self.total_records_processed,
                configuration=self._get_configuration_info(),
                system_info=self._get_system_info()
            )
            
            # Escribir archivo JSON
            with open(self.summary_file_path, 'w', encoding='utf-8') as f:
                json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)
            
            # También generar archivo TXT legible
            txt_path = self.summary_file_path.replace('.json', '.txt')
            self._generate_txt_summary(summary, txt_path)
            
            print(f"✅ Archivo de resumen generado: {self.summary_file_path}")
            print(f"✅ Resumen de texto generado: {txt_path}")
            
        except Exception as e:
            print(f"❌ Error generando archivo de resumen: {e}")
    
    def _generate_txt_summary(self, summary: ProcessingSummary, txt_path: str):
        """Genera un archivo de resumen en formato texto legible"""
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("           RESUMEN DE PROCESAMIENTO SONEL\n")
                f.write("=" * 60 + "\n\n")
                
                # Información general
                f.write(f"Sesión ID: {summary.session_id}\n")
                f.write(f"Inicio: {summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if summary.end_time:
                    f.write(f"Fin: {summary.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duración total: {summary.total_duration_seconds:.2f} segundos\n\n")
                
                # Estadísticas de archivos
                f.write("ESTADÍSTICAS DE ARCHIVOS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Total de archivos: {summary.total_files}\n")
                f.write(f"Procesados exitosamente: {summary.successful_files}\n")
                f.write(f"Con errores: {summary.failed_files}\n")
                f.write(f"Omitidos: {summary.skipped_files}\n")
                f.write(f"Tasa de éxito: {summary.success_rate:.1f}%\n")
                f.write(f"Tiempo promedio por archivo: {summary.average_file_time:.2f}s\n")
                f.write(f"Total de registros procesados: {summary.total_records_processed}\n\n")
                
                # Fases del procesamiento
                if summary.phases:
                    f.write("FASES DEL PROCESAMIENTO:\n")
                    f.write("-" * 30 + "\n")
                    for phase_name, phase_data in summary.phases.items():
                        f.write(f"{phase_name}:\n")
                        f.write(f"  Estado: {phase_data['status']}\n")
                        f.write(f"  Duración: {phase_data['duration']:.2f}s\n")
                        f.write(f"  Archivos procesados: {phase_data['files_processed']}\n\n")
                
                # Archivos con errores
                if summary.errors:
                    f.write("ERRORES ENCONTRADOS:\n")
                    f.write("-" * 30 + "\n")
                    for error in summary.errors:
                        f.write(f"Archivo: {error['filename']}\n")
                        f.write(f"Error: {error['error']}\n")
                        f.write(f"Timestamp: {error['timestamp']}\n\n")
                
                # Detalle de archivos (solo los primeros 20)
                if summary.files_details:
                    f.write("DETALLE DE ARCHIVOS (primeros 20):\n")
                    f.write("-" * 50 + "\n")
                    for file_detail in summary.files_details[:20]:
                        status_symbol = "✅" if file_detail['status'] == 'success' else "❌"
                        f.write(f"{status_symbol} {file_detail['filename']}\n")
                        f.write(f"   Estado: {file_detail['status']}\n")
                        f.write(f"   Tiempo: {file_detail['processing_time']:.2f}s\n")
                        f.write(f"   Registros: {file_detail['records']}\n")
                        if file_detail.get('error'):
                            f.write(f"   Error: {file_detail['error']}\n")
                        f.write("\n")
                
                f.write("=" * 60 + "\n")
                f.write("Resumen generado automáticamente por Sonel Data Extractor\n")
                f.write("=" * 60 + "\n")
                
        except Exception as e:
            print(f"❌ Error generando archivo TXT: {e}")
    
    def _get_configuration_info(self) -> Dict[str, Any]:
        """Obtiene información de la configuración"""
        # Aquí puedes agregar información de configuración relevante
        return {
            'session_id': self.session_id,
            'summary_file': self.summary_file_path
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema"""
        import platform
        import psutil
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_current_progress(self) -> Dict[str, Any]:
        """Obtiene el progreso actual"""
        progress_percentage = (self.processed_files / max(self.total_files, 1)) * 100
        
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'progress_percentage': progress_percentage,
            'current_phase': self.current_phase,
            'elapsed_time': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
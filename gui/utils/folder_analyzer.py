from PyQt5.QtCore import QThread, pyqtSignal
import os

# ===== NUEVA CLASE WORKER THREAD =====
class FolderAnalyzer(QThread):
    """Worker thread para analizar carpetas sin bloquear la UI"""
    
    # Señales para comunicarse con el hilo principal
    analysis_completed = pyqtSignal(dict)  # Resultado del análisis
    analysis_failed = pyqtSignal(str)      # Error en el análisis
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.should_stop = False
    
    def run(self):
        """Ejecutar análisis en segundo plano"""
        try:
            # Verificaciones básicas
            if not os.path.exists(self.folder_path):
                self.analysis_failed.emit("La carpeta no existe")
                return
            
            if not os.path.isdir(self.folder_path):
                self.analysis_failed.emit("La ruta no es una carpeta válida")
                return
            
            # Análisis optimizado con límites
            valid_extensions = ('.pqm702', '.pqm710', '.pqm711')
            file_count = 0
            sample_files = []
            MAX_SCAN_LIMIT = 200  # Límite reasonable
            MAX_SAMPLES = 5
            
            try:
                # Usar os.scandir para mejor performance
                with os.scandir(self.folder_path) as entries:
                    for entry in entries:
                        # Verificar si se debe detener
                        if self.should_stop:
                            return
                        
                        # Límite de seguridad
                        if file_count >= MAX_SCAN_LIMIT:
                            break
                        
                        # Verificación rápida de archivos válidos
                        if (entry.is_file() and 
                            any(entry.name.lower().endswith(ext) for ext in valid_extensions)):
                            file_count += 1
                            
                            # Guardar muestras para mostrar
                            if len(sample_files) < MAX_SAMPLES:
                                sample_files.append(entry.name)
            
            except (PermissionError, OSError) as e:
                self.analysis_failed.emit(f"Sin permisos de lectura: {str(e)}")
                return
            
            # Emitir resultado exitoso
            result = {
                'count': file_count,
                'files': sample_files,
                'path': self.folder_path,
                'max_reached': file_count >= MAX_SCAN_LIMIT
            }
            
            self.analysis_completed.emit(result)
            
        except Exception as e:
            self.analysis_failed.emit(f"Error inesperado: {str(e)}")
    
    def stop_analysis(self):
        """Detener el análisis si está en progreso"""
        self.should_stop = True
        if self.isRunning():
            self.quit()
            self.wait(1000)  # Esperar máximo 1 segundo

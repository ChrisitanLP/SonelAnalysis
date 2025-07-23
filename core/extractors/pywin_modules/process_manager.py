import psutil

class ProcessManager:
    """Maneja los procesos del sistema, especialmente los de Sonel Analysis"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def close_sonel_analysis_force(self):
        """
        Cierra todos los procesos relacionados con Sonel Analysis de forma forzada.
        """
        sonel_keywords = ['SonelAnalysis.exe', 'sonelanalysis.exe']
        closed = 0

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if any(keyword in proc_name for keyword in sonel_keywords):
                    proc.kill()
                    self.logger.info(f"💀 Proceso Sonel terminado: {proc.info['name']} (PID: {proc.info['pid']})")
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if closed == 0:
            self.logger.info("✅ No se encontraron procesos de Sonel para cerrar.")
        else:
            self.logger.info(f"✅ Se cerraron {closed} procesos de Sonel.")
        
        return closed > 0
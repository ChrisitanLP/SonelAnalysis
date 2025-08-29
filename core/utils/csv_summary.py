# utils/csv_utils.py
class CSVSummaryUtils:
    @staticmethod
    def _format_execution_time(seconds):
        """
        Formatea el tiempo de ejecución
        
        Args:
            seconds (int): Tiempo en segundos
            
        Returns:
            str: Tiempo formateado (MM:SS)
        """
        if seconds <= 0:
            return "0:00"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _format_file_size(size_bytes):
        """
        Formatea el tamaño del archivo
        
        Args:
            size_bytes (int): Tamaño en bytes
            
        Returns:
            str: Tamaño formateado
        """
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"

    @staticmethod
    def _calculate_average_speed(successful_files, total_time_seconds):
        """
        Calcula la velocidad promedio de procesamiento
        
        Args:
            successful_files (int): Número de archivos procesados exitosamente
            total_time_seconds (int): Tiempo total en segundos
            
        Returns:
            str: Velocidad promedio formateada
        """
        if total_time_seconds <= 0 or successful_files <= 0:
            return "N/A"
        
        files_per_minute = (successful_files / total_time_seconds) * 60
        return f"{files_per_minute:.1f} archivos/min"


    @staticmethod
    def _estimate_execution_time(file_size_bytes):
        """
        Estima el tiempo de ejecución basado en el tamaño del archivo
        
        Args:
            file_size_bytes (int): Tamaño del archivo en bytes
            
        Returns:
            int: Tiempo estimado en segundos
        """
        # Estimación: ~90 segundos por cada 2MB
        mb_size = file_size_bytes / (1024 * 1024)
        estimated_seconds = max(30, int(mb_size * 45))  # Mínimo 30 segundos
        return estimated_seconds

    @staticmethod
    def _get_empty_csv_summary():
        """
        Retorna un resumen vacío para casos de error o sin archivos
        
        Returns:
            dict: Resumen vacío con estructura correctaa
        """
        return {
            "processed_files": 0,
            "total_files": 0,
            "errors": 0,
            "warnings": 0,
            "csv_files_generated": 0,
            "execution_time": "0:00",
            "avg_speed": "N/A",
            "total_size": "0 B",
            "success_rate": 0.0,
            "total_records": 0,
            "files": []
        }
    
    @staticmethod
    def _format_execution_time_consolidated(total_seconds):
        """
        Formatea tiempo de ejecución consolidado para múltiples directorios
        
        Args:
            total_seconds (float): Tiempo total en segundos
            
        Returns:
            str: Tiempo formateado
        """
        if total_seconds <= 0:
            return "0:00"
            
        if total_seconds < 3600:  # Menos de 1 hora
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            return f"{minutes}:{seconds:02d}"
        else:  # Más de 1 hora
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}:{minutes:02d}"
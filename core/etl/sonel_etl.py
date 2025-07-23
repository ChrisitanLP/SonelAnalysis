#sonel_etl.py
import os
import json
from datetime import datetime
from config.logger import logger
from config.settings import load_config
from core.parser.csv_parser import CSVParser
from core.parser.excel_parser import ExcelParser
from core.database.operations import DataHandler
from core.utils.validators import extract_client_code
from core.database.connection import DatabaseConnection
from core.extractors.file_extractor import FileExtractor
from core.extractors.pygui_extractor import GUIExtractor
from core.transformers.voltage_transformer import VoltageTransformer
from core.utils.processing_registry import ProcessingRegistry, ProcessingStatus

class SonelETL:
    """Clase orquestadora del proceso ETL completo con control de procesamiento"""
    
    def __init__(self, config_file='config.ini', db_connection=None, registry_file=None):
        """
        Inicializa el orquestador ETL
       
        Args:
            config_file: Ruta al archivo de configuración
            db_connection: Conexión a base de datos existente (opcional)
            registry_file: Archivo de registro personalizado (opcional)
        """
        logger.info("🚀 Inicializando proceso ETL de Sonel")
        self.config = load_config(config_file)
        
        # Usar conexión proporcionada o crear una nueva
        if db_connection:
            self.db_connection = db_connection
        else:
            self.db_connection = DatabaseConnection(self.config)
        
        # Inicializar registro de procesamiento
        data_dir = self.config['PATHS']['data_dir']
        self.registry_file = registry_file or os.path.join(data_dir, "registro_procesamiento.json")
        self.registry = ProcessingRegistry(self.registry_file)
    
    def run(self, extraction_method='file', directory=None, file_path=None, force_reprocess=False):
        """
        Ejecuta el proceso completo de ETL con control de procesamiento
       
        Args:
            extraction_method: Método de extracción ('file' o 'gui')
            directory: Directorio específico a procesar (opcional)
            file_path: Ruta específica a un archivo a procesar (opcional)
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
           
        Returns:
            bool: True si el proceso fue exitoso
        """
        logger.info(f"🔁 Iniciando ejecución de ETL con método: {extraction_method}")
        
        # Limpiar archivos inexistentes del registro al inicio
        cleaned_count = self.registry.cleanup_missing_files()
        if cleaned_count > 0:
            logger.info(f"🧹 Limpieza de registro: {cleaned_count} archivos inexistentes eliminados")

        # Si se proporciona un archivo específico, procesarlo directamente
        if file_path:
            logger.info(f"Procesando archivo específico: {file_path}")
            return self.process_file(file_path, force_reprocess=force_reprocess)
            
        # Si se proporciona directorio, procesarlo directamente
        if directory or extraction_method == 'file':
            process_dir = directory if directory else self.config['PATHS']['data_dir']
            
            if not os.path.exists(process_dir):
                logger.error(f"❌ El directorio {process_dir} no existe")
                return False
                
            return self.process_directory(process_dir, force_reprocess=force_reprocess)
        
        # Proceso ETL estándar con extractor
        # Paso 1: Extracción
        logger.info("📥 Iniciando extracción de datos")
        extracted_data = self._extract_data(extraction_method, force_reprocess)
        if extracted_data is None:
            logger.info("ℹ️ No hay datos nuevos para procesar")
            return True  # No es un error, simplemente no hay archivos nuevos
           
        # Paso 2: Transformación
        logger.info("🔧 Iniciando transformación de datos")
        transformed_data = self._transform_data(extracted_data)
        if transformed_data is None:
            logger.error("❌ Fallo en la fase de transformación de datos")
            return False
           
        # Paso 3: Carga
        # En el flujo estándar, usamos un código genérico ya que no tenemos archivo
        # del cual extraer el código
        cliente_codigo = "ETL_STANDARD"
        # Importante: Como no hay archivo, no intentamos extraer código de él
        handler = DataHandler(self.db_connection)
        cliente_id = handler.get_or_create_codigo_id(cliente_codigo, None, should_extract=False)
        
        if not cliente_id:
            logger.error("❌ No se pudo obtener/crear el ID del cliente")
            return False
            
        # Ahora cargamos los datos con el ID ya obtenido
        logger.info(f"⬆️ Cargando datos transformados a la base de datos para cliente {cliente_codigo}")
        load_success = handler.insert_data_direct(transformed_data, cliente_id)
        if not load_success:
            logger.error("❌ Fallo en la fase de carga de datos")
            return False
           
        logger.info("✅ Proceso ETL completado exitosamente")
        return True
    
    def _extract_data(self, method, force_reprocess=False):
        """
        Ejecuta el paso de extracción según el método especificado
       
        Args:
            method: Método de extracción ('file' o 'gui')
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
           
        Returns:
            DataFrame con los datos extraídos o None si hay error
        """
        if method == 'file':
            extractor = FileExtractor(self.config, self.registry_file)
            if force_reprocess:
                return extractor.extract_all_files(force_reprocess=True)
            else:
                return extractor.extract()
        elif method == 'gui':
            extractor = GUIExtractor(self.config)
            return extractor.extract()
        else:
            logger.error(f"Método de extracción no válido: {method}")
            return None
    
    def _transform_data(self, data):
        """
        Ejecuta el paso de transformación de datos
        
        Args:
            data: DataFrame con los datos extraídos
            
        Returns:
            DataFrame transformado o None si hay error
        """
        return VoltageTransformer.transform(data)
    
    def _load_data(self, data, codigo, file_path):
        """
        Ejecuta el paso de carga de datos a la base de datos
       
        Args:
            data: DataFrame con los datos transformados
            codigo: Código del cliente
            file_path: Ruta al archivo original (para extraer código si es necesario)
           
        Returns:
            bool: True si la carga fue exitosa
        """
        logger.info(f"📦 Cargando datos para el código: {codigo}")
        connection = self.db_connection.get_connection()
        if not connection:
            return False
           
        handler = DataHandler(self.db_connection)
        
        # Determinar si debemos intentar extraer el código del archivo
        should_extract = file_path is not None
        return handler.insert_data(data, codigo, file_path, should_extract=should_extract)
    
    def close(self):
        """Cierra las conexiones y recursos"""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()
            logger.info("🧹 Recursos de ETL liberados correctamente")

    def process_file(self, file_path, force_reprocess=False):
        """
        Procesa un archivo individual con control de registro
        
        Args:
            file_path: Ruta al archivo a procesar
            force_reprocess: Si True, ignora el registro y procesa el archivo
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        # Capturar tiempo de inicio del procesamiento
        start_time = datetime.now()
        start_time_iso = start_time.isoformat() + 'Z'
        
        try:
            # Validar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"❌ El archivo {file_path} no existe")
                return False
            
            # Verificar si el archivo debe ser procesado (a menos que sea forzado)
            if not force_reprocess:
                should_process, reason = self.registry.should_process_file(file_path)
                if not should_process:
                    self.registry.register_processing_skipped(file_path, reason)
                    logger.info(f"⏭️  Archivo omitido: {os.path.basename(file_path)} - {reason}")
                    return True  # No es un error, simplemente se omitió
            
            # Registrar inicio del procesamiento
            cliente_codigo = extract_client_code(file_path)
            self.registry.register_processing_start(file_path, cliente_codigo)
            
            # Registrar la ruta completa para diagnóstico
            logger.info(f"📄 Procesando archivo: {file_path}")
                
            # Extraer datos del archivo según su tipo
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.xlsx':
                df = ExcelParser.parse(file_path)
            elif file_ext == '.csv':
                df = CSVParser.parse(file_path)
            else:
                error_msg = f"Formato de archivo no soportado: {file_path}"
                # 🔄 MEJORA: Calcular tiempo incluso en caso de error
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                error_info = {
                    "processing_time_seconds": processing_time,
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
                self.registry.register_processing_error(file_path, error_msg, error_info)
                logger.error(f"⚠️ {error_msg}")
                return False
            
            if df is None or df.empty:
                error_msg = f"No se extrajeron datos del archivo: {file_path}"
                # 🔄 MEJORA: Calcular tiempo incluso en caso de error
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                error_info = {
                    "processing_time_seconds": processing_time,
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
                self.registry.register_processing_error(file_path, error_msg, error_info)
                logger.error(f"⚠️ {error_msg}")
                return False
                
            # Transformar datos al formato requerido
            transformed_data = self._transform_data(df)
            
            if transformed_data is None or transformed_data.empty:
                error_msg = f"Transformación de datos fallida para archivo: {file_path}"
                # 🔄 MEJORA: Calcular tiempo incluso en caso de error
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                error_info = {
                    "processing_time_seconds": processing_time,
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
                self.registry.register_processing_error(file_path, error_msg, error_info)
                logger.error(f"⚠️ {error_msg}")
                return False
            
            # En el nuevo sistema, la función extract_client_code siempre devuelve un código
            # ya sea extraído o generado automáticamente, pero verificamos por si acaso
            if cliente_codigo is None:
                error_msg = f"No se pudo obtener código de cliente desde el archivo {file_path}"
                # 🔄 MEJORA: Calcular tiempo incluso en caso de error
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                error_info = {
                    "processing_time_seconds": processing_time,
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
                self.registry.register_processing_error(file_path, error_msg, error_info)
                logger.error(f"❌ {error_msg}")
                return False
            
            logger.info(f"📌 Código de cliente extraído: {cliente_codigo}")
            success = self._load_data(transformed_data, cliente_codigo, file_path)

            if success:
                # Calcular tiempo de procesamiento
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Registrar éxito con información adicional mejorada
                additional_info = {
                    "rows_processed": len(transformed_data),
                    "columns_processed": len(transformed_data.columns) if hasattr(transformed_data, 'columns') else 0,
                    "client_code": cliente_codigo,
                    "processing_time_seconds": processing_time,
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                }
                self.registry.register_processing_success(file_path, additional_info)
                logger.info(f"✅ Archivo procesado exitosamente: {file_path} | Cliente: {cliente_codigo} | Tiempo: {processing_time:.2f}s | Registros: {len(transformed_data)}")
                return True
            else:
                error_msg = f"Error al cargar datos desde archivo: {file_path}"
                # 🔄 MEJORA: Calcular tiempo incluso en caso de error
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                error_info = {
                    "processing_time_seconds": processing_time,
                    "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    "client_code": cliente_codigo
                }
                self.registry.register_processing_error(file_path, error_msg, error_info)
                logger.error(f"❌ {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Error crítico al procesar archivo {file_path}: {e}"
            # 🔄 MEJORA: Calcular tiempo incluso en caso de excepción
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            error_info = {
                "processing_time_seconds": processing_time,
                "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
            self.registry.register_processing_error(file_path, error_msg, error_info)
            logger.error(f"❌ {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def process_directory(self, directory=None, force_reprocess=False):
        """
        Procesa todos los archivos de un directorio con control de registro
        
        Args:
            directory: Directorio a procesar. Si es None, usa el configurado en config
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
            
        Returns:
            bool: True si se procesaron archivos exitosamente (al menos uno)
        """
        # 🔄 MEJORA: Capturar tiempo de inicio del procesamiento del directorio
        start_time = datetime.now()
        
        if directory is None:
            directory = self.config['PATHS']['data_dir']
            
        if not os.path.exists(directory):
            logger.error(f"❌ El directorio {directory} no existe")
            return False
            
        # Buscar archivos usando el extractor con control de registro
        file_extractor = FileExtractor(self.config, self.registry_file)
        
        if force_reprocess:
            files = file_extractor.find_files_in_directory(directory)
            logger.info(f"🔄 Modo de reprocesamiento forzado: procesando todos los archivos")
        else:
            files = file_extractor.find_files_to_process(directory)
        
        if not files:
            if not force_reprocess:
                logger.info(f"ℹ️ No se encontraron archivos nuevos para procesar en {directory}")
                # Mostrar estadísticas del registro
                self.print_processing_summary()
            else:
                logger.warning(f"⚠️ No se encontraron archivos para procesar en {directory}")
            return True  # No hay archivos nuevos no es un error
            
        # Procesar cada archivo
        total_files = len(files)
        logger.info(f"📄 {total_files} archivos encontrados para procesamiento")

        success_count = 0
        for i, file_path in enumerate(files, start=1):
            logger.info(f"📂 ({i}/{total_files}) Procesando: {os.path.basename(file_path)}")
            if self.process_file(file_path, force_reprocess=force_reprocess):
                success_count += 1
            # No registramos errores aquí porque ya se hace en process_file

        # 🔄 MEJORA: Calcular tiempo total del directorio y almacenarlo
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # 🔄 MEJORA: Guardar tiempo total en el registro para uso posterior
        self.registry.register_batch_processing_time(total_time, start_time, end_time)
        
        logger.info(f"📈 Resultado final: {success_count}/{total_files} archivos procesados con éxito en {total_time:.2f} segundos")
        
        output_file = self.save_processing_summary_to_file()
        if output_file:
            print(f"Resumen guardado en: {output_file}")

        # Mostrar resumen del registro
        self.print_processing_summary()
        
        return success_count > 0
    
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
                error_msg = file_data.get("error_message", "Sin mensaje")[:100]  # Limitar longitud
                logger.info(f"  - {os.path.basename(file_path)}: {error_msg}...")
    
    def reset_file_processing(self, file_path):
        """
        Reinicia el estado de procesamiento de un archivo específico
        
        Args:
            file_path: Ruta al archivo
        """
        file_extractor = FileExtractor(self.config, self.registry_file)
        file_extractor.reset_file_status(file_path)
        logger.info(f"🔄 Estado de procesamiento reiniciado para: {os.path.basename(file_path)}")
    
    def get_processing_report(self):
        """
        Obtiene un reporte detallado del procesamiento
        
        Returns:
            dict: Reporte con estadísticas y detalles
        """
        stats = self.registry.get_processing_stats()
        
        # Obtener archivos por estado
        
        error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
        pending_files = self.registry.get_files_by_status(ProcessingStatus.PENDING)
        
        report = {
            "statistics": stats,
            "error_files": [
                {
                    "file": os.path.basename(f),
                    "error": self.registry.registry_data["files"][f].get("error_message", "Sin mensaje")
                } for f in error_files[:10]  # Solo los primeros 10
            ],
            "pending_files": [os.path.basename(f) for f in pending_files[:10]],
            "registry_file": self.registry_file
        }
        
        return report
    
    def get_db_summary_for_gui(self):
        """
        Genera un resumen estructurado para la GUI después del procesamiento ETL
        
        Returns:
            dict: Resumen estructurado con métricas de BD para mostrar en la GUI
        """
        try:
            # Obtener estadísticas del registro
            stats = self.registry.get_processing_stats()
            
            # Obtener archivos por estado
            successful_files = self.registry.get_files_by_status(ProcessingStatus.SUCCESS)
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            pending_files = self.registry.get_files_by_status(ProcessingStatus.PENDING)
            
            # Calcular métricas
            total_files = stats['total_files']
            uploaded_files = stats['successful']
            failed_uploads = stats['errors']
            conflicts = 0  # Inicializar conflictos
            
            # 🔄 MEJORA: Calcular registros totales insertados y tiempo total REAL
            inserted_records = 0
            upload_time_seconds = 0
            total_file_size = 0
            files_data = []
            
            for file_path in successful_files:
                file_data = self.registry.registry_data["files"][file_path]
                additional_info = file_data.get("additional_info", {})
                
                # Sumar registros procesados
                rows_processed = additional_info.get("rows_processed", 0)
                inserted_records += rows_processed
                
                # 🔄 MEJORA: Sumar tiempo de procesamiento individual REAL
                file_processing_time = additional_info.get("processing_time_seconds", 0)
                upload_time_seconds += file_processing_time
                
                # Sumar tamaño de archivos
                file_size = additional_info.get("file_size_bytes", 0)
                total_file_size += file_size
                
                # 🔄 MEJORA: Preparar datos del archivo con tiempo preciso
                files_data.append({
                    'filename': os.path.basename(file_path),
                    'status': '✅ Subido',
                    'records': str(rows_processed),
                    'table': 'mediciones_planas',
                    'time': f"{file_processing_time:.1f}s" if file_processing_time > 0 else '0.0s',
                    'message': ''
                })
            
            # Agregar archivos con errores
            for file_path in error_files:
                file_data = self.registry.registry_data["files"][file_path]
                error_message = file_data.get("error_message", "Error desconocido")
                
                # 🔄 MEJORA: Obtener tiempo de procesamiento aunque haya fallado
                additional_info = file_data.get("additional_info", {})
                file_processing_time = additional_info.get("processing_time_seconds", 0)
                upload_time_seconds += file_processing_time  # Sumar también tiempo de archivos fallidos
                
                # Verificar si es un conflicto (ejemplo: duplicate key, constraint violation)
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
            
            # 🔄 MEJORA: Obtener tiempo total real del batch si está disponible
            batch_time = self.registry.get_batch_processing_time()
            if batch_time and batch_time > 0:
                upload_time_seconds = batch_time  # Usar tiempo total real del batch
            
            # Calcular tasa de éxito
            success_rate = (uploaded_files / total_files * 100) if total_files > 0 else 0
            
            # 🔄 MEJORA: Formatear tiempo total con precisión
            minutes = int(upload_time_seconds // 60)
            seconds = int(upload_time_seconds % 60)
            milliseconds = int((upload_time_seconds % 1) * 1000)
            upload_time_str = f"{minutes}:{seconds:02d}"
            if milliseconds > 0:
                upload_time_str += f".{milliseconds:03d}"
            
            # Formatear tamaño total de datos
            if total_file_size > 1024 * 1024:  # MB
                data_size_str = f"{total_file_size / (1024 * 1024):.1f} MB"
            elif total_file_size > 1024:  # KB
                data_size_str = f"{total_file_size / 1024:.1f} KB"
            else:
                data_size_str = f"{total_file_size} bytes"
            
            # Determinar estado de conexión
            connection_status = "Estable"
            try:
                if self.db_connection and self.db_connection.get_connection():
                    connection_status = "Estable"
                else:
                    connection_status = "Desconectado"
            except:
                connection_status = "Error"
            
            # Construir resumen estructurado
            summary_data = {
                'total_files': total_files,
                'uploaded_files': uploaded_files,
                'failed_uploads': failed_uploads,
                'conflicts': conflicts,
                'inserted_records': inserted_records,  # 🔄 MEJORA: Registros totales reales
                'success_rate': success_rate,
                'upload_time': upload_time_str,
                'processing_time_seconds': upload_time_seconds,  # 🔄 MEJORA: Tiempo total real
                'data_size': data_size_str,
                'updated_indexes': 4,  # Valor estático por ahora
                'connection_status': connection_status,
                'files': files_data  # 🔄 MEJORA: Incluye tiempo por archivo
            }
            
            logger.info(f"📊 Resumen BD generado: {uploaded_files}/{total_files} archivos, {inserted_records} registros, {upload_time_str} tiempo total")
            return summary_data
            
        except Exception as e:
            logger.error(f"❌ Error generando resumen BD: {e}")
            # Retornar estructura básica en caso de error
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

    def get_csv_summary_for_gui(self):
        """
        Genera un resumen estructurado para CSV/extracción GUI
        
        Returns:
            dict: Resumen estructurado con métricas de extracción CSV
        """
        try:
            stats = self.registry.get_processing_stats()
            
            # Obtener archivos procesados
            successful_files = self.registry.get_files_by_status(ProcessingStatus.SUCCESS)
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            
            # Calcular métricas CSV
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
            
            # Formatear tamaño
            if total_size > 1024 * 1024:  # MB
                size_str = f"{total_size / (1024 * 1024):.1f} MB"
            elif total_size > 1024:  # KB
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{total_size} bytes"
            
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

    def get_complete_summary_for_gui(self):
        """
        Genera un resumen completo combinando CSV y BD
        
        Returns:
            dict: Resumen completo del flujo
        """
        try:
            db_summary = self.get_db_summary_for_gui()
            csv_summary = self.get_csv_summary_for_gui()
            
            # 🔄 MEJORA: Usar el tiempo real calculado desde el registro
            total_time_seconds = db_summary.get('processing_time_seconds', 0)
            
            # 🔄 MEJORA: Formatear tiempo con mayor precisión
            minutes = int(total_time_seconds // 60)
            seconds = int(total_time_seconds % 60)
            milliseconds = int((total_time_seconds % 1) * 1000)
            total_time_str = f"{minutes}:{seconds:02d}"
            if milliseconds > 0:
                total_time_str += f".{milliseconds:03d}"
            
            # Determinar estado general
            if db_summary['failed_uploads'] == 0 and csv_summary['failed_extractions'] == 0:
                overall_status = "✅ Completado"
            elif db_summary['uploaded_files'] > 0 or csv_summary['extracted_files'] > 0:
                overall_status = "⚠️ Parcial"
            else:
                overall_status = "❌ Fallido"
            
            # 🔄 MEJORA: Retornar resumen completo con datos precisos
            return {
                'overall_status': overall_status,
                'total_files': db_summary['total_files'],
                'csv_extracted': csv_summary['extracted_files'],
                'db_uploaded': db_summary['uploaded_files'],
                'total_errors': db_summary['failed_uploads'] + csv_summary['failed_extractions'],
                'total_time': total_time_str,  # 🔄 MEJORA: Tiempo total real formateado
                'success_rate': db_summary['success_rate'],
                'data_processed': db_summary['inserted_records'],  # 🔄 MEJORA: Registros totales reales
                'connection_status': db_summary['connection_status'],
                'files': db_summary['files'],  # 🔄 MEJORA: Detalle por archivo con tiempos
                'data_size': db_summary['data_size'],
                'source_app': csv_summary['source_app'],
                'processing_time_seconds': total_time_seconds  # 🔄 MEJORA: Tiempo en segundos para cálculos
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando resumen completo: {e}")
            return {
                'overall_status': '❌ Error',
                'total_files': 0,
                'csv_extracted': 0,
                'db_uploaded': 0,
                'total_errors': 1,
                'total_time': '0:00',
                'success_rate': 0,
                'data_processed': 0,  # 🔄 MEJORA: Clave correcta
                'connection_status': 'Error',
                'files': [],
                'data_size': '0 bytes',
                'source_app': 'Sonel Analysis',
                'processing_time_seconds': 0
            }
    

    def save_processing_summary_to_file(self, output_file=None, include_files_detail=True):
        """
        Guarda un resumen completo del procesamiento ETL en un archivo JSON
        
        Args:
            output_file: Ruta del archivo de salida. Si es None, usa un nombre por defecto
            include_files_detail: Si True, incluye el detalle de cada archivo procesado
            
        Returns:
            str: Ruta del archivo generado o None si hay error
        """
        try:
            # Definir archivo de salida por defecto
            if output_file is None:
                data_dir = self.config['PATHS']['data_dir']
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(data_dir, f"resumen_etl.json")
            
            # Obtener resumen completo
            complete_summary = self.get_complete_summary_for_gui()
            db_summary = self.get_db_summary_for_gui()
            csv_summary = self.get_csv_summary_for_gui()
            
            # Obtener estadísticas del registro
            stats = self.registry.get_processing_stats()
            
            # Crear estructura de datos completa para guardar
            summary_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat() + 'Z',
                    "etl_version": "1.0",
                    "config_file": getattr(self, 'config_file', 'config.ini'),
                    "registry_file": self.registry_file
                },
                "overall_summary": complete_summary,
                "database_summary": {
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
                },
                "csv_summary": csv_summary,
                "processing_statistics": stats,
                "files_processed": []
            }
            
            # Agregar detalle de archivos si se solicita
            if include_files_detail and 'files' in db_summary:
                summary_data["files_processed"] = db_summary['files']
            
            # Agregar información adicional del registro
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
            
            # Agregar tiempo total del batch si está disponible
            batch_time = self.registry.get_batch_processing_time()
            if batch_time:
                summary_data["batch_processing"] = {
                    "total_time_seconds": batch_time,
                    "batch_start": self.registry.registry_data.get("batch_start_time", "N/A"),
                    "batch_end": self.registry.registry_data.get("batch_end_time", "N/A")
                }
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Guardar archivo JSON con formato legible
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Resumen ETL guardado en: {output_file}")
            logger.info(f"📁 Tamaño del archivo: {os.path.getsize(output_file)} bytes")
            
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error guardando resumen ETL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
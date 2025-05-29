import time
import logging
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import pyautogui
import os
from datetime import datetime
import threading
import sys

# ✅ CLASE PARA INDICADOR DE PROGRESO EN TIEMPO REAL
class ProgressIndicator:
    def __init__(self, logger):
        self.logger = logger
        self.is_running = False
        self.current_step = ""
        self.thread = None
        self.step_start_time = None
        
    def start(self, step_name):
        """Inicia el indicador de progreso para un paso específico"""
        self.current_step = step_name
        self.step_start_time = time.time()
        self.is_running = True
        self.thread = threading.Thread(target=self._show_progress, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Detiene el indicador de progreso"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def _show_progress(self):
        """Muestra el progreso en tiempo real"""
        counter = 0
        spinner_chars = "|/-\\"
        
        while self.is_running:
            elapsed_time = time.time() - self.step_start_time if self.step_start_time else 0
            spinner = spinner_chars[counter % len(spinner_chars)]
            
            # Mostrar en consola
            sys.stdout.write(f"\r🔄 {spinner} Ejecutando: {self.current_step} - Tiempo: {elapsed_time:.1f}s")
            sys.stdout.flush()
            
            # Log cada 10 segundos
            if counter % 20 == 0:  # Cada 10 segundos (0.5s * 20)
                self.logger.info(f"⏱️ PROGRESO: {self.current_step} - {elapsed_time:.1f}s transcurridos")
            
            time.sleep(0.5)
            counter += 1

# Configurar logging para escribir tanto en consola como en archivo
class DualHandler:
    def __init__(self, filename):
        self.terminal = open("CON", "w", encoding='utf-8') if os.name == 'nt' else None
        self.log_file = open(filename, 'w', encoding='utf-8')
        
    def write(self, message):
        if self.terminal:
            self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()
        
    def flush(self):
        if self.terminal:
            self.terminal.flush()
        self.log_file.flush()
        
    def close(self):
        if self.terminal:
            self.terminal.close()
        self.log_file.close()

# ✅ COORDENADAS GUI CENTRALIZADAS - Resolución 1920x1080
GUI_COORDINATES = {
    # Coordenadas principales del flujo de trabajo
    'config_1': (284, 144),
    'analisis_datos': (1238, 750),
    'mediciones': (182, 179),
    'check_usuario': (374, 389),
   
    # Coordenadas de exportación
    'tabla_esquina': (393, 436),
    'informes': (189, 365),
    'exportar_csv': (191, 426),
    'dialogo_nombre': (522, 689),
   
    # Coordenadas adicionales para estabilidad
    'ventana_principal': (960, 540),  # Centro de pantalla
    'boton_guardar': (700, 700),     # Botón guardar genérico
    'campo_archivo': (600, 500),     # Campo de nombre de archivo genérico
    'boton_cerrar': (1900, 10),      # Botón X para cerrar
}

class SonelAnalysisAutomator:
    def __init__(self, archivo_pqm, ruta_exe="D:/Wolfly/Sonel/SonelAnalysis.exe"):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.app = None
        self.main_window = None
        self.controles_mapeados = {}
        
        # Crear archivo de log con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"sonel_analysis_log_{timestamp}.txt"
        
        # Configurar logging dual (consola + archivo)
        self.dual_handler = DualHandler(self.log_filename)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.StreamHandler(self.dual_handler)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # ✅ INICIALIZAR INDICADOR DE PROGRESO
        self.progress = ProgressIndicator(self.logger)
        
        self.logger.info("="*80)
        self.logger.info("🚀 SONEL ANALYSIS AUTOMATOR - INICIADO")
        self.logger.info(f"📁 Archivo PQM: {archivo_pqm}")
        self.logger.info(f"📄 Log guardándose en: {self.log_filename}")
        self.logger.info("="*80)
        
    def safe_click(self, x, y, description, delay=2):
        """Realiza un clic seguro y registra la acción"""
        try:
            self.logger.info(f"🖱️ Clic en: {description} - ({x}, {y})")
            pyautogui.click(x, y)
            
            # ✅ MOSTRAR PROGRESO DURANTE LA ESPERA
            self.progress.start(f"Esperando después de clic en {description}")
            time.sleep(delay)
            self.progress.stop()
            print()  # Nueva línea después del spinner
            
            return True
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error en clic {description}: {e}")
            return False
            
    def inicializar_aplicacion(self):
        """Inicializa la aplicación Sonel Analysis"""
        try:
            self.progress.start("Verificando archivo PQM")
            
            if not os.path.exists(self.archivo_pqm):
                self.progress.stop()
                print()
                raise FileNotFoundError(f"El archivo {self.archivo_pqm} no existe")
            
            self.progress.stop()
            print()
            self.logger.info("✅ Archivo PQM verificado")
            
            self.progress.start("Iniciando Sonel Analysis")
            self.logger.info("🚀 Iniciando Sonel Analysis...")
            
            self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
            
            # Espera con indicador de progreso
            self.progress.stop()
            print()
            self.progress.start("Esperando carga completa de la aplicación")
            time.sleep(10)  # Esperar carga completa
            self.progress.stop()
            print()
            
            # Obtener ventana principal
            self.progress.start("Obteniendo ventana principal")
            ventanas = self.app.windows()
            self.logger.info(f"📋 Ventanas detectadas: {[w.window_text() for w in ventanas]}")
            
            self.main_window = self.app.top_window()
            self.main_window.set_focus()
            self.main_window.maximize()
            
            self.progress.stop()
            print()
            self.logger.info(f"🪟 Ventana principal: {self.main_window.window_text()}")
            return True
            
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error inicializando aplicación: {e}")
            return False
    
    def mapear_controles(self):
        """Mapea y extrae información de los controles disponibles"""
        try:
            self.progress.start("Mapeando controles disponibles")
            self.logger.info("🗺️ Mapeando controles disponibles...")
            
            # Extraer información completa de controles
            self.logger.info("📋 === ESTRUCTURA COMPLETA DE CONTROLES ===")
            self.main_window.print_control_identifiers()
            
            # Mapear controles específicos que necesitamos
            self._buscar_controles_especificos()
            
            self.progress.stop()
            print()
            return True
            
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error mapeando controles: {e}")
            return False
    
    def _buscar_controles_especificos(self):
        """Busca controles específicos por tipo y texto"""
        try:
            self.progress.start("Buscando controles específicos")
            
            # Buscar ventana de análisis
            dialogs = self.main_window.descendants(control_type="Window")
            for dialog in dialogs:
                title = dialog.window_text()
                if "Análisis" in title and ".pqm" in title:
                    self.controles_mapeados['ventana_analisis'] = dialog
                    self.logger.info(f"✅ Encontrada ventana de análisis: {title}")
                    break
            
            # Buscar TreeView (árbol de navegación)
            treeviews = self.main_window.descendants(control_type="Tree")
            if treeviews:
                self.controles_mapeados['tree_navegacion'] = treeviews[0]
                self.logger.info("✅ TreeView de navegación encontrado")
                
                # Explorar elementos del árbol
                self._explorar_tree_view(treeviews[0])
            
            # Buscar menús
            menus = self.main_window.descendants(control_type="MenuBar")
            if menus:
                self.controles_mapeados['menu_principal'] = menus[0]
                self.logger.info("✅ Menú principal encontrado")
            
            # Buscar botones
            buttons = self.main_window.descendants(control_type="Button")
            for button in buttons:
                button_text = button.window_text()
                if button_text:
                    self.controles_mapeados[f'button_{button_text.lower()}'] = button
                    self.logger.info(f"✅ Botón encontrado: {button_text}")
            
            self.progress.stop()
            print()
            
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error buscando controles específicos: {e}")
    
    def _explorar_tree_view(self, tree_control):
        """Explora los elementos del TreeView"""
        try:
            self.logger.info("🌳 Explorando TreeView...")
            
            # Obtener elementos del árbol
            tree_items = tree_control.descendants(control_type="TreeItem")
            
            for i, item in enumerate(tree_items):
                item_text = item.window_text()
                if item_text:
                    self.controles_mapeados[f'tree_item_{i}'] = item
                    self.logger.info(f"  📂 Item {i}: {item_text}")
                    
                    # Si es un elemento que necesitamos, guardarlo con nombre específico
                    if "Config" in item_text:
                        self.controles_mapeados['config_node'] = item
                    elif "Mediciones" in item_text:
                        self.controles_mapeados['mediciones_node'] = item
                    elif "Informes" in item_text:
                        self.controles_mapeados['informes_node'] = item
            
        except Exception as e:
            self.logger.error(f"❌ Error explorando TreeView: {e}")
    
    def ejecutar_flujo_completo(self):
        """Ejecuta TODOS los pasos del flujo siguiendo las coordenadas exactas"""
        try:
            self.logger.info("🧭 === INICIANDO FLUJO COMPLETO CON COORDENADAS EXACTAS ===")
            
            # PASO 1: Config (usando coordenadas exactas)
            self.logger.info("=== PASO 1: CONFIG ===")
            if not self.safe_click(GUI_COORDINATES['config_1'][0], GUI_COORDINATES['config_1'][1], "Config 1", 3):
                return False
            self._extraer_info_paso("Config 1")
            
            # PASO 2: Análisis de Datos
            self.logger.info("=== PASO 2: ANÁLISIS DE DATOS ===")
            if not self.safe_click(GUI_COORDINATES['analisis_datos'][0], GUI_COORDINATES['analisis_datos'][1], "Análisis de Datos", 3):
                return False
            self._extraer_info_paso("Análisis de Datos")
            
            # PASO 3: Mediciones (CON TIMEOUT PARA EVITAR CUELGUE)
            self.logger.info("=== PASO 3: MEDICIONES ===")
            self.logger.info("⚠️ INICIANDO PASO CRÍTICO - MEDICIONES")
            
            if not self.safe_click(GUI_COORDINATES['mediciones'][0], GUI_COORDINATES['mediciones'][1], "Mediciones", 3):
                return False
            
            # ✅ EXTRAER INFO CON TIMEOUT PARA EVITAR CUELGUE
            self.logger.info("🔍 Extrayendo información de Mediciones con timeout...")
            try:
                self._extraer_info_paso_con_timeout("Mediciones", timeout_seconds=30)
            except TimeoutError:
                self.logger.warning("⚠️ TIMEOUT en extracción de Mediciones - Continuando...")
            
            # PASO 4: Checkbox usuario
            self.logger.info("=== PASO 4: CHECKBOX USUARIO ===")
            if not self.safe_click(GUI_COORDINATES['check_usuario'][0], GUI_COORDINATES['check_usuario'][1], "Checkbox usuario", 3):
                return False
            self._extraer_info_paso("Checkbox usuario")
            
            # PASO 5: Tabla esquina
            self.logger.info("=== PASO 5: TABLA ESQUINA ===")
            if not self.safe_click(GUI_COORDINATES['tabla_esquina'][0], GUI_COORDINATES['tabla_esquina'][1], "Tabla esquina", 3):
                return False
            self._extraer_info_paso("Tabla esquina")
            
            # PASO 6: Menú Informes
            self.logger.info("=== PASO 6: MENÚ INFORMES ===")
            if not self.safe_click(GUI_COORDINATES['informes'][0], GUI_COORDINATES['informes'][1], "Menú Informes", 3):
                return False
            self._extraer_info_paso("Menú Informes")
            
            # PASO 7: Exportar CSV
            self.logger.info("=== PASO 7: EXPORTAR CSV ===")
            if not self.safe_click(GUI_COORDINATES['exportar_csv'][0], GUI_COORDINATES['exportar_csv'][1], "Exportar CSV", 3):
                return False
            self._extraer_info_paso("Exportar CSV")
            
            # PASO 8: Campo nombre archivo
            self.logger.info("=== PASO 8: CONFIGURAR NOMBRE DE ARCHIVO ===")
            if not self.safe_click(GUI_COORDINATES['dialogo_nombre'][0], GUI_COORDINATES['dialogo_nombre'][1], "Campo nombre archivo", 3):
                return False
            
            # Generar nombre del archivo CSV
            csv_base_name = self.generate_csv_filename(self.archivo_pqm)
            csv_full_path = f"D:\\Universidad\\8vo Semestre\\Practicas\\Sonel\\data\\archivos_csv\\{csv_base_name}.csv"
            
            # Limpiar campo y escribir nombre
            self.progress.start("Escribiendo nombre de archivo")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            pyautogui.write(csv_full_path)
            time.sleep(0.5)
            self.progress.stop()
            print()
            
            self.logger.info(f"💾 Nombre de archivo establecido: {csv_full_path}")
            
            self.progress.start("Guardando archivo CSV")
            pyautogui.press('enter')
            time.sleep(5)  # Esperar a que se complete la exportación
            self.progress.stop()
            print()
            
            self._extraer_info_paso("Configuración nombre archivo")
            
            # Verificar si el archivo se creó
            if os.path.exists(csv_full_path):
                file_size = os.path.getsize(csv_full_path)
                self.logger.info(f"✅ Archivo CSV creado exitosamente: {csv_full_path} ({file_size:,} bytes)")
            else:
                self.logger.warning(f"⚠️ No se pudo verificar la creación del archivo: {csv_full_path}")
            
            self.logger.info("✅ FLUJO COMPLETO FINALIZADO EXITOSAMENTE")
            return True
            
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error en flujo completo: {e}")
            return False
    
    def _extraer_info_paso_con_timeout(self, paso, timeout_seconds=30):
        """Extrae información con timeout para evitar cuelgues"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Timeout en extracción de {paso}")
        
        # Solo en sistemas Unix/Linux
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        try:
            self.progress.start(f"Extrayendo información de {paso}")
            self._extraer_info_paso(paso)
            self.progress.stop()
            print()
            
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancelar alarma
                
        except Exception as e:
            self.progress.stop()
            print()
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            if "Timeout" in str(e):
                raise TimeoutError(f"Timeout en {paso}")
            else:
                raise e
    
    def generate_csv_filename(self, pqm_file_path):
        """Genera nombre del archivo CSV basado en el archivo PQM"""
        try:
            base_name = os.path.splitext(os.path.basename(pqm_file_path))[0]
            # Limpiar caracteres especiales
            clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            return clean_name.replace(' ', '_')
        except Exception as e:
            self.logger.error(f"Error generando nombre CSV: {e}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"sonel_export_{timestamp}"
    
    def _extraer_info_paso(self, paso):
        """🚀 VERSIÓN OPTIMIZADA - SOLO DETECTA TABLAS SIN ANÁLISIS EXHAUSTIVO"""
        try:
            self.logger.info(f"📋 === INFORMACIÓN DESPUÉS DE: {paso} ===")
            
            # Extraer estructura completa de controles (esto es rápido)
            try:
                self.logger.info("🔍 === ESTRUCTURA COMPLETA DE CONTROLES ===")
                self.main_window.print_control_identifiers()
            except Exception as e:
                self.logger.error(f"❌ Error imprimiendo estructura: {e}")
            
            # ✅ PROCESAMIENTO OPTIMIZADO - SIN ANÁLISIS EXHAUSTIVO DE TABLAS
            control_types_to_process = [
                ("Window", "Window"),
                ("Dialog", "Window"), 
                ("Table", "Table"),      # ✅ OPTIMIZADO: Solo info básica
                ("DataGrid", "DataGrid"), # ✅ OPTIMIZADO: Solo info básica
                ("Text", "Text"),
                ("Edit", "Edit"),
                ("Button", "Button"),
                ("Tree", "Tree"),
                ("List", "List"),
                ("MenuItem", "MenuItem"),
                ("CheckBox", "CheckBox"),
                ("ComboBox", "ComboBox")
            ]
            
            for control_name, control_type in control_types_to_process:
                try:
                    controls = self.main_window.descendants(control_type=control_type)
                    if controls:
                        self.logger.info(f"\n🔍 === {control_name.upper()} - {len(controls)} ENCONTRADOS ===")
                        
                        for i, control in enumerate(controls):
                            try:
                                # Extraer información básica
                                text = control.window_text()
                                rect = control.rectangle()
                                auto_id = getattr(control.element_info, 'automation_id', '')
                                class_name = getattr(control.element_info, 'class_name', '')
                                control_type_info = getattr(control.element_info, 'control_type', '')
                                
                                self.logger.info(f"[{i}] === {control_name} BÁSICO ===")
                                self.logger.info(f"TEXTO: {text}")
                                self.logger.info(f"AUTO_ID: {auto_id}")
                                self.logger.info(f"CLASS: {class_name}")
                                self.logger.info(f"TYPE: {control_type_info}")
                                self.logger.info(f"POS: {rect}")
                                
                                # ✅ OPTIMIZACIÓN CLAVE: TABLAS SIN ANÁLISIS EXHAUSTIVO
                                if control_type == "Table" or control_type == "DataGrid":
                                    try:
                                        self.logger.info("=== 📊 TABLA DETECTADA - INFO BÁSICA SOLAMENTE ===")
                                        
                                        # ✅ SOLO CONTAR ELEMENTOS, NO PROCESARLOS UNO POR UNO
                                        try:
                                            rows = control.descendants(control_type="DataItem")
                                            headers = control.descendants(control_type="Header")
                                            cells = control.descendants(control_type="Custom")
                                            
                                            self.logger.info(f"📊 TABLA RESUMEN:")
                                            self.logger.info(f"   🔢 TOTAL FILAS: {len(rows)}")
                                            self.logger.info(f"   📋 TOTAL HEADERS: {len(headers)}")
                                            self.logger.info(f"   📦 TOTAL CELDAS: {len(cells)}")
                                            self.logger.info(f"   ✅ TABLA DETECTADA Y CONTABILIZADA")
                                            
                                            # ✅ SOLO MOSTRAR ALGUNOS HEADERS (NO TODOS)
                                            if headers and len(headers) > 0:
                                                self.logger.info("📋 ALGUNOS HEADERS ENCONTRADOS:")
                                                for h_idx, header in enumerate(headers[:5]):  # ✅ SOLO LOS PRIMEROS 5
                                                    header_text = header.window_text()
                                                    self.logger.info(f"   HEADER[{h_idx}]: {header_text}")
                                                
                                                if len(headers) > 5:
                                                    self.logger.info(f"   ... y {len(headers) - 5} headers más")
                                            
                                        except Exception as count_error:
                                            self.logger.info(f"Info conteo tabla - Error: {count_error}")
                                            self.logger.info("✅ TABLA DETECTADA (conteo no disponible)")
                                        
                                        self.logger.info("=== FIN INFO TABLA ===")
                                        
                                    except Exception as table_error:
                                        self.logger.info(f"Info tabla básica - Error: {table_error}")
                                        self.logger.info("✅ TABLA DETECTADA (info básica no disponible)")
                                
                                self.logger.info("=" * 30)
                                
                            except Exception as control_error:
                                self.logger.error(f"Error procesando {control_name}[{i}]: {control_error}")
                                
                except Exception as type_error:
                    self.logger.info(f"No se pudieron obtener controles {control_name}: {type_error}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error en extracción paso {paso}: {e}")
    
    def extraer_datos_completos_final(self):
        """Extrae TODOS los datos disponibles en la aplicación - ANÁLISIS FINAL OPTIMIZADO"""
        try:
            self.progress.start("Extracción final optimizada de datos")
            self.logger.info("📊 === EXTRACCIÓN FINAL OPTIMIZADA ===")
            
            # Estructura COMPLETA final
            self.logger.info("🔍 === ESTRUCTURA COMPLETA FINAL ===")
            try:
                self.main_window.print_control_identifiers()
            except Exception as e:
                self.logger.error(f"Error imprimiendo estructura final: {e}")
            
            # ✅ SOLO CONTROLES IMPORTANTES Y PROCESAMIENTO MÍNIMO
            important_control_types = [
                "Table", "DataGrid", "Text", "Button", "Tree", "List"
            ]
            
            self.progress.stop()
            print()
            self.logger.info("🔍 === EXTRACCIÓN OPTIMIZADA DE CONTROLES IMPORTANTES ===")
            
            for control_type in important_control_types:
                try:
                    self.progress.start(f"Procesando {control_type}")
                    controls = self.main_window.descendants(control_type=control_type)
                    
                    if controls:
                        self.logger.info(f"\n{'='*60}")
                        self.logger.info(f"🔍 TIPO: {control_type.upper()} - TOTAL: {len(controls)}")
                        self.logger.info(f"{'='*60}")
                        
                        # ✅ PROCESAMIENTO MÍNIMO - SOLO PRIMEROS 3 CONTROLES
                        for i, control in enumerate(controls[:3]):
                            try:
                                self.logger.info(f"\n--- [{control_type}][{i}] ---")
                                
                                text = control.window_text()
                                rect = control.rectangle()
                                element_info = control.element_info
                                auto_id = getattr(element_info, 'automation_id', '')
                                
                                self.logger.info(f"TEXT: {repr(text)}")
                                self.logger.info(f"AUTO_ID: {repr(auto_id)}")
                                self.logger.info(f"RECT: {rect}")
                                
                                # ✅ PARA TABLAS: SOLO INFO BÁSICA
                                if control_type in ["Table", "DataGrid"]:
                                    try:
                                        descendants_count = len(control.descendants())
                                        self.logger.info(f"TABLA INFO: {descendants_count} elementos internos total")
                                        self.logger.info("✅ TABLA PROCESADA BÁSICAMENTE")
                                    except:
                                        self.logger.info("✅ TABLA DETECTADA")
                                
                            except Exception as control_error:
                                self.logger.error(f"ERROR {control_type}[{i}]: {control_error}")
                    
                    self.progress.stop()
                    print()
                                
                except Exception as type_error:
                    self.progress.stop()
                    print()
                    if "No such" not in str(type_error):
                        self.logger.info(f"INFO - No {control_type}: {type_error}")
            
            self.logger.info("\n" + "="*60)
            self.logger.info("✅ EXTRACCIÓN OPTIMIZADA FINALIZADA")
            self.logger.info("="*60)
                    
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error en extracción completa final: {e}")
    
    def ejecutar_automatizacion_completa(self):
        """Ejecuta el flujo completo de automatización"""
        try:
            self.logger.info("🚀 === INICIANDO AUTOMATIZACIÓN COMPLETA ===")
            
            if not self.inicializar_aplicacion():
                self.logger.error("❌ Fallo en inicialización")
                return False
            
            if not self.mapear_controles():
                self.logger.error("❌ Fallo en mapeo de controles")
                return False
            
            if not self.ejecutar_flujo_completo():
                self.logger.error("❌ Fallo en ejecución del flujo")
                return False
            
            self.extraer_datos_completos_final()
            
            self.logger.info("✅ === AUTOMATIZACIÓN COMPLETADA EXITOSAMENTE ===")
            self.logger.info(f"📄 Información completa guardada en: {self.log_filename}")
            return True
            
        except Exception as e:
            self.progress.stop()
            print()
            self.logger.error(f"❌ Error en automatización completa: {e}")
            return False
        finally:
            self.progress.stop()
            
            if self.app:
                try:
                    self.app.kill()
                    self.logger.info("🔚 Aplicación cerrada")
                except:
                    pass
            
            # Cerrar el archivo de log
            try:
                self.dual_handler.close()
            except:
                pass

def main():
    # Configuración
    archivo_pqm = "/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm/9. Catiglata T 1225 C 0100234196.pqm702"
    
    # Crear y ejecutar automatizador
    automatizador = SonelAnalysisAutomator(archivo_pqm)
    exito = automatizador.ejecutar_automatizacion_completa()
    
    if exito:
        print(f"\n✅ Proceso completado exitosamente")
        print(f"📄 Revisa el archivo: {automatizador.log_filename}")
    else:
        print(f"\n❌ Proceso falló")
        print(f"📄 Revisa los errores en: {automatizador.log_filename}")

if __name__ == "__main__":
    main()
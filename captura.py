#import pyautogui
#import time

#print("Coloca el mouse donde desees capturar la coordenada...")
#time.sleep(5)
#x, y = pyautogui.position()
#print(f"Coordenadas capturadas: ({x}, {y})")

import time
import logging
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import pyautogui
import os
from datetime import datetime

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
            time.sleep(delay)
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en clic {description}: {e}")
            return False
            
    def inicializar_aplicacion(self):
        """Inicializa la aplicación Sonel Analysis"""
        try:
            if not os.path.exists(self.archivo_pqm):
                raise FileNotFoundError(f"El archivo {self.archivo_pqm} no existe")
            
            self.logger.info("🚀 Iniciando Sonel Analysis...")
            self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
            time.sleep(10)  # Esperar carga completa
            
            # Obtener ventana principal
            ventanas = self.app.windows()
            self.logger.info(f"📋 Ventanas detectadas: {[w.window_text() for w in ventanas]}")
            
            self.main_window = self.app.top_window()
            self.main_window.set_focus()
            self.main_window.maximize()
            
            self.logger.info(f"🪟 Ventana principal: {self.main_window.window_text()}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando aplicación: {e}")
            return False
    
    def mapear_controles(self):
        """Mapea y extrae información de los controles disponibles"""
        try:
            self.logger.info("🗺️ Mapeando controles disponibles...")
            
            # Extraer información completa de controles
            self.logger.info("📋 === ESTRUCTURA COMPLETA DE CONTROLES ===")
            self.main_window.print_control_identifiers()
            
            # Mapear controles específicos que necesitamos
            self._buscar_controles_especificos()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error mapeando controles: {e}")
            return False
    
    def _buscar_controles_especificos(self):
        """Busca controles específicos por tipo y texto"""
        try:
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
            
        except Exception as e:
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
            
            # PASO 3: Mediciones
            self.logger.info("=== PASO 3: MEDICIONES ===")
            if not self.safe_click(GUI_COORDINATES['mediciones'][0], GUI_COORDINATES['mediciones'][1], "Mediciones", 3):
                return False
            self._extraer_info_paso("Mediciones")
            
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
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            pyautogui.write(csv_full_path)
            time.sleep(0.5)
            
            self.logger.info(f"💾 Nombre de archivo establecido: {csv_full_path}")
            pyautogui.press('enter')
            time.sleep(5)  # Esperar a que se complete la exportación
            
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
            self.logger.error(f"❌ Error en flujo completo: {e}")
            return False
    
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
        """Extrae información COMPLETA después de cada paso de navegación"""
        try:
            self.logger.info(f"📋 === INFORMACIÓN COMPLETA DESPUÉS DE: {paso} ===")
            
            # Extraer estructura COMPLETA de controles
            try:
                self.logger.info("🔍 === ESTRUCTURA COMPLETA DE CONTROLES ===")
                self.main_window.print_control_identifiers()
            except Exception as e:
                self.logger.error(f"❌ Error imprimiendo estructura: {e}")
            
            # Extraer información de todos los controles
            all_control_types = [
                ("Window", "Window"),
                ("Dialog", "Window"), 
                ("Table", "Table"),
                ("DataGrid", "DataGrid"),
                ("Text", "Text"),
                ("Edit", "Edit"),
                ("Button", "Button"),
                ("Tree", "Tree"),
                ("List", "List"),
                ("MenuItem", "MenuItem"),
                ("CheckBox", "CheckBox"),
                ("ComboBox", "ComboBox")
            ]
            
            for control_name, control_type in all_control_types:
                try:
                    controls = self.main_window.descendants(control_type=control_type)
                    if controls:
                        self.logger.info(f"\n🔍 === {control_name.upper()} - {len(controls)} ENCONTRADOS ===")
                        
                        for i, control in enumerate(controls):
                            try:
                                # Extraer TODA la información
                                text = control.window_text()
                                rect = control.rectangle()
                                auto_id = getattr(control.element_info, 'automation_id', '')
                                class_name = getattr(control.element_info, 'class_name', '')
                                control_type_info = getattr(control.element_info, 'control_type', '')
                                
                                self.logger.info(f"[{i}] === {control_name} COMPLETO ===")
                                self.logger.info(f"TEXTO COMPLETO: {text}")
                                self.logger.info(f"AUTO_ID: {auto_id}")
                                self.logger.info(f"CLASS_NAME: {class_name}")
                                self.logger.info(f"CONTROL_TYPE: {control_type_info}")
                                self.logger.info(f"RECTANGLE: {rect}")
                                self.logger.info(f"POSICIÓN: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
                                
                                # Para controles específicos, extraer más información
                                if control_type == "Table" or control_type == "DataGrid":
                                    try:
                                        self.logger.info("=== INTENTANDO EXTRAER CONTENIDO DE TABLA ===")
                                        rows = control.descendants(control_type="DataItem")
                                        self.logger.info(f"FILAS ENCONTRADAS: {len(rows)}")
                                        
                                        for row_idx, row in enumerate(rows):
                                            row_text = row.window_text()
                                            self.logger.info(f"FILA[{row_idx}] TEXTO COMPLETO: {row_text}")
                                            
                                    except Exception as table_error:
                                        self.logger.info(f"Info tabla - Error: {table_error}")
                                
                                self.logger.info("=" * 50)
                                
                            except Exception as control_error:
                                self.logger.error(f"Error procesando {control_name}[{i}]: {control_error}")
                                
                except Exception as type_error:
                    self.logger.info(f"No se pudieron obtener controles {control_name}: {type_error}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error en extracción completa paso {paso}: {e}")
    
    def extraer_datos_completos_final(self):
        """Extrae TODOS los datos disponibles en la aplicación - ANÁLISIS FINAL"""
        try:
            self.logger.info("📊 === EXTRACCIÓN FINAL COMPLETA DE TODOS LOS DATOS ===")
            
            # Estructura COMPLETA final
            self.logger.info("🔍 === ESTRUCTURA COMPLETA FINAL ===")
            try:
                self.main_window.print_control_identifiers()
            except Exception as e:
                self.logger.error(f"Error imprimiendo estructura final: {e}")
            
            # Extraer TODOS los tipos de controles posibles
            all_control_types = [
                "Window", "Dialog", "Table", "DataGrid", "Text", "Edit", 
                "Button", "Tree", "List", "MenuItem", "CheckBox", "ComboBox",
                "ScrollBar", "Tab", "TabItem", "Pane", "Group", "Custom",
                "Image", "Hyperlink", "Document", "Calendar", "DataItem",
                "Header", "HeaderItem", "ListItem", "MenuBar", "Menu",
                "ProgressBar", "RadioButton", "Slider", "Spinner", "StatusBar",
                "ToolBar", "ToolTip", "TreeItem", "Application", "PropertyPage"
            ]
            
            self.logger.info("🔍 === EXTRACCIÓN EXHAUSTIVA DE TODOS LOS CONTROLES ===")
            
            for control_type in all_control_types:
                try:
                    controls = self.main_window.descendants(control_type=control_type)
                    if controls:
                        self.logger.info(f"\n{'='*60}")
                        self.logger.info(f"🔍 TIPO: {control_type.upper()} - TOTAL: {len(controls)}")
                        self.logger.info(f"{'='*60}")
                        
                        for i, control in enumerate(controls):
                            try:
                                self.logger.info(f"\n--- [{control_type}][{i}] INFORMACIÓN COMPLETA ---")
                                
                                # Extraer TODA la información disponible
                                text = control.window_text()
                                rect = control.rectangle()
                                
                                # Información del elemento
                                element_info = control.element_info
                                auto_id = getattr(element_info, 'automation_id', '')
                                class_name = getattr(element_info, 'class_name', '')
                                control_type_value = getattr(element_info, 'control_type', '')
                                name = getattr(element_info, 'name', '')
                                value = getattr(element_info, 'value', '')
                                help_text = getattr(element_info, 'help_text', '')
                                
                                # Log de toda la información
                                self.logger.info(f"WINDOW_TEXT: {repr(text)}")
                                self.logger.info(f"NAME: {repr(name)}")
                                self.logger.info(f"VALUE: {repr(value)}")
                                self.logger.info(f"AUTO_ID: {repr(auto_id)}")
                                self.logger.info(f"CLASS_NAME: {repr(class_name)}")
                                self.logger.info(f"CONTROL_TYPE: {repr(control_type_value)}")
                                self.logger.info(f"HELP_TEXT: {repr(help_text)}")
                                self.logger.info(f"RECTANGLE: {rect}")
                                self.logger.info(f"COORDINATES: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
                                self.logger.info(f"SIZE: Width={rect.width()}, Height={rect.height()}")
                                
                                # Para tablas y grillas, extraer contenido específico
                                if control_type in ["Table", "DataGrid"]:
                                    self.logger.info("--- EXTRACCIÓN ESPECÍFICA DE TABLA/DATAGRID ---")
                                    try:
                                        rows = control.descendants(control_type="DataItem")
                                        cells = control.descendants(control_type="Text")
                                        headers = control.descendants(control_type="HeaderItem")
                                        
                                        self.logger.info(f"FILAS_DATAITEM: {len(rows)}")
                                        self.logger.info(f"CELDAS_TEXT: {len(cells)}")
                                        self.logger.info(f"HEADERS: {len(headers)}")
                                        
                                        # Headers completos
                                        for h_idx, header in enumerate(headers):
                                            h_text = header.window_text()
                                            self.logger.info(f"HEADER[{h_idx}]: {repr(h_text)}")
                                        
                                        # Filas completas
                                        for r_idx, row in enumerate(rows):
                                            r_text = row.window_text()
                                            self.logger.info(f"ROW[{r_idx}]: {repr(r_text)}")
                                        
                                        # Celdas completas
                                        for c_idx, cell in enumerate(cells):
                                            c_text = cell.window_text()
                                            if c_text:
                                                self.logger.info(f"CELL[{c_idx}]: {repr(c_text)}")
                                                
                                    except Exception as table_error:
                                        self.logger.info(f"ERROR_TABLA: {table_error}")
                                
                                # Para árboles, extraer estructura
                                if control_type == "Tree":
                                    self.logger.info("--- EXTRACCIÓN ESPECÍFICA DE ÁRBOL ---")
                                    try:
                                        tree_items = control.descendants(control_type="TreeItem")
                                        self.logger.info(f"TREE_ITEMS: {len(tree_items)}")
                                        
                                        for t_idx, item in enumerate(tree_items):
                                            t_text = item.window_text()
                                            self.logger.info(f"TREE_ITEM[{t_idx}]: {repr(t_text)}")
                                            
                                    except Exception as tree_error:
                                        self.logger.info(f"ERROR_ÁRBOL: {tree_error}")
                                
                                self.logger.info("-" * 50)
                                
                            except Exception as control_error:
                                self.logger.error(f"ERROR procesando {control_type}[{i}]: {control_error}")
                                
                except Exception as type_error:
                    if "No such" not in str(type_error):
                        self.logger.info(f"INFO - No se encontraron controles {control_type}: {type_error}")
            
            self.logger.info("\n" + "="*60)
            self.logger.info("✅ EXTRACCIÓN COMPLETA FINALIZADA")
            self.logger.info("="*60)
                    
        except Exception as e:
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
            self.logger.error(f"❌ Error en automatización completa: {e}")
            return False
        finally:
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
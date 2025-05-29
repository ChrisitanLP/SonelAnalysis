import time
import logging
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import pyautogui
import os
from datetime import datetime
import threading
import sys

class SonelComponentExtractor:
    def __init__(self, archivo_pqm, ruta_exe="D:/Wolfly/Sonel/SonelAnalysis.exe"):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.app = None
        self.main_window = None
        self.analysis_window = None
        
        # Configurar logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"sonel_focused_extraction_{timestamp}.txt"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(self.log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("="*80)
        self.logger.info("🎯 EXTRACTOR OPTIMIZADO DE COMPONENTES SONEL ANALYSIS")
        self.logger.info(f"📁 Archivo PQM: {archivo_pqm}")
        self.logger.info("="*80)

    def conectar_ventana_analisis(self):
        """Conecta específicamente con la ventana de análisis activa"""
        try:
            self.logger.info("🔍 Conectando con ventana de análisis activa...")
            
            # Intentar conectar con aplicación existente
            try:
                self.app = Application(backend="uia").connect(title_re=".*Análisis.*")
                self.logger.info("✅ Conectado con aplicación existente")
            except:
                # Si no existe, iniciar nueva instancia
                self.logger.info("🚀 Iniciando nueva instancia de Sonel Analysis...")
                self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                time.sleep(10)  # Esperar carga completa
            
            # Obtener ventana principal
            self.main_window = self.app.top_window()
            self.main_window.set_focus()
            
            # Buscar ventana de análisis específica
            self.analysis_window = self._encontrar_ventana_analisis()
            
            if self.analysis_window:
                self.logger.info(f"✅ Ventana de análisis encontrada: {self.analysis_window.window_text()}")
                return True
            else:
                self.logger.error("❌ No se encontró ventana de análisis")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando con ventana: {e}")
            return False

    def _encontrar_ventana_analisis(self):
        """Encuentra la ventana específica de análisis que termina en 'Configuración 1'"""
        try:
            # Buscar ventana que contenga "Análisis" y ".pqm" y termine en "Configuración 1"
            windows = self.main_window.descendants(control_type="Window")
            for window in windows:
                title = window.window_text()
                if "Análisis" in title and ".pqm" in title and title.strip().endswith("Configuración 1"):
                    return window

            # Fallback: verificar si la ventana principal cumple con el patrón
            main_title = self.main_window.window_text()
            if "Análisis" in main_title and ".pqm" in main_title and main_title.strip().endswith("Configuración 1"):
                return self.main_window

            return None

        except Exception as e:
            self.logger.error(f"Error buscando ventana de análisis: {e}")
            return None


    def extraer_navegacion_lateral(self):
        """Extrae información de la sección de navegación lateral izquierda"""
        try:
            self.logger.info("\n🧭 === EXTRACCIÓN: NAVEGACIÓN LATERAL ===")
            
            elementos_buscados = ["General", "Mediciones", "Eventos", "Configuración"]
            navegacion_encontrada = {}
            
            # Buscar elementos de texto y botones
            for tipo_control in ["Text", "Button", "TreeItem"]:
                try:
                    controles = self.analysis_window.descendants(control_type=tipo_control)
                    
                    for control in controles:
                        texto = control.window_text().strip()
                        
                        if texto in elementos_buscados:
                            rect = control.rectangle()
                            navegacion_encontrada[texto] = {
                                'tipo': tipo_control,
                                'texto': texto,
                                'posicion': f"L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom}",
                                'control': control
                            }
                            
                            self.logger.info(f"✅ ENCONTRADO: {texto}")
                            self.logger.info(f"   Tipo: {tipo_control}")
                            self.logger.info(f"   Posición: {navegacion_encontrada[texto]['posicion']}")
                            
                except Exception as e:
                    self.logger.debug(f"Tipo {tipo_control} no disponible: {e}")
            
            self.logger.info(f"📊 RESUMEN NAVEGACIÓN: {len(navegacion_encontrada)} elementos encontrados")
            return navegacion_encontrada
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo navegación: {e}")
            return {}

    def extraer_mostrar_datos(self):
        """Extrae información de la sección 'Mostrar datos' con checkboxes"""
        try:
            self.logger.info("\n📊 === EXTRACCIÓN: SECCIÓN MOSTRAR DATOS ===")
            
            checkboxes_buscados = ["10s", "1 min", "10 min", "1h", "1 día"]
            checkboxes_encontrados = {}
            
            # Buscar checkboxes
            checkboxes = self.analysis_window.descendants(control_type="CheckBox")
            
            for checkbox in checkboxes:
                try:
                    texto = checkbox.window_text().strip()
                    
                    # Verificar si coincide con alguno de los buscados
                    for checkbox_buscado in checkboxes_buscados:
                        if checkbox_buscado in texto or texto == checkbox_buscado:
                            rect = checkbox.rectangle()
                            
                            # Obtener estado del checkbox
                            try:
                                estado = checkbox.get_toggle_state()
                            except:
                                estado = "Desconocido"
                            
                            checkboxes_encontrados[texto] = {
                                'texto': texto,
                                'estado': estado,
                                'posicion': f"L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom}",
                                'control': checkbox
                            }
                            
                            self.logger.info(f"✅ CHECKBOX: {texto}")
                            self.logger.info(f"   Estado: {estado}")
                            self.logger.info(f"   Posición: {checkboxes_encontrados[texto]['posicion']}")
                            
                except Exception as e:
                    self.logger.debug(f"Error procesando checkbox: {e}")
            
            # Buscar también en grupos con título "Mostrar datos"
            try:
                grupos = self.analysis_window.descendants(control_type="Group")
                for grupo in grupos:
                    if "Mostrar" in grupo.window_text() or "datos" in grupo.window_text():
                        self.logger.info(f"📋 Grupo encontrado: {grupo.window_text()}")
                        
                        # Buscar checkboxes dentro del grupo
                        checkboxes_grupo = grupo.descendants(control_type="CheckBox")
                        for cb in checkboxes_grupo:
                            texto = cb.window_text().strip()
                            if texto not in checkboxes_encontrados:
                                rect = cb.rectangle()
                                try:
                                    estado = cb.get_toggle_state()
                                except:
                                    estado = "Desconocido"
                                
                                checkboxes_encontrados[texto] = {
                                    'texto': texto,
                                    'estado': estado,
                                    'posicion': f"L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom}",
                                    'control': cb
                                }
                                
                                self.logger.info(f"✅ CHECKBOX (en grupo): {texto}")
                                self.logger.info(f"   Estado: {estado}")
                                
            except Exception as e:
                self.logger.debug(f"Error buscando en grupos: {e}")
            
            self.logger.info(f"📊 RESUMEN CHECKBOXES: {len(checkboxes_encontrados)} encontrados")
            return checkboxes_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo checkboxes: {e}")
            return {}

    def extraer_informes_graficos(self):
        """Extrae información de la sección 'Informes y gráficos'"""
        try:
            self.logger.info("\n📈 === EXTRACCIÓN: INFORMES Y GRÁFICOS ===")
            
            informes_encontrados = {}
            
            # Buscar ComboBox específicos
            comboboxes = self.analysis_window.descendants(control_type="ComboBox")
            
            for combobox in comboboxes:
                try:
                    rect = combobox.rectangle()
                    
                    # Obtener valor seleccionado
                    try:
                        valor_actual = combobox.selected_text()
                    except:
                        try:
                            valor_actual = combobox.get_value()
                        except:
                            valor_actual = "No disponible"
                    
                    # Obtener elementos disponibles
                    try:
                        items = combobox.item_texts()
                    except:
                        items = ["No disponibles"]
                    
                    informes_encontrados[f"ComboBox_{len(informes_encontrados)}"] = {
                        'tipo': 'ComboBox',
                        'valor_actual': valor_actual,
                        'opciones_disponibles': items,
                        'posicion': f"L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom}",
                        'control': combobox
                    }
                    
                    self.logger.info(f"✅ COMBOBOX ENCONTRADO:")
                    self.logger.info(f"   Valor actual: {valor_actual}")
                    self.logger.info(f"   Opciones: {items[:5]}{'...' if len(items) > 5 else ''}")
                    self.logger.info(f"   Posición: {informes_encontrados[f'ComboBox_{len(informes_encontrados)-1}']['posicion']}")
                    
                except Exception as e:
                    self.logger.debug(f"Error procesando combobox: {e}")
            
            # Buscar también elementos con texto "Informes"
            textos = self.analysis_window.descendants(control_type="Text")
            for texto in textos:
                if "Informe" in texto.window_text():
                    rect = texto.rectangle()
                    informes_encontrados[f"Texto_Informe_{len(informes_encontrados)}"] = {
                        'tipo': 'Text',
                        'texto': texto.window_text(),
                        'posicion': f"L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom}",
                        'control': texto
                    }
                    
                    self.logger.info(f"✅ TEXTO INFORME: {texto.window_text()}")
            
            self.logger.info(f"📊 RESUMEN INFORMES: {len(informes_encontrados)} elementos encontrados")
            return informes_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo informes: {e}")
            return {}

    def extraer_tabla_mediciones(self):
        """Extrae información de la tabla de mediciones inferior"""
        try:
            self.logger.info("\n📋 === EXTRACCIÓN: TABLA DE MEDICIONES ===")
            
            tablas_encontradas = {}
            
            # Buscar DataGrid y Table
            for tipo_tabla in ["DataGrid", "Table"]:
                try:
                    tablas = self.analysis_window.descendants(control_type=tipo_tabla)
                    
                    for i, tabla in enumerate(tablas):
                        try:
                            rect = tabla.rectangle()
                            
                            # Información básica de la tabla
                            tabla_info = {
                                'tipo': tipo_tabla,
                                'posicion': f"L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom}",
                                'control': tabla
                            }
                            
                            # Buscar headers/cabeceras
                            try:
                                headers = tabla.descendants(control_type="Header")
                                if headers:
                                    header_texts = []
                                    for header in headers[:10]:  # Solo primeros 10
                                        texto_header = header.window_text()
                                        if texto_header:
                                            header_texts.append(texto_header)
                                    
                                    tabla_info['cabeceras'] = header_texts
                                    self.logger.info(f"✅ TABLA {tipo_tabla}[{i}] - CABECERAS:")
                                    for header in header_texts:
                                        self.logger.info(f"   📋 {header}")
                                else:
                                    tabla_info['cabeceras'] = []
                                    
                            except Exception as e:
                                tabla_info['cabeceras'] = []
                                self.logger.debug(f"Error obteniendo headers: {e}")
                            
                            # Contar elementos
                            try:
                                filas = tabla.descendants(control_type="DataItem")
                                celdas = tabla.descendants(control_type="Custom")
                                
                                tabla_info['total_filas'] = len(filas)
                                tabla_info['total_celdas'] = len(celdas)
                                
                                self.logger.info(f"📊 ESTADÍSTICAS TABLA:")
                                self.logger.info(f"   🔢 Total filas: {len(filas)}")
                                self.logger.info(f"   📦 Total celdas: {len(celdas)}")
                                
                            except Exception as e:
                                tabla_info['total_filas'] = 0
                                tabla_info['total_celdas'] = 0
                                self.logger.debug(f"Error contando elementos: {e}")
                            
                            # Extraer primera fila de datos (si existe)
                            try:
                                primera_fila = []
                                filas = tabla.descendants(control_type="DataItem")
                                if filas:
                                    primera_fila_celdas = filas[0].descendants(control_type="Custom")
                                    for celda in primera_fila_celdas[:5]:  # Solo primeras 5 celdas
                                        texto_celda = celda.window_text()
                                        if texto_celda:
                                            primera_fila.append(texto_celda)
                                
                                tabla_info['primera_fila'] = primera_fila
                                
                                if primera_fila:
                                    self.logger.info(f"📋 PRIMERA FILA DATOS:")
                                    for j, celda in enumerate(primera_fila):
                                        self.logger.info(f"   [{j}] {celda}")
                                        
                            except Exception as e:
                                tabla_info['primera_fila'] = []
                                self.logger.debug(f"Error extrayendo primera fila: {e}")
                            
                            tablas_encontradas[f"{tipo_tabla}_{i}"] = tabla_info
                            self.logger.info(f"   Posición: {tabla_info['posicion']}")
                            
                        except Exception as e:
                            self.logger.debug(f"Error procesando tabla {tipo_tabla}[{i}]: {e}")
                            
                except Exception as e:
                    self.logger.debug(f"Tipo {tipo_tabla} no disponible: {e}")
            
            self.logger.info(f"📊 RESUMEN TABLAS: {len(tablas_encontradas)} encontradas")
            return tablas_encontradas
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo tablas: {e}")
            return {}

    def ejecutar_extraccion_completa(self):
        """Ejecuta la extracción completa de todos los componentes específicos"""
        try:
            self.logger.info("🎯 === INICIANDO EXTRACCIÓN COMPLETA OPTIMIZADA ===")
            
            if not self.conectar_ventana_analisis():
                return False
            
            # Extraer cada componente específico
            resultados = {}
            
            resultados['navegacion'] = self.extraer_navegacion_lateral()
            resultados['mostrar_datos'] = self.extraer_mostrar_datos()
            resultados['informes_graficos'] = self.extraer_informes_graficos()
            resultados['tabla_mediciones'] = self.extraer_tabla_mediciones()
            
            # Resumen final
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 === RESUMEN FINAL DE EXTRACCIÓN ===")
            self.logger.info(f"🧭 Navegación: {len(resultados['navegacion'])} elementos")
            self.logger.info(f"📊 Mostrar datos: {len(resultados['mostrar_datos'])} checkboxes")
            self.logger.info(f"📈 Informes: {len(resultados['informes_graficos'])} componentes")
            self.logger.info(f"📋 Tablas: {len(resultados['tabla_mediciones'])} tablas")
            self.logger.info("="*80)
            
            self.logger.info(f"✅ Extracción completada. Resultados en: {self.log_filename}")
            return resultados
            
        except Exception as e:
            self.logger.error(f"❌ Error en extracción completa: {e}")
            return None
        finally:
            # No cerrar la aplicación para permitir revisión manual
            pass

def main():
    # Configuración
    archivo_pqm = "/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm/9. Catiglata T 1225 C 0100234196.pqm702"
    
    # Crear y ejecutar extractor
    extractor = SonelComponentExtractor(archivo_pqm)
    resultados = extractor.ejecutar_extraccion_completa()
    
    if resultados:
        print(f"\n✅ Extracción completada exitosamente")
        print(f"📄 Detalles en: {extractor.log_filename}")
        
        # Mostrar resumen en consola
        print("\n🎯 === RESUMEN RÁPIDO ===")
        for categoria, datos in resultados.items():
            print(f"{categoria.upper()}: {len(datos)} elementos encontrados")
    else:
        print(f"\n❌ Extracción falló")
        print(f"📄 Revisa errores en: {extractor.log_filename}")

if __name__ == "__main__":
    main()
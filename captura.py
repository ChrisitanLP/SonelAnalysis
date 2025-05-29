import time
import logging
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import pyautogui
import os
from datetime import datetime
import threading
import sys

class SonelTreeExtractor:
    def __init__(self, archivo_pqm, ruta_exe="D:/Wolfly/Sonel/SonelAnalysis.exe"):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.app = None
        self.main_window = None
        self.analysis_window = None  # La ventana secundaria específica
        
        # Configurar logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"sonel_tree_analysis_{timestamp}.txt"
        
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
        self.logger.info("🌳 EXTRACTOR OPTIMIZADO - ÁRBOL DE CONFIGURACIÓN SONEL")
        self.logger.info(f"📁 Archivo PQM: {archivo_pqm}")
        self.logger.info("="*80)

    def conectar_ventana_analisis_secundaria(self):
        """Conecta específicamente con la ventana secundaria de análisis"""
        try:
            self.logger.info("🔍 Conectando con ventana de análisis secundaria...")
            
            # Conectar con aplicación existente o iniciar nueva
            try:
                self.app = Application(backend="uia").connect(title_re=".*Sonel.*|.*Analysis.*")
                self.logger.info("✅ Conectado con aplicación existente")
            except:
                self.logger.info("🚀 Iniciando nueva instancia de Sonel Analysis...")
                self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                time.sleep(10)  # Esperar carga completa
            
            # Obtener ventana principal
            self.main_window = self.app.top_window()
            self.main_window.set_focus()
            self.logger.info(f"🏠 Ventana principal: {self.main_window.window_text()}")
            
            # Buscar la ventana secundaria específica con "Análisis"
            self.analysis_window = self._encontrar_ventana_analisis_secundaria()
            
            if self.analysis_window:
                self.logger.info(f"✅ Ventana de análisis secundaria encontrada!")
                self.logger.info(f"📋 Título: {self.analysis_window.window_text()}")
                self.logger.info(f"📐 Posición: {self.analysis_window.rectangle()}")
                
                # Enfocar la ventana secundaria
                self.analysis_window.set_focus()
                return True
            else:
                self.logger.error("❌ No se encontró ventana de análisis secundaria")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando con ventana secundaria: {e}")
            return False

    def _encontrar_ventana_analisis_secundaria(self):
        """Encuentra la ventana secundaria específica que contiene 'Análisis'"""
        try:
            self.logger.info("🔍 Buscando ventana secundaria con 'Análisis'...")
            
            # Método 1: Buscar directamente por título con regex
            try:
                ventana_analisis = self.app.window(title_re=".*Análisis.*")
                if ventana_analisis.exists():
                    self.logger.info("✅ Método 1 exitoso: Encontrada por title_re")
                    return ventana_analisis
            except Exception as e:
                self.logger.debug(f"Método 1 falló: {e}")
            
            # Método 2: Buscar en descendientes de la ventana principal
            try:
                descendants = self.main_window.descendants(control_type="Window")
                for i, desc in enumerate(descendants):
                    title = desc.window_text()
                    if "Análisis" in title and ".pqm" in title:
                        self.logger.info(f"✅ Método 2 exitoso: Encontrada en descendiente {i}")
                        self.logger.info(f"   📋 Título completo: {title}")
                        return desc
            except Exception as e:
                self.logger.debug(f"Método 2 falló: {e}")
            
            # Método 3: Listar todas las ventanas y buscar
            try:
                windows = self.app.windows()
                for i, window in enumerate(windows):
                    title = window.window_text()
                    if "Análisis" in title:
                        self.logger.info(f"✅ Método 3 exitoso: Encontrada en ventana {i}")
                        self.logger.info(f"   📋 Título completo: {title}")
                        return window
            except Exception as e:
                self.logger.debug(f"Método 3 falló: {e}")
            
            return None

        except Exception as e:
            self.logger.error(f"Error buscando ventana secundaria: {e}")
            return None

    def extraer_arbol_configuracion(self):
        """Extrae información específica del árbol de configuración lateral izquierdo"""
        try:
            self.logger.info("\n🌳 === EXTRACCIÓN: ÁRBOL DE CONFIGURACIÓN ===")
            
            if not self.analysis_window:
                self.logger.error("❌ No hay ventana de análisis disponible")
                return {}
            
            arboles_encontrados = {}
            
            # Método 1: Buscar Tree directamente
            self.logger.info("🔍 Método 1: Buscando control Tree...")
            try:
                trees = self.analysis_window.descendants(control_type="Tree")
                for i, tree in enumerate(trees):
                    self.logger.info(f"🌳 Árbol {i} encontrado:")
                    detalles = self._analizar_arbol_detallado(tree, i)
                    if detalles:
                        arboles_encontrados[f"Tree_{i}"] = detalles
            except Exception as e:
                self.logger.debug(f"Error buscando Tree: {e}")
            
            # Método 2: Buscar TreeView (SysTreeView32)
            self.logger.info("🔍 Método 2: Buscando TreeView...")
            try:
                # Usar child_window para TreeView
                tree_view = self.analysis_window.child_window(class_name="SysTreeView32")
                if tree_view.exists():
                    self.logger.info("🌳 TreeView encontrado por class_name")
                    detalles = self._analizar_arbol_detallado(tree_view, "TreeView")
                    if detalles:
                        arboles_encontrados["TreeView_SysTreeView32"] = detalles
            except Exception as e:
                self.logger.debug(f"Error buscando TreeView: {e}")
            
            # Método 3: Buscar por control_type="TreeView"
            self.logger.info("🔍 Método 3: Buscando por control_type TreeView...")
            try:
                treeviews = self.analysis_window.descendants(control_type="TreeView")
                for i, tv in enumerate(treeviews):
                    self.logger.info(f"🌳 TreeView {i} encontrado por control_type:")
                    detalles = self._analizar_arbol_detallado(tv, f"TreeView_{i}")
                    if detalles:
                        arboles_encontrados[f"TreeView_ControlType_{i}"] = detalles
            except Exception as e:
                self.logger.debug(f"Error buscando TreeView por control_type: {e}")
            
            # Método 4: Buscar TreeItem directamente (nodos sueltos)
            self.logger.info("🔍 Método 4: Buscando TreeItems sueltos...")
            try:
                tree_items = self.analysis_window.descendants(control_type="TreeItem")
                if tree_items:
                    self.logger.info(f"📋 {len(tree_items)} TreeItems encontrados:")
                    items_info = self._analizar_tree_items(tree_items)
                    if items_info:
                        arboles_encontrados["TreeItems_Sueltos"] = items_info
            except Exception as e:
                self.logger.debug(f"Error buscando TreeItems: {e}")
            
            # Método 5: Imprimir identificadores si no se encuentra nada
            if not arboles_encontrados:
                self.logger.info("⚠️ No se encontraron árboles. Imprimiendo identificadores de control...")
                try:
                    self.analysis_window.print_control_identifiers(depth=3)
                except Exception as e:
                    self.logger.debug(f"Error imprimiendo identificadores: {e}")
            
            self.logger.info(f"📊 RESUMEN ÁRBOLES: {len(arboles_encontrados)} encontrados")
            return arboles_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo árbol de configuración: {e}")
            return {}

    def _analizar_arbol_detallado(self, tree_control, indice):
        """Analiza un control de árbol en detalle"""
        try:
            self.logger.info("="*60)
            self.logger.info(f"🌳 ANÁLISIS DETALLADO DEL ÁRBOL [{indice}]")
            
            # Información básica del control
            texto = tree_control.window_text()
            try:
                auto_id = tree_control.automation_id
            except:
                auto_id = "No disponible"
            
            try:
                class_name = tree_control.class_name
            except:
                class_name = "No disponible"
            
            rect = tree_control.rectangle()
            
            detalles = {
                'indice': indice,
                'texto': texto,
                'auto_id': auto_id,
                'class_name': class_name,
                'control_type': str(tree_control.element_info.control_type),
                'rectangle': f"(L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})",
                'posicion': f"Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}",
                'nodos': []
            }
            
            self.logger.info(f"📋 TEXTO: {texto}")
            self.logger.info(f"🔢 AUTO_ID: {auto_id}")
            self.logger.info(f"📝 CLASS_NAME: {class_name}")
            self.logger.info(f"📐 RECTANGLE: {detalles['rectangle']}")
            
            # Buscar nodos TreeItem dentro del árbol
            try:
                tree_items = tree_control.descendants(control_type="TreeItem")
                self.logger.info(f"🌿 {len(tree_items)} nodos encontrados:")
                
                for i, item in enumerate(tree_items[:10]):  # Limitar a 10 para evitar spam
                    try:
                        item_text = item.window_text()
                        item_rect = item.rectangle()
                        
                        # Verificar si es un nodo de configuración
                        es_configuracion = "Configuración" in item_text
                        
                        nodo_info = {
                            'indice': i,
                            'texto': item_text,
                            'es_configuracion': es_configuracion,
                            'rectangle': f"(L{item_rect.left}, T{item_rect.top}, R{item_rect.right}, B{item_rect.bottom})"
                        }
                        
                        detalles['nodos'].append(nodo_info)
                        
                        # Log detallado para nodos de configuración
                        if es_configuracion:
                            self.logger.info(f"   ⭐ [{i}] CONFIGURACIÓN: {item_text}")
                            self.logger.info(f"       📐 Pos: {nodo_info['rectangle']}")
                        else:
                            self.logger.info(f"   🌿 [{i}] {item_text}")
                        
                    except Exception as e:
                        self.logger.debug(f"Error procesando nodo {i}: {e}")
                
                # Buscar específicamente "Configuración 1"
                config1_encontrado = any("Configuración 1" in nodo['texto'] for nodo in detalles['nodos'])
                detalles['tiene_configuracion_1'] = config1_encontrado
                
                if config1_encontrado:
                    self.logger.info("🎯 ¡ENCONTRADO 'Configuración 1'!")
                
            except Exception as e:
                self.logger.debug(f"Error analizando nodos del árbol: {e}")
                detalles['nodos'] = []
            
            self.logger.info("="*60)
            return detalles
            
        except Exception as e:
            self.logger.error(f"Error en análisis detallado del árbol: {e}")
            return None

    def _analizar_tree_items(self, tree_items):
        """Analiza TreeItems encontrados de forma suelta"""
        try:
            items_info = {
                'total_items': len(tree_items),
                'items_configuracion': [],
                'otros_items': []
            }
            
            for i, item in enumerate(tree_items[:20]):  # Limitar para evitar spam
                try:
                    texto = item.window_text()
                    rect = item.rectangle()
                    
                    item_data = {
                        'indice': i,
                        'texto': texto,
                        'rectangle': f"(L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})"
                    }
                    
                    if "Configuración" in texto:
                        items_info['items_configuracion'].append(item_data)
                        self.logger.info(f"   ⭐ ConfigItem[{i}]: {texto}")
                    else:
                        items_info['otros_items'].append(item_data)
                        self.logger.info(f"   🌿 Item[{i}]: {texto}")
                        
                except Exception as e:
                    self.logger.debug(f"Error procesando TreeItem {i}: {e}")
            
            return items_info
            
        except Exception as e:
            self.logger.error(f"Error analizando TreeItems: {e}")
            return None

    def acceder_configuracion_1(self):
        """Intenta acceder específicamente al nodo 'Configuración 1'"""
        try:
            self.logger.info("\n🎯 === ACCESO ESPECÍFICO A 'CONFIGURACIÓN 1' ===")
            
            if not self.analysis_window:
                self.logger.error("❌ No hay ventana de análisis disponible")
                return False
            
            # Método 1: Buscar TreeItem con texto exacto
            try:
                config1_item = self.analysis_window.child_window(title="Configuración 1", control_type="TreeItem")
                if config1_item.exists():
                    self.logger.info("✅ Método 1: Encontrado por título exacto")
                    config1_item.click_input()
                    time.sleep(1)
                    self.logger.info("🖱️ Click realizado en 'Configuración 1'")
                    return True
            except Exception as e:
                self.logger.debug(f"Método 1 falló: {e}")
            
            # Método 2: Buscar en todos los TreeItems
            try:
                tree_items = self.analysis_window.descendants(control_type="TreeItem")
                for i, item in enumerate(tree_items):
                    texto = item.window_text()
                    if "Configuración 1" in texto:
                        self.logger.info(f"✅ Método 2: Encontrado en TreeItem {i}")
                        item.click_input()
                        time.sleep(1)
                        self.logger.info("🖱️ Click realizado en 'Configuración 1'")
                        return True
            except Exception as e:
                self.logger.debug(f"Método 2 falló: {e}")
            
            # Método 3: Usar coordenadas si se conoce la posición
            self.logger.info("⚠️ Métodos directos fallaron, intentando por coordenadas...")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error accediendo a 'Configuración 1': {e}")
            return False

    def ejecutar_analisis_completo(self):
        """Ejecuta el análisis completo del árbol de configuración"""
        try:
            self.logger.info("🎯 === INICIANDO ANÁLISIS COMPLETO DEL ÁRBOL ===")
            
            # 1. Conectar con ventana secundaria
            if not self.conectar_ventana_analisis_secundaria():
                return False
            
            # 2. Extraer información del árbol
            resultados_arbol = self.extraer_arbol_configuracion()
            
            # 3. Intentar acceder a 'Configuración 1'
            acceso_config1 = self.acceder_configuracion_1()
            
            # Resumen final
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 === RESUMEN ANÁLISIS COMPLETO ===")
            self.logger.info(f"🌳 Árboles encontrados: {len(resultados_arbol)}")
            self.logger.info(f"🎯 Acceso a 'Configuración 1': {'✅ Exitoso' if acceso_config1 else '❌ Falló'}")
            
            # Mostrar nodos de configuración encontrados
            config_nodes = 0
            for arbol_key, arbol_data in resultados_arbol.items():
                if isinstance(arbol_data, dict) and 'nodos' in arbol_data:
                    config_nodes += len([n for n in arbol_data['nodos'] if n.get('es_configuracion', False)])
            
            self.logger.info(f"⭐ Nodos de configuración: {config_nodes}")
            self.logger.info("="*80)
            
            self.logger.info(f"✅ Análisis completado. Detalles en: {self.log_filename}")
            
            return {
                'arboles': resultados_arbol,
                'acceso_configuracion_1': acceso_config1,
                'ventana_analisis': self.analysis_window is not None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error en análisis completo: {e}")
            return None
        finally:
            # No cerrar para permitir inspección manual
            pass

def main():
    # Configuración
    archivo_pqm = "/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm/9. Catiglata T 1225 C 0100234196.pqm702"
    
    # Crear y ejecutar extractor optimizado
    extractor = SonelTreeExtractor(archivo_pqm)
    resultados = extractor.ejecutar_analisis_completo()
    
    if resultados:
        print(f"\n✅ Análisis completado exitosamente")
        print(f"📄 Detalles completos en: {extractor.log_filename}")
        
        # Mostrar resumen en consola
        print("\n🎯 === RESUMEN RÁPIDO ===")
        print(f"🌳 Árboles encontrados: {len(resultados['arboles'])}")
        print(f"🎯 Ventana de análisis: {'✅' if resultados['ventana_analisis'] else '❌'}")
        print(f"⭐ Acceso a Configuración 1: {'✅' if resultados['acceso_configuracion_1'] else '❌'}")
        
        # Listar árboles encontrados
        if resultados['arboles']:
            print("\n📋 Árboles detectados:")
            for key, data in resultados['arboles'].items():
                if isinstance(data, dict):
                    nodos = len(data.get('nodos', []))
                    print(f"   • {key}: {nodos} nodos")
    else:
        print(f"\n❌ Análisis falló")
        print(f"📄 Revisa errores en: {extractor.log_filename}")

if __name__ == "__main__":
    main()
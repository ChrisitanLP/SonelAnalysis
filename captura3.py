import time
import logging
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import pyautogui

class MenuContextualDetector:
    def __init__(self, extractor_instance):
        """
        Inicializa el detector usando la instancia del extractor principal
        """
        self.extractor = extractor_instance
        self.logger = extractor_instance.logger
        self.analysis_window = extractor_instance.analysis_window
        self.app = extractor_instance.app
        
        # Coordenadas conocidas
        self.coordenadas = {
            'informes': (189, 365),
            'exportar_csv': (191, 426)
        }

    def detectar_ventanas_antes_click(self):
        """Captura el estado de ventanas antes del clic"""
        try:
            ventanas_antes = []
            
            # Método 1: Ventanas de la aplicación actual
            try:
                app_windows = self.app.windows()
                for window in app_windows:
                    ventanas_antes.append({
                        'title': window.window_text(),
                        'class': window.class_name(),
                        'handle': window.handle,
                        'rect': window.rectangle()
                    })
            except Exception as e:
                self.logger.debug(f"Error obteniendo ventanas de app: {e}")
            
            # Método 2: Todas las ventanas del sistema relacionadas
            try:
                all_windows = Application(backend="uia").windows()
                for window in all_windows:
                    title = window.window_text()
                    # Filtrar ventanas relacionadas con Sonel
                    if any(keyword in title.lower() for keyword in ['sonel', 'análisis', 'analysis', 'pqm']) or not title:
                        ventanas_antes.append({
                            'title': title,
                            'class': window.class_name(),
                            'handle': window.handle,
                            'rect': window.rectangle()
                        })
            except Exception as e:
                self.logger.debug(f"Error obteniendo todas las ventanas: {e}")
            
            return ventanas_antes
            
        except Exception as e:
            self.logger.error(f"Error detectando ventanas antes: {e}")
            return []

    def detectar_ventanas_nuevas(self, ventanas_antes):
        """Detecta ventanas que aparecieron después del clic"""
        try:
            time.sleep(0.5)  # Esperar a que aparezca el menú
            ventanas_nuevas = []
            
            # Obtener ventanas actuales
            try:
                current_windows = Application(backend="uia").windows()
                handles_antes = [v['handle'] for v in ventanas_antes]
                
                for window in current_windows:
                    if window.handle not in handles_antes:
                        ventanas_nuevas.append(window)
                        
            except Exception as e:
                self.logger.debug(f"Error comparando ventanas: {e}")
            
            return ventanas_nuevas
            
        except Exception as e:
            self.logger.error(f"Error detectando ventanas nuevas: {e}")
            return []

    def buscar_menu_por_coordenadas(self, coordenada_objetivo):
        """Busca controles cerca de las coordenadas específicas"""
        try:
            controles_candidatos = []
            
            # Buscar en todas las ventanas disponibles
            try:
                all_windows = Application(backend="uia").windows()
                
                for window in all_windows:
                    try:
                        # Buscar en todos los descendientes
                        descendants = window.descendants()
                        
                        for control in descendants:
                            try:
                                rect = control.rectangle()
                                texto = control.window_text().strip()
                                
                                # Verificar proximidad a coordenadas objetivo
                                distancia_x = abs(rect.left - coordenada_objetivo[0])
                                distancia_y = abs(rect.top - coordenada_objetivo[1])
                                
                                # Si está cerca (tolerancia de 50 píxeles)
                                if distancia_x <= 50 and distancia_y <= 50:
                                    controles_candidatos.append({
                                        'control': control,
                                        'texto': texto,
                                        'rect': rect,
                                        'distancia': (distancia_x, distancia_y),
                                        'control_type': control.element_info.control_type,
                                        'window_parent': window.window_text()
                                    })
                                    
                                # También buscar si contiene "CSV" o "Informe"
                                if texto and ("CSV" in texto.upper() or "INFORME" in texto.upper()):
                                    controles_candidatos.append({
                                        'control': control,
                                        'texto': texto,
                                        'rect': rect,
                                        'distancia': (distancia_x, distancia_y),
                                        'control_type': control.element_info.control_type,
                                        'window_parent': window.window_text(),
                                        'encontrado_por': 'contenido_texto'
                                    })
                                    
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error buscando por coordenadas: {e}")
            
            return controles_candidatos
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda por coordenadas: {e}")
            return []

    def buscar_menu_por_tipo_popup(self):
        """Busca menús tipo popup o ventanas temporales"""
        try:
            menus_encontrados = []
            
            # Tipos de control que suelen ser menús contextuales
            tipos_menu = ["Menu", "MenuItem", "Popup", "Window", "Pane"]
            
            try:
                all_windows = Application(backend="uia").windows()
                
                for window in all_windows:
                    try:
                        window_title = window.window_text()
                        window_class = window.class_name()
                        
                        # Buscar ventanas que podrían ser menús
                        if (not window_title or 
                            "popup" in window_class.lower() or 
                            "menu" in window_class.lower() or
                            "dropdown" in window_class.lower()):
                            
                            # Buscar controles dentro de estas ventanas
                            descendants = window.descendants()
                            
                            for control in descendants:
                                try:
                                    texto = control.window_text().strip()
                                    control_type = str(control.element_info.control_type)
                                    
                                    if texto and ("CSV" in texto.upper() or "INFORME" in texto.upper()):
                                        menus_encontrados.append({
                                            'control': control,
                                            'texto': texto,
                                            'control_type': control_type,
                                            'rect': control.rectangle(),
                                            'window_parent': window_title,
                                            'window_class': window_class,
                                            'metodo': 'busqueda_popup'
                                        })
                                        
                                except Exception as e:
                                    continue
                                    
                    except Exception as e:
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error buscando popup: {e}")
            
            return menus_encontrados
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda popup: {e}")
            return []

    def detectar_informe_csv_completo(self):
        """Método principal que combina todas las estrategias de detección"""
        try:
            self.logger.info("\n🎯 === DETECCIÓN AVANZADA: INFORME CSV ===")
            
            # 1. Buscar y hacer clic en botón "Informes"
            button_informes = None
            buttons = self.analysis_window.descendants(control_type="Button")
            
            for button in buttons:
                texto_button = button.window_text().strip()
                if "Informe" in texto_button or "Informes" in texto_button:
                    button_informes = button
                    self.logger.info(f"✅ Botón 'Informes' encontrado: {texto_button}")
                    break
            
            if not button_informes:
                self.logger.error("❌ No se encontró botón 'Informes'")
                return {}
            
            # 2. Capturar estado antes del clic
            self.logger.info("📸 Capturando estado antes del clic...")
            ventanas_antes = self.detectar_ventanas_antes_click()
            
            # 3. Hacer clic en el botón
            self.logger.info("🖱️ Haciendo clic en 'Informes'...")
            button_informes.click_input()
            time.sleep(1)  # Esperar a que aparezca el menú
            
            resultados_deteccion = {}
            
            # 4. Estrategia 1: Detectar ventanas nuevas
            self.logger.info("🔍 Estrategia 1: Detectando ventanas nuevas...")
            ventanas_nuevas = self.detectar_ventanas_nuevas(ventanas_antes)
            
            if ventanas_nuevas:
                self.logger.info(f"✅ {len(ventanas_nuevas)} ventanas nuevas detectadas")
                
                for i, window in enumerate(ventanas_nuevas):
                    try:
                        descendants = window.descendants()
                        for j, control in enumerate(descendants):
                            texto = control.window_text().strip()
                            if "CSV" in texto.upper() or "INFORME" in texto.upper():
                                detalles = self.extractor._log_control_details(control, f"nueva_{i}_{j}", "VentanaNueva")
                                resultados_deteccion[f"VentanaNueva_{i}_{j}"] = detalles
                                
                    except Exception as e:
                        self.logger.debug(f"Error procesando ventana nueva: {e}")
            
            # 5. Estrategia 2: Búsqueda por coordenadas
            self.logger.info("🎯 Estrategia 2: Búsqueda por coordenadas...")
            candidatos_coordenadas = self.buscar_menu_por_coordenadas(self.coordenadas['exportar_csv'])
            
            if candidatos_coordenadas:
                self.logger.info(f"✅ {len(candidatos_coordenadas)} candidatos por coordenadas")
                
                for i, candidato in enumerate(candidatos_coordenadas):
                    try:
                        detalles = self.extractor._log_control_details(candidato['control'], f"coord_{i}", "PorCoordenadas")
                        if detalles:
                            detalles['distancia_objetivo'] = candidato['distancia']
                            detalles['metodo_deteccion'] = 'coordenadas'
                            detalles['window_parent'] = candidato['window_parent']
                            resultados_deteccion[f"PorCoordenadas_{i}"] = detalles
                            
                    except Exception as e:
                        self.logger.debug(f"Error procesando candidato coordenadas: {e}")
            
            # 6. Estrategia 3: Búsqueda por tipo popup
            self.logger.info("📋 Estrategia 3: Búsqueda por tipo popup...")
            menus_popup = self.buscar_menu_por_tipo_popup()
            
            if menus_popup:
                self.logger.info(f"✅ {len(menus_popup)} menús popup encontrados")
                
                for i, menu in enumerate(menus_popup):
                    try:
                        detalles = self.extractor._log_control_details(menu['control'], f"popup_{i}", "MenuPopup")
                        if detalles:
                            detalles['metodo_deteccion'] = 'popup'
                            detalles['window_parent'] = menu['window_parent']
                            detalles['window_class'] = menu['window_class']
                            resultados_deteccion[f"MenuPopup_{i}"] = detalles
                            
                    except Exception as e:
                        self.logger.debug(f"Error procesando menú popup: {e}")
            
            # 7. Estrategia 4: Búsqueda exhaustiva en todos los descendants actuales
            self.logger.info("🔍 Estrategia 4: Búsqueda exhaustiva...")
            try:
                # Buscar en la ventana de análisis
                all_descendants = self.analysis_window.descendants()
                
                for i, control in enumerate(all_descendants):
                    try:
                        texto = control.window_text().strip()
                        if texto and ("CSV" in texto.upper() or "INFORME" in texto.upper()):
                            if "Informe CSV" in texto:  # Coincidencia exacta
                                detalles = self.extractor._log_control_details(control, f"exhaustiva_{i}", "BusquedaExhaustiva")
                                if detalles:
                                    detalles['metodo_deteccion'] = 'busqueda_exhaustiva'
                                    detalles['coincidencia'] = 'exacta'
                                    resultados_deteccion[f"BusquedaExhaustiva_{i}"] = detalles
                                    
                    except Exception as e:
                        continue
                        
            except Exception as e:
                self.logger.debug(f"Error en búsqueda exhaustiva: {e}")
            
            # 8. Resumen de resultados
            self.logger.info("\n" + "="*60)
            self.logger.info("📊 RESUMEN DETECCIÓN INFORME CSV")
            self.logger.info(f"🆕 Ventanas nuevas: {len([k for k in resultados_deteccion.keys() if 'VentanaNueva' in k])}")
            self.logger.info(f"🎯 Por coordenadas: {len([k for k in resultados_deteccion.keys() if 'PorCoordenadas' in k])}")
            self.logger.info(f"📋 Menús popup: {len([k for k in resultados_deteccion.keys() if 'MenuPopup' in k])}")
            self.logger.info(f"🔍 Búsqueda exhaustiva: {len([k for k in resultados_deteccion.keys() if 'BusquedaExhaustiva' in k])}")
            self.logger.info(f"📊 TOTAL ENCONTRADO: {len(resultados_deteccion)}")
            self.logger.info("="*60)
            
            # 9. Cerrar menú (hacer clic fuera)
            try:
                pyautogui.click(100, 100)  # Clic fuera del menú para cerrarlo
                time.sleep(0.5)
            except:
                pass
            
            return resultados_deteccion
            
        except Exception as e:
            self.logger.error(f"❌ Error en detección completa: {e}")
            return {}

# Función para integrar con tu extractor existente
def agregar_deteccion_menu_contextual(extractor_instance):
    """
    Agrega la funcionalidad de detección de menús contextuales al extractor existente
    """
    detector = MenuContextualDetector(extractor_instance)
    return detector.detectar_informe_csv_completo()

# Modificación para tu método extraer_informes_graficos existente
def extraer_informes_graficos_mejorado(self):
    """
    Versión mejorada de tu método extraer_informes_graficos que incluye detección de menús contextuales
    """
    try:
        self.logger.info("\n📈 === EXTRACCIÓN: INFORMES Y GRÁFICOS (MEJORADO) ===")
        
        # Tu código existente...
        informes_encontrados = {}
        index = 0
        
        # ... (mantén todo tu código existente hasta antes del resumen final)
        
        # NUEVA FUNCIONALIDAD: Detección de menú contextual
        self.logger.info("\n🎯 === DETECCIÓN AVANZADA DE MENÚ CONTEXTUAL ===")
        
        detector = MenuContextualDetector(self)
        menu_contextual_resultados = detector.detectar_informe_csv_completo()
        
        # Agregar resultados del menú contextual
        for key, value in menu_contextual_resultados.items():
            informes_encontrados[f"MenuContextual_{key}"] = value
        
        # Resumen final mejorado
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 RESUMEN ESPECÍFICO - INFORMES Y GRÁFICOS (MEJORADO)")
        
        combo_informes = len([k for k in informes_encontrados.keys() if "ComboBox" in k])
        button_graficos = len([k for k in informes_encontrados.keys() if "Button" in k])
        menu_contextual = len([k for k in informes_encontrados.keys() if "MenuContextual" in k])
        textos_relacionados = len([k for k in informes_encontrados.keys() if "Text" in k])
        
        self.logger.info(f"🔽 ComboBox 'Informes': {combo_informes} encontrados")
        self.logger.info(f"🔘 Button 'Gráficos': {button_graficos} encontrados")
        self.logger.info(f"🎯 Menú Contextual: {menu_contextual} elementos encontrados")
        self.logger.info(f"📋 Textos relacionados: {textos_relacionados} encontrados")
        self.logger.info(f"📊 TOTAL ELEMENTOS: {len(informes_encontrados)}")
        self.logger.info("="*60)
        
        return informes_encontrados
        
    except Exception as e:
        self.logger.error(f"❌ Error extrayendo informes y gráficos mejorado: {e}")
        return {}
    
# EJEMPLO DE USO DIRECTO (para pruebas rápidas)
def probar_deteccion_menu_contextual():
    """
    Función de prueba para el detector de menús contextuales
    """
    from captura2 import SonelComponentExtractor
    # Usar tu extractor existente
    archivo_pqm = "/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm/9. Catiglata T 1225 C 0100234196.pqm702"
    extractor = SonelComponentExtractor(archivo_pqm)
    
    if extractor.conectar_ventana_analisis():
        # Crear detector y ejecutar
        detector = MenuContextualDetector(extractor)
        resultados = detector.detectar_informe_csv_completo()
        
        print(f"\n🎯 RESULTADOS DE DETECCIÓN DE MENÚ CONTEXTUAL:")
        print(f"📊 Total elementos encontrados: {len(resultados)}")
        
        for key, value in resultados.items():
            print(f"\n--- {key} ---")
            print(f"Texto: {value.get('texto', 'N/A')}")
            print(f"Tipo: {value.get('control_type', 'N/A')}")
            print(f"Posición: {value.get('posicion', 'N/A')}")
            print(f"Método: {value.get('metodo_deteccion', 'N/A')}")
    else:
        print("❌ No se pudo conectar con la ventana de análisis")


if __name__ == "__main__":
    # Ejecutar prueba
    probar_deteccion_menu_contextual()
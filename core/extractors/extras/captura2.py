import re
import time
import logging
import os
import traceback
import pyautogui
import pyperclip
from time import sleep
from datetime import datetime
from pywinauto import Desktop, mouse, findwindows
from pywinauto import Application
from pyautogui import click, moveTo, position
from pywinauto.mouse import move
from pywinauto.keyboard import send_keys
from pynput.mouse import Button, Listener as MouseListener

from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper

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

    def conectar_ventana_analisis(self, modo_configuracion=False):
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
            self.analysis_window = self._encontrar_ventana_analisis(modo_configuracion)
            
            if self.analysis_window:
                self.logger.info(f"✅ Ventana de análisis encontrada: {self.analysis_window}")
                return True
            else:
                self.logger.error("❌ No se encontró ventana de análisis")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando con ventana: {e}")
            return False

    def _encontrar_ventana_analisis(self, modo_configuracion=False):
        """
            Encuentra la ventana específica de análisis.
            
            Si modo_configuracion=True, busca la que termina en 'Configuración 1'.
        """
        try:
            self.main_window.wait("exists enabled visible ready", timeout=10)


            # Buscar ventana que contenga "Análisis" y ".pqm" y termine en "Configuración 1"
            windows = self.main_window.descendants(control_type="Window")
            for window in windows:
                try:
                    title = window.window_text()
                    if "Análisis" in title and ".pqm" in title and title.strip():
                        if not modo_configuracion or title.strip().endswith("Configuración 1"):
                            return window
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo leer una ventana: {e}")
                    continue

            # Fallback: verificar si la ventana principal cumple con el patrón
            main_title = self.main_window.window_text()
            if "Análisis" in main_title and ".pqm" in main_title and main_title.strip():
                if not modo_configuracion or main_title.strip().endswith("Configuración 1"):
                    return self.main_window

            return None

        except Exception as e:
            self.logger.error(f"Error buscando ventana de análisis: {e}")
            return None
        
    def _log_control_details(self, control, index, tipo_esperado=""):
        """Registra los detalles completos de un control en el formato solicitado"""
        try:
            texto = control.window_text()
            auto_id = getattr(control, 'automation_id', '') or ''
            class_name = getattr(control, 'class_name', '') or ''
            control_type = control.element_info.control_type
            rect = control.rectangle()

            # Obtener info del padre inmediato
            parent = None
            try:
                parent = control.parent()
                parent_info = f"{parent.element_info.control_type} - {parent.window_text()}"
            except Exception:
                parent_info = "Desconocido"
            
            self.logger.info("="*50)
            self.logger.info(f"[{index}] === {tipo_esperado} COMPLETO ===")
            self.logger.info(f"Analysis window: {self.analysis_window}")
            self.logger.info(f"TEXTO COMPLETO: {texto}")
            self.logger.info(f"AUTO_ID: {auto_id}")
            self.logger.info(f"CONTROL: {control}")
            self.logger.info(f"CLASS_NAME: {class_name}")
            self.logger.info(f"CONTROL_TYPE: {control_type}")
            self.logger.info(f"RECTANGLE: (L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})")
            self.logger.info(f"POSICIÓN: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
            self.logger.info(f"PADRE: {control.parent()}")
            self.logger.info("="*50)
            
            return {
                'texto': texto,
                'auto_id': auto_id,
                'class_name': class_name,
                'control_type': str(control_type),
                'rectangle': f"(L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})",
                'posicion': f"Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}",
                'control': control,
                'parent_info': parent_info,
            }
            
        except Exception as e:
            self.logger.error(f"Error registrando detalles del control: {e}")
            return None
        
    def extraer_navegacion_configuracion(self):
        """
        Navega al árbol de configuración y expande 'Configuración 1'
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self.logger.info(f"Metodo navegar abol de configuracion: (current_analysis_window) '{self.analysis_window}'")  

            # 2. VERIFICAR QUE LA VENTANA ES VÁLIDA
            try:
                # Test si la ventana responde
                _ = self.analysis_window.window_text()
                self.logger.info("✅ Ventana de análisis válida y accesible")
            except Exception as window_error:
                self.logger.error(f"❌ Ventana de análisis no válida: {window_error}")
                return False
            
            # 3. ESPERAR A QUE LA VENTANA CARGUE COMPLETAMENTE
            max_attempts = 5
            tree_controls = None
            
            for attempt in range(max_attempts):
                try:
                    # Buscar controles TreeItem con manejo de errores específico
                    tree_controls = self.analysis_window.descendants(control_type="TreeItem")
                    
                    if tree_controls:
                        break
                    else:
                        self.logger.warning(f"⚠️ Intento {attempt + 1}: No se encontraron TreeItem")
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)
                            
                except Exception as search_error:
                    self.logger.error(f"❌ Error en intento {attempt + 1} buscando TreeItem: {search_error}")
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
            
            # 4. VALIDAR QUE SE ENCONTRÓ EL TreeItem
            if not tree_controls:
                self.logger.error("❌ No se encontró control TreeItem después de todos los intentos")
                return False
            
            # 5. PROCESAR EL TreeItem directamente si su texto es 'Configuración 1'
            for tree in tree_controls:
                text = tree.window_text()
                if "Configuración 1" in text or "Configuration 1" in text:
                    self.logger.info(f"✅ Usando TreeItem que ya contiene 'Configuración 1': {text}")
                    return self._expand_configuration_item(tree)
            
        except Exception as e:
            self.logger.error(f"❌ Error general en navegación de árbol: {e}")
            # Agregar información de debug adicional
            self.logger.error(f"❌ Tipo de error: {type(e).__name__}")
            self.logger.error(f"❌ Ventana actual: {self.analysis_window}")
            return False
        
    def _expand_configuration_item(self, config_item):
        """
        Expande el elemento de configuración usando múltiples métodos
        
        Args:
            config_item: Elemento TreeItem a expandir
            
        Returns:
            bool: True si se expandió exitosamente
        """
        try:
            # Método: Usar coordenadas directas
            try:
                rect = config_item.rectangle()
                center_x = (rect.left + rect.right) // 2
                center_y = (rect.top + rect.bottom) // 2
                
                # Usar pyautogui o win32gui para click directo
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                self.logger.info(f"🔓 Click directo en coordenadas ({center_x}, {center_y})")
                return True
            except Exception as e:
                self.logger.warning(f"⚠️ Falló click directo: {e}")
            
            self.logger.error("❌ Falló expansión con todos los métodos")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error expandiendo configuración: {e}")
            return False
        
    def extraer_boton_analisis(self):
        """
        Hace clic en el botón 'Análisis de datos'
        
        Returns:
            bool: True si el clic fue exitoso
        """
        try:
            self.logger.info(f"Metodo click analisis buton: (current_analysis_window)'{self.analysis_window}'")  
            
            # Buscar botón "Análisis de datos"
            buttons = self.analysis_window.descendants(control_type="Button", title="Análisis de datos")
            if not buttons:
                # Buscar en inglés
                buttons = self.analysis_window.descendants(control_type="Button", title="Data Analysis")
            
            if buttons:
                analysis_button = buttons[0]
                
                # Hacer clic
                analysis_button.click()
                time.sleep(0.5)
                
                self.logger.info("✅ Clic en 'Análisis de datos' ejecutado")
                return True
            else:
                self.logger.error("❌ Botón 'Análisis de datos' no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en 'Análisis de datos': {e}")
            return False

    def extraer_navegacion_lateral(self):
        """Extrae información específica del elemento 'Mediciones' en la navegación lateral"""
        try:
            self.logger.info("\n🧭 === EXTRACCIÓN: NAVEGACIÓN LATERAL (MEDICIONES) ===")

            mediciones_encontradas = {}
            index = 0

            # Buscar elementos que contengan "Mediciones"
            for tipo_control in ["CheckBox", "Button", "Text", "TreeItem"]:
                try:
                    controles = self.analysis_window.descendants(control_type=tipo_control)

                    for control in controles:
                        texto = control.window_text().strip()

                        if "Mediciones" in texto:
                            detalles = self._log_control_details(control, index, tipo_control)
                            if detalles:
                                mediciones_encontradas[f"Mediciones_{index}"] = detalles
                                index += 1

                            # Si es un CheckBox, hacer clic
                            if tipo_control == "CheckBox":
                                try:
                                    estado = control.get_toggle_state()
                                    if estado != 1:
                                        self.logger.info("☑️ Haciendo clic en el CheckBox 'Mediciones'...")
                                        control.click_input()
                                        time.sleep(0.5)
                                        self.logger.info("✅ CheckBox 'Mediciones' activado")
                                    else:
                                        self.logger.info("🔘 CheckBox 'Mediciones' ya estaba activado")
                                except Exception as e_click:
                                    self.logger.warning(f"⚠️ No se pudo hacer clic en el CheckBox 'Mediciones': {e_click}")

                except Exception as e:
                    self.logger.debug(f"Tipo {tipo_control} no disponible: {e}")

            self.logger.info(f"📊 RESUMEN NAVEGACIÓN: {len(mediciones_encontradas)} elementos 'Mediciones' encontrados")
            return mediciones_encontradas

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo navegación: {e}")
            return {}

    def extraer_mostrar_datos(self):
        """Extrae información específica de la sección central con opciones de filtro"""
        try:
            self.logger.info("\n📊 === EXTRACCIÓN: SECCIÓN CENTRAL - OPCIONES DE FILTRO ===")
            
            elementos_encontrados = {}
            index = 0

            # 1. Buscar Radio Buttons: "Estándar" y "Usuario"
            self.logger.info("\n🔘 Buscando Radio Buttons dentro de 'Mostrar datos'...")
            self.logger.info(f"{self.analysis_window}")
            
            # Buscar el contenedor padre (GroupBox)
            groupboxes = self.analysis_window.children(control_type="Group")

            for groupbox in groupboxes:
                detalles = self._log_control_details(groupbox, index, "GroupBox")
                try:
                    titulo_group = groupbox.window_text().strip()
                    if titulo_group == "Mostrar datos":
                        self.logger.info(f"✅ Encontrado GroupBox: '{titulo_group}'")
                        
                        # Ahora buscar RadioButtons solo dentro de este GroupBox
                        radiobuttons = groupbox.descendants(control_type="RadioButton")
                        
                        for radio in radiobuttons:
                            texto = radio.window_text().strip()
                            if texto in ["Estándar", "Usuario"]:
                                self.logger.info(f"✅ RadioButton encontrado: '{texto}'")
                                
                                # Procesar elemento encontrado
                                try:
                                    estado = radio.get_toggle_state()
                                    elementos_encontrados[f"RadioButton_{texto}"] = {
                                        'texto': texto,
                                        'estado': estado,
                                        'padre': titulo_group
                                    }
                                    
                                    # Seleccionar Usuario si es necesario
                                    if texto == "Usuario" and estado != 1:
                                        radio.select()
                                        time.sleep(0.1)
                                        self.logger.info("✅ RadioButton 'Usuario' seleccionado")
                                    
                                except Exception as e:
                                    self.logger.error(f"❌ Error procesando '{texto}': {e}")
                        
                                index += 1  # Salir del loop una vez encontrado el GroupBox correcto
                        
                except Exception as e:
                    self.logger.error(f"❌ Error con GroupBox: {e}")

            # 2. Buscar CheckBoxes: "Prom.", "Min.", "Instant.", "Máx."
            self.logger.info("\n☑️ Buscando CheckBoxes de medición...")
            checkboxes_medicion = ["Prom.", "Mín.", "Instant.", "Máx."]
            checkboxes = self.analysis_window.descendants(control_type="CheckBox")
            for checkbox in checkboxes:
                texto = checkbox.window_text().strip()
                for medicion in checkboxes_medicion:
                    if medicion in texto or texto == medicion:
                        detalles = self._log_control_details(checkbox, index, "CheckBox")
                        if detalles:
                            # Obtener estado del checkbox
                            try:
                                estado = checkbox.get_toggle_state()
                                detalles['estado'] = estado
                            except:
                                detalles['estado'] = "Desconocido"
                            
                            elementos_encontrados[f"CheckBox_Medicion_{texto}_{index}"] = detalles

                            # Lógica para activar solo "Prom." y desactivar los demás
                            try:
                                if texto == "Prom.":
                                    if estado != 1:
                                        self.logger.info(f"✅ Activando checkbox '{texto}'...")
                                        checkbox.toggle()
                                    else:
                                        self.logger.info(f"✔️ Checkbox '{texto}' ya está activado.")
                                else:
                                    if estado == 1:
                                        self.logger.info(f"🚫 Desactivando checkbox '{texto}'...")
                                        checkbox.toggle()
                                    else:
                                        self.logger.info(f"✔️ Checkbox '{texto}' ya está desactivado.")
                            except Exception as e:
                                self.logger.error(f"❌ Error al cambiar estado del checkbox '{texto}': {e}")

                            index += 1

            self.logger.info(f"📊 RESUMEN FILTROS: {len(elementos_encontrados)} elementos encontrados")
            return elementos_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo opciones de filtro: {e}")
            return {}
        
    # OPCIÓN 2: Agregar como método separado (más seguro)
    def extraer_informes_graficos(self):
        """Extrae información específica de la sección 'Informes y gráficos'"""
        try:
            self.logger.info("\n📈 === EXTRACCIÓN: INFORMES Y GRÁFICOS ===")

            index = 0
            informes_encontrados = self._buscar_informes(index)
            index += len(informes_encontrados)

            # Buscar texto relacionado
            self.logger.info("\n📋 Buscando elementos de texto relacionados...")
            textos = self.analysis_window.descendants(control_type="Text")
            for texto in textos:
                try:
                    texto_content = texto.window_text().strip()
                    if any(k in texto_content for k in ["Informes", "Gráficos", "Informes y gráficos"]):
                        detalles = self._log_control_details(texto, index, "Text")
                        if detalles:
                            detalles['contenido_relevante'] = texto_content
                            informes_encontrados[f"Text_Relacionado_{index}"] = detalles
                            index += 1
                            self.logger.info(f"   📋 TEXTO relacionado: {texto_content}")
                except Exception as e:
                    self.logger.debug(f"Error procesando texto: {e}")

            # Resumen final
            self.logger.info("\n" + "="*60)
            self.logger.info("📊 RESUMEN ESPECÍFICO - INFORMES Y GRÁFICOS")
            combo_informes = len([k for k in informes_encontrados if "ComboBox" in k])
            button_graficos = len([k for k in informes_encontrados if "Button_Graficos" in k])
            textos_relacionados = len([k for k in informes_encontrados if "Text" in k])
            self.logger.info(f"🔽 ComboBox/Button 'Informes': {combo_informes} encontrados")
            self.logger.info(f"🔘 Botones 'Gráficos': {button_graficos} encontrados")
            self.logger.info(f"📋 Textos relacionados: {textos_relacionados}")

            return informes_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo informes y gráficos: {e}")
            return {}
        
    def extraer_configuracion_principal_mediciones(self):
        """
        Busca y desactiva el checkbox 'Seleccionar todo' si está activado,
        y hace clic en el botón 'Expandir todo'.
        """
        try:
            self.logger.info("\n🔧 Buscando 'Seleccionar todo' y 'Expandir todo'...")

            componentes_clave = {
                "Seleccionar todo": {
                    "tipo": "CheckBox",
                    "accion": "desactivar"
                },
                "Expandir todo": {
                    "tipo": "Button",
                    "accion": "click"
                }
            }

            for control in self.analysis_window.descendants():
                texto = control.window_text().strip()
                if texto in componentes_clave:
                    tipo_esperado = componentes_clave[texto]["tipo"]
                    tipo_control = control.friendly_class_name()

                    if tipo_control != tipo_esperado:
                        self.logger.warning(f"⚠️ Tipo inesperado para '{texto}': {tipo_control} (esperado: {tipo_esperado})")
                        continue

                    detalles = self._log_control_details(control, 0, tipo_control)
                    
                    if tipo_control == "CheckBox":
                        try:
                            estado = control.get_toggle_state()
                            detalles["estado_inicial"] = estado

                            if estado == 1:  # Si está activado
                                self.logger.info(f"🔄 Desactivando checkbox '{texto}'...")
                                control.toggle()
                            else:
                                self.logger.info(f"✔️ Checkbox '{texto}' ya está desactivado.")
                        except Exception as e:
                            self.logger.error(f"❌ No se pudo obtener o cambiar el estado de '{texto}': {e}")

                    elif tipo_control == "Button":
                        try:
                            self.logger.info(f"🖱️ Clic en el botón '{texto}'...")
                            control.click_input()
                        except Exception as e:
                            self.logger.error(f"❌ Error al hacer clic en el botón '{texto}': {e}")

        except Exception as e:
            self.logger.error(f"❌ Error general en 'desactivar_seleccionar_todo_y_expandir': {e}")


    def extraer_componentes_arbol_mediciones_(self):
        """Extrae los componentes dentro del árbol de mediciones utilizando distintos métodos: por control, por título/nombre y por contenido.
        También filtra por nombres clave como Tensión, Corriente, Potencia, Energía, etc.
        """
        try:
            self.logger.info("\n🌳 === EXTRACCIÓN DE COMPONENTES DEL ÁRBOL DE MEDICIONES ===")

            arbol_componentes = {}
            index = 0

            # Palabras clave que nos interesan extraer (normalizadas)
            palabras_clave = [
                "tension u", "tension ul-l", "tension u l-l",
                "Potencia P", "potencia q1", "potencia sn", "potencia s",
                "energia p+", "energia p-"
            ]

            def normalizar_texto(texto):
                """Quita etiquetas HTML y símbolos para comparación"""
                texto = re.sub(r"<sub>(.*?)</sub>", r"\1", texto, flags=re.IGNORECASE)
                texto = re.sub(r"[<>_/]", "", texto)  # Elimina restos de etiquetas o subíndices
                return texto.lower().strip()

            def contiene_palabra_clave(texto):
                texto_normalizado = normalizar_texto(texto)
                return any(clave in texto_normalizado for clave in palabras_clave)

            # === FORMA 1: Por control directo (TreeItem) ===
            tree_items = self.analysis_window.descendants(control_type="TreeItem")
            self.logger.info(f"🔍 Forma 1: Detectados {len(tree_items)} TreeItem(s)")
            
            for item in tree_items:
                texto = item.window_text().strip()
                hijos = item.children()
                detalles = self._log_control_details(item, index, "TreeItem")

                if len(hijos) > 0:
                    self.logger.info(f"📁 Nodo raíz detectado: '{texto}' con {len(hijos)} hijos")
                    detalles['tipo'] = "Nodo raíz"
                else:
                    self.logger.info(f"📄 Item hijo: '{texto}'")
                    detalles['tipo'] = "Item hijo"

                if contiene_palabra_clave(texto):
                    detalles['clave_detectada'] = True
                    arbol_componentes[f"Clave_Forma1_{index}"] = detalles
                    self.logger.info(f"✅ Coincidencia clave detectada en Forma 1: '{texto}'")
                else:
                    detalles['clave_detectada'] = False
                    arbol_componentes[f"Forma1_TreeItem_{index}"] = detalles

                index += 1

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo árbol de mediciones: {e}")
            return {}
    

    def extraer_componentes_arbol_mediciones(self):
        """
        Extrae los componentes dentro del árbol de mediciones utilizando scroll inteligente
        y aplica lógica de selección a los elementos que coinciden con palabras clave.
        
        Características:
        - Scroll solo dentro del área del TreeView
        - Detección automática de nuevos elementos
        - Prevención de bucles infinitos
        - Filtrado por palabras clave relevantes
        - Selección automática de elementos relevantes
        - Manejo robusto de errores
        """
        try:
            self.logger.info("\n🌳 === EXTRACCIÓN Y SELECCIÓN DE COMPONENTES DEL ÁRBOL DE MEDICIONES ===")

            arbol_componentes = {}
            index = 0
            elementos_seleccionados = 0
            elementos_no_seleccionables = 0

            # Palabras clave que nos interesan extraer (normalizadas)
            palabras_clave = [
                "tensión u", "tensión ul-l", "tensión u l-l",
                "potencia p", "potencia q1", "potencia sn", "potencia s"
            ]

            def normalizar_texto(texto):
                """Quita etiquetas HTML y símbolos para comparación"""
                texto = re.sub(r"<sub>(.*?)</sub>", r"\1", texto, flags=re.IGNORECASE)
                texto = re.sub(r"[<>_/]", "", texto)  # Elimina restos de etiquetas o subíndices
                return texto.lower().strip()

            def contiene_palabra_clave(texto):
                texto_normalizado = normalizar_texto(texto)
                return any(clave in texto_normalizado for clave in palabras_clave)

            def verificar_y_seleccionar_elemento(item, texto):
                """
                Verifica si el elemento es seleccionable y lo selecciona haciendo clic en el área del checkbox.
                Retorna información sobre el estado de selección.
                """
                nonlocal elementos_seleccionados, elementos_no_seleccionables
                
                try:
                    # Verificar si contiene palabra clave
                    if not contiene_palabra_clave(texto):
                        return {
                            'seleccionado': False,
                            'accion': 'no_es_clave',
                            'es_clave': False
                        }
                    
                    # Es palabra clave, intentar selección
                    try:
                        # Este conjunto guarda los nombres ya seleccionados (puedes moverlo al inicio del proceso)
                        self.seleccionados_previamente = getattr(self, 'seleccionados_previamente', set())

                        # Verificamos si ya fue seleccionado anteriormente
                        if texto in self.seleccionados_previamente:
                            self.logger.info(f"🔁 '{texto}' ya fue seleccionado previamente. Saltando clic.")
                            return {
                                'seleccionado': True,
                                'accion': 'ya_seleccionado',
                                'coordenadas': None,
                                'estado_previo': None,
                                'es_clave': True,
                                'metodo': 'omitido_por_repeticion'
                            }

                        # Obtener las coordenadas del elemento
                        rect = item.rectangle()
                        
                        # Calcular coordenadas del checkbox (área izquierda del TreeItem)
                        # Basándome en tu imagen, el checkbox está en la parte izquierda
                        checkbox_x = rect.left + 15  # Aproximadamente 15 pixels desde el borde izquierdo
                        checkbox_y = rect.top + (rect.height() // 2)  # Centro vertical del elemento
                        
                        self.logger.info(f"📍 Intentando clic en checkbox de '{texto}' en coordenadas ({checkbox_x}, {checkbox_y})")
                        self.logger.info(f"📐 Rectángulo del elemento: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
                        
                        # Verificar estado actual si es posible
                        estado_previo = None
                        try:
                            # Intentar obtener estado de selección de diferentes maneras
                            if hasattr(item, 'is_selected'):
                                estado_previo = item.is_selected()
                            elif hasattr(item, 'get_toggle_state'):
                                estado_previo = item.get_toggle_state() == 1
                            else:
                                # Buscar checkbox hijo
                                checkboxes = item.descendants(control_type="CheckBox")
                                if checkboxes:
                                    checkbox = checkboxes[0]
                                    if hasattr(checkbox, 'get_toggle_state'):
                                        estado_previo = checkbox.get_toggle_state() == 1
                                    elif hasattr(checkbox, 'is_checked'):
                                        estado_previo = checkbox.is_checked()
                        except Exception as e:
                            self.logger.debug(f"🔍 No se pudo determinar estado previo de '{texto}': {e}")
                        
                        # Realizar clic en el área del checkbox
                        try:
                            # Método 1: Clic directo en coordenadas calculadas
                            mouse.click(coords=(checkbox_x, checkbox_y))
                            sleep(0.45)  # Pequeña pausa para que se registre el clic
                            
                            self.logger.info(f"✅ Clic realizado en checkbox de '{texto}'")
                            self.seleccionados_previamente.add(texto)
                            elementos_seleccionados += 1
                            
                            return {
                                'seleccionado': True,
                                'accion': 'click_checkbox',
                                'coordenadas': (checkbox_x, checkbox_y),
                                'estado_previo': estado_previo,
                                'es_clave': True,
                                'metodo': 'click_coordenadas'
                            }
                            
                        except Exception as click_error:
                            self.logger.warning(f"⚠️ Error con clic en coordenadas para '{texto}': {click_error}")
                            
                            # Método 2: Intentar buscar y hacer clic en checkbox hijo
                            try:
                                checkboxes = item.descendants(control_type="CheckBox")
                                if checkboxes:
                                    checkbox = checkboxes[0]
                                    checkbox.click()
                                    sleep(0.45)
                                    
                                    self.logger.info(f"✅ Checkbox hijo clickeado para '{texto}'")
                                    elementos_seleccionados += 1
                                    
                                    return {
                                        'seleccionado': True,
                                        'accion': 'click_checkbox_hijo',
                                        'estado_previo': estado_previo,
                                        'es_clave': True,
                                        'metodo': 'checkbox_descendant'
                                    }
                            except Exception as checkbox_error:
                                self.logger.warning(f"⚠️ Error con checkbox hijo para '{texto}': {checkbox_error}")
                            
                            # Método 3: Clic en el TreeItem completo como fallback
                            try:
                                item.click()
                                sleep(0.45)
                                
                                self.logger.info(f"📄 Clic en TreeItem completo para '{texto}'")
                                elementos_seleccionados += 1
                                
                                return {
                                    'seleccionado': True,
                                    'accion': 'click_treeitem',
                                    'estado_previo': estado_previo,
                                    'es_clave': True,
                                    'metodo': 'treeitem_click'
                                }
                                
                            except Exception as treeitem_error:
                                self.logger.error(f"❌ Todos los métodos de clic fallaron para '{texto}': {treeitem_error}")
                                elementos_no_seleccionables += 1
                                
                                return {
                                    'seleccionado': False,
                                    'accion': 'error_todos_metodos',
                                    'errores': {
                                        'click_coordenadas': str(click_error),
                                        'checkbox_hijo': str(checkbox_error),
                                        'treeitem_click': str(treeitem_error)
                                    },
                                    'es_clave': True
                                }
                    
                    except Exception as e:
                        self.logger.error(f"❌ Error crítico verificando selección de '{texto}': {e}")
                        elementos_no_seleccionables += 1
                        return {
                            'seleccionado': False,
                            'accion': 'error_critico',
                            'error': str(e),
                            'es_clave': True
                        }
                        
                except Exception as e:
                    self.logger.error(f"❌ Error crítico general en verificar_y_seleccionar_elemento: {e}")
                    return {
                        'seleccionado': False,
                        'accion': 'error_critico_general',
                        'error': str(e),
                        'es_clave': contiene_palabra_clave(texto)
                    }
                
            def calcular_area_scroll():
                """Calcula el área de scroll basándose en los elementos TreeItem visibles"""
                try:
                    tree_items = self.analysis_window.descendants(control_type="TreeItem")
                    if not tree_items:
                        return 250, 560  # Valores por defecto del log
                    
                    # Obtener coordenadas de todos los elementos TreeItem
                    min_x = float('inf')
                    max_x = float('-inf')
                    min_y = float('inf')
                    max_y = float('-inf')
                    
                    for item in tree_items:
                        try:
                            rect = item.rectangle()
                            min_x = min(min_x, rect.left)
                            max_x = max(max_x, rect.right)
                            min_y = min(min_y, rect.top)
                            max_y = max(max_y, rect.bottom)
                        except:
                            continue
                    
                    # Calcular centro del área
                    if min_x != float('inf'):
                        x_center = (min_x + max_x) // 2
                        y_center = (min_y + max_y) // 2
                        self.logger.info(f"📐 Área TreeView calculada: X={min_x}-{max_x}, Y={min_y}-{max_y}")
                        self.logger.info(f"🎯 Centro para scroll: ({x_center}, {y_center})")
                        return x_center, y_center
                    else:
                        return 250, 560  # Fallback a valores del log
                except Exception as e:
                    self.logger.warning(f"⚠️ Error calculando área de scroll: {e}. Usando valores por defecto.")
                    return 250, 560

            def realizar_scroll_inteligente(x_scroll, y_scroll, direccion=-3):
                """Realiza scroll en el área específica del TreeView"""
                try:
                    # Mover cursor al área de scroll
                    mouse.move(coords=(x_scroll, y_scroll))
                    sleep(0.1)  # Pequeña pausa para asegurar posicionamiento
                    
                    # Realizar scroll
                    mouse.scroll(coords=(x_scroll, y_scroll), wheel_dist=direccion)
                    sleep(0.5)  # Pausa para que la interfaz se actualice
                    
                    self.logger.info(f"🔄 Scroll realizado en ({x_scroll}, {y_scroll}) con distancia {direccion}")
                    return True
                except Exception as e:
                    self.logger.error(f"❌ Error realizando scroll: {e}")
                    return False

            def obtener_elementos_actuales():
                """Obtiene todos los elementos TreeItem actuales con sus identificadores únicos"""
                elementos_actuales = {}
                try:
                    tree_items = self.analysis_window.descendants(control_type="TreeItem")
                    for item in tree_items:
                        try:
                            texto = item.window_text().strip()
                            key_id = item.element_info.runtime_id
                            rect = item.rectangle()
                            
                            # Crear identificador único combinando runtime_id y posición
                            identificador = f"{tuple(key_id)}_{rect.top}_{rect.left}"
                            
                            elementos_actuales[identificador] = {
                                'item': item,
                                'texto': texto,
                                'rect': rect,
                                'runtime_id': key_id
                            }
                        except:
                            continue
                except Exception as e:
                    self.logger.warning(f"⚠️ Error obteniendo elementos actuales: {e}")
                
                return elementos_actuales

            # === INICIO DEL PROCESO DE EXTRACCIÓN Y SELECCIÓN ===
            
            # Calcular área de scroll
            x_scroll, y_scroll = calcular_area_scroll()
            
            # Control de scroll inteligente
            elementos_vistos = set()
            intentos_sin_cambios = 0
            max_intentos_sin_cambios = 3
            max_scrolls_totales = 3  # Límite máximo de scrolls para evitar bucles infinitos
            scrolls_realizados = 0
            
            self.logger.info(f"🖱️ Iniciando extracción con scroll y selección en área: ({x_scroll}, {y_scroll})")
            
            while intentos_sin_cambios < max_intentos_sin_cambios and scrolls_realizados < max_scrolls_totales:
                
                # Obtener elementos actuales
                elementos_actuales = obtener_elementos_actuales()
                elementos_nuevos = 0
                
                # Procesar elementos
                for identificador, elemento_info in elementos_actuales.items():
                    if identificador in elementos_vistos:
                        continue
                    
                    elementos_vistos.add(identificador)
                    elementos_nuevos += 1
                    
                    item = elemento_info['item']
                    texto = elemento_info['texto']
                    
                    # Log de detalles del control
                    detalles = self._log_control_details(item, index, "TreeItem")
                    
                    # Aplicar lógica de selección
                    resultado_seleccion = verificar_y_seleccionar_elemento(item, texto)
                    detalles.update(resultado_seleccion)
                    
                    # Determinar tipo de elemento
                    try:
                        hijos = item.children()
                        if len(hijos) > 0:
                            self.logger.info(f"📁 Nodo raíz detectado: '{texto}' con {len(hijos)} hijos")
                            detalles['tipo'] = "Nodo raíz"
                            detalles['num_hijos'] = len(hijos)
                        else:
                            self.logger.info(f"📄 Item hijo: '{texto}'")
                            detalles['tipo'] = "Item hijo"
                            detalles['num_hijos'] = 0
                    except:
                        detalles['tipo'] = "Elemento sin hijos detectables"
                        detalles['num_hijos'] = 0
                    
                    # Almacenar elemento con información de selección
                    if detalles.get('es_clave', False):
                        if detalles.get('seleccionado', False):
                            arbol_componentes[f"Seleccionado_Clave_{index}"] = detalles
                            self.logger.info(f"🎯 Elemento seleccionado: '{texto}' - Acción: {detalles.get('accion', 'N/A')}")
                        else:
                            arbol_componentes[f"NoSeleccionado_Clave_{index}"] = detalles
                            self.logger.info(f"⚠️ Elemento clave no seleccionado: '{texto}' - Razón: {detalles.get('accion', 'N/A')}")
                    else:
                        arbol_componentes[f"Normal_TreeItem_{index}"] = detalles
                    
                    index += 1
                
                # Evaluar si hacer scroll
                if elementos_nuevos > 0:
                    self.logger.info(f"🔍 Se detectaron {elementos_nuevos} elementos nuevos")
                    intentos_sin_cambios = 0
                    
                    # Hacer scroll para buscar más elementos
                    if realizar_scroll_inteligente(x_scroll, y_scroll):
                        scrolls_realizados += 1
                        sleep(0.8)  # Pausa para que la interfaz se estabilice
                    else:
                        break
                        
                else:
                    intentos_sin_cambios += 1
                    self.logger.info(f"⏸️ No se detectaron elementos nuevos (intento {intentos_sin_cambios}/{max_intentos_sin_cambios})")
                    
                    if intentos_sin_cambios < max_intentos_sin_cambios:
                        # Intentar scroll adicional por si hay más contenido
                        if realizar_scroll_inteligente(x_scroll, y_scroll):
                            scrolls_realizados += 1
                            sleep(1.0)  # Pausa más larga cuando no hay elementos nuevos
                        else:
                            break
            
            # === FINALIZACIÓN Y RESUMEN ===
            
            razon_finalizacion = ""
            if intentos_sin_cambios >= max_intentos_sin_cambios:
                razon_finalizacion = f"No se detectaron elementos nuevos después de {max_intentos_sin_cambios} intentos"
            elif scrolls_realizados >= max_scrolls_totales:
                razon_finalizacion = f"Se alcanzó el límite máximo de {max_scrolls_totales} scrolls"
            else:
                razon_finalizacion = "Proceso completado exitosamente"
            
            # Estadísticas finales
            elementos_con_clave = sum(1 for comp in arbol_componentes.values() if comp.get('es_clave', False))
            elementos_sin_clave = len(arbol_componentes) - elementos_con_clave
            
            self.logger.info("\n" + "="*60)
            self.logger.info("📊 === RESUMEN DE EXTRACCIÓN Y SELECCIÓN ===")
            self.logger.info(f"✅ Total de elementos extraídos: {len(arbol_componentes)}")
            self.logger.info(f"🎯 Elementos con palabras clave: {elementos_con_clave}")
            self.logger.info(f"📄 Elementos sin palabras clave: {elementos_sin_clave}")
            self.logger.info(f"✔️ Elementos seleccionados exitosamente: {elementos_seleccionados}")
            self.logger.info(f"⚠️ Elementos no seleccionables: {elementos_no_seleccionables}")
            self.logger.info(f"🔄 Scrolls realizados: {scrolls_realizados}")
            self.logger.info(f"🏁 Razón de finalización: {razon_finalizacion}")
            self.logger.info("="*60)
            
            return arbol_componentes

        except Exception as e:
            self.logger.error(f"❌ Error crítico en extracción del árbol de mediciones: {e}")
            self.logger.error(f"📍 Detalles del error: {type(e).__name__}: {str(e)}")
            return {}

    def _buscar_informes(self, index): 
        informes_encontrados = {}

        self.logger.info("\n🔘 Buscando botón 'Informes' y sus opciones...")

        for i, button in enumerate(self.analysis_window.descendants(control_type="Button")):
            try:
                texto = button.window_text().strip()
                if "Informe" in texto:
                    detalles = self._log_control_details(button, index, "Button")
                    if detalles:
                        detalles['metodo_deteccion'] = "Por texto botón"

                        try:
                            button.click_input()
                            time.sleep(1.2)  # Esperar menú emergente

                            x, y = pyautogui.position()
                            move(coords=(x, y + 52))
                            time.sleep(0.5)
                            click(button='left')

                        except Exception as submenu_err:
                            self.logger.warning(f"⚠️  No se pudieron obtener los subelementos del botón 'Informes': {submenu_err}")

                        informes_encontrados[f"Button_Informes_{index}"] = detalles
                        index += 1
            except Exception as e:
                self.logger.debug(f"Error en botón 'Informes': {e}")

        # Fallback: detectar por contenido visible
        buttons = self.analysis_window.descendants(control_type="Button")
        for button in buttons:
            try:
                texto_button = button.window_text().strip()
                if "Informe" in texto_button or "Informes" in texto_button:
                    ya_encontrado = any("Button_Informes" in k for k in informes_encontrados)
                    if not ya_encontrado:
                        detalles = self._log_control_details(button, index, "Button")
                        if detalles:
                            detalles['funcionalidad'] = "Abre vista gráfica del análisis"
                            detalles['metodo_deteccion'] = "Por contenido de texto"
                            detalles['opcion_prioritaria'] = "Informe CSV" if "CSV" in texto_button.upper() else None
                            informes_encontrados[f"Button_Graficos_Contenido_{index}"] = detalles
                            index += 1
                            self.logger.info(f"   ✅ BUTTON encontrado por contenido: {texto_button}")
            except Exception as e:
                self.logger.debug(f"Error procesando botón: {e}")

        return informes_encontrados
    
    def _explorar_controles(self, ventana, nivel=0, max_nivel=2):
        """Explora recursivamente los controles de una ventana hasta cierto nivel de profundidad"""
        if nivel > max_nivel:
            return
        
        try:
            hijos = ventana.children()
            for i, hijo in enumerate(hijos):
                indent = "  " * nivel
                self.logger.info(f"{indent}▶️ Nivel {nivel} - Control {i}")
                self._log_control_details(hijo, index=f"{nivel}.{i}", tipo_esperado=f"Nivel {nivel}")
                
                # Recursivamente explora hijos
                self._explorar_controles(hijo, nivel=nivel+1, max_nivel=max_nivel)
        except Exception as e:
            self.logger.error(f"Error explorando controles en nivel {nivel}: {e}")

    def guardar_archivo_csv(self, nombre_archivo: str):
        """
        Guarda el archivo CSV usando únicamente métodos de pywinauto sin coordenadas ni pyautogui.
        """

        try:
            time.sleep(2)
            print("🔍 Buscando ventana de guardado dentro de Sonel...")

            if not hasattr(self, 'app') or not self.app:
                print("❌ No hay conexión con la aplicación Sonel")
                return False

            guardar_ventana = None

            if hasattr(self, 'main_window'):
                dialogs = self.main_window.descendants(control_type="Window")
                for i, dialog in enumerate(dialogs):
                    try:
                        self._log_control_details(dialog, index=i, tipo_esperado="Dialogo candidato")
                        if dialog.is_visible() and ("Guardar" in dialog.window_text() or dialog.child_window(title="Guardar", control_type="Button").exists()):
                            guardar_ventana = dialog
                            print(f"✅ Diálogo de guardado encontrado: '{dialog.window_text()}'")
                            break
                    except Exception as e:
                        self.logger.warning(f"⚠️ Diálogo no procesado: {e}")

            if not guardar_ventana:
                print("❌ No se encontró ventana de guardado.")
                return False
            
            # Asegurar que la ventana esté en primer plano
            try:
                guardar_ventana.set_focus()
                guardar_ventana.restore()
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ No se pudo enfocar la ventana: {e}")

            # Localizar el campo de texto "Nombre"
            campo_control = None

            for idx, ctrl in enumerate(guardar_ventana.descendants()):
                if isinstance(ctrl, EditWrapper):
                    try:
                        padre = ctrl.parent()
                        if padre and "Imágenes" in padre.window_text():
                            campo_control = ctrl
                            self._log_control_details(ctrl, index=idx, tipo_esperado="Campo Nombre (EditWrapper)")
                            break
                    except Exception as e:
                        self.logger.warning(f"⚠️ No se pudo evaluar padre de componente Edit #{idx}: {e}")

            if not campo_control:
                raise Exception("❌ No se encontró el campo de nombre para guardar el archivo.")

            # Estrategia 1: Método estándar con verificaciones adicionales
            try:
                print("🔄 Intentando estrategia 1: Método estándar...")
                pyperclip.copy(nombre_archivo)

                # Verificar visibilidad antes de proceder
                if not campo_control.is_visible():
                    print("⚠️ Campo no visible, intentando scroll y focus...")
                    try:
                        campo_control.scroll_into_view()
                        time.sleep(0.2)
                    except:
                        pass
                
                # Intentar establecer foco múltiples veces
                for i in range(3):
                    try:
                        campo_control.set_focus()
                        time.sleep(0.2)
                        break
                    except Exception as e:
                        if i == 2:
                            raise e
                        time.sleep(0.3)

                campo_control.click_input(double=True)

                # Limpiar y escribir
                send_keys("^a{DEL}")
                time.sleep(0.2)
                send_keys("^v")
                time.sleep(0.2)

                print(f"📎 Nombre establecido en el campo (Estrategia 1): {nombre_archivo}")
                success = True
                
            except Exception as e:
                print(f"⚠️ Estrategia falló: {e}")

            time.sleep(0.5)

            # Localizar el botón "Guardar"
            boton_guardar_control = None
            
            try:
                for idx, ctrl in enumerate(guardar_ventana.descendants(control_type="Button")):
                    if isinstance(ctrl, ButtonWrapper) and ctrl.window_text() and ctrl.window_text().strip().lower() == "guardar":
                        boton_guardar_control = ctrl
                        self._log_control_details(ctrl, index=idx, tipo_esperado="Botón Guardar (Descendants)")
                        break
            except Exception as e:
                print(f"⚠️ Fallo al buscar 'Guardar': {e}")

            if not boton_guardar_control:
                raise Exception("❌ No se encontró el botón 'Guardar'.")

            # Hacer clic en el botón Guardar
            try:
                boton_guardar_control.set_focus()
                time.sleep(0.2)
                boton_guardar_control.invoke()  # Alternativa: click() o click_input()
                print("💾 Archivo guardado correctamente usando pywinauto.")
                return True
            except Exception as e:
                print(f"❌ Error al hacer clic en Guardar: {e}")
                traceback.print_exc()
                return False

        except Exception as e:
            print(f"❌ Error en guardar_archivo_csv: {e}")
            return False

    def extraer_tabla_mediciones(self):
        """Extrae información de la tabla de mediciones inferior"""
        try:
            self.logger.info("\n📋 === EXTRACCIÓN: TABLA DE MEDICIONES ===")

            tablas_encontradas = {}
            index = 0

            # Buscar tipos de controles que podrían contener tablas
            tipos_posibles = ["DataGrid", "Table"]

            for tipo_tabla in tipos_posibles:
                try:
                    tablas = self.analysis_window.descendants(control_type=tipo_tabla)

                    for tabla in tablas:
                        try:
                            detalles = self._log_control_details(tabla, index, tipo_tabla)

                            # Mover mouse y hacer clic en esquina superior izquierda del rectángulo con offset +3 en X
                            rect = tabla.rectangle()
                            x = rect.left + 3
                            y = rect.top
                            self.logger.info(f"🖱️ Moviendo mouse a ({x}, {y}) y haciendo clic...")
                            moveTo(x, y, duration=0.3)
                            click()
                            self.logger.info("✅ Click realizado.")
                            
                            tablas_encontradas[f"{tipo_tabla}_{index}"] = detalles
                            index += 1

                        except Exception as e:
                            self.logger.debug(f"Error procesando tabla {tipo_tabla}[{index}]: {e}")

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
            
            #self.conectar_ventana_analisis()
            #self.extraer_navegacion_configuracion()
            #self.extraer_boton_analisis()
            
            #time.sleep(1.1)
            self.conectar_ventana_analisis(modo_configuracion=True)
            resultados = {}            
            time.sleep(1)
            resultados['navegacion'] = self.extraer_navegacion_lateral()
            time.sleep(1)
            resultados['mostrar_datos'] = self.extraer_mostrar_datos()
            time.sleep(2)
            resultados['opciones_configuracion'] = self.extraer_configuracion_principal_mediciones()
            time.sleep(2)
            resultados['arbol_mediciones'] = self.extraer_componentes_arbol_mediciones()
            time.sleep(1)
            resultados['tabla_mediciones'] = self.extraer_tabla_mediciones()
            time.sleep(2)
            resultados['informes_graficos'] = self.extraer_informes_graficos()
            time.sleep(1)

            nombre_archivo = r"D:\Universidad\8vo Semestre\Practicas\Sonel\data\archivos_csv\archivo_prueba_40VerificacionFuncionamiento.csv"
            self.guardar_archivo_csv(nombre_archivo)
            #resultados['exportar_csv'] = self.extraer_componente_por_coordenadas(nombre_componente="Informe CSV", coordenadas=(191, 426))

            # Resumen final
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 === RESUMEN FINAL DE EXTRACCIÓN ===")
            self.logger.info(f"🧭 Navegación: {len(resultados['navegacion'])} elementos")
            self.logger.info(f"📊 Mostrar datos: {len(resultados['mostrar_datos'])} elementos")
            self.logger.info(f"📈 Informes: {len(resultados['informes_graficos'])} componentes")
            #self.logger.info(f"📋 Tablas: {len(resultados['tabla_mediciones'])} tablas")
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
        #for categoria, datos in resultados.items():
        #    print(f"{categoria.upper()}: {len(datos)} elementos encontrados")
    else:
        print(f"\n❌ Extracción falló")
        print(f"📄 Revisa errores en: {extractor.log_filename}")

if __name__ == "__main__":
    main()
import os
import re
import json
import time
import psutil
import logging
import traceback
import pyautogui
import pyperclip
from time import sleep
from pathlib import Path
from datetime import datetime
from pywinauto.mouse import move
from pywinauto import Application
from pywinauto.keyboard import send_keys
from pyautogui import click, moveTo, position
from pywinauto import Desktop, mouse, findwindows
from pynput.mouse import Button, Listener as MouseListener
from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper

class SonelAnalisisInicial:
    """Clase especializada para manejar la vista inicial de análisis"""
    
    def __init__(self, archivo_pqm, ruta_exe="D:/Wolfly/Sonel/SonelAnalysis.exe"):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.app = None
        self.ventana_inicial = None

        # Configurar logger SOLO PARA CONSOLA
        self.logger = logging.getLogger(f"{__name__}_inicial")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [INICIAL] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info("="*60)
        self.logger.info("🎯 EXTRACTOR VISTA INICIAL - SONEL ANALYSIS")
        self.logger.info(f"📁 Archivo PQM: {archivo_pqm}")
        self.logger.info("="*60)

    def conectar(self):
        """Conecta con la vista inicial de análisis"""
        try:
            self.logger.info("🔍 Conectando con vista inicial...")
            
            # Establecer conexión con la aplicación
            try:
                self.app = Application(backend="uia").connect(title_re=".*Análisis.*")
                self.logger.info("✅ Conectado con aplicación existente")
            except:
                self.logger.info("🚀 Iniciando nueva instancia...")
                self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                time.sleep(10)
            
            # Obtener ventana inicial específica
            main_window = self.app.top_window()
            main_window.set_focus()
            
            # Buscar ventana que NO termine en "Configuración 1"
            windows = main_window.descendants(control_type="Window")
            for window in windows:
                try:
                    title = window.window_text()
                    if ("Análisis" in title and ".pqm" in title and title.strip() 
                        and not title.strip().endswith("Configuración 1")):
                        self.ventana_inicial = window
                        self.logger.info(f"✅ Vista inicial encontrada: {title}")
                        return True
                except Exception:
                    continue
            
            # Fallback: usar ventana principal si cumple criterios
            main_title = main_window.window_text()
            if ("Análisis" in main_title and ".pqm" in main_title and main_title.strip() 
                and not main_title.strip().endswith("Configuración 1")):
                self.ventana_inicial = main_window
                self.logger.info(f"✅ Vista inicial (main): {main_title}")
                return True
            
            self.logger.error("❌ No se encontró vista inicial")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando vista inicial: {e}")
            return False

    def navegar_configuracion(self):
        """Navega al árbol de configuración y expande 'Configuración 1'"""
        try:
            self.logger.info("🌳 Navegando árbol de configuración...")
            
            if not self.ventana_inicial:
                self.logger.error("❌ No hay ventana inicial conectada")
                return False
            
            # Buscar TreeItem con "Configuración 1"
            tree_controls = self.ventana_inicial.descendants(control_type="TreeItem")
            
            for tree in tree_controls:
                texto = tree.window_text()
                if "Configuración 1" in texto or "Configuration 1" in texto:
                    self.logger.info(f"✅ TreeItem encontrado: {texto}")
                    return self._expandir_configuracion(tree)
            
            self.logger.error("❌ TreeItem 'Configuración 1' no encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error navegando configuración: {e}")
            return False

    def _expandir_configuracion(self, config_item):
        """Expande el elemento de configuración"""
        try:
            rect = config_item.rectangle()
            center_x = (rect.left + rect.right) // 2
            center_y = (rect.top + rect.bottom) // 2
            
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)
            
            self.logger.info(f"🔓 Click en configuración ({center_x}, {center_y})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error expandiendo configuración: {e}")
            return False

    def ejecutar_analisis(self):
        """Hace clic en el botón 'Análisis de datos'"""
        try:
            self.logger.info("🎯 Ejecutando análisis de datos...")
            
            # Buscar botón "Análisis de datos"
            buttons = self.ventana_inicial.descendants(control_type="Button", title="Análisis de datos")
            if not buttons:
                buttons = self.ventana_inicial.descendants(control_type="Button", title="Data Analysis")
            
            if buttons:
                analysis_button = buttons[0]
                analysis_button.click()
                time.sleep(2)  # Esperar a que se abra la ventana de configuración
                
                self.logger.info("✅ Análisis de datos ejecutado")
                return True
            else:
                self.logger.error("❌ Botón 'Análisis de datos' no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando análisis: {e}")
            return False

    def get_app_reference(self):
        """Retorna la referencia de la aplicación para usar en la segunda clase"""
        return self.app


class SonelConfiguracion:
    """Clase especializada para manejar la vista de configuración"""
    
    def __init__(self, app_reference=None):
        self.app = app_reference
        self.ventana_configuracion = None
        self.main_window = None

        # Configurar logger SOLO PARA CONSOLA
        self.logger = logging.getLogger(f"{__name__}_configuracion")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [CONFIGURACION] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info("="*60)
        self.logger.info("⚙️ EXTRACTOR VISTA CONFIGURACIÓN - SONEL ANALYSIS")
        self.logger.info("="*60)

    def conectar(self, app_reference=None):
        """Conecta con la vista de configuración"""
        try:
            self.logger.info("🔍 Conectando con vista de configuración...")
            
            if app_reference:
                self.app = app_reference
            
            if not self.app:
                # Fallback: conectar directamente si no hay referencia
                self.app = Application(backend="uia").connect(title_re=".*Análisis.*")
            
            # Esperar a que aparezca la ventana de configuración
            time.sleep(2)
            
            # Buscar ventana que termine en "Configuración 1"
            main_window = self.app.top_window()
            windows = main_window.descendants(control_type="Window")
            self.main_window = main_window
            
            for window in windows:
                try:
                    title = window.window_text()
                    if ("Análisis" in title and ".pqm" in title and title.strip() 
                        and title.strip().endswith("Configuración 1")):
                        self.ventana_configuracion = window
                        self.logger.info(f"✅ Vista configuración encontrada: {title}")
                        return True
                except Exception:
                    continue
            
            # Fallback: verificar ventana principal
            main_title = main_window.window_text()
            if ("Análisis" in main_title and ".pqm" in main_title and main_title.strip() 
                and main_title.strip().endswith("Configuración 1")):
                self.ventana_configuracion = main_window
                self.logger.info(f"✅ Vista configuración (main): {main_title}")
                return True
            
            self.logger.error("❌ No se encontró vista de configuración")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando configuración: {e}")
            return False

    def extraer_navegacion_lateral(self):
        """Extrae y activa elementos de navegación lateral (Mediciones)"""
        try:
            self.logger.info("🧭 Extrayendo navegación lateral...")
            
            mediciones_encontradas = {}
            index = 0
            
            for tipo_control in ["CheckBox", "Button", "Text", "TreeItem"]:
                try:
                    controles = self.ventana_configuracion.descendants(control_type=tipo_control)
                    
                    for control in controles:
                        texto = control.window_text().strip()
                        
                        if "Mediciones" in texto:
                            detalles = self._log_control_details(control, index, tipo_control)
                            if detalles:
                                mediciones_encontradas[f"Mediciones_{index}"] = detalles
                                index += 1
                            
                            # Activar CheckBox si es necesario
                            if tipo_control == "CheckBox":
                                try:
                                    estado = control.get_toggle_state()
                                    if estado != 1:
                                        control.click_input()
                                        time.sleep(0.5)
                                        self.logger.info("✅ CheckBox 'Mediciones' activado")
                                except Exception as e_click:
                                    self.logger.warning(f"⚠️ Error activando CheckBox: {e_click}")
                
                except Exception:
                    continue
            
            self.logger.info(f"📊 Navegación: {len(mediciones_encontradas)} elementos encontrados")
            return mediciones_encontradas
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo navegación: {e}")
            return {}

    def configurar_filtros_datos(self):
        """Configura filtros de datos (Usuario, Prom., etc.)"""
        try:
            self.logger.info("⚙️ Configurando filtros de datos...")
            elementos_configurados = {}
            
            # 1. Seleccionar RadioButton "Usuario"
            radiobuttons = self.ventana_configuracion.descendants(control_type="RadioButton")
            for radio in radiobuttons:
                texto = radio.window_text().strip()
                if texto == "Usuario":
                    try:
                        estado = radio.get_toggle_state()
                        if estado != 1:
                            radio.select()
                            self.logger.info("✅ RadioButton 'Usuario' seleccionado")
                        elementos_configurados["RadioButton_Usuario"] = "Seleccionado"
                    except Exception as e:
                        self.logger.error(f"❌ Error seleccionando 'Usuario': {e}")
            
            # 2. Configurar CheckBoxes de medición
            checkboxes_config = {
                "Prom.": True,   # Activar
                "Mín.": False,   # Desactivar
                "Instant.": False,  # Desactivar
                "Máx.": False    # Desactivar
            }
            
            checkboxes = self.ventana_configuracion.descendants(control_type="CheckBox")
            for checkbox in checkboxes:
                texto = checkbox.window_text().strip()
                
                for medicion, debe_estar_activo in checkboxes_config.items():
                    if medicion in texto or texto == medicion:
                        try:
                            estado_actual = checkbox.get_toggle_state()
                            
                            if debe_estar_activo and estado_actual != 1:
                                checkbox.toggle()
                                self.logger.info(f"✅ Activando '{texto}'")
                            elif not debe_estar_activo and estado_actual == 1:
                                checkbox.toggle()
                                self.logger.info(f"🚫 Desactivando '{texto}'")
                            
                            elementos_configurados[f"CheckBox_{texto}"] = "Configurado"
                            
                        except Exception as e:
                            self.logger.error(f"❌ Error configurando '{texto}': {e}")
            
            self.logger.info(f"📊 Filtros: {len(elementos_configurados)} elementos configurados")
            return elementos_configurados
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando filtros: {e}")
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

            for control in self.ventana_configuracion.descendants():
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
                    tree_items = self.ventana_configuracion.descendants(control_type="TreeItem")
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
                    tree_items = self.ventana_configuracion.descendants(control_type="TreeItem")
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
                    tablas = self.ventana_configuracion.descendants(control_type=tipo_tabla)

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
        
    
    def extraer_informes_graficos(self):
        """Extrae información específica de la sección 'Informes y gráficos'"""
        try:
            self.logger.info("\n📈 === EXTRACCIÓN: INFORMES Y GRÁFICOS ===")

            index = 0
            informes_encontrados = self._buscar_informes(index)
            index += len(informes_encontrados)

            # Buscar texto relacionado
            self.logger.info("\n📋 Buscando elementos de texto relacionados...")
            textos = self.ventana_configuracion.descendants(control_type="Text")
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

            return informes_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo informes y gráficos: {e}")
            return {}

    def _buscar_informes(self, index): 
        informes_encontrados = {}

        self.logger.info("\n🔘 Buscando botón 'Informes' y sus opciones...")

        for i, button in enumerate(self.ventana_configuracion.descendants(control_type="Button")):
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
        buttons = self.ventana_configuracion.descendants(control_type="Button")
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

    def guardar_archivo_csv(self, nombre_archivo: str):
        """
        Guarda el archivo CSV usando únicamente métodos de pywinauto sin coordenadas ni pyautogui.
        """
        try:
            self.logger.info(f"💾 Guardando archivo CSV: {nombre_archivo}")
            time.sleep(2)
            
            if not self.app:
                self.logger.error("❌ No hay conexión con la aplicación Sonel")
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
                self.logger.warning(f"⚠️ No se pudo enfocar la ventana: {e}")

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
                self.logger.error("❌ No se encontró el campo de nombre para guardar el archivo.")
                return False

            # Estrategia: Método estándar con verificaciones adicionales
            try:
                self.logger.info("🔄 Estableciendo nombre del archivo...")
                # ✅ Normalizar nombre del archivo
                nombre_archivo = nombre_archivo.strip()
                if "." in nombre_archivo:
                    partes = nombre_archivo.split(".")
                    nombre_sin_puntos = "".join(partes[:-1])  # quitar puntos del nombre
                    extension = partes[-1]
                    nombre_archivo = f"{nombre_sin_puntos}.{extension}"
                else:
                    self.logger.warning("⚠️ El nombre del archivo no contenía una extensión explícita.")

                pyperclip.copy(nombre_archivo)

                # Verificar visibilidad antes de proceder
                if not campo_control.is_visible():
                    self.logger.warning("⚠️ Campo no visible, intentando scroll y focus...")
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

                self.logger.info(f"📎 Nombre establecido en el campo: {nombre_archivo}")
                
            except Exception as e:
                self.logger.error(f"❌ Error estableciendo nombre: {e}")
                return False

            time.sleep(0.5)

            # Localizar el botón "Guardar"
            boton_guardar_control = None
            
            try:
                for idx, ctrl in enumerate(guardar_ventana.descendants(control_type="Button")):
                    if isinstance(ctrl, ButtonWrapper) and ctrl.window_text() and ctrl.window_text().strip().lower() == "guardar":
                        boton_guardar_control = ctrl
                        self._log_control_details(ctrl, index=idx, tipo_esperado="Botón Guardar")
                        break
            except Exception as e:
                self.logger.warning(f"⚠️ Error buscando botón 'Guardar': {e}")

            if not boton_guardar_control:
                self.logger.error("❌ No se encontró el botón 'Guardar'.")
                return False

            # Hacer clic en el botón Guardar
            try:
                boton_guardar_control.set_focus()
                time.sleep(0.2)
                boton_guardar_control.invoke()
                self.logger.info("✅ Archivo CSV guardado correctamente usando pywinauto.")
                return True
            except Exception as e:
                self.logger.error(f"❌ Error al hacer clic en Guardar: {e}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error general en guardar_archivo_csv: {e}")
            return False

    def _log_control_details(self, control, index, tipo_esperado=""):
        """Registra detalles del control"""
        try:
            texto = control.window_text()
            auto_id = getattr(control, 'automation_id', '') or ''
            class_name = getattr(control, 'class_name', '') or ''
            control_type = control.element_info.control_type
            rect = control.rectangle()
            
            self.logger.info(f"[{index}] {tipo_esperado}: {texto}")
            self.logger.info(f"  AUTO_ID: {auto_id}")
            self.logger.info(f"  RECT: (L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})")
            
            return {
                'texto': texto,
                'auto_id': auto_id,
                'class_name': class_name,
                'control_type': str(control_type),
                'rectangle': f"(L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})",
                'control': control
            }
            
        except Exception as e:
            self.logger.error(f"Error registrando control: {e}")
            return None


class SonelExtractorCompleto:
    """Coordinador principal que maneja ambas clases con procesamiento dinámico"""
    
    def __init__(self, input_dir=None, output_dir=None, ruta_exe=None):
        # Configuración de rutas
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # Configuración de paths por defecto
        self.PATHS = {
            'input_dir': input_dir or os.path.join(BASE_DIR, 'data', 'archivos_pqm'),
            'output_dir': output_dir or os.path.join(BASE_DIR, 'data', 'archivos_csv'),
            'export_dir': output_dir or os.path.join(BASE_DIR, 'data', 'archivos_csv'),
            'sonel_exe_path': ruta_exe or 'D:\\Wolfly\\Sonel\\SonelAnalysis.exe',
            'temp_dir': os.path.join(BASE_DIR, 'temp'),
            'process_file_dir': os.path.join(BASE_DIR, 'data', 'archivos_pqm')
        }
        
        # Configuración de delays para verificación
        self.delays = {
            'file_verification': 2  # Segundos entre verificaciones
        }
        
        # Archivo de seguimiento de procesados
        self.processed_files_json = os.path.join(
            self.PATHS['process_file_dir'],
            'procesados.json'
        )

        # Crear directorios si no existen
        os.makedirs(self.PATHS['output_dir'], exist_ok=True)
        os.makedirs(self.PATHS['process_file_dir'], exist_ok=True)
        os.makedirs(self.PATHS['temp_dir'], exist_ok=True)
        
        # Configurar logger SOLO PARA CONSOLA
        self.logger = logging.getLogger(f"{__name__}_complete")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [COMPLETE] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info("="*80)
        self.logger.info("🚀 EXTRACTOR COMPLETO SONEL ANALYSIS - INICIO")
        self.logger.info(f"📁 Directorio entrada: {self.PATHS['input_dir']}")
        self.logger.info(f"📁 Directorio salida: {self.PATHS['output_dir']}")
        self.logger.info("="*80)

    def _verify_file_creation(self, csv_path, max_attempts=5):
        """
        Verifica la creación del archivo CSV
        
        Args:
            csv_path: Ruta del archivo a verificar
            max_attempts: Número máximo de intentos de verificación
            
        Returns:
            bool: True si el archivo fue creado exitosamente
        """
        verification_attempts = 0
        
        self.logger.info(f"🔍 Iniciando verificación de archivo: {os.path.basename(csv_path)}")
        
        while verification_attempts < max_attempts:
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                if file_size > 100:  # Archivo debe tener contenido mínimo
                    self.logger.info(f"✅ Archivo verificado exitosamente: {os.path.basename(csv_path)} ({file_size} bytes)")
                    return True
                else:
                    self.logger.warning(f"⚠️ Archivo existe pero muy pequeño ({file_size} bytes)")
            
            verification_attempts += 1
            time.sleep(self.delays['file_verification'])
            self.logger.info(f"🔄 Verificación {verification_attempts}/{max_attempts} - Buscando: {os.path.basename(csv_path)}")
        
        self.logger.error(f"❌ Archivo no pudo ser verificado después de {max_attempts} intentos: {os.path.basename(csv_path)}")
        return False

    def _get_expected_csv_name(self, archivo_pqm):
        """
        Genera el nombre esperado del archivo CSV basado en el archivo PQM original
        
        Args:
            archivo_pqm: Ruta del archivo .pqm702
            
        Returns:
            str: Nombre completo esperado del archivo CSV
        """
        # Obtener el nombre completo del archivo sin extensión
        file_stem = Path(archivo_pqm).stem
        # Crear nombre CSV con sufijo _procesado
        csv_name = f"{file_stem}.csv"
        return os.path.join(self.PATHS['output_dir'], csv_name)

    def _find_generated_csv(self, expected_csv_path, archivo_pqm):
        """
        Busca el archivo CSV generado, considerando posibles variaciones en el nombre
        
        Args:
            expected_csv_path: Ruta esperada del archivo CSV
            archivo_pqm: Archivo PQM original para extraer información
            
        Returns:
            str|None: Ruta del archivo CSV encontrado o None si no se encuentra
        """
        # Primero verificar si existe con el nombre esperado
        if os.path.exists(expected_csv_path):
            return expected_csv_path
        
        # Extraer información del archivo original
        original_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem
        
        # Buscar posibles variaciones del nombre
        possible_names = [
            f"{file_stem}.csv",
            f"{file_stem}_procesado.csv",
        ]
        
        # Si el nombre tiene números al inicio, buscar también solo con esos números
        import re
        match = re.match(r'^(\d+)', file_stem)
        if match:
            number_prefix = match.group(1)
            possible_names.extend([
                f"{number_prefix}.csv",
                f"{number_prefix}_procesado.csv"
            ])
        
        # Buscar en el directorio de salida
        for possible_name in possible_names:
            possible_path = os.path.join(self.PATHS['output_dir'], possible_name)
            if os.path.exists(possible_path):
                self.logger.info(f"📂 Archivo CSV encontrado con nombre alternativo: {possible_name}")
                return possible_path
        
        # Buscar cualquier archivo CSV creado recientemente
        try:
            csv_files = [f for f in os.listdir(self.PATHS['output_dir']) if f.endswith('.csv')]
            if csv_files:
                # Ordenar por fecha de modificación (más reciente primero)
                csv_files_with_time = []
                for csv_file in csv_files:
                    csv_path = os.path.join(self.PATHS['output_dir'], csv_file)
                    mtime = os.path.getmtime(csv_path)
                    csv_files_with_time.append((csv_file, mtime, csv_path))
                
                csv_files_with_time.sort(key=lambda x: x[1], reverse=True)
                
                # Verificar si el archivo más reciente fue creado en los últimos 5 minutos
                if csv_files_with_time:
                    most_recent = csv_files_with_time[0]
                    time_diff = time.time() - most_recent[1]
                    
                    if time_diff < 300:  # 5 minutos
                        self.logger.info(f"📂 Posible archivo CSV encontrado (creado recientemente): {most_recent[0]}")
                        return most_recent[2]
        
        except Exception as e:
            self.logger.warning(f"⚠️ Error buscando archivos CSV alternativos: {e}")
        
        return None

    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        
        Returns:
            Lista de rutas de archivos .pqm702
        """
        try:
            if not os.path.exists(self.PATHS['input_dir']):
                self.logger.error(f"❌ Directorio de entrada no existe: {self.PATHS['input_dir']}")
                return []
            
            pqm_files = []
            for file in os.listdir(self.PATHS['input_dir']):
                if file.lower().endswith('.pqm702'):
                    ruta_normalizada = os.path.join(self.PATHS['input_dir'], file).replace("\\", "/")
                    pqm_files.append(ruta_normalizada)
            
            # Ordenar archivos para procesamiento consistente
            pqm_files.sort()
            
            self.logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702 en {self.PATHS['input_dir']}")
            for i, file in enumerate(pqm_files, 1):
                self.logger.info(f"   {i}. {os.path.basename(file)}")
            
            return pqm_files
            
        except Exception as e:
            self.logger.error(f"Error obteniendo archivos .pqm702: {e}")
            return []

    def obtener_estadisticas_procesados(self):
        """
        Obtiene estadísticas de archivos procesados
        
        Returns:
            dict: Estadísticas de procesamiento
        """
        try:
            if not os.path.exists(self.processed_files_json):
                return {"total": 0, "archivos": []}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            return {
                "total": len(processed_data),
                "archivos": list(processed_data.keys()),
                "ultimo_procesado": max(
                    processed_data.values(), 
                    key=lambda x: x.get('fecha', ''), 
                    default={}
                ).get('fecha', 'N/A') if processed_data else 'N/A'
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {"total": 0, "archivos": [], "error": str(e)}

    def ya_ha_sido_procesado(self, file_path):
        """
        Verifica si un archivo ya ha sido procesado anteriormente
        
        Args:
            file_path (str): Ruta completa del archivo a verificar
            
        Returns:
            bool: True si ya fue procesado, False si no
        """
        try:
            # Obtener nombre base del archivo sin ruta
            file_name = os.path.basename(file_path)
            
            # Verificar si existe el archivo JSON
            if not os.path.exists(self.processed_files_json):
                return False
            
            # Leer archivo JSON
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            # Verificar si el archivo está registrado
            if file_name in processed_data:
                entry = processed_data[file_name]

                # Verificar si fue exitoso
                if entry.get("exitoso", False):
                    self.logger.info(f"⏭️  Saltando {file_name} (ya procesado exitosamente)")
                    return True
                else:
                    self.logger.info(f"🔁 Reintentando procesamiento de {file_name} (procesamiento anterior fallido)")
                    return False
            else:
                return False
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Error leyendo JSON de procesados: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error verificando archivo procesado {file_path}: {e}")
            return False

    def registrar_archivo_procesado(self, file_path, resultado_exitoso=True, csv_path=None):
        """
        Registra un archivo como procesado exitosamente
        
        Args:
            file_path (str): Ruta completa del archivo procesado
            resultado_exitoso (bool): Si el procesamiento fue exitoso
            csv_path (str): Ruta del archivo CSV generado (opcional)
        """
        try:
            # Obtener información del archivo
            file_name = os.path.basename(file_path)
            file_stem = Path(file_path).stem
            file_ext = Path(file_path).suffix.lstrip('.')
            
            # Cargar datos existentes o crear estructura vacía
            processed_data = {}
            if os.path.exists(self.processed_files_json):
                try:
                    with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning("Archivo JSON corrupto, creando uno nuevo")
                    processed_data = {}
            
            # Crear registro del archivo procesado
            registro = {
                "nombre": file_stem,
                "extension": file_ext,
                "fecha": datetime.now().isoformat(),
                "exitoso": resultado_exitoso
            }
            
            # Agregar información del CSV si está disponible
            if csv_path and os.path.exists(csv_path):
                registro["csv_generado"] = os.path.basename(csv_path)
                registro["csv_size"] = os.path.getsize(csv_path)
                registro["csv_verificado"] = True
            else:
                registro["csv_verificado"] = False
            
            # Agregar registro del archivo procesado
            processed_data[file_name] = registro
            
            # Guardar archivo JSON actualizado
            os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
            status = "✅" if resultado_exitoso else "❌"
            csv_info = f" (CSV: {os.path.basename(csv_path)})" if csv_path else ""
            self.logger.info(f"📝 Registrado {status}: {file_name}{csv_info}")
            
        except Exception as e:
            self.logger.error(f"Error registrando archivo procesado {file_path}: {e}")

    def ejecutar_extraccion_archivo(self, archivo_pqm):
        """Ejecuta el flujo completo para un archivo específico"""
        nombre_archivo = os.path.basename(archivo_pqm)
        csv_path_generado = None
        proceso_exitoso = False  # Variable para controlar el estado real del proceso
        
        try:
            self.logger.info(f"\n🎯 Procesando: {nombre_archivo}")
            
            # FASE 1: Vista inicial
            self.logger.info("--- FASE 1: VISTA INICIAL ---")
            extractor_inicial = SonelAnalisisInicial(archivo_pqm, self.PATHS['sonel_exe_path'])
            
            if not extractor_inicial.conectar():
                self.logger.error("❌ Error conectando vista inicial")
                return False
            
            if not extractor_inicial.navegar_configuracion():
                self.logger.error("❌ Error navegando configuración")
                return False
            
            if not extractor_inicial.ejecutar_analisis():
                self.logger.error("❌ Error ejecutando análisis")
                return False
            
            # FASE 2: Vista configuración
            self.logger.info("--- FASE 2: VISTA CONFIGURACIÓN ---")
            extractor_config = SonelConfiguracion()
            app_ref = extractor_inicial.get_app_reference()
            
            if not extractor_config.conectar(app_ref):
                self.logger.error("❌ Error conectando vista configuración")
                return False
            
            # Ejecutar extracciones en configuración - MANEJO DE ERRORES MEJORADO
            try:
                time.sleep(1)
                if not extractor_config.extraer_navegacion_lateral():
                    self.logger.warning("⚠️ Falló extracción navegación lateral, continuando...")
                    # NO retornar False aquí, solo advertir
                
                time.sleep(1)
                if not extractor_config.configurar_filtros_datos():
                    self.logger.warning("⚠️ Falló configuración filtros, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(2)
                if not extractor_config.extraer_configuracion_principal_mediciones():
                    self.logger.warning("⚠️ Falló extracción configuración principal, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(2)
                if not extractor_config.extraer_componentes_arbol_mediciones():
                    self.logger.warning("⚠️ Falló extracción árbol mediciones, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(1)
                if not extractor_config.extraer_tabla_mediciones():
                    self.logger.warning("⚠️ Falló extracción tabla mediciones, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(2)
                if not extractor_config.extraer_informes_graficos():
                    self.logger.warning("⚠️ Falló extracción informes gráficos, continuando...")
                    # NO retornar False aquí, solo advertir

            except Exception as e:
                self.logger.warning(f"⚠️ Error en fase de extracción, pero continuando: {e}")
                # NO retornar False, continuar con el guardado

            # FASE 3: Guardar y verificar archivo CSV - ESTA ES LA FASE CRÍTICA
            self.logger.info("--- FASE 3: GUARDADO Y VERIFICACIÓN CSV ---")
            
            try:
                # Generar nombre esperado del CSV
                expected_csv_path = self._get_expected_csv_name(archivo_pqm)
                self.logger.info(f"📄 Archivo CSV esperado: {os.path.basename(expected_csv_path)}")
                
                # Guardar archivo CSV
                time.sleep(1)
                save_result = extractor_config.guardar_archivo_csv(expected_csv_path)
                
                # Si el guardado falló, aún intentar verificar
                if not save_result:
                    self.logger.warning("⚠️ Comando de guardado retornó False, pero verificando archivo...")
                
                # Esperar un poco para que se complete la escritura
                time.sleep(3)

                # Buscar el archivo CSV con nombres alternativos
                self.logger.info(f"🔍 Iniciando verificación de archivo")
                found_csv = self._find_generated_csv(expected_csv_path, archivo_pqm)
                
                if found_csv and self._verify_file_creation(found_csv):
                    csv_path_generado = found_csv
                    proceso_exitoso = True  # ÉXITO confirmado por archivo alternativo
                    self.logger.info(f"✅ CSV encontrado y verificado: {os.path.basename(found_csv)}")
                    
                    # Renombrar el archivo encontrado al nombre esperado si es diferente
                    if found_csv != expected_csv_path:
                        try:
                            os.rename(found_csv, expected_csv_path)
                            csv_path_generado = expected_csv_path
                            self.logger.info(f"📝 Archivo renombrado a: {os.path.basename(expected_csv_path)}")
                        except Exception as e:
                            self.logger.warning(f"⚠️ No se pudo renombrar el archivo: {e}")
                else:
                    self.logger.error("❌ No se pudo verificar la creación del archivo CSV")
                    proceso_exitoso = False
                        
            except Exception as e:
                self.logger.error(f"❌ Error crítico en fase de guardado: {e}")
                proceso_exitoso = False

            # Log del resultado final
            if proceso_exitoso:
                self.logger.info(f"✅ Procesamiento exitoso: {nombre_archivo}")
            else:
                self.logger.error(f"❌ Procesamiento falló: {nombre_archivo} - No se generó CSV válido")
            
            return proceso_exitoso

        except Exception as e:
            self.logger.error(f"❌ Error general procesando {nombre_archivo}: {e}")
            proceso_exitoso = False
            return False
        finally:
            # Siempre registrar el resultado, incluyendo información del CSV si se generó
            self.registrar_archivo_procesado(archivo_pqm, proceso_exitoso, csv_path_generado)
    
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

    def ejecutar_extraccion_completa_dinamica(self):
        """Ejecuta el flujo completo para todos los archivos no procesados"""
        try:
            # Obtener estadísticas iniciales
            stats = self.obtener_estadisticas_procesados()
            self.logger.info(f"📊 Archivos ya procesados: {stats['total']}")
            if stats['total'] > 0:
                self.logger.info(f"📅 Último procesado: {stats['ultimo_procesado']}")
            
            # Obtener lista de archivos
            archivos_pqm = self.get_pqm_files()
            if not archivos_pqm:
                self.logger.warning("⚠️  No se encontraron archivos .pqm702 para procesar")
                return None
            
            # Filtrar archivos ya procesados
            archivos_pendientes = [
                archivo for archivo in archivos_pqm 
                if not self.ya_ha_sido_procesado(archivo)
            ]
            
            if not archivos_pendientes:
                self.logger.info("✅ Todos los archivos ya han sido procesados")
                return {"procesados": 0, "saltados": len(archivos_pqm)}
            
            self.logger.info(f"🔄 Archivos pendientes de procesar: {len(archivos_pendientes)}")
            
            # Procesar cada archivo
            resultados_globales = {
                "procesados_exitosos": 0,
                "procesados_fallidos": 0,
                "saltados": len(archivos_pqm) - len(archivos_pendientes),
                "csvs_verificados": 0,
                "detalles": []
            }
            
            for i, archivo in enumerate(archivos_pendientes, 1):
                nombre_archivo = os.path.basename(archivo)
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📁 Procesando archivo {i}/{len(archivos_pendientes)}: {nombre_archivo}")
                self.logger.info(f"{'='*60}")
                
                # EJECUTAR PROCESAMIENTO
                resultado = self.ejecutar_extraccion_archivo(archivo)
                
                # EVALUAR RESULTADO Y ACTUAR EN CONSECUENCIA
                if resultado is True:
                    # ÉXITO - No forzar cierre
                    resultados_globales["procesados_exitosos"] += 1
                    resultados_globales["csvs_verificados"] += 1
                    resultados_globales["detalles"].append({
                        "archivo": nombre_archivo,
                        "estado": "exitoso",
                        "csv_verificado": True
                    })
                    self.logger.info(f"✅ Archivo procesado exitosamente: {nombre_archivo}")
                    
                    # CIERRE SUAVE - Solo cerrar procesos, no forzar
                    try:
                        time.sleep(2)  # Dar tiempo para que termine correctamente
                        self.close_sonel_analysis_force()  # Limpieza preventiva
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error en limpieza post-éxito: {e}")
                    
                else:
                    # FALLO - Aquí sí forzar cierre
                    resultados_globales["procesados_fallidos"] += 1
                    resultados_globales["detalles"].append({
                        "archivo": nombre_archivo,
                        "estado": "fallido",
                        "csv_verificado": False
                    })
                    self.logger.error(f"❌ Archivo procesado con error: {nombre_archivo}")
                    
                    # CIERRE FORZOSO por error
                    try:
                        self.close_sonel_analysis_force()
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error en cierre forzoso: {e}")

                # Pausa entre archivos para estabilidad
                if i < len(archivos_pendientes):
                    self.logger.info("⏳ Pausa entre archivos...")
                    time.sleep(4)
            
            # Resumen final
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 RESUMEN FINAL DE PROCESAMIENTO")
            self.logger.info(f"✅ Procesados exitosamente: {resultados_globales['procesados_exitosos']}")
            self.logger.info(f"📄 CSVs verificados: {resultados_globales['csvs_verificados']}")
            self.logger.info(f"❌ Procesados con error: {resultados_globales['procesados_fallidos']}")
            self.logger.info(f"⏭️  Saltados (ya procesados): {resultados_globales['saltados']}")
            self.logger.info(f"📁 Total de archivos: {len(archivos_pqm)}")
            self.logger.info("="*80)

            # Limpieza final
            self.logger.info("🧹 Limpieza final de procesos Sonel Analysis...")
            try:
                self.close_sonel_analysis_force()
            except Exception as e:
                self.logger.warning(f"⚠️ Error en limpieza final: {e}")
            
            return resultados_globales
            
        except Exception as e:
            self.logger.error(f"❌ Error en extracción completa dinámica: {e}")
            return None


# Uso del extractor con procesamiento dinámico
if __name__ == "__main__":
    # Configuración de rutas (puedes personalizar estas rutas)
    input_directory = "D:\\Universidad\\8vo Semestre\\Practicas\\Sonel\\data\\archivos_pqm"
    output_directory = "D:\\Universidad\\8vo Semestre\\Practicas\\Sonel\\data\\archivos_csv"
    sonel_exe_path = "D:\\Wolfly\\Sonel\\SonelAnalysis.exe"
    
    # Crear extractor con procesamiento dinámico
    extractor = SonelExtractorCompleto(
        input_dir=input_directory,
        output_dir=output_directory,
        ruta_exe=sonel_exe_path
    )
    
    # Ejecutar procesamiento completo
    resultados = extractor.ejecutar_extraccion_completa_dinamica()
    
    if resultados:
        print("\n" + "="*50)
        print("✅ PROCESAMIENTO COMPLETADO")
        print(f"📊 Exitosos: {resultados['procesados_exitosos']}")
        print(f"📄 CSVs verificados: {resultados['csvs_verificados']}")
        print(f"❌ Fallidos: {resultados['procesados_fallidos']}")
        print(f"⏭️  Saltados: {resultados['saltados']}")
        print("="*50)
    else:
        print("❌ Error en el procesamiento general")
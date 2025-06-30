import re
import time
import logging
import pyperclip
import pyautogui
from time import sleep
from pywinauto.mouse import move
from pywinauto.keyboard import send_keys
from pyautogui import moveTo, click, position
from pywinauto import Desktop, mouse, findwindows
from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper

class SonelExecutor:
    """Ejecuta acciones principales de extracción y configuración"""
    
    def __init__(self, ventana_configuracion, app=None, main_window=None):
        self.ventana_configuracion = ventana_configuracion
        self.app = app
        self.main_window = main_window
        
        # Configurar logger
        self.logger = logging.getLogger(f"{__name__}_executor")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [EXECUTOR] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

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
                            pyautogui.click(button='left')

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

            if hasattr(self, 'main_window') and self.main_window:
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
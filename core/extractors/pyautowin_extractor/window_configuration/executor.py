import re
import os
import time
import logging
import pyperclip
import pyautogui
from time import sleep
from pywinauto import mouse
from datetime import datetime
from pywinauto.mouse import move
from pyautogui import moveTo, click
from pywinauto.keyboard import send_keys
from config.logger import get_logger
from core.utils.text_normalize import TextUtils
from core.utils.file_save import ComponentesGuardado
from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper
from config.settings import get_full_config, get_all_possible_translations, get_all_excluded_terms

class SonelExecutor:
    """Ejecuta acciones principales de extracción y configuración"""
    
    def __init__(self, ventana_configuracion, app=None, main_window=None):
        self.ventana_configuracion = ventana_configuracion
        self.app = app
        self.main_window = main_window
        
        # Configurar logger
        config = get_full_config()
        self.logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

        self.save_file = ComponentesGuardado(logger=self.logger)

    def extraer_configuracion_principal_mediciones(self):
        """
        Busca y desactiva el checkbox 'Seleccionar todo' si está activado,
        y hace clic en el botón 'Expandir todo'.
        ✅ VERSIÓN MULTIIDIOMA
        """
        try:
            self.logger.info("\n🔧 Buscando 'Seleccionar todo' y 'Expandir todo' (multiidioma)...")
            
            # Obtener traducciones para todos los idiomas
            select_all_texts = get_all_possible_translations('ui_controls', 'select_all')
            expand_all_texts = get_all_possible_translations('ui_controls', 'expand_all')
            
            self.logger.info(f"🌐 Buscando 'Seleccionar todo' en: {select_all_texts}")
            self.logger.info(f"🌐 Buscando 'Expandir todo' en: {expand_all_texts}")

            componentes_encontrados = {
                'select_all': None,
                'expand_all': None
            }

            # Buscar componentes con enfoque multiidioma
            for control in self.ventana_configuracion.descendants():
                try:
                    texto = control.window_text().strip()
                    if not texto:
                        continue

                    tipo_control = control.friendly_class_name()
                    
                    # Verificar 'Seleccionar todo'
                    if not componentes_encontrados['select_all'] and TextUtils.texto_coincide(texto, select_all_texts):
                        if tipo_control == "CheckBox":
                            componentes_encontrados['select_all'] = control
                            self.logger.info(f"✅ 'Seleccionar todo' encontrado: '{texto}' ({tipo_control})")
                            self.save_file.guardar_coordenada_componente(control, "CheckBox", "select_all")
                        else:
                            self.logger.warning(f"⚠️ Texto coincide pero tipo incorrecto para 'Seleccionar todo': {tipo_control}")

                    # Verificar 'Expandir todo'
                    elif not componentes_encontrados['expand_all'] and TextUtils.texto_coincide(texto, expand_all_texts):
                        if tipo_control == "Button":
                            componentes_encontrados['expand_all'] = control
                            self.logger.info(f"✅ 'Expandir todo' encontrado: '{texto}' ({tipo_control})")
                            self.save_file.guardar_coordenada_componente(control, "Button", "expand_all")
                        else:
                            self.logger.warning(f"⚠️ Texto coincide pero tipo incorrecto para 'Expandir todo': {tipo_control}")

                    # Si ya encontramos ambos, podemos terminar la búsqueda
                    if componentes_encontrados['select_all'] and componentes_encontrados['expand_all']:
                        break

                except Exception as e:
                    self.logger.debug(f"Error procesando control: {e}")

            # Procesar componentes encontrados
            # Procesar 'Seleccionar todo'
            if componentes_encontrados['select_all']:
                control = componentes_encontrados['select_all']
                try:
                    estado = control.get_toggle_state()
                    self.logger.info(f"🔍 Estado actual del checkbox: {estado}")

                    if estado == 1:  # Si está activado
                        self.logger.info("🔄 Desactivando checkbox 'Seleccionar todo'...")
                        control.toggle()
                        self.logger.info("✅ Checkbox desactivado")
                    else:
                        self.logger.info("✔️ Checkbox 'Seleccionar todo' ya está desactivado")
                except Exception as e:
                    self.logger.error(f"❌ Error manipulando checkbox 'Seleccionar todo': {e}")
            else:
                self.logger.warning("⚠️ No se encontró el checkbox 'Seleccionar todo' en ningún idioma")

            # Procesar 'Expandir todo'
            if componentes_encontrados['expand_all']:
                control = componentes_encontrados['expand_all']
                try:
                    self.logger.info("🖱️ Haciendo clic en 'Expandir todo'...")
                    control.click_input()
                    self.logger.info("✅ Clic en 'Expandir todo' realizado")
                except Exception as e:
                    self.logger.error(f"❌ Error haciendo clic en 'Expandir todo': {e}")
            else:
                self.logger.warning("⚠️ No se encontró el botón 'Expandir todo' en ningún idioma")

        except Exception as e:
            self.logger.error(f"❌ Error general en 'extraer_configuracion_principal_mediciones': {e}")


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

            # Obtener palabras clave en todos los idiomas soportados
            palabras_clave = get_all_possible_translations('measurement_keywords')
            terminos_excluidos = get_all_excluded_terms()

            self.logger.info(f"🌐 Palabras clave multiidioma cargadas: {len(palabras_clave)} términos")
            self.logger.debug(f"📝 Términos: {palabras_clave}")
            self.logger.debug(f"❌ Términos excluidos: {terminos_excluidos}")

            def normalizar_texto(texto):
                """Quita etiquetas HTML y símbolos para comparación multiidioma"""
                if not texto:
                    return ""
                
                # Eliminar etiquetas HTML
                texto = re.sub(r"<sub>(.*?)</sub>", r"\1", texto, flags=re.IGNORECASE)
                texto = re.sub(r"<.*?>", "", texto)  # Eliminar cualquier etiqueta HTML
                
                # Eliminar símbolos y caracteres especiales
                texto = re.sub(r"[<>_/\-\(\)\[\]{}]", " ", texto)
                
                # Normalizar espacios
                texto = re.sub(r'\s+', ' ', texto)
                
                return texto.lower().strip()

            def contiene_termino(texto):
                """
                Verifica si el texto contiene alguna palabra clave multiidioma
                y NO contiene términos excluidos
                """
                from core.utils.text_normalize import TextUtils  # Importar aquí para evitar dependencias circulares
                
                # PRIMERA VERIFICACIÓN: Comprobar si contiene términos excluidos
                if TextUtils.contiene_termino_excluido(texto, terminos_excluidos):
                    self.logger.info(f"🚫 Texto '{texto}' contiene término excluido - RECHAZADO")
                    return False
                
                # SEGUNDA VERIFICACIÓN: Comprobar si contiene palabras clave válidas
                texto_normalizado = TextUtils.normalizar_texto(texto)
                for clave in palabras_clave:
                    clave_normalizada = TextUtils.normalizar_texto(clave)
                    if clave_normalizada in texto_normalizado:
                        self.logger.info(f"✅ Texto '{texto}' contiene palabra clave válida: '{clave}'")
                        return True
                
                return False

            def verificar_y_seleccionar_elemento(item, texto):
                """
                Verifica si el elemento es seleccionable y lo selecciona haciendo clic en el área del checkbox.
                Retorna información sobre el estado de selección.
                """
                nonlocal elementos_seleccionados, elementos_no_seleccionables
                
                try:
                    # Verificar si contiene palabra clave
                    if not contiene_termino(texto):
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
                        'es_clave': contiene_termino(texto)
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

            def realizar_scroll_inteligente(x_scroll, y_scroll, direccion=-4):
                """Realiza scroll en el área específica del TreeView"""
                try:
                    # Mover cursor al área de scroll
                    mouse.move(coords=(x_scroll, y_scroll))
                    sleep(0.1)  # Pequeña pausa para asegurar posicionamiento
                    
                    # Realizar scroll
                    mouse.scroll(coords=(x_scroll, y_scroll), wheel_dist=direccion)
                    sleep(0.8)  # Pausa para que la interfaz se actualice
                    
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

                            self.save_file.guardar_coordenada_componente(item, "TreeItem", f"componentes_mediciones_{index}")
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

                            self.save_file.guardar_coordenada_componente(tabla, tipo_tabla, f"table_{index}")

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

            reports_texts = get_all_possible_translations('ui_controls', 'reports')
            self.logger.info(f"🌐 Buscando elementos de texto relacionados con 'Informes y gráficos' en: {reports_texts}")

            index = 0
            informes_encontrados = self._buscar_informes(index)
            index += len(informes_encontrados)

            # Buscar texto relacionado
            self.logger.info("\n📋 Buscando elementos de texto relacionados...")
            textos = self.ventana_configuracion.descendants(control_type="Text")
            for texto in textos:
                try:
                    texto_content = texto.window_text().strip()
                    if texto_content and TextUtils.texto_coincide(texto_content, reports_texts):
                        detalles = self._log_control_details(texto, index, "Text")
                        if detalles:
                            detalles['contenido_relevante'] = texto_content

                            self.save_file.guardar_coordenada_componente(texto, "Text", f"reports_{index}")

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
        
        # Importar traducciones multiidioma
        from config.settings import get_all_possible_translations
        
        # Obtener términos de informes en todos los idiomas
        report_terms = get_all_possible_translations('ui_controls', 'reports')
        
        self.logger.info(f"\n🔘 Buscando botón 'Informes' multiidioma...")
        self.logger.info(f"🌐 Términos de búsqueda: {report_terms}")

        def normalizar_para_busqueda(texto):
            """Normaliza texto para búsqueda multiidioma"""
            if not texto:
                return ""
            texto = texto.lower().strip()
            # Eliminar acentos y caracteres especiales
            texto = re.sub(r'[áàäâ]', 'a', texto)
            texto = re.sub(r'[éèëê]', 'e', texto)
            texto = re.sub(r'[íìïî]', 'i', texto)
            texto = re.sub(r'[óòöô]', 'o', texto)
            texto = re.sub(r'[úùüû]', 'u', texto)
            texto = re.sub(r'[^\w\s]', ' ', texto)
            texto = re.sub(r'\s+', ' ', texto)
            return texto.strip()

        def contiene_termino(texto):
            """Verifica si el texto contiene algún término de informe"""
            texto_normalizado = normalizar_para_busqueda(texto)
            for termino in report_terms:
                termino_normalizado = normalizar_para_busqueda(termino)
                if termino_normalizado in texto_normalizado:
                    return True
            return False

        # Buscar botones de informes
        for i, button in enumerate(self.ventana_configuracion.descendants(control_type="Button")):
            try:
                texto = button.window_text().strip()
                if contiene_termino(texto):
                    detalles = self._log_control_details(button, index, "Button")
                    if detalles:
                        detalles['metodo_deteccion'] = "Por texto botón multiidioma"
                        detalles['termino_encontrado'] = texto
                        self.save_file.guardar_coordenada_componente(button, "Button", f"reports_{index}")

                        try:
                            self.logger.info(f"🖱️ Haciendo clic en botón de informes: '{texto}'")
                            button.click_input()
                            time.sleep(1.2)  # Esperar menú emergente

                            x, y = pyautogui.position()
                            move(coords=(x, y + 52))
                            time.sleep(0.5)
                            pyautogui.click(button='left')

                        except Exception as submenu_err:
                            self.logger.warning(f"⚠️ No se pudieron obtener los subelementos del botón 'Informes': {submenu_err}")

                        informes_encontrados[f"Button_Informes_{index}"] = detalles
                        index += 1
                        break  # Solo procesar el primer botón encontrado
            except Exception as e:
                self.logger.debug(f"Error en botón 'Informes': {e}")

        # Fallback: detectar por contenido visible con multiidioma
        if not informes_encontrados:
            buttons = self.ventana_configuracion.descendants(control_type="Button")
            for button in buttons:
                try:
                    texto_button = button.window_text().strip()
                    if contiene_termino(texto_button):
                        detalles = self._log_control_details(button, index, "Button")
                        if detalles:
                            detalles['funcionalidad'] = "Abre vista gráfica del análisis"
                            detalles['metodo_deteccion'] = "Por contenido de texto multiidioma"
                            detalles['termino_encontrado'] = texto_button
                            self.save_file.guardar_coordenada_componente(button, "Button", f"reports_fallback_{index}")
                            
                            # Detectar si es CSV específicamente
                            if any(term in texto_button.upper() for term in ['CSV']):
                                detalles['opcion_prioritaria'] = "Informe CSV"
                            
                            informes_encontrados[f"Button_Graficos_Contenido_{index}"] = detalles
                            index += 1
                            self.logger.info(f"✅ BUTTON encontrado por contenido multiidioma: {texto_button}")
                            break
                except Exception as e:
                    self.logger.debug(f"Error procesando botón: {e}")

        return informes_encontrados

    def guardar_archivo_csv(self, nombre_archivo: str):
        """
        Guarda el archivo CSV usando múltiples estrategias de búsqueda para mayor robustez.
        """
        try:
            if os.path.sep in nombre_archivo or '/' in nombre_archivo:
                csv_filename_only = os.path.basename(nombre_archivo)
                self.logger.info(f"💾 Guardando archivo CSV: {csv_filename_only}")
                self.logger.info(f"   📁 Ruta completa: {nombre_archivo}")
            else:
                csv_filename_only = nombre_archivo
                self.logger.info(f"💾 Guardando archivo CSV: {csv_filename_only}")
            
            time.sleep(2)
            self.logger.info(f"💾 Guardando archivo CSV: {nombre_archivo}")

            # Obtener todas las traducciones posibles para 'save'
            save_terms = get_all_possible_translations('ui_controls', 'save')
            self.logger.info(f"🌐 Buscando diálogo 'Guardar' en términos: {save_terms}")
            
            if not self.app:
                self.logger.error("❌ No hay conexión con la aplicación Sonel")
                return False

            guardar_ventana = None

            if hasattr(self, 'main_window') and self.main_window:
                dialogs = self.main_window.descendants(control_type="Window")
                for i, dialog in enumerate(dialogs):
                    try:
                        self._log_control_details(dialog, index=i, tipo_esperado="Dialogo candidato")
                        dialog_text = dialog.window_text()
                        
                        # Verificar si es diálogo de guardar usando multiidioma
                        if (dialog.is_visible() and 
                            (TextUtils.texto_coincide(dialog_text, save_terms) or 
                            dialog.child_window(control_type="Button").exists())):
                            
                            # Verificar si tiene botón guardar
                            try:
                                for ctrl in dialog.descendants(control_type="Button"):
                                    if TextUtils.texto_coincide(ctrl.window_text(), save_terms):
                                        guardar_ventana = dialog
                                        print(f"✅ Diálogo de guardado encontrado: '{dialog_text}'")
                                        break
                            except:
                                pass
                            
                            if guardar_ventana:
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

            # NUEVA ESTRATEGIA: Múltiples métodos para encontrar el campo de nombre
            campo_control = self._buscar_campo_nombre_multiples_estrategias(guardar_ventana)
            
            if not campo_control:
                self.logger.error("❌ No se encontró el campo de nombre para guardar el archivo con ninguna estrategia.")
                return False

            # Estrategia: Método estándar con verificaciones adicionales
            try:
                self.logger.info("🔄 Estableciendo nombre del archivo...")
                # ✅ Normalizar nombre del archivo
                archivo_a_guardar = nombre_archivo.strip()

                # Extraer carpeta y nombre
                carpeta = os.path.dirname(archivo_a_guardar)
                nombre = os.path.basename(archivo_a_guardar)

                if "." in nombre:
                    partes = nombre.split(".")
                    nombre_sin_puntos = "".join(partes[:-1])  # quitar puntos intermedios
                    extension = partes[-1]
                    nombre = f"{nombre_sin_puntos}.{extension}"
                else:
                    self.logger.warning("⚠️ El nombre del archivo no contenía una extensión explícita.")

                # Reconstruir ruta completa con nombre sanitizado
                nombre_final = self._aplicar_numeracion_incremental_csv(carpeta, nombre)
                archivo_a_guardar = os.path.join(carpeta, nombre_final)

                # Logs para debugging
                self.logger.info(f"   📁 Ruta base: {carpeta}")
                self.logger.info(f"   📄 Nombre sanitizado: {nombre}")
                self.logger.info(f"   📄 Nombre final (con numeración si aplica): {nombre_final}")
                self.logger.info(f"   💾 Guardando como: {archivo_a_guardar}")

                pyperclip.copy(archivo_a_guardar)

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

            save_terms = get_all_possible_translations('ui_controls', 'save')
            self.logger.info(f"🌐 Buscando botón 'Guardar' en términos: {save_terms}")

            def es_boton_guardar(texto):
                """Verifica si el texto corresponde a un botón de guardar en cualquier idioma"""
                if not texto:
                    return False
                texto_normalizado = texto.strip().lower()
                for termino in save_terms:
                    if termino.lower() == texto_normalizado:
                        return True
                return False
            
            try:
                for idx, ctrl in enumerate(guardar_ventana.descendants(control_type="Button")):
                    if isinstance(ctrl, ButtonWrapper) and es_boton_guardar(ctrl.window_text()):
                        boton_guardar_control = ctrl
                        self._log_control_details(ctrl, index=idx, tipo_esperado="Botón Guardar (multiidioma)")
                        self.save_file.guardar_coordenada_componente(boton_guardar_control, "ButtonWrapper", "boton_guardar")
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
        
    def _aplicar_numeracion_incremental_csv(self, carpeta, nombre_archivo):
        """
        Aplica numeración incremental al nombre del archivo CSV si ya existe.
        
        Args:
            carpeta (str): Directorio donde se guardará el archivo
            nombre_archivo (str): Nombre del archivo original con extensión
            
        Returns:
            str: Nombre del archivo con numeración incremental si es necesario
        """
        import os
        
        # Ruta completa del archivo original
        ruta_completa = os.path.join(carpeta, nombre_archivo)
        
        # Si no existe, usar el nombre original
        if not os.path.exists(ruta_completa):
            self.logger.info(f"   ✅ Nombre disponible: {nombre_archivo}")
            return nombre_archivo
        
        # Extraer nombre base y extensión
        nombre_base, extension = os.path.splitext(nombre_archivo)
        
        # Buscar el siguiente número disponible
        contador = 1
        max_intentos = 500
        
        while contador <= max_intentos:
            nombre_numerado = f"{contador}_{nombre_base}{extension}"
            ruta_numerada = os.path.join(carpeta, nombre_numerado)
            
            if not os.path.exists(ruta_numerada):
                self.logger.info(f"   🔄 Archivo ya existe, aplicando numeración: {nombre_numerado}")
                self.logger.info(f"   📝 Número asignado: {contador}")
                return nombre_numerado
            
            contador += 1
        
        # Si se agotaron los intentos, usar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_timestamp = f"{timestamp}_{nombre_base}{extension}"
        
        self.logger.warning(f"⚠️ Se agotaron {max_intentos} intentos de numeración")
        self.logger.info(f"   🕐 Usando timestamp: {nombre_timestamp}")
        
        return nombre_timestamp

    def _buscar_campo_nombre_multiples_estrategias(self, guardar_ventana):
        """
        Busca el campo de nombre del archivo usando múltiples estrategias.
        Retorna el primer campo EditWrapper encontrado o None.
        """
        campo_control = None
        
        # ESTRATEGIA 1: Búsqueda por padre con término "Imágenes" (método original)
        self.logger.info("🔍 Estrategia 1: Buscando por padre con término 'Imágenes'")
        try:
            image_terms = get_all_possible_translations('ui_controls', 'image')
            self.logger.info(f"🌐 Términos de imagen: {image_terms}")
            
            def es_campo_imagenes(texto_control, lista_traducciones):
                """Verifica si el texto corresponde a 'Imágenes' en cualquier idioma"""
                if not texto_control:
                    return False
                texto_normalizado = TextUtils.normalizar_texto(texto_control)
                for traduccion in lista_traducciones:
                    if TextUtils.normalizar_texto(traduccion) in texto_normalizado:
                        return True
                return False

            for idx, ctrl in enumerate(guardar_ventana.descendants()):
                if isinstance(ctrl, EditWrapper):
                    try:
                        padre = ctrl.parent()
                        if padre and es_campo_imagenes(padre.window_text(), image_terms):
                            campo_control = ctrl
                            self._log_control_details(ctrl, index=idx, tipo_esperado="Campo Nombre (Estrategia 1 - EditWrapper por padre)")
                            self.save_file.guardar_coordenada_componente(campo_control, "EditWrapper", "nombre_archivo")
                            self.logger.info("✅ Campo encontrado con Estrategia 1")
                            return campo_control
                    except Exception as e:
                        self.logger.warning(f"⚠️ No se pudo evaluar padre de componente Edit #{idx}: {e}")
        except Exception as e:
            self.logger.warning(f"⚠️ Error en Estrategia 1: {e}")
        
        # ESTRATEGIA 2: Buscar todos los EditWrapper y tomar el más probable (por posición o características)
        self.logger.info("🔍 Estrategia 2: Buscando todos los EditWrapper disponibles")
        try:
            edit_controls = []
            for idx, ctrl in enumerate(guardar_ventana.descendants()):
                if isinstance(ctrl, EditWrapper):
                    try:
                        details = self._log_control_details(ctrl, index=idx, tipo_esperado="EditWrapper encontrado (Estrategia 2)")
                        if details:
                            edit_controls.append((ctrl, details, idx))
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error procesando EditWrapper #{idx}: {e}")
            
            if edit_controls:
                # Priorizar el último EditWrapper encontrado (suele ser el campo de nombre)
                campo_control = edit_controls[-1][0]
                self.logger.info(f"✅ Campo seleccionado con Estrategia 2: EditWrapper índice {edit_controls[-1][2]}")
                self.save_file.guardar_coordenada_componente(campo_control, "EditWrapper", "nombre_archivo")
                return campo_control
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error en Estrategia 2: {e}")
        
        # ESTRATEGIA 3: Buscar por automation_id o class_name conocidos
        self.logger.info("🔍 Estrategia 3: Buscando por automation_id conocidos")
        try:
            automation_ids_conocidos = ["fileNameTextBox", "txtFileName", "edtNombre", "1001", "FileNameEdit"]
            
            for automation_id in automation_ids_conocidos:
                try:
                    ctrl = guardar_ventana.child_window(auto_id=automation_id, control_type="Edit")
                    if ctrl.exists():
                        campo_control = ctrl
                        self.logger.info(f"✅ Campo encontrado con Estrategia 3: automation_id='{automation_id}'")
                        self.save_file.guardar_coordenada_componente(campo_control, "EditWrapper", "nombre_archivo")
                        return campo_control
                except Exception as e:
                    self.logger.debug(f"automation_id '{automation_id}' no encontrado: {e}")
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Error en Estrategia 3: {e}")
        
        # ESTRATEGIA 4: Buscar por posición (EditWrapper en la parte inferior del diálogo)
        self.logger.info("🔍 Estrategia 4: Buscando por posición (EditWrapper más abajo)")
        try:
            edit_controls_con_posicion = []
            for idx, ctrl in enumerate(guardar_ventana.descendants()):
                if isinstance(ctrl, EditWrapper):
                    try:
                        rect = ctrl.rectangle()
                        edit_controls_con_posicion.append((ctrl, rect.top, idx))
                    except Exception as e:
                        self.logger.debug(f"Error obteniendo posición de EditWrapper #{idx}: {e}")
            
            if edit_controls_con_posicion:
                # Ordenar por posición Y (de arriba a abajo) y tomar el último
                edit_controls_con_posicion.sort(key=lambda x: x[1])  # Ordenar por top
                campo_control = edit_controls_con_posicion[-1][0]  # El más abajo
                idx_seleccionado = edit_controls_con_posicion[-1][2]
                
                self.logger.info(f"✅ Campo seleccionado con Estrategia 4: EditWrapper más abajo (índice {idx_seleccionado})")
                self.save_file.guardar_coordenada_componente(campo_control, "EditWrapper", "nombre_archivo")
                return campo_control
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error en Estrategia 4: {e}")
        
        # ESTRATEGIA 5: Último recurso - primer EditWrapper encontrado
        self.logger.info("🔍 Estrategia 5: Último recurso - primer EditWrapper")
        try:
            for idx, ctrl in enumerate(guardar_ventana.descendants()):
                if isinstance(ctrl, EditWrapper):
                    try:
                        campo_control = ctrl
                        self._log_control_details(ctrl, index=idx, tipo_esperado="EditWrapper (Último recurso - Estrategia 5)")
                        self.logger.info(f"⚠️ Campo seleccionado con Estrategia 5 (último recurso): índice {idx}")
                        self.save_file.guardar_coordenada_componente(campo_control, "EditWrapper", "nombre_archivo")
                        return campo_control
                    except Exception as e:
                        self.logger.debug(f"Error en último recurso con EditWrapper #{idx}: {e}")
                        continue
                        
        except Exception as e:
            self.logger.warning(f"⚠️ Error en Estrategia 5: {e}")
        
        self.logger.error("❌ Ninguna estrategia pudo encontrar un campo de nombre válido")
        return None

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
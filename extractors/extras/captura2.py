import re
import time
import logging
import os
from datetime import datetime
from pywinauto import Desktop
from pywinauto import Application

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
        
    def _encontrar_ventana_(self):
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

    def _log_control_details(self, control, index, tipo_esperado=""):
        """Registra los detalles completos de un control en el formato solicitado"""
        try:
            texto = control.window_text()
            auto_id = getattr(control, 'automation_id', '') or ''
            class_name = getattr(control, 'class_name', '') or ''
            control_type = control.element_info.control_type
            rect = control.rectangle()
            
            self.logger.info("="*50)
            self.logger.info(f"[{index}] === {tipo_esperado} COMPLETO ===")
            self.logger.info(f"TEXTO COMPLETO: {texto}")
            self.logger.info(f"AUTO_ID: {auto_id}")
            self.logger.info(f"CLASS_NAME: {class_name}")
            self.logger.info(f"CONTROL_TYPE: {control_type}")
            self.logger.info(f"RECTANGLE: (L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})")
            self.logger.info(f"POSICIÓN: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
            self.logger.info("="*50)
            
            return {
                'texto': texto,
                'auto_id': auto_id,
                'class_name': class_name,
                'control_type': str(control_type),
                'rectangle': f"(L{rect.left}, T{rect.top}, R{rect.right}, B{rect.bottom})",
                'posicion': f"Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}",
                'control': control
            }
            
        except Exception as e:
            self.logger.error(f"Error registrando detalles del control: {e}")
            return None

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
            self.logger.info("\n🔘 Buscando Radio Buttons...")
            radiobuttons = self.analysis_window.descendants(control_type="RadioButton")
            for radio in radiobuttons:
                texto = radio.window_text().strip()
                if texto in ["Estándar", "Usuario"]:
                    detalles = self._log_control_details(radio, index, "RadioButton")
                    if detalles:
                        # Obtener estado del radio button
                        try:
                            estado = radio.get_toggle_state()
                            detalles['estado'] = estado
                        except:
                            detalles['estado'] = "Desconocido"
                        
                        elementos_encontrados[f"RadioButton_{texto}_{index}"] = detalles
                        index += 1

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
                            index += 1

            # 3. Buscar CheckBoxes de fase: "L1", "L2", "L3", "N (Σ)"
            self.logger.info("\n⚡ Buscando CheckBoxes de fase...")
            fases = ["L1", "L2", "L3", "N (Σ)", "N(Σ)", "N"]
            for checkbox in checkboxes:
                texto = checkbox.window_text().strip()
                for fase in fases:
                    if fase in texto or texto == fase:
                        detalles = self._log_control_details(checkbox, index, "CheckBox")
                        if detalles:
                            # Obtener estado del checkbox
                            try:
                                estado = checkbox.get_toggle_state()
                                detalles['estado'] = estado
                            except:
                                detalles['estado'] = "Desconocido"
                            
                            elementos_encontrados[f"CheckBox_Fase_{texto}_{index}"] = detalles
                            index += 1

            # 4. Buscar ComboBoxes
            self.logger.info("\n📋 Buscando ComboBoxes...")
            comboboxes = self.analysis_window.descendants(control_type="ComboBox")
            for i, combobox in enumerate(comboboxes):
                try:
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
                    
                    # Determinar tipo de ComboBox basado en contenido
                    tipo_combo = "ComboBox_General"
                    if "Absoluto" in str(items) or "Absoluto" in valor_actual:
                        tipo_combo = "ComboBox_MostrarArmonicos"
                    elif any(keyword in str(items).lower() for keyword in ["potencia", "energía", "energia"]):
                        if "potencia" in str(items).lower():
                            tipo_combo = "ComboBox_Potencia"
                        elif "energía" in str(items).lower() or "energia" in str(items).lower():
                            tipo_combo = "ComboBox_Energia"
                    
                    detalles = self._log_control_details(combobox, index, "ComboBox")
                    if detalles:
                        detalles['valor_actual'] = valor_actual
                        detalles['opciones_disponibles'] = items
                        detalles['tipo_combobox'] = tipo_combo
                        
                        elementos_encontrados[f"{tipo_combo}_{index}"] = detalles
                        index += 1
                        
                        self.logger.info(f"   💡 Valor actual: {valor_actual}")
                        self.logger.info(f"   📝 Opciones: {items[:3]}{'...' if len(items) > 3 else ''}")
                    
                except Exception as e:
                    self.logger.debug(f"Error procesando combobox {i}: {e}")

            # 5. Buscar elementos adicionales con texto relacionado
            self.logger.info("\n🔍 Buscando elementos de texto relacionados...")
            textos_relacionados = ["Mostrar armónicos", "Potencia", "Energía", "Usuario", "Estándar"]
            textos = self.analysis_window.descendants(control_type="Text")
            for texto_control in textos:
                texto = texto_control.window_text().strip()
                for relacionado in textos_relacionados:
                    if relacionado.lower() in texto.lower():
                        detalles = self._log_control_details(texto_control, index, "Text")
                        if detalles:
                            elementos_encontrados[f"Text_{relacionado}_{index}"] = detalles
                            index += 1
                        break

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

            # Buscar gráficos con lógica actual
            self.logger.info("\n🎨 Buscando botones 'Gráficos'...")
            buttons = self.analysis_window.descendants(control_type="Button")

            # Método 1: Título exacto
            try:
                graficos_btn = self.analysis_window.child_window(title="Gráficos", control_type="Button")
                if graficos_btn.exists():
                    detalles = self._log_control_details(graficos_btn, index, "Button")
                    if detalles:
                        detalles['funcionalidad'] = "Abre vista gráfica del análisis"
                        detalles['metodo_deteccion'] = "Por título exacto"
                        informes_encontrados[f"Button_Graficos_{index}"] = detalles
                        index += 1
                        self.logger.info("   ✅ BUTTON 'Gráficos' encontrado por título exacto")
            except Exception as e:
                self.logger.debug(f"No se encontró botón 'Gráficos': {e}")

            # Método 2: Por contenido textual
            for button in buttons:
                try:
                    texto_button = button.window_text().strip()
                    if "Gráfico" in texto_button or "Gráficos" in texto_button:
                        ya_encontrado = any("Button_Graficos" in k for k in informes_encontrados)
                        if not ya_encontrado:
                            detalles = self._log_control_details(button, index, "Button")
                            if detalles:
                                detalles['funcionalidad'] = "Abre vista gráfica del análisis"
                                detalles['metodo_deteccion'] = "Por contenido de texto"
                                informes_encontrados[f"Button_Graficos_Contenido_{index}"] = detalles
                                index += 1
                                self.logger.info(f"   ✅ BUTTON encontrado por contenido: {texto_button}")
                except Exception as e:
                    self.logger.debug(f"Error procesando botón: {e}")

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
        
    def extraer_componentes_arbol_mediciones(self):
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
                "corriente i", "potencia p", "potencia q1", "potencia sn", "potencia s",
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

            # === FORMA 2: Por nombre o título del control ===
            self.logger.info(f"\n🔍 Forma 2: Búsqueda por nombre/título")
            for item in self.analysis_window.descendants():
                name = item.element_info.name or ""
                texto = item.window_text().strip()
                completo = f"{name} {texto}".strip()

                if contiene_palabra_clave(completo):
                    detalles = self._log_control_details(item, index, "Nombre/Título")
                    detalles['tipo'] = "Título/Nombrado"
                    detalles['clave_detectada'] = True
                    arbol_componentes[f"Clave_Forma2_{index}"] = detalles
                    self.logger.info(f"✅ Coincidencia clave detectada en Forma 2: '{completo}'")
                    index += 1

            # === FORMA 3: Por contenido profundo ===
            self.logger.info(f"\n🔍 Forma 3: Búsqueda por contenido profundo")
            for item in self.analysis_window.descendants():
                textos = item.texts()
                texto_visible = " ".join(textos).strip()

                if contiene_palabra_clave(texto_visible):
                    detalles = self._log_control_details(item, index, "Contenido")
                    detalles['tipo'] = "Contenido relevante"
                    detalles['clave_detectada'] = True
                    arbol_componentes[f"Clave_Forma3_{index}"] = detalles
                    self.logger.info(f"✅ Coincidencia clave detectada en Forma 3: '{texto_visible}'")
                    index += 1

            self.logger.info(f"\n🌳 Total elementos extraídos: {len(arbol_componentes)}")
            return arbol_componentes

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo árbol de mediciones: {e}")
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

                            desktop = Desktop(backend="uia")
                            popup_windows = desktop.windows(control_type="Window", visible_only=True)

                            opciones = []
                            contiene_csv = False
                            encontrado_algo = False

                            for win in popup_windows:
                                try:
                                    elementos = win.descendants(control_type="MenuItem") + \
                                                win.descendants(control_type="Button") + \
                                                win.descendants(control_type="Text")

                                    for item in elementos:
                                        try:
                                            texto_item = item.window_text().strip()
                                            if texto_item:
                                                encontrado_algo = True
                                                opciones.append(texto_item)
                                                if "CSV" in texto_item.upper():
                                                    contiene_csv = True
                                                    detalles['opcion_prioritaria'] = texto_item
                                        except Exception as e:
                                            self.logger.debug(f"Error leyendo subelemento: {e}")
                                except Exception as e:
                                    self.logger.debug(f"Error accediendo a ventana emergente: {e}")

                            if encontrado_algo:
                                detalles['opciones_disponibles'] = opciones
                                detalles['contiene_informes_csv'] = contiene_csv
                            else:
                                self.logger.warning("⚠️  No se encontraron opciones dentro de ninguna ventana emergente.")

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

    def extraer_tabla_mediciones(self):
        """Extrae información de la tabla de mediciones inferior"""
        try:
            self.logger.info("\n📋 === EXTRACCIÓN: TABLA DE MEDICIONES ===")

            tablas_encontradas = {}
            index = 0

            # Cabeceras esperadas
            textos_esperados = ["Tiempo (UTC-5)", "f L1 instante. 10 s S [Hz]"]

            # Buscar tipos de controles que podrían contener tablas
            tipos_posibles = ["DataGrid", "Table", "Pane", "Group"]

            for tipo_tabla in tipos_posibles:
                try:
                    tablas = self.analysis_window.descendants(control_type=tipo_tabla)

                    for tabla in tablas:
                        try:
                            detalles = self._log_control_details(tabla, index, tipo_tabla)
                            if detalles:
                                # Buscar headers
                                try:
                                    headers = tabla.descendants(control_type="Header")
                                    header_texts = [h.window_text() for h in headers if h.window_text().strip()]
                                    detalles['cabeceras'] = header_texts
                                    self.logger.info(f"   📋 CABECERAS: {header_texts}")
                                except Exception as e:
                                    detalles['cabeceras'] = []
                                    self.logger.debug(f"Error obteniendo headers: {e}")

                                # Buscar filas y celdas
                                try:
                                    filas = tabla.descendants(control_type="DataItem")
                                    celdas = tabla.descendants(control_type="Text") + tabla.descendants(control_type="Custom")
                                    detalles['total_filas'] = len(filas)
                                    detalles['total_celdas'] = len(celdas)
                                    self.logger.info(f"   🔢 Total filas: {len(filas)}")
                                    self.logger.info(f"   📦 Total celdas: {len(celdas)}")
                                except Exception as e:
                                    detalles['total_filas'] = 0
                                    detalles['total_celdas'] = 0
                                    self.logger.debug(f"Error contando elementos: {e}")

                                # Explorar primeras filas
                                try:
                                    primeras_filas_info = []
                                    coincidencias = []

                                    for fila_index, fila in enumerate(filas[:3]):
                                        fila.highlight()  # Para depuración visual, opcional
                                        fila_celdas = fila.descendants(control_type="Text") or fila.descendants(control_type="Custom")
                                        texto_fila = [c.window_text().strip() for c in fila_celdas if c.window_text().strip()]
                                        primeras_filas_info.append(texto_fila)

                                        for texto in texto_fila:
                                            for esperado in textos_esperados:
                                                if esperado.lower() in texto.lower():
                                                    coincidencias.append(texto)

                                    detalles['primeras_filas'] = primeras_filas_info
                                    detalles['coincidencias_esperadas'] = coincidencias

                                    self.logger.info("📄 Primeras filas detectadas:")
                                    for idx, fila in enumerate(primeras_filas_info):
                                        self.logger.info(f"   ▸ Fila {idx}: {fila}")
                                    if coincidencias:
                                        self.logger.info(f"   ✅ COINCIDENCIAS ENCONTRADAS: {coincidencias}")
                                except Exception as e:
                                    detalles['primeras_filas'] = []
                                    detalles['coincidencias_esperadas'] = []
                                    self.logger.debug(f"Error extrayendo primeras filas: {e}")

                                # Extraer la primera celda directamente
                                try:
                                    primera_celda_texto = self.extraer_primera_celda_tabla(tabla)
                                    detalles['primera_celda'] = primera_celda_texto
                                    if primera_celda_texto:
                                        self.logger.info(f"   🔘 Primera celda directa: {primera_celda_texto}")
                                except Exception as e:
                                    detalles['primera_celda'] = None
                                    self.logger.debug(f"Error extrayendo primera celda directa: {e}")

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

    def extraer_primera_celda_tabla(self, tabla):
        """Extrae la primera celda de la primera fila de una tabla dada"""
        try:
            self.logger.info(f"\n🔎 Intentando extraer primera celda de tabla")

            filas = tabla.descendants(control_type="DataItem")
            if not filas:
                self.logger.warning("⚠️ No se encontraron filas (DataItem) en la tabla.")
                return None

            fila_0 = filas[0]
            fila_0.highlight()  # Para confirmar visualmente

            primera_fila_celdas = fila_0.descendants(control_type="Text") or fila_0.descendants(control_type="Custom")
            if not primera_fila_celdas:
                self.logger.warning("⚠️ No se encontraron celdas (Text/Custom) en la primera fila.")
                return None

            primera_celda = primera_fila_celdas[0]
            texto = primera_celda.window_text().strip()
            self.logger.info(f"✅ Primera celda detectada: '{texto}'")
            return texto
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo primera celda: {e}")
            return None

    def ejecutar_extraccion_completa(self):
        """Ejecuta la extracción completa de todos los componentes específicos"""
        try:
            self.logger.info("🎯 === INICIANDO EXTRACCIÓN COMPLETA OPTIMIZADA ===")
            
            if not self.conectar_ventana_analisis():
                return False
            
            # Extraer cada componente específico
            resultados = {}
            
            time.sleep(1)
            resultados['navegacion'] = self.extraer_navegacion_lateral()
            time.sleep(1.5)
            resultados['mostrar_datos'] = self.extraer_mostrar_datos()
            time.sleep(2.5)
            resultados['informes_graficos'] = self.extraer_informes_graficos()
            time.sleep(2)
            resultados['arbol_mediciones'] = self.extraer_componentes_arbol_mediciones()
            time.sleep(1)
            resultados['tabla_mediciones'] = self.extraer_tabla_mediciones()
            
            # Resumen final
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 === RESUMEN FINAL DE EXTRACCIÓN ===")
            self.logger.info(f"🧭 Navegación: {len(resultados['navegacion'])} elementos")
            self.logger.info(f"📊 Mostrar datos: {len(resultados['mostrar_datos'])} elementos")
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
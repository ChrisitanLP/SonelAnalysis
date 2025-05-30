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
            checkboxes_medicion = ["Prom.", "Min.", "Instant.", "Máx."]
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
    def extraer_menu_contextual_informe_csv(self):
        """
        Método específico para detectar el menú contextual "Informe CSV"
        """
        try:
            self.logger.info("\n🎯 === DETECCIÓN ESPECÍFICA: MENÚ CONTEXTUAL INFORME CSV ===")
            
            # Importar la clase detector
            from captura3 import MenuContextualDetector  # Ajusta la importación
            
            detector = MenuContextualDetector(self)
            resultados = detector.detectar_informe_csv_completo()
            
            self.logger.info(f"✅ Detección de menú contextual completada: {len(resultados)} elementos encontrados")
            return resultados
            
        except Exception as e:
            self.logger.error(f"❌ Error en detección de menú contextual: {e}")
            return {}

    def extraer_informes_graficos(self):
        """Extrae información específica de la sección 'Informes y gráficos'"""
        try:
            self.logger.info("\n📈 === EXTRACCIÓN: INFORMES Y GRÁFICOS ===")
            
            informes_encontrados = {}
            index = 0
            
            # 1. Buscar SplitButton "Informes" específicamente
            self.logger.info("\n🔽 Buscando SplitButton 'Informes'...")
            
            # Método 1: Buscar por título exacto
            try:
                informes_combo = self.analysis_window.child_window(title="Informes", control_type="SplitButton")
                if informes_combo.exists():
                    detalles = self._log_control_details(informes_combo, index, "SplitButton")
                    if detalles:
                        # Obtener valor actual
                        try:
                            valor_actual = informes_combo.get_value()
                        except:
                            try:
                                valor_actual = informes_combo.selected_text()
                            except:
                                valor_actual = "No disponible"
                        
                        # Obtener opciones disponibles
                        try:
                            items = informes_combo.item_texts()
                        except:
                            items = ["No disponibles"]
                        
                        detalles['valor_actual'] = valor_actual
                        detalles['opciones_disponibles'] = items
                        detalles['metodo_deteccion'] = "Por título exacto"
                        
                        # Verificar si contiene "Informes CSV"
                        contiene_csv = any("CSV" in str(item).upper() for item in items)
                        detalles['contiene_informes_csv'] = contiene_csv
                        
                        informes_encontrados[f"ComboBox_Informes_{index}"] = detalles
                        index += 1
                        
                        self.logger.info(f"   ✅ ENCONTRADO por título exacto")
                        self.logger.info(f"   💡 Valor actual: {valor_actual}")
                        self.logger.info(f"   📝 Opciones: {items}")
                        self.logger.info(f"   📊 Contiene 'Informes CSV': {contiene_csv}")
                        
            except Exception as e:
                self.logger.debug(f"No se encontró ComboBox por título exacto: {e}")
            
            # Método 2: Buscar por contenido "Informes" en todos los ComboBox
            self.logger.info("\n🔍 Buscando ComboBox que contenga 'Informes'...")
            comboboxes = self.analysis_window.descendants(control_type="ComboBox")
            
            for i, combo in enumerate(comboboxes):
                try:
                    texto_combo = combo.window_text().strip()
                    
                    # Verificar si contiene "Informes" o si ya fue encontrado
                    if "Informes" in texto_combo or "Informe" in texto_combo:
                        # Evitar duplicados
                        ya_encontrado = any("ComboBox_Informes" in key for key in informes_encontrados.keys())
                        if not ya_encontrado:
                            detalles = self._log_control_details(combo, index, "ComboBox")
                            if detalles:
                                # Obtener valor actual
                                try:
                                    valor_actual = combo.get_value()
                                except:
                                    try:
                                        valor_actual = combo.selected_text()
                                    except:
                                        valor_actual = "No disponible"
                                
                                # Obtener opciones disponibles
                                try:
                                    items = combo.item_texts()
                                except:
                                    items = ["No disponibles"]
                                
                                detalles['valor_actual'] = valor_actual
                                detalles['opciones_disponibles'] = items
                                detalles['metodo_deteccion'] = "Por contenido de texto"
                                
                                # Verificar si contiene "Informes CSV"
                                contiene_csv = any("CSV" in str(item).upper() for item in items)
                                detalles['contiene_informes_csv'] = contiene_csv
                                
                                informes_encontrados[f"ComboBox_Informes_Contenido_{index}"] = detalles
                                index += 1
                                
                                self.logger.info(f"   ✅ ENCONTRADO por contenido: {texto_combo}")
                                self.logger.info(f"   💡 Valor actual: {valor_actual}")
                                self.logger.info(f"   📝 Opciones: {items}")
                                self.logger.info(f"   📊 Contiene 'Informes CSV': {contiene_csv}")
                    
                    # También verificar opciones internas del ComboBox
                    else:
                        try:
                            items = combo.item_texts()
                            contiene_informes = any("Informe" in str(item) for item in items)
                            contiene_csv = any("CSV" in str(item).upper() for item in items)
                            
                            if contiene_informes or contiene_csv:
                                # Evitar duplicados
                                ya_encontrado = any("ComboBox_Informes" in key for key in informes_encontrados.keys())
                                if not ya_encontrado:
                                    detalles = self._log_control_details(combo, index, "ComboBox")
                                    if detalles:
                                        try:
                                            valor_actual = combo.get_value()
                                        except:
                                            try:
                                                valor_actual = combo.selected_text()
                                            except:
                                                valor_actual = "No disponible"
                                        
                                        detalles['valor_actual'] = valor_actual
                                        detalles['opciones_disponibles'] = items
                                        detalles['metodo_deteccion'] = "Por opciones internas"
                                        detalles['contiene_informes_csv'] = contiene_csv
                                        
                                        informes_encontrados[f"ComboBox_ConOpciones_{index}"] = detalles
                                        index += 1
                                        
                                        self.logger.info(f"   ✅ ENCONTRADO por opciones internas")
                                        self.logger.info(f"   💡 Valor actual: {valor_actual}")
                                        self.logger.info(f"   📝 Opciones relevantes: {[item for item in items if 'Informe' in str(item) or 'CSV' in str(item).upper()]}")
                        except:
                            pass
                
                except Exception as e:
                    self.logger.debug(f"Error procesando ComboBox {i}: {e}")
            
            # Método 3: Buscar por contenido "Informes" en todos los Button
            self.logger.info("\n🔘 Buscando botón 'Informes' y opción 'Informe CSV'...")

            buttons = self.analysis_window.descendants(control_type="Button")
            for index, button in enumerate(buttons):
                try:
                    texto_button = button.window_text().strip()
                    if "Informe" in texto_button or "Informes" in texto_button:
                        ya_encontrado = any("Button_Informes" in key for key in informes_encontrados.keys())
                        if not ya_encontrado:
                            detalles = self._log_control_details(button, index, "Button")
                            if detalles:
                                detalles['metodo_deteccion'] = "Por contenido de texto"
                                informes_encontrados[f"Button_Informes_Contenido_{index}"] = detalles
                                self.logger.info(f"   ✅ BUTTON encontrado por contenido: {texto_button}")

                                # Hacer clic para desplegar las opciones
                                button.click_input()
                                time.sleep(1)

                                # 🔍 Buscar por contenido el texto "Informe CSV" como hiciste antes
                                posibles_opciones = self.analysis_window.descendants()
                                for sub_index, opcion in enumerate(posibles_opciones):
                                    try:
                                        texto_opcion = opcion.window_text().strip()
                                        if "Informe CSV" in texto_opcion:
                                            self.logger.info(f"      ✅ Opción encontrada: {texto_opcion}")

                                            informes_encontrados[f"Opcion_Informe_CSV_{sub_index}"] = {
                                                "titulo": texto_opcion,
                                                "indice": sub_index,
                                                "rect": opcion.rectangle().dump() if hasattr(opcion, "rectangle") else None,
                                                "control_type": opcion.friendly_class_name(),
                                                "metodo_deteccion": "Por contenido de texto tras click en 'Informes'"
                                            }

                                            # (Opcional) Ejecutar la opción automáticamente:
                                            # opcion.click_input()
                                            break
                                    except Exception as e:
                                        self.logger.debug(f"Error evaluando opción: {e}")
                except Exception as e:
                    self.logger.debug(f"Error procesando Button: {e}")

            
            # Método 1: Buscar por título exacto
            try:
                graficos_btn = self.analysis_window.child_window(title="Gráficos", control_type="Button")
                if graficos_btn.exists():
                    detalles = self._log_control_details(graficos_btn, index, "Button")
                    if detalles:
                        detalles['funcionalidad'] = "Abre vista gráfica del análisis"
                        detalles['metodo_deteccion'] = "Por título exacto"
                        
                        informes_encontrados[f"Button_Graficos_{index}"] = detalles
                        index += 1
                        
                        self.logger.info(f"   ✅ BUTTON 'Gráficos' encontrado por título exacto")
                        
            except Exception as e:
                self.logger.debug(f"No se encontró Button por título exacto: {e}")
            
            # Método 2: Buscar por contenido "Gráficos" en todos los Button
            buttons = self.analysis_window.descendants(control_type="Button")
            for button in buttons:
                try:
                    texto_button = button.window_text().strip()
                    if "Gráfico" in texto_button or "Grafico" in texto_button:
                        # Evitar duplicados
                        ya_encontrado = any("Button_Graficos" in key for key in informes_encontrados.keys())
                        if not ya_encontrado:
                            detalles = self._log_control_details(button, index, "Button")
                            if detalles:
                                detalles['funcionalidad'] = "Abre vista gráfica del análisis"
                                detalles['metodo_deteccion'] = "Por contenido de texto"
                                
                                informes_encontrados[f"Button_Graficos_Contenido_{index}"] = detalles
                                index += 1
                                
                                self.logger.info(f"   ✅ BUTTON encontrado por contenido: {texto_button}")
                
                except Exception as e:
                    self.logger.debug(f"Error procesando Button: {e}")
            
            # 3. Buscar elementos de texto relacionados con "Informes y gráficos"
            self.logger.info("\n📋 Buscando elementos de texto relacionados...")
            textos = self.analysis_window.descendants(control_type="Text")
            for texto in textos:
                try:
                    texto_content = texto.window_text().strip()
                    if any(keyword in texto_content for keyword in ["Informes y gráficos", "Informes", "Gráficos"]):
                        detalles = self._log_control_details(texto, index, "Text")
                        if detalles:
                            detalles['contenido_relevante'] = texto_content
                            informes_encontrados[f"Text_Relacionado_{index}"] = detalles
                            index += 1
                            
                            self.logger.info(f"   📋 TEXTO relacionado: {texto_content}")
                
                except Exception as e:
                    self.logger.debug(f"Error procesando texto: {e}")
            
            # Resumen final con información específica
            self.logger.info("\n" + "="*60)
            self.logger.info("📊 RESUMEN ESPECÍFICO - INFORMES Y GRÁFICOS")
            
            combo_informes = len([k for k in informes_encontrados.keys() if "ComboBox" in k])
            button_graficos = len([k for k in informes_encontrados.keys() if "Button" in k])
            textos_relacionados = len([k for k in informes_encontrados.keys() if "Text" in k])
            
            self.logger.info(f"🔽 ComboBox 'Informes': {combo_informes} encontrados")
            self.logger.info(f"🔘 Button 'Gráficos': {button_graficos} encontrados")  
            self.logger.info(f"📋 Textos relacionados: {textos_relacionados} encontrados")
            self.logger.info(f"📊 TOTAL ELEMENTOS: {len(informes_encontrados)}")
            self.logger.info("="*60)
            
            return informes_encontrados
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo informes y gráficos: {e}")
            return {}


    def extraer_tabla_mediciones(self):
        """Extrae información de la tabla de mediciones inferior"""
        try:
            self.logger.info("\n📋 === EXTRACCIÓN: TABLA DE MEDICIONES ===")
            
            tablas_encontradas = {}
            index = 0
            
            # Buscar DataGrid y Table
            for tipo_tabla in ["DataGrid", "Table"]:
                try:
                    tablas = self.analysis_window.descendants(control_type=tipo_tabla)
                    
                    for tabla in tablas:
                        try:
                            detalles = self._log_control_details(tabla, index, tipo_tabla)
                            if detalles:
                                # Buscar headers/cabeceras
                                try:
                                    headers = tabla.descendants(control_type="Header")
                                    if headers:
                                        header_texts = []
                                        for header in headers[:10]:  # Solo primeros 10
                                            texto_header = header.window_text()
                                            if texto_header:
                                                header_texts.append(texto_header)
                                        
                                        detalles['cabeceras'] = header_texts
                                        self.logger.info(f"   📋 CABECERAS: {header_texts}")
                                    else:
                                        detalles['cabeceras'] = []
                                        
                                except Exception as e:
                                    detalles['cabeceras'] = []
                                    self.logger.debug(f"Error obteniendo headers: {e}")
                                
                                # Contar elementos
                                try:
                                    filas = tabla.descendants(control_type="DataItem")
                                    celdas = tabla.descendants(control_type="Custom")
                                    
                                    detalles['total_filas'] = len(filas)
                                    detalles['total_celdas'] = len(celdas)
                                    
                                    self.logger.info(f"   🔢 Total filas: {len(filas)}")
                                    self.logger.info(f"   📦 Total celdas: {len(celdas)}")
                                    
                                except Exception as e:
                                    detalles['total_filas'] = 0
                                    detalles['total_celdas'] = 0
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
                                    
                                    detalles['primera_fila'] = primera_fila
                                    
                                    if primera_fila:
                                        self.logger.info(f"   📋 PRIMERA FILA: {primera_fila}")
                                        
                                except Exception as e:
                                    detalles['primera_fila'] = []
                                    self.logger.debug(f"Error extrayendo primera fila: {e}")
                                
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
            
            if not self.conectar_ventana_analisis():
                return False
            
            # Extraer cada componente específico
            resultados = {}
            
            resultados['navegacion'] = self.extraer_navegacion_lateral()
            resultados['mostrar_datos'] = self.extraer_mostrar_datos()
            resultados['informes_graficos'] = self.extraer_informes_graficos()
            resultados['tabla_mediciones'] = self.extraer_tabla_mediciones()
            
            # NUEVO: Extraer menús contextuales
            resultados['menu_contextual'] = self.extraer_menu_contextual_informe_csv()

            # Resumen final
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 === RESUMEN FINAL DE EXTRACCIÓN ===")
            self.logger.info(f"🧭 Navegación: {len(resultados['navegacion'])} elementos")
            self.logger.info(f"📊 Mostrar datos: {len(resultados['mostrar_datos'])} elementos")
            self.logger.info(f"📈 Informes: {len(resultados['informes_graficos'])} componentes")
            self.logger.info(f"📋 Tablas: {len(resultados['tabla_mediciones'])} tablas")
            self.logger.info(f"🎯 Menús contextuales: {len(resultados['menu_contextual'])} elementos")
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
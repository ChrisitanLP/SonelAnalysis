import os
import json
import time
import logging
import pyautogui
from datetime import datetime
from config.logger import get_logger
from core.utils.text_normalize import TextUtils
from core.utils.wait_handler import WaitHandler
from core.utils.file_save import ComponentesGuardado
from config.settings import get_full_config, get_all_possible_translations, CHECKBOXES_CONFIG

class SonelNavigator:
    """Maneja la navegación y filtros de la interfaz"""
    
    def __init__(self, ventana_configuracion):
        self.ventana_configuracion = ventana_configuracion
        self.wait_handler = WaitHandler()
        
        # Configurar logger
        config = get_full_config()
        self.logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

        self.save_file = ComponentesGuardado(logger=self.logger)
        
        # Definir componentes requeridos
        self.componentes_requeridos = {
            "RadioButton": ["User"],
            "CheckBox": ["MIN", "MAX", "INSTANT"]
        }

    def _identificar_checkbox_por_config(self, texto_checkbox):
        """
        Identifica el tipo de checkbox basándose en CHECKBOXES_CONFIG y su texto.
        
        Args:
            texto_checkbox (str): Texto del checkbox a identificar
        
        Returns:
            tuple: (checkbox_id, debe_estar_activo) o (None, None) si no se identifica
        """
        texto_normalizado = texto_checkbox.strip()
        
        # Buscar coincidencia exacta en CHECKBOXES_CONFIG
        for config_text, estado_deseado in CHECKBOXES_CONFIG.items():
            if config_text == texto_normalizado or config_text.lower() == texto_normalizado.lower():
                # Mapear a nuestros IDs estándar basándose en las palabras clave
                checkbox_id = self._mapear_texto_a_id(config_text)
                if checkbox_id:
                    return checkbox_id, estado_deseado
        
        # Si no hay coincidencia exacta, buscar contenido parcial
        for config_text, estado_deseado in CHECKBOXES_CONFIG.items():
            if (config_text.lower() in texto_normalizado.lower() or 
                TextUtils.normalizar_texto(config_text) in TextUtils.normalizar_texto(texto_normalizado)):
                checkbox_id = self._mapear_texto_a_id(config_text)
                if checkbox_id:
                    return checkbox_id, estado_deseado
        
        return None, None
    
    def _mapear_texto_a_id(self, config_text):
        """
        Mapea el texto de configuración a un ID estándar.
        
        Args:
            config_text (str): Texto de configuración
        
        Returns:
            str: ID del checkbox o None si no se puede mapear
        """
        config_lower = config_text.lower()
        
        # Mapeo para Minimum/Mínimo
        if any(term in config_lower for term in ["min", "mín", "minimum", "mínimo"]):
            return "MIN"
        
        # Mapeo para Maximum/Máximo
        elif any(term in config_lower for term in ["max", "máx", "maximum", "máximo"]):
            return "MAX"
        
        # Mapeo para Instant/Instantáneo - CORREGIDO
        elif any(term in config_lower for term in ["instant", "instantaneous", "instantáneo", "inst"]):
            return "INSTANT"
        
        return None

    def extraer_navegacion_lateral(self):
        """Extrae y activa elementos de navegación lateral (Mediciones)"""
        try:
            self.logger.info("🧭 Extrayendo navegación lateral...")

            measurements = get_all_possible_translations('ui_controls', 'measurements')
            self.logger.info(f"🌐 Buscando 'Meciciones' en: {measurements}")

            # Esperar que la ventana esté lista con sus controles
            if not self.wait_handler.esperar_controles_disponibles(self.ventana_configuracion, 
                                                    ["CheckBox"], 
                                                    timeout=20):
                self.logger.error("❌ Timeout: Controles de navegación no disponibles")
                return {}
            
            mediciones_encontradas = {}
            index = 0
            
            for tipo_control in ["CheckBox", "Button", "Text", "TreeItem"]:
                try:
                    controles = self.ventana_configuracion.descendants(control_type=tipo_control)
                    
                    for control in controles:
                        texto = control.window_text().strip()
                        
                        if TextUtils.texto_coincide(texto, measurements):
                            detalles = self._log_control_details(control, index, tipo_control)
                            if detalles:
                                self.save_file.guardar_coordenada_componente(control, tipo_control, f"measurements_{index}")
                                mediciones_encontradas[f"Mediciones_{index}"] = detalles
                                index += 1
                            
                            # Activar CheckBox si es necesario
                            if tipo_control == "CheckBox":
                                try:
                                    estado = control.get_toggle_state()
                                    if estado != 1:
                                        control.click_input()
                                        time.sleep(0.2)
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
        
    def seleccionar_radiobutton_usuario_por_coordenadas(self, ruta_salida="componentes_configuracion.json"):
        """Selecciona el radiobutton 'Usuario' usando las coordenadas guardadas en el archivo, si existe."""
        if not os.path.exists(ruta_salida):
            self.logger.warning("📁 No existe archivo de componentes. Se usará selección tradicional.")
            return False

        try:
            with open(ruta_salida, "r", encoding="utf-8") as f:
                componentes = json.load(f)

            user_translations = get_all_possible_translations('ui_controls', 'user')
            user_translations_norm = [TextUtils.normalizar_texto(t) for t in user_translations]

            for comp in componentes:
                if comp["tipo"] != "RadioButton":
                    continue

                texto = TextUtils.normalizar_texto(comp["texto"])
                if any(t in texto for t in user_translations_norm):
                    rect = comp["rect"]
                    x = int((rect["left"] + rect["right"]) / 2)
                    y = int((rect["top"] + rect["bottom"]) / 2)

                    self.logger.info(f"🖱️ Clic en coordenadas ({x}, {y}) para seleccionar RadioButton '{comp['texto']}'")
                    pyautogui.moveTo(x, y, duration=0.2)
                    pyautogui.click()
                    return True

            self.logger.warning("❌ No se encontró el radiobutton 'Usuario' en archivo de componentes.")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error usando coordenadas del archivo: {e}")
            return False

    def configurar_radiobutton_usuario(self):
        """Selecciona el radiobutton 'Usuario' en la ventana de configuración."""
        try:
            self.logger.info("🔘 Configurando radiobutton 'Usuario'...")

            # Verificar si hay cambio de idioma antes de usar coordenadas
            if self.save_file.detectar_cambio_idioma(self.ventana_configuracion, self.componentes_requeridos):
                self.logger.info("🌐 Cambio de idioma detectado, limpiando coordenadas de RadioButton")
                self.save_file.limpiar_coordenadas_componentes({"RadioButton": self.componentes_requeridos["RadioButton"]})

            # Intentar usar coordenadas guardadas (solo si no hay cambio de idioma)
            if self.seleccionar_radiobutton_usuario_por_coordenadas():
                self.logger.info("✅ Selección del radiobutton 'Usuario' realizada por coordenadas.")
                return [], {}

            # Si no existen coordenadas guardadas o hay cambio de idioma, hacer el proceso completo
            user_translations = get_all_possible_translations('ui_controls', 'user')
            self.logger.info(f"🌐 Buscando 'Usuario' en: {user_translations}")

            radiobuttons = self.ventana_configuracion.descendants(control_type="RadioButton")
            self.radiobuttons_cache = radiobuttons
            elementos_configurados = {}

            for radio in radiobuttons:
                texto = radio.window_text().strip()
                texto_norm = TextUtils.normalizar_texto(texto)

                if any(TextUtils.normalizar_texto(user_text) in texto_norm for user_text in user_translations):
                    try:
                        estado = radio.get_toggle_state()
                        if estado != 1:
                            radio.select()
                            self.logger.info(f"✅ RadioButton '{texto}' seleccionado")
                        else:
                            self.logger.info(f"ℹ️ RadioButton '{texto}' ya estaba seleccionado")
                        
                        # Guardar coordenada del componente encontrado
                        self.save_file.guardar_coordenada_componente(radio, "RadioButton", "User")
                        elementos_configurados[f"RadioButton_{texto}"] = "Seleccionado"
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error seleccionando '{texto}': {e}")

            return radiobuttons, elementos_configurados

        except Exception as e:
            self.logger.error(f"❌ Error configurando radiobuttons: {e}")
            return [], {}

    def configurar_checkboxes_filtros(self):
        """Activa o desactiva checkboxes según configuración usando CHECKBOXES_CONFIG"""
        try:
            self.logger.info("☑️ Configurando checkboxes de filtros...")

            # Verificar si hay cambio de idioma antes de usar coordenadas
            if self.save_file.detectar_cambio_idioma(self.ventana_configuracion, self.componentes_requeridos):
                self.logger.info("🌐 Cambio de idioma detectado, limpiando coordenadas de CheckBox")
                self.save_file.limpiar_coordenadas_componentes({"CheckBox": self.componentes_requeridos["CheckBox"]})

            # Verificar si tenemos todas las coordenadas necesarias
            checkboxes_pendientes = []
            for checkbox_id in self.componentes_requeridos["CheckBox"]:
                if not self.save_file.obtener_coordenada_componente("CheckBox", checkbox_id):
                    checkboxes_pendientes.append(checkbox_id)
            
            # Si tenemos todas las coordenadas, usar coordenadas
            if not checkboxes_pendientes:
                self.logger.info("📍 Usando coordenadas guardadas para todos los checkboxes")
                elementos_configurados = {}
                for checkbox_id in self.componentes_requeridos["CheckBox"]:
                    if self.seleccionar_checkbox_por_coordenadas(checkbox_id):
                        coordenada = self.save_file.obtener_coordenada_componente("CheckBox", checkbox_id)
                        elementos_configurados[f"CheckBox_{coordenada.get('texto', checkbox_id)}"] = f"Configurado por coordenadas (ID: {checkbox_id})"
                return [], elementos_configurados

            self.logger.info(f"🔍 Faltan coordenadas para: {checkboxes_pendientes}, procediendo con búsqueda manual")

            checkboxes = self.ventana_configuracion.descendants(control_type="CheckBox")
            elementos_configurados = {}
            checkboxes_encontrados = {}

            for checkbox in checkboxes:
                texto = checkbox.window_text().strip()
                
                # Usar el nuevo método de identificación
                checkbox_id, debe_estar_activo = self._identificar_checkbox_por_config(texto)
                
                if checkbox_id and debe_estar_activo is not None:
                    try:
                        estado_actual = checkbox.get_toggle_state()

                        if debe_estar_activo and estado_actual != 1:
                            checkbox.toggle()
                            self.logger.info(f"✅ Activando '{texto}' (ID: {checkbox_id})")
                        elif not debe_estar_activo and estado_actual == 1:
                            checkbox.toggle()
                            self.logger.info(f"🚫 Desactivando '{texto}' (ID: {checkbox_id})")
                        else:
                            self.logger.info(f"ℹ️ CheckBox '{texto}' (ID: {checkbox_id}) ya tiene el estado correcto")

                        # Guardar coordenada del checkbox encontrado
                        self.save_file.guardar_coordenada_componente(checkbox, "CheckBox", checkbox_id)
                        checkboxes_encontrados[checkbox_id] = checkbox
                        elementos_configurados[f"CheckBox_{texto}"] = f"Configurado (ID: {checkbox_id})"
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error configurando '{texto}': {e}")
                else:
                    # Log de checkboxes no identificados para debugging
                    self.logger.debug(f"🔍 CheckBox no identificado: '{texto}'")

            # Verificar que se encontraron todos los checkboxes requeridos
            checkboxes_no_encontrados = [cb_id for cb_id in self.componentes_requeridos["CheckBox"] 
                                    if cb_id not in checkboxes_encontrados]
            
            if checkboxes_no_encontrados:
                self.logger.warning(f"⚠️ No se encontraron estos checkboxes: {checkboxes_no_encontrados}")
            else:
                self.logger.info("✅ Todos los checkboxes requeridos fueron encontrados y configurados")

            return checkboxes, elementos_configurados

        except Exception as e:
            self.logger.error(f"❌ Error configurando checkboxes: {e}")
            return [], {}
        
    def guardar_info_componentes(self, radiobuttons, checkboxes, ruta_salida="componentes_configuracion.json"):
        """Guarda información de RadioButtons y CheckBoxes proporcionados (si no existe el archivo)."""
        if os.path.exists(ruta_salida):
            self.logger.info(f"📁 Información de componentes ya existe en '{ruta_salida}'")
            return

        try:
            self.logger.info("📥 Guardando información de RadioButtons y CheckBoxes...")

            componentes = []

            for control_type, controles in [("RadioButton", radiobuttons), ("CheckBox", checkboxes)]:
                for control in controles:
                    try:
                        info = {
                            "tipo": control_type,
                            "texto": control.window_text().strip(),
                            "control_id": control.control_id(),
                            "class_name": control.friendly_class_name(),
                            "rect": {
                                "left": control.rectangle().left,
                                "top": control.rectangle().top,
                                "right": control.rectangle().right,
                                "bottom": control.rectangle().bottom
                            },
                            "padre": control.parent().window_text().strip() if control.parent() else None
                        }
                        componentes.append(info)
                    except Exception as e:
                        self.logger.warning(f"⚠️ No se pudo obtener información de un {control_type}: {e}")

            with open(ruta_salida, "w", encoding="utf-8") as f:
                json.dump(componentes, f, indent=4, ensure_ascii=False)

            self.logger.info(f"✅ Información guardada en '{ruta_salida}'")

        except Exception as e:
            self.logger.error(f"❌ Error al guardar componentes: {e}")

    def configurar_radiobutton(self):
        """Ejecuta configuración completa de radiobutton Usuario"""
        try:
            self.logger.info("⚙️ Configurando radiobutton Usuario...")

            radios_resultado = self.configurar_radiobutton_usuario()
            radios = radios_resultado[0] if isinstance(radios_resultado, tuple) else []
            
            # Solo guardar si se encontraron radiobuttons (búsqueda manual)
            if radios:
                self.save_file.guardar_radiobuttons(radios)

            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error configurando radiobutton: {e}")
            return False

    def configurar_checkboxes(self):
        """Ejecuta configuración completa de checkboxes"""
        try:
            self.logger.info("⚙️ Configurando checkboxes...")

            checks, elementos_check = self.configurar_checkboxes_filtros()
            
            # Solo guardar si se encontraron checkboxes (búsqueda manual)
            if checks:
                self.save_file.guardar_checkboxes(checks)
            
            total_config = elementos_check.copy()
            self.logger.info(f"📊 Checkboxes: {len(total_config)} elementos configurados")

            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error configurando checkboxes: {e}")
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
        

    def seleccionar_radiobutton_usuario_por_coordenadas(self):
        """Selecciona el radiobutton Usuario usando coordenadas guardadas"""
        try:
            coordenada = self.save_file.obtener_coordenada_componente("RadioButton", "User")
            if not coordenada:
                self.logger.info("📍 No hay coordenadas guardadas para RadioButton User")
                return False
            
            # Usar las coordenadas para hacer clic
            pyautogui.click(coordenada["x"], coordenada["y"])
            time.sleep(0.5)
            
            self.logger.info(f"✅ RadioButton 'User' seleccionado por coordenadas ({coordenada['x']}, {coordenada['y']})")
            self._actualizar_coordenada_usada("RadioButton", "User", coordenada.get("texto", ""))
        
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando RadioButton por coordenadas: {e}")
            return False

    def seleccionar_checkbox_por_coordenadas(self, identificador):
        """Selecciona un checkbox específico usando coordenadas guardadas"""
        try:
            coordenada = self.save_file.obtener_coordenada_componente("CheckBox", identificador)
            if not coordenada:
                self.logger.info(f"📍 No hay coordenadas guardadas para CheckBox {identificador}")
                return False
            
            # Obtener estado deseado desde CHECKBOXES_CONFIG
            texto_guardado = coordenada.get("texto", "")
            _, debe_estar_activo = self._identificar_checkbox_por_config(texto_guardado)
            
            if debe_estar_activo is None:
                self.logger.warning(f"⚠️ No se pudo determinar estado deseado para {identificador}")
                return False
            
            pyautogui.click(coordenada["x"], coordenada["y"])
            time.sleep(0.5)
            
            accion = "activado" if debe_estar_activo else "desactivado"
            self.logger.info(f"✅ CheckBox '{identificador}' {accion} por coordenadas ({coordenada['x']}, {coordenada['y']})")
            self._actualizar_coordenada_usada("CheckBox", identificador, texto_guardado)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando CheckBox {identificador} por coordenadas: {e}")
            return False
        
    def _actualizar_coordenada_usada(self, tipo_componente, identificador, texto):
        """Actualiza el timestamp de una coordenada que fue utilizada exitosamente"""
        try:
            # Crear nueva entrada con timestamp actualizado para mantener la coordenada fresca
            nueva_coordenada = {
                "x": self.save_file.obtener_coordenada_componente(tipo_componente, identificador)["x"],
                "y": self.save_file.obtener_coordenada_componente(tipo_componente, identificador)["y"],
                "rect": self.save_file.obtener_coordenada_componente(tipo_componente, identificador)["rect"],
                "texto": texto,
                "timestamp": str(datetime.now())
            }
            
            clave = f"{tipo_componente}_{identificador}"
            self.save_file.guardar_coordenadas({clave: nueva_coordenada})
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error actualizando coordenada {tipo_componente}_{identificador}: {e}")
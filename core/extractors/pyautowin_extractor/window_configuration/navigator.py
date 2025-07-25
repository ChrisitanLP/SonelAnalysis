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
            "CheckBox": ["AVG", "MIN", "MAX", "INSTANT"]
        }

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

            # Intentar usar coordenadas guardadas
            if self.seleccionar_radiobutton_usuario_por_coordenadas():
                self.logger.info("✅ Selección del radiobutton 'Usuario' realizada por coordenadas.")
                return [], {}

            # Si no existen coordenadas guardadas, hacer el proceso completo
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
        """Activa o desactiva checkboxes según configuración"""
        try:
            self.logger.info("☑️ Configurando checkboxes de filtros...")

            # Verificar si ya existe el archivo de configuración
            if os.path.exists("componentes_configuracion.json"):
                self.logger.info("📁 Información de componentes ya existe en 'componentes_configuracion.json'")
                
                # Verificar si tenemos coordenadas para los checkboxes necesarios
                checkboxes_pendientes = []
                for checkbox_id in self.componentes_requeridos["CheckBox"]:
                    if not self.save_file.obtener_coordenada_componente("CheckBox", checkbox_id):
                        checkboxes_pendientes.append(checkbox_id)
                
                # Si tenemos todas las coordenadas, usar coordenadas
                if not checkboxes_pendientes:
                    self.logger.info("📍 Usando coordenadas guardadas para checkboxes")
                    for checkbox_id in self.componentes_requeridos["CheckBox"]:
                        self.seleccionar_checkbox_por_coordenadas(checkbox_id)
                    return [], {}

            checkboxes = self.ventana_configuracion.descendants(control_type="CheckBox")
            elementos_configurados = {}
            checkboxes_encontrados = {}

            for checkbox in checkboxes:
                texto = checkbox.window_text().strip()
                debe_estar_activo = None
                checkbox_id = None

                # Identificar el checkbox y determinar si debe estar activo
                for config_text, estado_deseado in CHECKBOXES_CONFIG.items():
                    if (config_text.lower() in texto.lower() or
                            TextUtils.normalizar_texto(config_text) == TextUtils.normalizar_texto(texto)):
                        debe_estar_activo = estado_deseado
                        # Mapear a nuestros IDs estándar
                        if "avg" in config_text.lower() or "prom" in config_text.lower():
                            checkbox_id = "AVG"
                        elif "min" in config_text.lower():
                            checkbox_id = "MIN"
                        elif "max" in config_text.lower():
                            checkbox_id = "MAX"
                        elif "instant" in config_text.lower():
                            checkbox_id = "INSTANT"
                        break

                if debe_estar_activo is not None and checkbox_id:
                    try:
                        estado_actual = checkbox.get_toggle_state()

                        if debe_estar_activo and estado_actual != 1:
                            checkbox.toggle()
                            self.logger.info(f"✅ Activando '{texto}'")
                        elif not debe_estar_activo and estado_actual == 1:
                            checkbox.toggle()
                            self.logger.info(f"🚫 Desactivando '{texto}'")

                        # Guardar coordenada del checkbox encontrado
                        self.save_file.guardar_coordenada_componente(checkbox, "CheckBox", checkbox_id)
                        checkboxes_encontrados[checkbox_id] = checkbox
                        elementos_configurados[f"CheckBox_{texto}"] = "Configurado"
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error configurando '{texto}': {e}")

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

    def configurar_filtros_datos(self):
        """Ejecuta configuración completa de filtros: radio y checkboxes"""
        try:
            self.logger.info("⚙️ Configurando filtros de datos...")

            #if not self.wait_handler.esperar_controles_disponibles(
            #        self.ventana_configuracion, ["RadioButton", "CheckBox"], timeout=15):
            #    self.logger.error("❌ Timeout: Controles de filtros no disponibles")
            #    return False

            radios_resultado = self.configurar_radiobutton_usuario()
            radios = radios_resultado[0] if isinstance(radios_resultado, tuple) else []

            # Paso 2: Checkboxes
            checks, elementos_check = self.configurar_checkboxes_filtros()

            # Paso 3: Guardar información (solo si no existía)
            self.guardar_info_componentes(radios, checks)

            # Paso 4: Log final
            total_config = elementos_check.copy()
            if isinstance(radios_resultado, tuple):
                total_config.update(radios_resultado[1])
            self.logger.info(f"📊 Filtros: {len(total_config)} elementos configurados")

            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error configurando filtros: {e}")
            return False
        
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
            
            # Usar las coordenadas para hacer clic
            pyautogui.click(coordenada["x"], coordenada["y"])
            time.sleep(0.5)
            
            self.logger.info(f"✅ CheckBox '{identificador}' procesado por coordenadas ({coordenada['x']}, {coordenada['y']})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando CheckBox {identificador} por coordenadas: {e}")
            return False

import time
import logging
from config.logger import get_logger
from utils.text_normalize import TextUtils
from utils.wait_handler import WaitHandler
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

            # 1. Seleccionar RadioButton "Usuario" (multiidioma)
            user_translations = get_all_possible_translations('ui_controls', 'user')
            self.logger.info(f"🌐 Buscando 'Usuario' en: {user_translations}")

            # Esperar que los controles estén disponibles
            if not self.wait_handler.esperar_controles_disponibles(self.ventana_configuracion, 
                                                    ["RadioButton", "CheckBox"], 
                                                    timeout=15):
                self.logger.error("❌ Timeout: Controles de filtros no disponibles")
                return {}

            elementos_configurados = {}

            # 1. Seleccionar RadioButton "Usuario"
            radiobuttons = self.ventana_configuracion.descendants(control_type="RadioButton")
            for radio in radiobuttons:
                texto = radio.window_text().strip()
                texto_norm = TextUtils.normalizar_texto(texto)
                
                # Verificar coincidencia multiidioma
                if any(TextUtils.normalizar_texto(user_text) in texto_norm for user_text in user_translations):
                    try:
                        estado = radio.get_toggle_state()
                        if estado != 1:
                            radio.select()
                            self.logger.info(f"✅ RadioButton '{texto}' seleccionado")
                        elementos_configurados[f"RadioButton_{texto}"] = "Seleccionado"
                    except Exception as e:
                        self.logger.error(f"❌ Error seleccionando '{texto}': {e}")
            
            checkboxes = self.ventana_configuracion.descendants(control_type="CheckBox")
            for checkbox in checkboxes:
                texto = checkbox.window_text().strip()
                
                # Buscar coincidencia en configuración multiidioma
                debe_estar_activo = None
                for config_text, estado_deseado in CHECKBOXES_CONFIG.items():
                    if (config_text.lower() in texto.lower() or 
                        TextUtils.normalizar_texto(config_text) == TextUtils.normalizar_texto(texto)):
                        debe_estar_activo = estado_deseado
                        break
                
                if debe_estar_activo is not None:
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
import time
import logging

class SonelNavigator:
    """Maneja la navegación y filtros de la interfaz"""
    
    def __init__(self, ventana_configuracion):
        self.ventana_configuracion = ventana_configuracion
        
        # Configurar logger
        self.logger = logging.getLogger(f"{__name__}_navigator")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [NAVIGATOR] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

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
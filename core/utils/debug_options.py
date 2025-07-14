from config.logger import logger

class WindowDebugHelper:
    def __init__(self, parent_extractor):
        self.parent = parent_extractor

    def _debug_available_controls(self):
        """Método de debug para listar controles disponibles"""
        try:
            logger.info("🔍 DEBUG: Listando todos los controles disponibles...")
            all_controls = self.parent.current_analysis_window.descendants()
            
            control_types = {}
            for control in all_controls[:20]:  # Limitar a 20 para evitar spam
                try:
                    control_type = control.element_info.control_type
                    control_types[control_type] = control_types.get(control_type, 0) + 1
                except:
                    pass
            
            logger.info("📊 Tipos de controles encontrados:")
            for ctrl_type, count in control_types.items():
                logger.info(f"   - {ctrl_type}: {count}")

            logger.info("🧪 Textos de TreeItems disponibles:")
            for i, control in enumerate(self.parent.current_analysis_window.descendants(control_type="TreeItem")[:20]):
                try:
                    logger.info(f"  TreeItem[{i}]: '{control.window_text()}'")
                except:
                    logger.info(f"  TreeItem[{i}]: <sin texto>")
                
        except Exception as debug_error:
            logger.error(f"❌ Error en debug de controles: {debug_error}")

    def _debug_available_radiobuttons(self):
        """Debug para listar todos los RadioButtons disponibles"""
        try:
            logger.info("🔍 DEBUG: RadioButtons disponibles:")
            radiobuttons = self.parent.current_analysis_window.descendants(control_type="RadioButton")
            
            for i, rb in enumerate(radiobuttons[:10]):
                try:
                    text = rb.window_text().strip()
                    selected = rb.is_selected()
                    logger.info(f"   [{i}] '{text}' - {'Seleccionado' if selected else 'No seleccionado'}")
                except Exception as e:
                    logger.info(f"   [{i}] <Error obteniendo info: {e}>")
                    
        except Exception as e:
            logger.error(f"❌ Error en debug de RadioButtons: {e}")

    def _debug_available_checkboxes(self):
        """Debug para listar todos los CheckBoxes disponibles"""
        try:
            logger.info("🔍 DEBUG: CheckBoxes disponibles:")
            checkboxes = self.parent.current_analysis_window.descendants(control_type="CheckBox")
            
            for i, cb in enumerate(checkboxes[:10]):
                try:
                    text = cb.window_text().strip()
                    state = cb.get_toggle_state()
                    logger.info(f"   [{i}] '{text}' - {'Activado' if state else 'Desactivado'}")
                except Exception as e:
                    logger.info(f"   [{i}] <Error obteniendo info: {e}>")
                    
        except Exception as e:
            logger.error(f"❌ Error en debug de CheckBoxes: {e}")

    def _debug_available_groups(self):
        """Debug para listar todos los grupos disponibles y sus radiobuttons"""
        try:
            logger.info("🔍 DEBUG: Grupos disponibles:")
            groups = self.parent.current_analysis_window.descendants(control_type="Group")
            
            for i, group in enumerate(groups[:5]):
                try:
                    group_text = group.window_text().strip()
                    rect = group.rectangle()
                    logger.info(f"   Grupo [{i}] '{group_text}' - Pos: {rect}")
                    
                    radiobuttons_in_group = group.descendants(control_type="RadioButton")
                    for j, rb in enumerate(radiobuttons_in_group[:3]):
                        try:
                            rb_text = rb.window_text().strip()
                            rb_rect = rb.rectangle()
                            selected = rb.is_selected()
                            logger.info(f"     RadioButton [{j}] '{rb_text}' - Pos: {rb_rect} - {'Seleccionado' if selected else 'No seleccionado'}")
                        except Exception as e:
                            logger.info(f"     RadioButton [{j}] <Error: {e}>")
                            
                except Exception as e:
                    logger.info(f"   Grupo [{i}] <Error obteniendo info: {e}>")
                    
        except Exception as e:
            logger.error(f"❌ Error en debug de Grupos: {e}")

    def _debug_available_windows(self):
        """
        Método de debug para mostrar todas las ventanas disponibles
        """
        try:
            logger.debug("🐛 DEBUG: Listando todas las ventanas disponibles...")
            all_controls = self.parent.main_window.descendants()
            
            window_count = 0
            for control in all_controls:
                try:
                    title = control.window_text().strip()
                    control_type = control.control_type()
                    
                    if title and ("Análisis" in title or "Configuración" in title):
                        window_count += 1
                        logger.debug(f"🪟 Ventana {window_count}: '{title}' [{control_type}]")
                        
                except:
                    continue
                    
            if window_count == 0:
                logger.debug("🐛 No se encontraron ventanas con 'Análisis' o 'Configuración'")
                
        except Exception as e:
            logger.debug(f"🐛 Error en debug de ventanas: {e}")
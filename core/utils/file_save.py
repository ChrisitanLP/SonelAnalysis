# componentes_guardado.py
import os
import json
from pathlib import Path
from datetime import datetime
from config.settings import get_full_config, load_config

class ComponentesGuardado:
    def __init__(self, logger=None, ruta_salida="componentes_configuracion.json", ruta_coordenadas=None):
        self.logger = logger or self._get_default_logger()

        # Cargar configuración global
        config_file = 'config.ini'
        self.config = load_config(config_file)

        self.ruta_salida = ruta_salida
        self.ruta_coordenadas = ruta_coordenadas or os.path.join(self.config['PATHS']['output_dir'], "component_positions.json")
    
    def _get_default_logger(self):
        import logging
        logger = logging.getLogger("ComponentesGuardado")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def cargar_coordenadas_guardadas(self):
        """Carga las coordenadas guardadas del archivo persistente"""
        try:
            if os.path.exists(self.ruta_coordenadas):
                with open(self.ruta_coordenadas, "r", encoding="utf-8") as f:
                    coordenadas = json.load(f)
                self.logger.info(f"📁 Coordenadas cargadas desde '{self.ruta_coordenadas}'")
                return coordenadas
            else:
                self.logger.info(f"📄 Archivo de coordenadas '{self.ruta_coordenadas}' no existe, se creará")
                return {}
        except Exception as e:
            self.logger.error(f"❌ Error cargando coordenadas: {e}")
            return {}
    
    def guardar_coordenadas(self, nuevas_coordenadas):
        """Guarda o actualiza coordenadas sin perder datos existentes"""
        try:
            # Cargar coordenadas existentes
            coordenadas_actuales = self.cargar_coordenadas_guardadas()
            
            # Actualizar con las nuevas coordenadas
            coordenadas_actuales.update(nuevas_coordenadas)
            
            # Guardar el archivo actualizado
            with open(self.ruta_coordenadas, "w", encoding="utf-8") as f:
                json.dump(coordenadas_actuales, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"✅ Coordenadas actualizadas en '{self.ruta_coordenadas}'")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error guardando coordenadas: {e}")
            return False
    
    def obtener_coordenada_componente(self, tipo_componente, identificador):
        """Obtiene la coordenada de un componente específico"""
        coordenadas = self.cargar_coordenadas_guardadas()
        clave = f"{tipo_componente}_{identificador}"
        return coordenadas.get(clave)
    
    def tiene_coordenadas_necesarias(self, componentes_requeridos):
        """Verifica si todas las coordenadas necesarias están guardadas
        
        Args:
            componentes_requeridos: dict con formato {"tipo_componente": ["id1", "id2"]}
        """
        coordenadas = self.cargar_coordenadas_guardadas()
        
        for tipo, identificadores in componentes_requeridos.items():
            for identificador in identificadores:
                clave = f"{tipo}_{identificador}"
                if clave not in coordenadas:
                    self.logger.info(f"⚠️ Falta coordenada para: {clave}")
                    return False
        
        self.logger.info("✅ Todas las coordenadas necesarias están disponibles")
        return True
    
    def guardar_coordenada_componente(self, control, tipo_componente, identificador):
        """Guarda la coordenada de un componente individual"""
        try:
            coordenada = {
                "x": (control.rectangle().left + control.rectangle().right) // 2,
                "y": (control.rectangle().top + control.rectangle().bottom) // 2,
                "rect": {
                    "left": control.rectangle().left,
                    "top": control.rectangle().top,
                    "right": control.rectangle().right,
                    "bottom": control.rectangle().bottom
                },
                "texto": control.window_text().strip(),
                "timestamp": str(datetime.now()) if 'datetime' in globals() else "unknown"
            }
            
            clave = f"{tipo_componente}_{identificador}"
            nuevas_coordenadas = {clave: coordenada}
            
            return self.guardar_coordenadas(nuevas_coordenadas)
        except Exception as e:
            self.logger.error(f"❌ Error guardando coordenada de {tipo_componente}_{identificador}: {e}")
            return False
    
    def guardar_info_componentes(self, radiobuttons, checkboxes):
        """Guarda todos los componentes si el archivo aún no existe."""
        if os.path.exists(self.ruta_salida):
            self.logger.info(f"📁 Información de componentes ya existe en '{self.ruta_salida}'")
            return

        self.logger.info("📥 Guardando información de RadioButtons y CheckBoxes...")
        componentes = []
        componentes += self._procesar_controles(radiobuttons, "RadioButton")
        componentes += self._procesar_controles(checkboxes, "CheckBox")
        self._guardar_en_archivo(componentes)

    def guardar_radiobuttons(self, radiobuttons):
        """Agrega o actualiza solo RadioButtons en el archivo."""
        self.logger.info("🔘 Guardando información de RadioButtons...")
        nuevos = self._procesar_controles(radiobuttons, "RadioButton")
        self._merge_y_guardar(nuevos, tipo="RadioButton")

    def guardar_checkboxes(self, checkboxes):
        """Agrega o actualiza solo CheckBoxes en el archivo."""
        self.logger.info("☑️ Guardando información de CheckBoxes...")
        nuevos = self._procesar_controles(checkboxes, "CheckBox")
        self._merge_y_guardar(nuevos, tipo="CheckBox")

    def _procesar_controles(self, controles, tipo):
        """Extrae la información útil de una lista de controles."""
        componentes = []
        for control in controles:
            try:
                info = {
                    "tipo": tipo,
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
                self.logger.warning(f"⚠️ No se pudo obtener información de un {tipo}: {e}")
        return componentes

    def _guardar_en_archivo(self, componentes):
        try:
            with open(self.ruta_salida, "w", encoding="utf-8") as f:
                json.dump(componentes, f, indent=4, ensure_ascii=False)
            self.logger.info(f"✅ Información guardada en '{self.ruta_salida}'")
        except Exception as e:
            self.logger.error(f"❌ Error al guardar componentes: {e}")

    def _merge_y_guardar(self, nuevos_componentes, tipo):
        try:
            if os.path.exists(self.ruta_salida):
                with open(self.ruta_salida, "r", encoding="utf-8") as f:
                    existentes = json.load(f)
                existentes = [c for c in existentes if c["tipo"] != tipo]
            else:
                existentes = []

            todos = existentes + nuevos_componentes
            self._guardar_en_archivo(todos)
        except Exception as e:
            self.logger.error(f"❌ Error al actualizar componentes '{tipo}': {e}")

    def verificar_primera_ejecucion(self):
        """
        Verifica si es la primera ejecución basándose en la existencia de archivos de coordenadas.
        Retorna True si es la primera ejecución, False en caso contrario.
        """
        import os
        
        # Verificar si existe el archivo de coordenadas
        if os.path.exists(self.ruta_coordenadas):
            self.logger.info("📁 Archivo de coordenadas existe, no es primera ejecución")
            return False
        else:
            self.logger.info("🆕 Primera ejecución detectada, se capturarán coordenadas")
            return True
        
    def obtener_resumen_coordenadas_guardadas(self):
        """
        Retorna un resumen de las coordenadas guardadas
        """
        coordenadas = self.cargar_coordenadas_guardadas()
        
        resumen = {
            'total_componentes': len(coordenadas),
            'tipos_componentes': {},
            'componentes_por_tipo': {}
        }
        
        for clave, datos in coordenadas.items():
            # Extraer tipo del componente de la clave (formato: tipo_identificador)
            if '_' in clave:
                tipo = clave.split('_')[0]
                resumen['tipos_componentes'][tipo] = resumen['tipos_componentes'].get(tipo, 0) + 1
                
                if tipo not in resumen['componentes_por_tipo']:
                    resumen['componentes_por_tipo'][tipo] = []
                resumen['componentes_por_tipo'][tipo].append(clave)
        
        self.logger.info(f"📊 Resumen de coordenadas: {resumen['total_componentes']} componentes guardados")
        for tipo, cantidad in resumen['tipos_componentes'].items():
            self.logger.info(f"  📍 {tipo}: {cantidad} componentes")
        
        return resumen
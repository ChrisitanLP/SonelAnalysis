# componentes_guardado.py
import os
import json
import logging
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
    
    def detectar_cambio_idioma(self, ventana_configuracion, componentes_requeridos):
        """
        Detecta si ha ocurrido un cambio de idioma comparando los textos actuales
        con los textos guardados en las coordenadas.
        """
        try:
            # Si no existen coordenadas guardadas, no puede haber cambio de idioma
            if not os.path.exists(self.ruta_coordenadas):
                self.logger.info("📄 No hay coordenadas previas, no se puede detectar cambio de idioma")
                return False
                
            coordenadas = self.cargar_coordenadas_guardadas()
            
            # Verificar RadioButtons
            if "RadioButton" in componentes_requeridos:
                for identificador in componentes_requeridos["RadioButton"]:
                    clave = f"RadioButton_{identificador}"
                    if clave in coordenadas and self._verificar_componente_cambio_idioma(
                        ventana_configuracion, "RadioButton", coordenadas[clave]
                    ):
                        return True

            # Verificar CheckBoxes - MEJORADO para todos los tipos
            if "CheckBox" in componentes_requeridos:
                for identificador in componentes_requeridos["CheckBox"]:
                    clave = f"CheckBox_{identificador}"
                    if clave in coordenadas and self._verificar_componente_cambio_idioma(
                        ventana_configuracion, "CheckBox", coordenadas[clave]
                    ):
                        return True
            
            self.logger.info("✅ No se detectó cambio de idioma")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error detectando cambio de idioma: {e}")
            # En caso de error, asumir que hay cambio para forzar actualización
            return True
        
    def _verificar_componente_cambio_idioma(self, ventana_configuracion, tipo_componente, datos_guardados):
        """
        Verifica si un componente específico ha cambiado de idioma.
        
        Returns:
            bool: True si se detecta cambio de idioma
        """
        try:
            texto_guardado = datos_guardados.get("texto", "").strip()
            rect_guardado = datos_guardados["rect"]
            
            # Buscar componentes del tipo especificado
            controles = ventana_configuracion.descendants(control_type=tipo_componente)
            
            for control in controles:
                rect_actual = control.rectangle()
                
                # Comparar posición aproximada (tolerancia de ±20 pixels)
                if (abs(rect_actual.left - rect_guardado["left"]) <= 20 and
                    abs(rect_actual.top - rect_guardado["top"]) <= 20):
                    
                    texto_actual = control.window_text().strip()
                    if texto_actual != texto_guardado:
                        self.logger.info(f"🌐 Cambio de idioma detectado en {tipo_componente}: '{texto_guardado}' -> '{texto_actual}'")
                        return True
                    return False  # Mismo texto, no hay cambio
            
            # Si no se encuentra el componente en la posición esperada
            self.logger.info(f"🌐 Componente {tipo_componente} no encontrado en posición esperada, posible cambio de idioma")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando cambio de idioma para {tipo_componente}: {e}")
            return True

    def limpiar_coordenadas_componentes(self, componentes_requeridos):
        """
        Elimina las coordenadas de componentes específicos del archivo de coordenadas.
        
        Args:
            componentes_requeridos: dict con formato {"tipo_componente": ["id1", "id2"]}
        """
        try:
            coordenadas = self.cargar_coordenadas_guardadas()
            coordenadas_actualizadas = coordenadas.copy()
            
            componentes_eliminados = 0
            for tipo, identificadores in componentes_requeridos.items():
                for identificador in identificadores:
                    clave = f"{tipo}_{identificador}"
                    if clave in coordenadas_actualizadas:
                        del coordenadas_actualizadas[clave]
                        componentes_eliminados += 1
                        self.logger.info(f"🗑️ Coordenada eliminada: {clave}")
            
            if componentes_eliminados > 0:
                # Guardar archivo actualizado
                with open(self.ruta_coordenadas, "w", encoding="utf-8") as f:
                    json.dump(coordenadas_actualizadas, f, indent=4, ensure_ascii=False)
                
                self.logger.info(f"✅ Se eliminaron {componentes_eliminados} coordenadas del archivo")
            else:
                self.logger.info("ℹ️ No se encontraron coordenadas para eliminar")
                
        except Exception as e:
            self.logger.error(f"❌ Error limpiando coordenadas: {e}")
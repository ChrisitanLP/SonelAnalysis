import os
import time
import pyperclip
import pyautogui
from pywinauto import mouse
from datetime import datetime
from config.logger import get_logger
from core.utils.coordinates_utils import CoordinatesUtils

class GuiConfiguracion:
    """Maneja la vista de configuración de Sonel Analysis usando coordenadas GUI"""
    
    def __init__(self, coordinates):
        self.coordinates = coordinates
        self.app_reference = None
        
        # Logger específico
        self.logger = get_logger("gui_config", f"{__name__}_gui_config")
        
        # Configurar pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
        
        self.logger.info("🎛️ GuiConfiguracion iniciado")
    
    def conectar(self, app_reference):
        """
        Conecta con la referencia de la aplicación
        
        Args:
            app_reference: Referencia al proceso de la aplicación
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            self.app_reference = app_reference
            
            if not self.app_reference or self.app_reference.poll() is not None:
                self.logger.error("❌ Referencia de aplicación no válida")
                return False
            
            self.logger.info("✅ Conectado a la vista de configuración")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando a configuración: {e}")
            return False
    
    def extraer_navegacion_lateral_gui(self):
        """
        Extrae información de navegación lateral usando coordenadas
        
        Returns:
            bool: True si la extracción fue exitosa
        """
        try:
            self.logger.info("📋 Extrayendo navegación lateral...")
            
            # Buscar elementos de navegación lateral
            navigation_elements = [
                "CheckBox_select_all",
                "Button_expand_all"
            ]
            
            extraidos = 0
            for element_key in navigation_elements:
                if element_key in self.coordinates:
                    coord_info = self.coordinates[element_key]
                    texto = coord_info.get('texto', 'Sin texto')
                    x, y = CoordinatesUtils.get_coordinate_center(coord_info)
                    
                    self.logger.info(f"📍 {element_key}: '{texto}' en ({x}, {y})")
                    
                    pyautogui.moveTo(x, y)
                    pyautogui.click()

                    extraidos += 1
                    self.logger.info(f"✅ Elemento '{texto}' configurado")
                else:
                    self.logger.warning(f"⚠️ No se encontró coordenada para: {element_key}")
            
            self.logger.info(f"✅ Navegación lateral extraída: {extraidos} elementos")
            return extraidos > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo navegación lateral: {e}")
            return False
    
    def configurar_radiobutton_gui(self):
        """
        Configura radiobuttons usando coordenadas
        
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            self.logger.info("🔘 Configurando radiobuttons...")
            
            # Buscar RadioButton_User
            radio_key = "RadioButton_User"
            if radio_key not in self.coordinates:
                self.logger.warning(f"⚠️ No se encontró coordenada para: {radio_key}")
                return True  # No es crítico
            
            radio_coord = self.coordinates[radio_key]
            x, y = CoordinatesUtils.get_coordinate_center(radio_coord)
            texto = radio_coord.get('texto', 'User')
            
            self.logger.info(f"🎯 Seleccionando radiobutton '{texto}' en ({x}, {y})")
            
            # Hacer clic en el radiobutton
            pyautogui.click(x, y)
            time.sleep(2)
            
            self.logger.info("✅ Radiobutton configurado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando radiobutton: {e}")
            return False
    
    def configurar_checkboxes_gui(self):
        """
        Configura checkboxes usando coordenadas
        
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            self.logger.info("☑️ Configurando checkboxes...")
            
            # Lista de checkboxes a configurar
            checkbox_elements = [
                "CheckBox_MIN",
                "CheckBox_MAX", 
                "CheckBox_INSTANT"
            ]
            
            configurados = 0
            for checkbox_key in checkbox_elements:
                if checkbox_key in self.coordinates:
                    checkbox_coord = self.coordinates[checkbox_key]
                    x, y = CoordinatesUtils.get_coordinate_center(checkbox_coord)
                    texto = checkbox_coord.get('texto', checkbox_key)
                    
                    self.logger.info(f"🎯 Marcando checkbox '{texto}' en ({x}, {y})")
                    
                    # Hacer clic en el checkbox
                    pyautogui.click(x, y)
                    time.sleep(0.5)
                    configurados += 1
                else:
                    self.logger.warning(f"⚠️ No se encontró coordenada para: {checkbox_key}")
            
            self.logger.info(f"✅ Checkboxes configurados: {configurados}")
            return configurados > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando checkboxes: {e}")
            return False
    
    def extraer_configuracion_principal_mediciones_gui(self):
        """
        Extrae configuración principal de mediciones usando coordenadas
        
        Returns:
            bool: True si la extracción fue exitosa
        """
        try:
            self.logger.info("📊 Extrayendo configuración principal de mediciones...")
            time.sleep(3)

            # Buscar checkbox principal de mediciones
            main_checkbox_key = "CheckBox_measurements_0"
            if main_checkbox_key in self.coordinates:
                checkbox_coord = self.coordinates[main_checkbox_key]
                x, y = CoordinatesUtils.get_coordinate_center(checkbox_coord)
                texto = checkbox_coord.get('texto', 'Measurements')
                
                self.logger.info(f"📍 Mediciones principales: '{texto}' en ({x}, {y})")
                
                # Hacer clic para expandir/activar mediciones
                pyautogui.click(x, y)
                time.sleep(2)
                
                self.logger.info("✅ Configuración principal de mediciones extraída")
                return True
            else:
                self.logger.warning("⚠️ No se encontró checkbox principal de mediciones")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo configuración de mediciones: {e}")
            return False
    
    def extraer_componentes_arbol_mediciones_gui(self):
        """
        Extrae componentes del árbol de mediciones usando coordenadas y scroll.
        Realiza clic en el borde izquierdo centrado verticalmente.
        
        Returns:
            bool: True si la extracción fue exitosa
        """
        try:
            self.logger.info("🌳 Extrayendo componentes del árbol de mediciones...")

            tree_elements = [key for key in self.coordinates.keys() 
                            if key.startswith("TreeItem_componentes_mediciones")]

            if not tree_elements:
                self.logger.warning("⚠️ No se encontraron elementos del árbol de mediciones")
                return False

            # Función modificada: cálculo del centro del scroll (sin cambios)
            def calcular_area_scroll_coordenadas():
                xs = []
                ys = []
                for key in tree_elements:
                    coord = self.coordinates[key]
                    if 'rect' in coord:
                        rect = coord['rect']
                        center_x = (rect['left'] + rect['right']) // 2
                        center_y = (rect['top'] + rect['bottom']) // 2
                        xs.append(center_x)
                        ys.append(center_y)
                if not xs or not ys:
                    return 250, 560  # fallback

                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                x_center = (min_x + max_x) // 2
                y_center = (min_y + max_y) // 2

                self.logger.info(f"📐 Área TreeView desde coordenadas: X={min_x}-{max_x}, Y={min_y}-{max_y}")
                self.logger.info(f"🎯 Centro estimado para scroll: ({x_center}, {y_center})")
                return x_center, y_center

            def realizar_scroll_inteligente(x_scroll, y_scroll, direccion=-3):
                try:
                    mouse.move(coords=(x_scroll, y_scroll))
                    time.sleep(0.1)
                    mouse.scroll(coords=(x_scroll, y_scroll), wheel_dist=direccion)
                    time.sleep(0.5)
                    self.logger.info(f"🔄 Scroll realizado en ({x_scroll}, {y_scroll}) con distancia {direccion}")
                    return True
                except Exception as e:
                    self.logger.error(f"❌ Error realizando scroll: {e}")
                    return False

            x_scroll, y_scroll = calcular_area_scroll_coordenadas()

            extraidos = 0
            intentos_scroll = 0
            max_intentos = 10
            visitados = set()
            screen_height = pyautogui.size().height

            while extraidos < len(tree_elements) and intentos_scroll < max_intentos:
                for element_key in tree_elements:
                    if element_key in visitados:
                        continue

                    coord_info = self.coordinates[element_key]
                    texto = coord_info.get('texto', 'Sin texto')

                    # 🔧 NUEVO: obtener punto en borde izquierdo centrado verticalmente
                    if 'rect' in coord_info:
                        rect = coord_info['rect']
                        x = rect['left'] + 3  # offset leve para evitar bordes duros
                        y = (rect['top'] + rect['bottom']) // 2
                    else:
                        x, y = CoordinatesUtils.get_coordinate_center(coord_info)  # fallback

                    if 0 < y < screen_height:
                        self.logger.info(f"📍 {element_key}: '{texto}' en ({x}, {y}) [clic lateral centrado]")
                        pyautogui.moveTo(x, y)
                        pyautogui.click()
                        time.sleep(0.3)
                        extraidos += 1
                        visitados.add(element_key)
                    else:
                        self.logger.info(f"🔍 {element_key} no visible aún (Y={y}), se intentará scroll.")

                if extraidos < len(tree_elements):
                    realizar_scroll_inteligente(x_scroll, y_scroll, direccion=-3)
                    intentos_scroll += 1

            self.logger.info(f"✅ Componentes del árbol extraídos: {extraidos}")
            return extraidos > 0

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo componentes del árbol: {e}")
            return False
    
    def extraer_tabla_mediciones_gui(self):
        """
        Extrae información de la tabla de mediciones usando coordenadas
        
        Returns:
            bool: True si la extracción fue exitosa
        """
        try:
            self.logger.info("📋 Extrayendo tabla de mediciones...")

            table_key = "Table_table_0"
            if table_key in self.coordinates:
                table_coord = self.coordinates[table_key]

                if 'rect' in table_coord:
                    rect = table_coord['rect']
                    x = rect['left'] + 3  # offset para evitar bordes exactos
                    y = rect['top']

                    self.logger.info(f"📍 Tabla encontrada: esquina superior izquierda en ({x}, {y})")

                    # Hacer clic en la esquina superior izquierda para activarla
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                    time.sleep(2)

                    self.logger.info("✅ Tabla de mediciones seleccionada correctamente")
                    return True
                else:
                    self.logger.warning("⚠️ No se encontró rectángulo delimitador en la coordenada de la tabla")
                    return False
            else:
                self.logger.warning("⚠️ No se encontró la coordenada 'Table_table_0'")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo tabla de mediciones: {e}")
            return False
    
    def extraer_informes_graficos_gui(self):
        """
        Extrae información de informes gráficos usando coordenadas
        
        Returns:
            bool: True si la extracción fue exitosa
        """
        try:
            self.logger.info("📈 Extrayendo informes gráficos...")
            
            # Buscar botón de reportes
            reports_button_key = "Button_reports_0"
            if reports_button_key in self.coordinates:
                reports_coord = self.coordinates[reports_button_key]
                x, y = CoordinatesUtils.get_coordinate_center(reports_coord)
                texto = reports_coord.get('texto', 'Reports')
                
                self.logger.info(f"🎯 Haciendo clic en '{texto}' en ({x}, {y})")
                
                # Hacer clic en reportes
                pyautogui.click(x, y)
                time.sleep(3)

                new_y = y + 50
                self.logger.info(f"🖱️ Haciendo segundo clic en coordenada desplazada ({x}, {new_y})")
                pyautogui.click(x, new_y)
                time.sleep(3)
                
                self.logger.info("✅ Informes gráficos extraídos")
                return True
            else:
                self.logger.warning("⚠️ No se encontró botón de reportes")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo informes gráficos: {e}")
            return False
    
    def guardar_archivo_csv(self, expected_csv_path: str):
        """
        Guarda el archivo CSV usando coordenadas para la interfaz

        Args:
            expected_csv_path: Ruta esperada del archivo CSV

        Returns:
            bool: True si el guardado fue exitoso
        """
        try:
            self.logger.info(f"💾 Guardando archivo CSV: {expected_csv_path}")

            name_field_key = "EditWrapper_nombre_archivo"
            save_button_key = "ButtonWrapper_boton_guardar"

            if name_field_key not in self.coordinates or save_button_key not in self.coordinates:
                self.logger.error("❌ No se encontraron elementos necesarios para guardar")
                return False

            # === Nombre limpio del archivo ===
            nombre_archivo = expected_csv_path

            # ✅ Normalizar nombre del archivo
            nombre_archivo = nombre_archivo.strip()

            # Extraer carpeta y nombre
            carpeta = os.path.dirname(nombre_archivo)
            nombre = os.path.basename(nombre_archivo)
            
            if "." in nombre:
                partes = nombre.split(".")
                nombre_sin_puntos = "".join(partes[:-1])
                extension = partes[-1]
                nombre = f"{nombre_sin_puntos}.{extension}"
            else:
                self.logger.warning("⚠️ El nombre del archivo no contenía una extensión explícita.")

            nombre_final = self._aplicar_numeracion_incremental_csv(carpeta, nombre)
            archivo_a_guardar = os.path.join(carpeta, nombre_final)

            # Logs para debugging
            self.logger.info(f"   📁 Ruta base: {carpeta}")
            self.logger.info(f"   📄 Nombre sanitizado: {nombre}")
            self.logger.info(f"   📄 Nombre final (con numeración si aplica): {nombre_final}")
            self.logger.info(f"   💾 Guardando como: {archivo_a_guardar}")


            pyperclip.copy(archivo_a_guardar)
            self.logger.info(f"📝 Nombre normalizado y copiado: {archivo_a_guardar}")

            # === Clic en el campo de nombre ===
            name_coord = self.coordinates[name_field_key]
            x, y = CoordinatesUtils.get_coordinate_center(name_coord)
            self.logger.info(f"🎯 Haciendo clic en campo nombre en ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(0.9)

            # Limpiar y pegar
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.9)

            # === Clic en botón guardar ===
            save_coord = self.coordinates[save_button_key]
            x, y = CoordinatesUtils.get_coordinate_center(save_coord)
            self.logger.info(f"🎯 Haciendo clic en 'Guardar' en ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(4)

            self.logger.info("✅ Comando de guardado ejecutado")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error guardando archivo CSV: {e}")
            return False
    
    def get_coordinates_summary(self):
        """
        Obtiene un resumen de las coordenadas disponibles
        
        Returns:
            dict: Resumen de coordenadas
        """
        return CoordinatesUtils.get_coordinates_summary(self.coordinates)
    

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
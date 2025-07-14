import re
import time
import logging
import os
import traceback
import pyautogui
import pyperclip
from config.logger import logger
from time import sleep
from datetime import datetime
from pywinauto import Desktop, mouse, findwindows
from pywinauto import Application
from pyautogui import click, moveTo, position
from pywinauto.mouse import move
from pywinauto.keyboard import send_keys
from pynput.mouse import Button, Listener as MouseListener
from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper

class SonelAnalisisInicial:
    """Clase especializada para manejar la vista inicial de análisis"""
    
    def __init__(self, parent_extractor):
        """
        Inicializa la clase con referencia al extractor principal
        
        Args:
            parent_extractor: Instancia del PywinautoExtractor principal
        """
        self.parent_extractor = parent_extractor
        self.archivo_pqm = parent_extractor.archivo_pqm
        self.ruta_exe = parent_extractor.sonel_exe_path
        self.delays = parent_extractor.delays
        
        self.app = None
        self.ventana_inicial = None

        logger.info("="*60)
        logger.info("🎯 EXTRACTOR VISTA INICIAL - SONEL ANALYSIS")
        logger.info(f"📁 Archivo PQM: {self.archivo_pqm}")
        logger.info("="*60)

    def conectar(self):
        """Conecta con la vista inicial de análisis"""
        try:
            logger.info("🔍 Conectando con vista inicial...")
            
            # Establecer conexión con la aplicación
            try:
                self.app = Application(backend="uia").connect(title_re=".*Análisis.*")
                logger.info("✅ Conectado con aplicación existente")
            except:
                logger.info("🚀 Iniciando nueva instancia...")
                self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                time.sleep(10)
            
            # Obtener ventana inicial específica
            try:
                main_window = self.app.top_window()
                main_window.set_focus()
                
                # Buscar ventana que NO termine en "Configuración 1"
                windows = main_window.descendants(control_type="Window")
                for window in windows:
                    try:
                        title = window.window_text()
                        if ("Análisis" in title and ".pqm" in title and title.strip() 
                            and not title.strip().endswith("Configuración 1")):
                            self.ventana_inicial = window
                            logger.info(f"✅ Vista inicial encontrada: {title}")
                            return True
                    except Exception:
                        continue
                
                # Fallback: usar ventana principal si cumple criterios
                main_title = main_window.window_text()
                if ("Análisis" in main_title and ".pqm" in main_title and main_title.strip() 
                    and not main_title.strip().endswith("Configuración 1")):
                    self.ventana_inicial = main_window
                    logger.info(f"✅ Vista inicial (main): {main_title}")
                    return True
                
                logger.error("❌ No se encontró vista inicial")
                return False
                
            except Exception as window_error:
                logger.error(f"❌ Error obteniendo ventana: {window_error}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error conectando vista inicial: {e}")
            return False

    def navegar_configuracion(self):
        """Navega al árbol de configuración y expande 'Configuración 1'"""
        try:
            logger.info("🌳 Navegando árbol de configuración...")
            
            if not self.ventana_inicial:
                logger.error("❌ No hay ventana inicial conectada")
                return False
            
            # Buscar TreeItem con "Configuración 1"
            tree_controls = self.ventana_inicial.descendants(control_type="TreeItem")
            
            for tree in tree_controls:
                texto = tree.window_text()
                if "Configuración 1" in texto or "Configuration 1" in texto:
                    logger.info(f"✅ TreeItem encontrado: {texto}")
                    return self._expandir_configuracion(tree)
            
            logger.error("❌ TreeItem 'Configuración 1' no encontrado")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error navegando configuración: {e}")
            return False

    def _expandir_configuracion(self, config_item):
        """Expande el elemento de configuración"""
        try:
            rect = config_item.rectangle()
            center_x = (rect.left + rect.right) // 2
            center_y = (rect.top + rect.bottom) // 2
            
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)
            
            logger.info(f"🔓 Click en configuración ({center_x}, {center_y})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error expandiendo configuración: {e}")
            return False

    def ejecutar_analisis(self):
        """Hace clic en el botón 'Análisis de datos'"""
        try:
            logger.info("🎯 Ejecutando análisis de datos...")
            
            # Buscar botón "Análisis de datos"
            buttons = self.ventana_inicial.descendants(control_type="Button", title="Análisis de datos")
            if not buttons:
                buttons = self.ventana_inicial.descendants(control_type="Button", title="Data Analysis")
            
            if buttons:
                analysis_button = buttons[0]
                analysis_button.click()
                time.sleep(2)  # Esperar a que se abra la ventana de configuración
                
                logger.info("✅ Análisis de datos ejecutado")
                return True
            else:
                logger.error("❌ Botón 'Análisis de datos' no encontrado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando análisis: {e}")
            return False

    def get_app_reference(self):
        """Retorna la referencia de la aplicación para usar en la segunda clase"""
        return self.app
    
    def configuracion_primera_ventana(self):
        """
        Configura la primera ventana de análisis con las opciones requeridas
        
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            # Esperar a que aparezca la nueva ventana
            logger.info("⏳ Esperando carga de ventana de análisis...")
            time.sleep(self.delays['window_activation'])
            
            # FASE 1: Vista inicial
            logger.info("\n--- FASE 1: VISTA INICIAL ---")

            if not self.conectar():
                logger.error("❌ Error conectando vista inicial")
                return None
            
            if not self.navegar_configuracion():
                logger.error("❌ Error navegando configuración")
                return None
            
            if not self.ejecutar_analisis():
                logger.error("❌ Error ejecutando análisis")
                return None
            
            logger.info("✅ Configuración de primera ventana completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando primer ventana: {e}")
            logger.error(f"❌ Detalles del error: {type(e).__name__}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
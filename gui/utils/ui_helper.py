from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox

class UIHelpers:
    """Utilidades de interfaz con estilo empresarial moderno."""
    
    @staticmethod
    def warn_select_folder(parent):
        """
        Muestra una alerta indicando que se debe seleccionar una carpeta.
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Selección de Carpeta Requerida")
        msg.setText("Selecciona una carpeta antes de continuar")
        msg.setInformativeText("Para proceder con la operación, primero debes seleccionar una carpeta que contenga archivos .pqm702")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        # Aplicar estilo según el tema actual
        UIHelpers._apply_message_box_theme(msg, parent)
        
        msg.exec_()
    
    @staticmethod
    def show_success_message(parent, title, message, details=None):
        """
        Muestra un mensaje de éxito con estilo empresarial.
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setInformativeText(details)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        UIHelpers._apply_message_box_theme(msg, parent)
        msg.exec_()
    
    @staticmethod
    def show_error_message(parent, title, message, details=None):
        """
        Muestra un mensaje de error con estilo empresarial.
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setInformativeText(details)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        UIHelpers._apply_message_box_theme(msg, parent)
        msg.exec_()
    
    @staticmethod
    def show_confirmation_dialog(parent, title, message, details=None):
        """
        Muestra un diálogo de confirmación con estilo empresarial.
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setInformativeText(details)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        UIHelpers._apply_message_box_theme(msg, parent)
        
        return msg.exec_() == QMessageBox.Yes
    
    @staticmethod
    def show_info_message(parent, title, message, details=None):
        """
        Muestra un diálogo de información con estilo empresarial.
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setInformativeText(details)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)

        # Aplicar estilo corporativo/empresarial
        UIHelpers._apply_message_box_theme(msg, parent)

        msg.exec_()
    
    @staticmethod
    def _apply_message_box_theme(msg, parent):
        """
        Aplica el tema (claro/oscuro) al QMessageBox según el tema actual del parent.
        MODIFICACIÓN: En modo oscuro, NO aplica estilos para mantener legibilidad.
        """
        try:
            # Obtener el estado del tema del parent
            is_dark_mode = getattr(parent, 'is_dark_mode', False)
            
            if is_dark_mode:
                # MODO OSCURO: NO aplicar estilos personalizados
                # Los cuadros de diálogo mantendrán su apariencia nativa del sistema
                # para garantizar la legibilidad
                pass
            else:
                # MODO CLARO: Aplicar estilo empresarial personalizado
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #ffffff;
                        color: #212121;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 14px;
                    }
                    
                    QMessageBox QLabel {
                        color: #212121;
                        font-size: 14px;
                        padding: 10px;
                    }
                    
                    QMessageBox QPushButton {
                        background-color: #1976D2;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 20px;
                        font-size: 13px;
                        font-weight: 600;
                        min-width: 80px;
                    }
                    
                    QMessageBox QPushButton:hover {
                        background-color: #1565C0;
                    }
                    
                    QMessageBox QPushButton:pressed {
                        background-color: #0d47a1;
                    }
                    
                    QMessageBox QPushButton:default {
                        background-color: #1976D2;
                        border: 2px solid #42A5F5;
                    }
                    
                    QMessageBox QLabel#qt_msgbox_label {
                        font-weight: 600;
                        font-size: 15px;
                        color: #212121;
                    }
                    
                    QMessageBox QLabel#qt_msgbox_informativelabel {
                        font-weight: 400;
                        font-size: 13px;
                        color: #666666;
                    }
                """)
            
            # Configurar fuente solo para modo claro
            if not is_dark_mode:
                font = QFont("Segoe UI", 10)
                msg.setFont(font)
            
        except Exception as e:
            # En caso de error, no aplicar ningún estilo
            print(f"Error aplicando tema al MessageBox: {e}")
            pass
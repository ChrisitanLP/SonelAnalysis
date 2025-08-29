from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel

class ModernCard(QFrame):
    """Widget personalizado para crear tarjetas modernas"""
    def __init__(self, title="", content_widget=None, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("ModernCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            layout.addWidget(title_label)
        
        if content_widget:
            layout.addWidget(content_widget)
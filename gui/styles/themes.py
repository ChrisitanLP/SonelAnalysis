class ThemeManager:
    """Gestor de temas con estilo empresarial moderno y paleta de colores profesional."""
    
    def __init__(self):
        pass

    def get_stylesheet(self, is_dark_mode):
        """Aplicar tema claro u oscuro con estilo empresarial moderno"""

        if is_dark_mode:
            return self._get_dark_theme()
        else:
            return self._get_light_theme()

    def _get_dark_theme(self):
        """Tema oscuro empresarial con gradientes y sombras"""

        return """
            QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QWidget {
                    color: #ffffff;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QFrame#HeaderFrame {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 16px;
                }
                
                QFrame#ContentFrame {
                    background-color: transparent;
                }
                
                QFrame#FooterFrame {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QWidget#ControlPanel {
                    background-color: transparent;
                }
                
                QWidget#StatusPanel {
                    background-color: transparent;
                }
                
                QFrame#ModernCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QFrame#StatusCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QLabel#MainTitle {
                    font-size: 28px;
                    font-weight: 700;
                    color: #ffffff;
                    margin-bottom: -8px;
                }
                
                QLabel#Subtitle {
                    font-size: 14px;
                    color: #b0b0b0;
                    font-weight: 400;
                }
                
                QLabel#Description {
                    font-size: 12px;
                    color: #888888;
                    margin-top: 8px;
                }
                
                QLabel#CardTitle {
                    font-size: 16px;
                    font-weight: 600;
                    color: #ffffff;
                }
                
                QLabel#StatusTitle {
                    font-size: 12px;
                    color: #b0b0b0;
                    font-weight: 500;
                }
                
                QLabel#FolderInfo {
                    font-size: 13px;
                    color: #b0b0b0;
                    padding: 12px;
                    background-color: #3d3d3d;
                    border: 1px solid #505050;
                    border-radius: 8px;
                }
                
                QLabel#ProgressLabel {
                    font-size: 13px;
                    color: #b0b0b0;
                    font-weight: 500;
                }
                
                QLabel#SummaryLabel {
                    font-size: 12px;
                    line-height: 1.5;
                    color: #ffffff;
                }
                
                QLabel#SystemInfo, QLabel#VersionInfo {
                    color: #888888;
                    font-size: 11px;
                    font-weight: 500;
                }
                
                QLabel#ConnectionStatus {
                    color: #4CAF50;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 10px 18px;
                    background-color: rgba(76, 175, 80, 0.15);
                    border-radius: 6px;
                }
                
                QToolButton#ThemeButton {
                    background-color: transparent;
                    color: #ffffff;
                    border: 2px solid #505050;
                    border-radius: 8px;
                    padding: 1px 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                QToolButton#ThemeButton:hover {
                    background-color: #3d3d3d;
                    border-color: #1976D2;
                }
                
                QPushButton#ActionButton_primary {
                    background-color: #1976D2;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_primary:hover {
                    background-color: #1565C0;
                }
                
                QPushButton#ActionButton_secondary {
                    background-color: transparent;
                    color: #ffffff;
                    border: 2px solid #505050;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_secondary:hover {
                    background-color: #3d3d3d;
                    border-color: #1976D2;
                }
                
                QProgressBar#ProgressBar {
                    background-color: #3d3d3d;
                    border: none;
                    border-radius: 6px;
                    text-align: center;
                    color: #ffffff;
                }
                
                QProgressBar#ProgressBar::chunk {
                    background-color: #1976D2;
                    border-radius: 6px;
                }
                
                QTextEdit#LogText {
                    background-color: #2d2d2d;
                    border: 1px solid #505050;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    color: #ffffff;
                }

                QWidget#GeneralHeader {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QWidget#StatusContainer {
                    background-color: #1976D2;
                    border-radius: 12px;
                }
                
                QLabel#MainStatusLabel {
                    color: #ffffff;
                    font-size: 18px;
                    font-weight: 700;
                }
                
                QLabel#MainStatusDetail {
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 14px;
                    font-weight: 500;
                }
                
                QWidget#KeyMetricsContainer {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QWidget#KeyMetricWidget {
                    background-color: #3d3d3d;
                    border: 1px solid #505050;
                    border-radius: 8px;
                }
                
                QWidget#KeyMetricWidget:hover {
                    background-color: #4d4d4d;
                    border-color: #1976D2;
                }
                
                QLabel#KeyMetricValue {
                    font-size: 20px;
                    font-weight: 700;
                    text-align: center;
                }
                
                QLabel#KeyMetricDescription {
                    color: #b0b0b0;
                    font-size: 11px;
                    font-weight: 500;
                    text-align: center;
                }
                
                QFrame#DetailedMetricsCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QWidget#CompactMetricCard {
                    background-color: #3d3d3d;
                    border: 1px solid #505050;
                    border-radius: 8px;
                }
                
                QWidget#CompactMetricCard:hover {
                    background-color: #4d4d4d;
                    border-color: #1976D2;
                }
                
                QLabel#MetricIcon {
                    font-size: 16px;
                    text-align: center;
                }
                
                QLabel#CompactMetricTitle {
                    color: #b0b0b0;
                    font-size: 10px;
                    font-weight: 500;
                }
                
                QLabel#CompactMetricValue {
                    font-size: 13px;
                    font-weight: 600;
                }
                
                QFrame#PerformanceCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QLabel#ProgressMetricLabel {
                    color: #b0b0b0;
                    font-size: 12px;
                    font-weight: 500;
                }
                
                QLabel#ProgressValueLabel {
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: 600;
                    text-align: right;
                }
                
                QFrame#ActivityLogCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QLabel#LogStatus {
                    color: #4CAF50;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                QTextEdit#ActivityLogText {
                    background-color: #1e1e1e;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    color: #ffffff;
                }
                
                QFrame#ExecutiveSummaryCard {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
                
                QTabWidget#SummaryTabs {
                    background-color: transparent;
                    border: none;
                }
                
                QTabWidget#SummaryTabs::pane {
                    background-color: transparent;
                    border: none;
                }
                
                QTabWidget#SummaryTabs QTabBar::tab {
                    background-color: #3d3d3d;
                    color: #b0b0b0;
                    border: 1px solid #505050;
                    border-bottom: none;
                    border-radius: 6px 6px 0 0;
                    padding: 8px 16px;
                    margin-right: 2px;
                    font-size: 12px;
                    font-weight: 500;
                }
                
                QTabWidget#SummaryTabs QTabBar::tab:selected {
                    background-color: #1976D2;
                    color: #ffffff;
                    border-color: #1976D2;
                }
                
                QTabWidget#SummaryTabs QTabBar::tab:hover:!selected {
                    background-color: #4d4d4d;
                    border-color: #606060;
                }
                
                QLabel#SummaryContent {
                    color: #ffffff;
                    font-size: 12px;
                    line-height: 1.6;
                }
            """

    def _get_light_theme(self):
        """Tema claro empresarial con gradientes y sombras"""
        
        return """
            QMainWindow {
                    background-color: #f5f6f7;
                    color: #212121;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QWidget {
                    color: #212121;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                
                QFrame#HeaderFrame {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 16px;
                }
                
                QFrame#ContentFrame {
                    background-color: transparent;
                }
                
                QFrame#FooterFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QWidget#ControlPanel {
                    background-color: transparent;
                }
                
                QWidget#StatusPanel {
                    background-color: transparent;
                }
                
                QFrame#ModernCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QFrame#StatusCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QLabel#MainTitle {
                    font-size: 28px;
                    font-weight: 700;
                    color: #212121;
                    margin-bottom: -8px;
                }
                
                QLabel#Subtitle {
                    font-size: 14px;
                    color: #666666;
                    font-weight: 400;
                }
                
                QLabel#Description {
                    font-size: 12px;
                    color: #9e9e9e;
                    margin-top: 8px;
                }
                
                QLabel#CardTitle {
                    font-size: 16px;
                    font-weight: 600;
                    color: #212121;
                }
                
                QLabel#StatusTitle {
                    font-size: 12px;
                    color: #666666;
                    font-weight: 500;
                }
                
                QLabel#FolderInfo {
                    font-size: 13px;
                    color: #666666;
                    padding: 12px;
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                }
                
                QLabel#ProgressLabel {
                    font-size: 13px;
                    color: #666666;
                    font-weight: 500;
                }
                
                QLabel#SummaryLabel {
                    font-size: 12px;
                    line-height: 1.5;
                    color: #212121;
                }
                
                QLabel#SystemInfo, QLabel#VersionInfo {
                    color: #9e9e9e;
                    font-size: 11px;
                    font-weight: 500;
                }
                
                QLabel#ConnectionStatus {
                    color: #4CAF50;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 10px 18px;
                    background-color: rgba(76, 175, 80, 0.1);
                    border-radius: 6px;
                }
                
                QToolButton#ThemeButton {
                    background-color: transparent;
                    color: #212121;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 1px 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                QToolButton#ThemeButton:hover {
                    background-color: #f5f5f5;
                    border-color: #1976D2;
                }
                
                QPushButton#ActionButton_primary {
                    background-color: #1976D2;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_primary:hover {
                    background-color: #1565C0;
                }
                
                QPushButton#ActionButton_secondary {
                    background-color: transparent;
                    color: #212121;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                
                QPushButton#ActionButton_secondary:hover {
                    background-color: #f5f5f5;
                    border-color: #1976D2;
                }
                
                QProgressBar#ProgressBar {
                    background-color: #f0f0f0;
                    border: none;
                    border-radius: 6px;
                    text-align: center;
                    color: #212121;
                }
                
                QProgressBar#ProgressBar::chunk {
                    background-color: #1976D2;
                    border-radius: 6px;
                }
                
                QTextEdit#LogText {
                    background-color: #fafafa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    color: #212121;
                }

                QWidget#GeneralHeader {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QWidget#StatusContainer {
                    background-color: #1976D2;
                    border-radius: 12px;
                }
                
                QLabel#MainStatusLabel {
                    color: #ffffff;
                    font-size: 18px;
                    font-weight: 700;
                }
                
                QLabel#MainStatusDetail {
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 14px;
                    font-weight: 500;
                }
                
                QWidget#KeyMetricsContainer {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QWidget#KeyMetricWidget {
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                }
                
                QWidget#KeyMetricWidget:hover {
                    background-color: #f0f2f5;
                    border-color: #1976D2;
                }
                
                QLabel#KeyMetricValue {
                    font-size: 20px;
                    font-weight: 700;
                    text-align: center;
                }
                
                QLabel#KeyMetricDescription {
                    color: #666666;
                    font-size: 11px;
                    font-weight: 500;
                    text-align: center;
                }
                
                QFrame#DetailedMetricsCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QWidget#CompactMetricCard {
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                }
                
                QWidget#CompactMetricCard:hover {
                    background-color: #f0f2f5;
                    border-color: #1976D2;
                }
                
                QLabel#MetricIcon {
                    font-size: 16px;
                    text-align: center;
                }
                
                QLabel#CompactMetricTitle {
                    color: #666666;
                    font-size: 10px;
                    font-weight: 500;
                }
                
                QLabel#CompactMetricValue {
                    font-size: 13px;
                    font-weight: 600;
                }
                
                QFrame#PerformanceCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QLabel#ProgressMetricLabel {
                    color: #666666;
                    font-size: 12px;
                    font-weight: 500;
                }
                
                QLabel#ProgressValueLabel {
                    color: #212121;
                    font-size: 11px;
                    font-weight: 600;
                    text-align: right;
                }
                
                QFrame#ActivityLogCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QLabel#LogStatus {
                    color: #4CAF50;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                QTextEdit#ActivityLogText {
                    background-color: #fafafa;
                    border: 1px solid #e1e5e9;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    color: #212121;
                }
                
                QFrame#ExecutiveSummaryCard {
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 12px;
                }
                
                QTabWidget#SummaryTabs {
                    background-color: transparent;
                    border: none;
                }
                
                QTabWidget#SummaryTabs::pane {
                    background-color: transparent;
                    border: none;
                }
                
                QTabWidget#SummaryTabs QTabBar::tab {
                    background-color: #f8f9fa;
                    color: #666666;
                    border: 1px solid #e1e5e9;
                    border-bottom: none;
                    border-radius: 6px 6px 0 0;
                    padding: 8px 16px;
                    margin-right: 2px;
                    font-size: 12px;
                    font-weight: 500;
                }
                
                QTabWidget#SummaryTabs QTabBar::tab:selected {
                    background-color: #1976D2;
                    color: #ffffff;
                    border-color: #1976D2;
                }
                
                QTabWidget#SummaryTabs QTabBar::tab:hover:!selected {
                    background-color: #f0f2f5;
                    border-color: #c1c7cd;
                }
                
                QLabel#SummaryContent {
                    color: #212121;
                    font-size: 12px;
                    line-height: 1.6;
                }
            """
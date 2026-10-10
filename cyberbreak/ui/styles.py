"""
CyberBreak Design System & Ultra-Modern QSS Stylesheet
By lilami only — Military-grade offensive/defensive aesthetics.
High contrast, neon mint (#00ff66), cyber blue (#00b8ff), and alert crimson (#ff2a4b).
"""

MAIN_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0b0c10;
    color: #f0f3fa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: transparent;
    color: #f0f3fa;
}

/* Sidebar Navigation Frame */
QFrame#SidebarFrame {
    background-color: #101117;
    border-right: 1px solid #222533;
}

/* Sidebar List Navigation */
QListWidget#Sidebar {
    background-color: transparent;
    border: none;
    padding: 10px 6px;
    outline: none;
}

QListWidget#Sidebar::item {
    padding: 10px 14px;
    margin: 3px 6px;
    border-radius: 6px;
    color: #9da3ba;
    font-weight: 500;
    font-size: 13px;
    border-left: 3px solid transparent;
}

QListWidget#Sidebar::item:hover {
    background-color: #1a1c26;
    color: #ffffff;
}

QListWidget#Sidebar::item:selected {
    background-color: #16261d;
    color: #00ff66;
    border-left: 3px solid #00ff66;
    font-weight: 700;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0f1016;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2b2f42;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #00ff66;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Standard Buttons - High Contrast against #13141c cards */
QPushButton {
    background-color: #212433;
    color: #ffffff;
    border: 1px solid #363b52;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #2b2f44;
    border-color: #00ff66;
    color: #00ff66;
}

QPushButton:pressed {
    background-color: #161824;
}

QPushButton:disabled {
    background-color: #161720;
    color: #55596b;
    border-color: #242633;
}

/* Neon Mint Action Buttons */
QPushButton#AccentButton {
    background-color: #00ff66;
    color: #050a06;
    border: 1px solid #00ff66;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QPushButton#AccentButton:hover {
    background-color: #2eff7b;
    border-color: #2eff7b;
    color: #000000;
}

QPushButton#AccentButton:pressed {
    background-color: #00d957;
}

/* Cyber Blue Action Buttons */
QPushButton#CyanButton, QPushButton#SecondaryButton {
    background-color: #00b8ff;
    color: #040b12;
    border: 1px solid #00b8ff;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QPushButton#CyanButton:hover, QPushButton#SecondaryButton:hover {
    background-color: #33c7ff;
    border-color: #33c7ff;
    color: #000000;
}

/* Danger / Panic Buttons */
QPushButton#PanicButton, QPushButton#DangerButton {
    background-color: #ff2a4b;
    color: #ffffff;
    border: 1px solid #ff4763;
    font-weight: 800;
    letter-spacing: 1px;
}

QPushButton#PanicButton:hover, QPushButton#DangerButton:hover {
    background-color: #ff4763;
    border-color: #ff6e84;
}

QPushButton#PanicButton:pressed, QPushButton#DangerButton:pressed {
    background-color: #d91b39;
}

/* Warning Buttons */
QPushButton#WarningButton {
    background-color: #ffaa00;
    color: #0f0a00;
    border: 1px solid #ffaa00;
    font-weight: 800;
}

QPushButton#WarningButton:hover {
    background-color: #ffbb22;
}

/* Outline / Ghost Buttons */
QPushButton#OutlineButton {
    background-color: transparent;
    color: #a4abbf;
    border: 1px solid #373b4f;
    font-weight: 600;
}

QPushButton#OutlineButton:hover {
    background-color: #1a1c27;
    color: #ffffff;
    border-color: #555c78;
}

/* Text Inputs */
QLineEdit {
    background-color: #151722;
    color: #f0f3fa;
    border: 1px solid #2f344a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #00ff66;
    background-color: #181b29;
}

/* ComboBox Dropdowns */
QComboBox {
    background-color: #1c1e2b;
    color: #ffffff;
    border: 1px solid #33384f;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #00ff66;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #151722;
    border: 1px solid #33384f;
    selection-background-color: #1e2822;
    selection-color: #00ff66;
    color: #ffffff;
    padding: 4px;
}

/* SpinBox */
QSpinBox {
    background-color: #151722;
    color: #ffffff;
    border: 1px solid #2f344a;
    border-radius: 6px;
    padding: 6px 10px;
}

/* Terminal & Log Viewer */
QPlainTextEdit#Terminal {
    background-color: #08090d;
    color: #00ff66;
    font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    border: 1px solid #1f2333;
    border-radius: 6px;
    padding: 10px;
}

/* Progress Bars */
QProgressBar {
    background-color: #141620;
    border: 1px solid #2c3044;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    height: 18px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b8ff, stop:1 #00ff66);
    border-radius: 5px;
}

/* Card Widget Frame */
QFrame#Card {
    background-color: #13141b;
    border: 1px solid #242736;
    border-radius: 8px;
}

/* Table Widget */
QTableWidget {
    background-color: #12131a;
    border: 1px solid #232635;
    border-radius: 6px;
    gridline-color: #202331;
    color: #e5e9f5;
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget::item:selected {
    background-color: #1b2620;
    color: #00ff66;
}

QHeaderView::section {
    background-color: #171924;
    color: #8c93ab;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #262a3b;
    font-weight: 700;
    font-size: 11px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #242736;
    background-color: #12131a;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #161822;
    color: #8e95ac;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:hover {
    color: #ffffff;
    background-color: #1e212e;
}

QTabBar::tab:selected {
    background-color: #12131a;
    color: #00ff66;
    border-top: 2px solid #00ff66;
}

/* Headings */
QLabel#HeaderTitle {
    font-size: 19px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel#HeaderSubtitle {
    font-size: 12px;
    color: #838a9e;
}

QLabel#CardTitle {
    font-size: 13px;
    font-weight: 700;
    color: #e2e6f3;
}

QLabel#CardValue {
    font-size: 20px;
    font-weight: 800;
    color: #00ff66;
}

/* Status Pills */
QLabel#StatusPillSecure {
    background-color: #0f2416;
    color: #00ff66;
    border: 1px solid #00ff66;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 800;
    font-size: 11px;
}

QLabel#StatusPillWarning {
    background-color: #2b1d10;
    color: #ffaa00;
    border: 1px solid #ffaa00;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 800;
    font-size: 11px;
}

QLabel#StatusPillDanger {
    background-color: #2b1116;
    color: #ff3344;
    border: 1px solid #ff3344;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 800;
    font-size: 11px;
}

/* Giant Leak Alert Banner */
QFrame#LeakAlertBanner {
    background-color: #240d12;
    border: 2px solid #ff2a4b;
    border-radius: 8px;
}

/* Giant Secured Fortress Banner */
QFrame#ShieldSecureBanner {
    background-color: #0a1f12;
    border: 2px solid #00ff66;
    border-radius: 8px;
}
"""

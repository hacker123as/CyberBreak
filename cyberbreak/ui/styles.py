"""
CyberBreak Design System & QSS (Qt Style Sheets)
Palette:
- Background:  #121214 (deep charcoal)
- Surface:     #1c1c1f (elevated card)
- Surface Alt: #242429
- Border:      #2a2a30
- Primary:     #00ff66 (toxic mint neon)
- Secondary:   #00b8ff (cyber blue)
- Alert/Panic: #ff3344 (high-voltage red)
- Text Main:   #f0f0f5
- Text Muted:  #8c8c96
"""

MAIN_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #121214;
    color: #f0f0f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: transparent;
    color: #f0f0f5;
}

/* Sidebar List Navigation */
QListWidget#Sidebar {
    background-color: #161619;
    border: none;
    border-right: 1px solid #242428;
    padding: 12px 6px;
    outline: none;
}

QListWidget#Sidebar::item {
    padding: 11px 14px;
    margin: 3px 6px;
    border-radius: 6px;
    color: #9a9aa5;
    font-weight: 500;
    font-size: 13px;
}

QListWidget#Sidebar::item:hover {
    background-color: #202025;
    color: #ffffff;
}

QListWidget#Sidebar::item:selected {
    background-color: #1e2822;
    color: #00ff66;
    border-left: 3px solid #00ff66;
    font-weight: 600;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #141417;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a2a32;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #00ff66;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Standard Buttons */
QPushButton {
    background-color: #1f1f24;
    color: #f0f0f5;
    border: 1px solid #2e2e38;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #27272e;
    border-color: #00ff66;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #151518;
}

/* Accent Action Buttons */
QPushButton#AccentButton {
    background-color: #00ff66;
    color: #0a0a0c;
    border: 1px solid #00ff66;
    font-weight: 700;
}

QPushButton#AccentButton:hover {
    background-color: #22ff77;
    border-color: #22ff77;
}

/* Panic Buttons */
QPushButton#PanicButton {
    background-color: #ff3344;
    color: #ffffff;
    border: 1px solid #ff4d5d;
    font-weight: 800;
    letter-spacing: 1px;
}

QPushButton#PanicButton:hover {
    background-color: #ff4d5d;
    border-color: #ff6675;
}

/* Text Inputs */
QLineEdit {
    background-color: #18181c;
    color: #f0f0f5;
    border: 1px solid #2e2e38;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #00ff66;
    background-color: #1a1a1f;
}

/* Terminal & Log Viewer */
QPlainTextEdit#Terminal {
    background-color: #09090b;
    color: #00ff66;
    font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    border: 1px solid #1f1f24;
    border-radius: 6px;
    padding: 10px;
}

/* Card Widget Frame */
QFrame#Card {
    background-color: #1c1c1f;
    border: 1px solid #27272d;
    border-radius: 8px;
}

/* Headings */
QLabel#HeaderTitle {
    font-size: 19px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#HeaderSubtitle {
    font-size: 12px;
    color: #7a7a85;
}

QLabel#CardTitle {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#CardValue {
    font-size: 20px;
    font-weight: 700;
    color: #00ff66;
}

QLabel#StatusPillSecure {
    background-color: #12281a;
    color: #00ff66;
    border: 1px solid #00ff66;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 700;
    font-size: 11px;
}

QLabel#StatusPillWarning {
    background-color: #2b1f14;
    color: #ffaa00;
    border: 1px solid #ffaa00;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 700;
    font-size: 11px;
}

QLabel#StatusPillDanger {
    background-color: #2b1418;
    color: #ff3344;
    border: 1px solid #ff3344;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: 700;
    font-size: 11px;
}
"""

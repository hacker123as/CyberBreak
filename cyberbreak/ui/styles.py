MAIN_STYLESHEET = """
QWidget {
    color: #e8edf9; font-family: "Inter", "SF Pro Display", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px; background: transparent;
}
QMainWindow, QDialog { background: #101727; }
QToolTip { color: #edf1ff; background: #26324b; border: 1px solid #46516a; border-radius: 6px; padding: 7px 10px; }
QFrame#SidebarFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(29, 37, 57, 210), stop:1 rgba(19, 26, 42, 190));
    border: 1px solid rgba(207, 223, 255, 22); border-radius: 24px;
}
QFrame#TopBar { background: rgba(173, 198, 245, 7); border: 1px solid rgba(207, 223, 255, 16); border-radius: 18px; }
QLabel#BrandTitle { font-size: 18px; font-weight: 600; color: #f4f6ff; }
QLabel#BrandSubtitle { font-size: 11px; color: #8290ae; }
QLabel#SectionLabel { font-size: 10px; font-weight: 600; color: #7d8aa8; padding: 6px 12px; }
QLabel#Breadcrumb { font-size: 13px; font-weight: 600; color: #d5def1; }
QLabel#Muted { color: #8998b8; font-size: 11px; }
QLabel#Eyebrow { font-size: 10px; font-weight: 600; color: #9eb6ff; }
QLabel#HeroTitle { font-size: 29px; font-weight: 600; color: #f5f7ff; }
QLabel#HeroSubtitle { font-size: 13px; color: #acb8d0; }
QLabel#HeaderTitle { font-size: 25px; font-weight: 600; color: #f4f6ff; }
QLabel#HeaderSubtitle { font-size: 12px; color: #a0aec8; }
QLabel#CardTitle { font-size: 13px; font-weight: 600; color: #dce4f6; }
QLabel#CardValue { font-size: 24px; font-weight: 600; color: #f0f4ff; }
QLabel#StatusText { font-size: 11px; color: #b7c4df; }
QLabel#SettingTitle { font-size: 13px; font-weight: 600; color: #dce4f6; }
QLabel#DialogTitle { font-size: 22px; font-weight: 600; color: #f0f4ff; }
QLabel#ErrorLabel { font-size: 12px; color: #ffabba; }
QLabel#MonoValue { font-family: "Cascadia Code", "DejaVu Sans Mono", monospace; font-size: 12px; color: #aebfdc; }
QFrame#Divider { background: rgba(193, 215, 255, 18); border: none; max-height: 1px; }
QLabel#SessionBadge { background: rgba(160, 183, 232, 10); color: #b5c2de; border: 1px solid rgba(197, 216, 255, 20); border-radius: 12px; padding: 5px 10px; font-size: 11px; }
QListWidget#Sidebar { border: none; background: transparent; outline: none; padding: 0; }
QListWidget#Sidebar::item { border: none; color: #a4b0cb; margin: 1px 0; padding: 0; }
QListWidget#Sidebar::item:selected, QListWidget#Sidebar::item:hover { background: transparent; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 7px; margin: 5px 0; }
QScrollBar::handle:vertical { background: rgba(174, 193, 235, 50); min-height: 30px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: rgba(174, 193, 235, 95); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 7px; margin: 0 5px; }
QScrollBar::handle:horizontal { background: rgba(174, 193, 235, 50); min-width: 30px; border-radius: 3px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QPushButton, QToolButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(194, 210, 249, 20), stop:1 rgba(194, 210, 249, 8));
    border: 1px solid rgba(194, 211, 249, 36); border-radius: 11px; color: #dce5fb;
    padding: 10px 15px; font-size: 12px; font-weight: 600;
}
QPushButton:hover, QToolButton:hover { background: rgba(165, 190, 250, 30); border-color: rgba(173, 194, 250, 85); color: #ffffff; }
QPushButton:pressed, QToolButton:pressed { background: rgba(127, 156, 239, 40); }
QPushButton:focus, QToolButton:focus { border: 1px solid #a2b8ff; }
QPushButton:disabled, QToolButton:disabled { color: #74819c; background: rgba(187, 205, 245, 5); border-color: rgba(187, 205, 245, 12); }
QPushButton#AccentButton { color: #ffffff; border: 1px solid #91acff; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #799afa, stop:1 #5f7ee5); }
QPushButton#AccentButton:hover { background: #89a6ff; border-color: #b1c3ff; }
QPushButton#AccentButton:pressed { background: #5674d8; }
QPushButton#AccentButton:disabled { background: #344363; border-color: #465574; color: #91a1c0; }
QPushButton#CyanButton, QPushButton#SecondaryButton { color: #b5c9ff; background: rgba(116, 150, 255, 25); border-color: rgba(134, 167, 255, 65); }
QPushButton#CyanButton:hover, QPushButton#SecondaryButton:hover { background: rgba(116, 150, 255, 45); border-color: #8daaff; }
QPushButton#OutlineButton { background: rgba(189, 210, 255, 4); border-color: rgba(189, 210, 255, 28); color: #bdcae5; }
QPushButton#OutlineButton:hover { background: rgba(189, 210, 255, 18); color: #f4f6ff; }
QPushButton#DangerButton, QPushButton#PanicButton { color: #ffb5c2; background: rgba(241, 104, 133, 22); border: 1px solid rgba(255, 142, 167, 74); }
QPushButton#DangerButton:hover, QPushButton#PanicButton:hover { background: rgba(241, 104, 133, 42); border-color: #ff94aa; }
QPushButton#WarningButton { color: #f5d59d; background: rgba(235, 181, 104, 22); border: 1px solid rgba(235, 181, 104, 60); }
QPushButton#WarningButton:hover { background: rgba(235, 181, 104, 38); }
QPushButton#SearchButton { text-align: left; color: #95a4c2; font-weight: 400; background: rgba(11, 18, 33, 75); padding: 9px 13px; }
QToolButton#MotionButton { padding: 9px; border-radius: 11px; }
QToolButton#MotionButton:checked { color: #afc2ff; background: rgba(125, 161, 255, 28); border-color: rgba(125, 161, 255, 65); }
QLineEdit, QComboBox, QSpinBox {
    color: #e4ebfb; background: rgba(8, 15, 29, 95); border: 1px solid rgba(185, 207, 255, 28);
    border-radius: 10px; padding: 9px 12px; min-height: 18px; selection-background-color: #607fd4;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #91aaff; background: rgba(26, 39, 65, 160); }
QLineEdit:disabled, QComboBox:disabled { color: #7885a0; }
QComboBox { min-width: 100px; padding-right: 28px; }
QComboBox:hover { border-color: rgba(171, 196, 255, 95); }
QComboBox::drop-down { width: 25px; border: none; }
QComboBox QAbstractItemView { background: #202b42; border: 1px solid #3c4a65; selection-background-color: #354d7f; color: #e4ebfb; padding: 5px; outline: none; }
QSpinBox::up-button, QSpinBox::down-button { width: 20px; border: none; }
QCheckBox { color: #c5d0e9; spacing: 9px; padding: 4px 0; }
QCheckBox::indicator { width: 17px; height: 17px; background: rgba(188, 209, 255, 10); border: 1px solid #596987; border-radius: 5px; }
QCheckBox::indicator:checked { background: #80a0ff; border: 3px solid #adc2ff; }
QCheckBox::indicator:focus { border-color: #b9ccff; }
QFrame#Card, QFrame#InfoCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(188, 211, 255, 14), stop:1 rgba(145, 173, 222, 5));
    border: 1px solid rgba(201, 223, 255, 27); border-radius: 18px;
}
QFrame#GlassCard { border: none; background: transparent; }
QFrame#LeakAlertBanner { background: rgba(209, 85, 116, 20); border: 1px solid rgba(255, 138, 162, 60); border-radius: 18px; }
QFrame#ShieldSecureBanner { background: rgba(75, 195, 169, 16); border: 1px solid rgba(109, 222, 199, 60); border-radius: 18px; }
QLabel#StatusPillSecure, QLabel#StatusPillWarning, QLabel#StatusPillDanger, QLabel#StatusPillNeutral { border-radius: 9px; padding: 4px 8px; font-size: 10px; font-weight: 600; }
QLabel#StatusPillSecure { color: #85e4ce; background: rgba(81, 191, 163, 20); border: 1px solid rgba(108, 220, 191, 35); }
QLabel#StatusPillWarning { color: #f2d29b; background: rgba(224, 171, 95, 18); border: 1px solid rgba(243, 200, 129, 35); }
QLabel#StatusPillDanger { color: #ffabba; background: rgba(224, 109, 133, 18); border: 1px solid rgba(248, 151, 173, 35); }
QLabel#StatusPillNeutral { color: #a9bde9; background: rgba(146, 180, 250, 15); border: 1px solid rgba(174, 199, 249, 25); }
QPlainTextEdit, QTextEdit { color: #b7c7e5; background: rgba(6, 12, 24, 100); border: 1px solid rgba(161, 189, 239, 24); border-radius: 12px; padding: 12px; selection-background-color: #3e5689; }
QPlainTextEdit#Terminal, QTextEdit#Terminal { color: #b8d7d2; font-family: "Cascadia Code", "JetBrains Mono", "DejaVu Sans Mono", monospace; font-size: 12px; background: rgba(7, 14, 25, 170); border-radius: 14px; }
QTableWidget, QTableView {
    color: #c6d2e9; background: rgba(14, 23, 39, 90); alternate-background-color: rgba(190, 213, 255, 5);
    border: 1px solid rgba(192, 214, 255, 24); border-radius: 12px; gridline-color: rgba(192, 214, 255, 10);
    selection-background-color: rgba(122, 162, 255, 30); selection-color: #e4ecff;
}
QTableWidget::item { padding: 6px 10px; border-bottom: 1px solid rgba(186, 207, 246, 8); }
QTableWidget::item:selected { background: rgba(122, 162, 255, 27); color: #e4ecff; }
QTableWidget QPushButton, QTableView QPushButton {
    padding: 3px 10px; min-height: 24px; max-height: 28px; font-size: 11px; font-weight: 600;
    border-radius: 7px; margin: 0;
}
QHeaderView { background: transparent; }
QHeaderView::section { color: #95a8cb; background: #1d2a40; border: none; border-bottom: 1px solid #33435d; padding: 10px; font-size: 11px; font-weight: 600; }
QTableCornerButton::section { background: #1d2a40; border: none; }
QTabWidget::pane { background: rgba(137, 173, 238, 5); border: 1px solid rgba(186, 207, 246, 20); border-radius: 14px; top: 7px; }
QTabBar::tab { color: #9aaac9; background: rgba(161, 190, 249, 6); border: 1px solid transparent; border-radius: 9px; padding: 9px 14px; margin: 0 5px 8px 0; font-size: 12px; }
QTabBar::tab:hover { color: #e4ecff; background: rgba(161, 190, 249, 16); }
QTabBar::tab:selected { color: #c8d6ff; background: rgba(127, 163, 255, 24); border: 1px solid rgba(171, 195, 255, 55); }
QProgressBar { color: #e1eaff; background: rgba(129, 154, 205, 12); border: none; border-radius: 7px; min-height: 14px; text-align: center; font-size: 10px; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7497fa, stop:1 #76d1d0); border-radius: 7px; }
QGroupBox { border: 1px solid rgba(190, 211, 255, 25); border-radius: 14px; margin-top: 14px; padding: 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 5px; color: #c2d0eb; }
QMenu { background: #202c44; color: #dae4fa; border: 1px solid #405270; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #354d7f; }
QListWidget#CommandResults { border: none; background: transparent; outline: none; }
QListWidget#CommandResults::item { color: #c9d6f0; padding: 12px; margin: 2px 0; border-radius: 10px; }
QListWidget#CommandResults::item:selected { color: #eaf0ff; background: rgba(125, 162, 255, 30); }
QDialog#CommandPalette { background: #1b263c; border: 1px solid #516486; border-radius: 20px; }
"""

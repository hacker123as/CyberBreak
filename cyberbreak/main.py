import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from cyberbreak.ui.main_window import MainWindow

def main():
    # Enforce High-DPI scaling
    app = QApplication(sys.argv)
    app.setApplicationName("CyberBreak")
    app.setApplicationDisplayName("CyberBreak Security Fortress")
    app.setDesktopFileName("cyberbreak.desktop")

    # Set icon if present
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "cyberbreak.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

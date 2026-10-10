import sys
import os
from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from cyberbreak.ui.main_window import MainWindow

def main():
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI" if sys.platform == "win32" else "Noto Sans", 10))
    app.setApplicationName("CyberBreak")
    app.setApplicationDisplayName("CyberBreak")
    app.setDesktopFileName("cyberbreak.desktop")

    icon_path = os.path.join(os.path.dirname(__file__), "assets", "cyberbreak.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

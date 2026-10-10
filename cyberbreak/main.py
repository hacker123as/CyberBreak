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

    if "--browser" in sys.argv or "--private-browser" in sys.argv:
        from cyberbreak.ui.widgets.private_browser import StandaloneBrowserWindow
        initial_url = "https://duckduckgo.com"
        for arg in sys.argv[1:]:
            if arg.startswith("http://") or arg.startswith("https://"):
                initial_url = arg
                break
        window = StandaloneBrowserWindow(initial_url=initial_url)
        window.show()
    else:
        from cyberbreak.ui.main_window import MainWindow
        window = MainWindow()
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

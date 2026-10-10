from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtGui import QGuiApplication
from cyberbreak.core.executor import log

class ClipboardGuard(QObject):
    """Automatically scrubs system clipboard to defeat memory-scraping malware."""

    def __init__(self, timeout_seconds: int = 30):
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.wipe_clipboard)
        self.last_content = ""

        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.dataChanged.connect(self.on_clipboard_changed)

    def on_clipboard_changed(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            text = clipboard.text()
            if text and text != self.last_content:
                self.last_content = text
                log(f"Clipboard updated. Auto-scrub countdown armed ({self.timeout_seconds}s)", "CLIP")
                self.timer.start(self.timeout_seconds * 1000)

    def wipe_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.clear()
            self.last_content = ""
            log("Clipboard memory cleared by security guard", "OK")

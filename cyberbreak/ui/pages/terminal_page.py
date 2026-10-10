from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, QFrame
)
from PyQt6.QtCore import Qt
from cyberbreak.core.executor import GLOBAL_LOGGER

class TerminalPage(QWidget):
    """Full-screen live forensic terminal and subprocess execution audit log."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("LIVE FORENSIC AUDIT TERMINAL")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Captures stdout, stderr, kernel calls, and security events in real-time")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        clear_btn = QPushButton("CLEAR LOG")
        clear_btn.clicked.connect(self.clear_terminal)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Terminal output widget
        self.terminal = QPlainTextEdit()
        self.terminal.setObjectName("Terminal")
        self.terminal.setReadOnly(True)
        self.terminal.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.terminal)

        # Connect global logger
        GLOBAL_LOGGER.log_message.connect(self.append_log)

    def append_log(self, level: str, message: str):
        self.terminal.appendPlainText(message)
        # Scroll to bottom
        sb = self.terminal.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def clear_terminal(self):
        self.terminal.clear()

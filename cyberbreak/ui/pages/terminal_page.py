from PyQt6.QtWidgets import QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, QFrame
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from cyberbreak.core.executor import GLOBAL_LOGGER
from cyberbreak.ui.widgets.glass import GlassFrame, icon

class TerminalPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(8)
        title = QLabel('Activity log')
        title.setObjectName('HeaderTitle')
        title.setWordWrap(True)
        subtitle = QLabel('A live record of commands, system responses, and security events.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        clear_btn = QPushButton('Clear log')
        clear_btn.clicked.connect(self.clear_terminal)
        header.addWidget(clear_btn)
        layout.addLayout(header)
        self.terminal = QPlainTextEdit()
        self.terminal.setObjectName('Terminal')
        self.terminal.setReadOnly(True)
        self.terminal.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.terminal)
        GLOBAL_LOGGER.log_message.connect(self.append_log)

    def append_log(self, level: str, message: str):
        self.terminal.appendPlainText(message)
        sb = self.terminal.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def clear_terminal(self):
        self.terminal.clear()

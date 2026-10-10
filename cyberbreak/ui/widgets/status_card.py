from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from cyberbreak.ui.widgets.glass import GlassFrame, icon


class StatusCard(GlassFrame):
    def __init__(self, title: str, value: str = "—", subtitle: str = "", pill_text: str = "", pill_type: str = "SECURE", parent=None, icon_name: str = "activity"):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon(icon_name, "#8fa8ff", 18).pixmap(18, 18))
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: rgba(143, 168, 255, 18); border: 1px solid rgba(143, 168, 255, 26); border-radius: 10px;")
        header.addWidget(self.icon_label)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setMinimumWidth(0)
        header.addWidget(self.title_label, 1)
        layout.addLayout(header)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("CardValue")
        self.value_label.setTextFormat(Qt.TextFormat.PlainText)
        self.value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.value_label.setWordWrap(True)
        self.value_label.setMinimumWidth(0)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.value_label.setToolTip(str(value))
        layout.addWidget(self.value_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("HeaderSubtitle")
        self.subtitle_label.setTextFormat(Qt.TextFormat.PlainText)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMinimumWidth(0)
        self.subtitle_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.subtitle_label.setStyleSheet("font-size: 11px; color: #a4aec8; background: transparent; border: none;")
        layout.addWidget(self.subtitle_label, 1)

        footer = QHBoxLayout()
        self.pill_label = QLabel()
        self.pill_label.setTextFormat(Qt.TextFormat.PlainText)
        self.pill_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.set_pill(pill_text, pill_type)
        footer.addWidget(self.pill_label)
        footer.addStretch()
        layout.addLayout(footer)
        self.set_value(value)

    def set_value(self, value: str):
        text = str(value)
        self.value_label.setText(text)
        self.value_label.setToolTip(text)
        size = 18 if len(text) > 24 else 22 if len(text) > 16 else 28
        self.value_label.setStyleSheet(f"font-size: {size}px; font-weight: 600; color: #f4f6ff; background: transparent; border: none;")

    def set_pill(self, text: str, pill_type: str = "SECURE"):
        self.pill_label.setVisible(bool(text))
        self.pill_label.setText(str(text))
        self.pill_label.setToolTip(str(text))
        names = {"SECURE": "StatusPillSecure", "WARN": "StatusPillWarning"}
        self.pill_label.setObjectName(names.get(pill_type, "StatusPillDanger"))
        self.pill_label.style().unpolish(self.pill_label)
        self.pill_label.style().polish(self.pill_label)
        self.pill_label.update()

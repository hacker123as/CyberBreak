from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class StatusCard(QFrame):
    """Reusable card with title, value, subtitle, and visual status pill."""

    def __init__(self, title: str, value: str = "---", subtitle: str = "", pill_text: str = "", pill_type: str = "SECURE", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Header with title and status pill
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.pill_label = QLabel(pill_text)
        self.set_pill(pill_text, pill_type)
        header_layout.addWidget(self.pill_label)
        layout.addLayout(header_layout)

        # Value display
        self.value_label = QLabel(value)
        self.value_label.setObjectName("CardValue")
        layout.addWidget(self.value_label)

        # Subtitle
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("HeaderSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def set_pill(self, text: str, pill_type: str = "SECURE"):
        if not text:
            self.pill_label.setVisible(False)
            return
        self.pill_label.setVisible(True)
        self.pill_label.setText(text)
        if pill_type == "SECURE":
            self.pill_label.setObjectName("StatusPillSecure")
        elif pill_type == "WARN":
            self.pill_label.setObjectName("StatusPillWarning")
        else:
            self.pill_label.setObjectName("StatusPillDanger")
        self.pill_label.setStyle(self.pill_label.style())

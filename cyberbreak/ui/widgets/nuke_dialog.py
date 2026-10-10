from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from cyberbreak.core.nuke_engine import NukeEngine
from cyberbreak.ui.widgets.glass import GlassFrame, icon


class NukeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authorize drive destruction")
        self.setMinimumSize(540, 390)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        heading = QHBoxLayout()
        warning_icon = QLabel()
        warning_icon.setPixmap(icon("alert", "#ff8294", 28).pixmap(28, 28))
        warning_icon.setFixedSize(36, 36)
        heading.addWidget(warning_icon)
        title = QLabel("Permanent drive destruction")
        title.setObjectName("DialogTitle")
        title.setWordWrap(True)
        heading.addWidget(title, 1)
        layout.addLayout(heading)

        warning = GlassFrame()
        warning.setObjectName("GlassCard")
        warning_layout = QVBoxLayout(warning)
        warning_layout.setContentsMargins(18, 18, 18, 18)
        description = QLabel(
            "This action destroys LUKS encryption headers, discards drive blocks, "
            "and crashes the kernel. All affected data is permanently lost. "
            "This operation cannot be undone."
        )
        description.setObjectName("HeaderSubtitle")
        description.setWordWrap(True)
        warning_layout.addWidget(description)
        layout.addWidget(warning)

        prompt = QLabel("Master authorization passphrase")
        prompt.setObjectName("SettingTitle")
        layout.addWidget(prompt)
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Enter your passphrase")
        self.pass_input.setAccessibleName("Master authorization passphrase")
        self.pass_input.textChanged.connect(self._update_authorization)
        layout.addWidget(self.pass_input)

        self.error_label = QLabel("Authorization failed. Check your passphrase.")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("OutlineButton")
        cancel.setDefault(True)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.nuke_btn = QPushButton("Destroy drives")
        self.nuke_btn.setObjectName("PanicButton")
        self.nuke_btn.setIcon(icon("alert", "#ff8294"))
        self.nuke_btn.setAutoDefault(False)
        self.nuke_btn.setEnabled(False)
        self.nuke_btn.clicked.connect(self.on_nuke_clicked)
        buttons.addWidget(self.nuke_btn)
        layout.addLayout(buttons)
        self.pass_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def _update_authorization(self, value):
        self.nuke_btn.setEnabled(bool(value.strip()))
        self.error_label.hide()

    def on_nuke_clicked(self):
        entered = self.pass_input.text().strip()
        if not entered:
            return
        if NukeEngine.verify_password(entered):
            NukeEngine.execute_panic_nuke(entered)
            self.accept()
        else:
            self.pass_input.clear()
            self.error_label.show()
            self.pass_input.setFocus()

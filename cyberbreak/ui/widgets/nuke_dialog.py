from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from cyberbreak.core.nuke_engine import NukeEngine

class NukeDialog(QDialog):
    """High-contrast crimson modal for confirming master cryptographic drive wipe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CRITICAL AUTHORIZATION: MASTER PANIC NUKE")
        self.setFixedSize(480, 280)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Danger warning header
        title = QLabel("PERMANENT DATA OBLITERATION")
        title.setObjectName("HeaderTitle")
        title.setStyleSheet("color: #ff3344; font-size: 18px; font-weight: 800;")
        layout.addWidget(title)

        desc = QLabel(
            "WARNING: This action immediately destroys LUKS cryptographic headers, "
            "fires blkdiscard NAND block purges on all drives, and crashes the kernel to defeat "
            "cold-boot forensic dumps. This operation is PERMANENT and CANNOT BE UNDONE."
        )
        desc.setObjectName("HeaderSubtitle")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #f0f0f5; font-size: 12px; line-height: 1.4;")
        layout.addWidget(desc)

        prompt = QLabel("Enter Master Authorization Passphrase to Proceed:")
        prompt.setStyleSheet("color: #ffaa00; font-weight: 600;")
        layout.addWidget(prompt)

        # Password input field
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Enter passphrase (e.g. 1234567890)")
        self.pass_input.setStyleSheet("border: 2px solid #ff3344; padding: 10px; font-size: 14px;")
        layout.addWidget(self.pass_input)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.nuke_btn = QPushButton("EXECUTE MASTER NUKE")
        self.nuke_btn.setObjectName("PanicButton")
        self.nuke_btn.setStyleSheet(
            "background-color: #ff2233; color: #ffffff; font-weight: 800; "
            "border: 2px solid #ff5566; padding: 12px; border-radius: 6px;"
        )
        self.nuke_btn.clicked.connect(self.on_nuke_clicked)
        btn_layout.addWidget(self.nuke_btn)

        layout.addLayout(btn_layout)

    def on_nuke_clicked(self):
        entered = self.pass_input.text().strip()
        if not entered:
            return
        if NukeEngine.verify_password(entered):
            # Authorize execution
            NukeEngine.execute_panic_nuke(entered)
            self.accept()
        else:
            self.pass_input.clear()
            self.pass_input.setPlaceholderText("AUTHORIZATION FAILED - INVALID PASSPHRASE")
            self.pass_input.setStyleSheet("border: 2px solid #ff0000; background-color: #2b1418; padding: 10px;")

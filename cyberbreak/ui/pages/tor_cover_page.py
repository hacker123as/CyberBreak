from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from cyberbreak.core.tor_controller import TorController, DecoyTrafficGenerator
from cyberbreak.ui.widgets.status_card import StatusCard

class TorCoverPage(QWidget):
    """Tor control port and background decoy cover traffic engine."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.decoy_engine = DecoyTrafficGenerator()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("TOR CONTROLLER & DECOY COVER TRAFFIC")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Tor circuit control, stream isolation, and anti-timing decoy packet injection")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        layout.addLayout(header)

        # Grid Cards
        grid = QGridLayout()
        grid.setSpacing(16)

        self.tor_card = StatusCard(
            "TOR CONTROL PORT (9051)",
            "Ready",
            "Authenticated IPC control socket",
            "STANDBY",
            "SECURE"
        )
        grid.addWidget(self.tor_card, 0, 0)

        self.decoy_card = StatusCard(
            "DECOY COVER TRAFFIC",
            "Inactive",
            "Synthetic HTTP dummy packet generator",
            "STOPPED",
            "WARN"
        )
        grid.addWidget(self.decoy_card, 0, 1)

        layout.addLayout(grid)

        # Tor Controls Frame
        tor_frame = QFrame()
        tor_frame.setObjectName("Card")
        t_layout = QVBoxLayout(tor_frame)
        t_layout.setContentsMargins(18, 18, 18, 18)
        t_layout.setSpacing(12)

        t_title = QLabel("TOR CIRCUIT MANAGEMENT")
        t_title.setObjectName("CardTitle")
        t_layout.addWidget(t_title)

        t_row = QHBoxLayout()
        self.newnym_btn = QPushButton("REQUEST NEW TOR IDENTITY (NEWNYM)")
        self.newnym_btn.setObjectName("AccentButton")
        self.newnym_btn.clicked.connect(self.on_newnym)
        t_row.addWidget(self.newnym_btn)
        t_row.addStretch()
        t_layout.addLayout(t_row)

        layout.addWidget(tor_frame)

        # Decoy Traffic Frame
        decoy_frame = QFrame()
        decoy_frame.setObjectName("Card")
        d_layout = QVBoxLayout(decoy_frame)
        d_layout.setContentsMargins(18, 18, 18, 18)
        d_layout.setSpacing(12)

        d_title = QLabel("SYNTHETIC COVER TRAFFIC GENERATOR")
        d_title.setObjectName("CardTitle")
        d_layout.addWidget(d_title)

        d_desc = QLabel(
            "Emits background dummy HTTPS requests to randomized high-traffic public domains with "
            "variable packet sizes and intervals to prevent passive ISP packet-timing correlation."
        )
        d_desc.setObjectName("HeaderSubtitle")
        d_desc.setWordWrap(True)
        d_layout.addWidget(d_desc)

        d_row = QHBoxLayout()
        self.decoy_toggle_btn = QPushButton("START COVER TRAFFIC GENERATOR")
        self.decoy_toggle_btn.clicked.connect(self.on_toggle_decoy)
        d_row.addWidget(self.decoy_toggle_btn)
        d_row.addStretch()
        d_layout.addLayout(d_row)

        layout.addWidget(decoy_frame)
        layout.addStretch()

    def on_newnym(self):
        ok, res = TorController.signal_new_identity()
        if ok:
            self.tor_card.set_value("NEWNYM Dispatched")
            self.tor_card.set_pill("REBUILT", "SECURE")
        else:
            self.tor_card.set_value("Connection Error")
            self.tor_card.set_pill("OFFLINE", "WARN")

    def on_toggle_decoy(self):
        if not self.decoy_engine.running:
            self.decoy_engine = DecoyTrafficGenerator()
            self.decoy_engine.start_generator()
            self.decoy_card.set_value("Active")
            self.decoy_card.set_pill("RUNNING", "SECURE")
            self.decoy_toggle_btn.setText("STOP COVER TRAFFIC GENERATOR")
            self.decoy_toggle_btn.setStyleSheet("border-color: #ffaa00; color: #ffaa00;")
        else:
            self.decoy_engine.stop_generator()
            self.decoy_card.set_value("Inactive")
            self.decoy_card.set_pill("STOPPED", "WARN")
            self.decoy_toggle_btn.setText("START COVER TRAFFIC GENERATOR")
            self.decoy_toggle_btn.setStyleSheet("")

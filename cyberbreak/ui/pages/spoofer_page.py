from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from cyberbreak.core.spoofer_engine import SpooferEngine
from cyberbreak.ui.widgets.status_card import StatusCard

class SpooferPage(QWidget):
    """Hardware, MAC, Hostname, and Machine-ID spoofer interface."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("HARDWARE & IDENTITY SPOOFER")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Randomize physical network MACs, OEM hostnames, machine-id, and UTC timezone")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        refresh_btn = QPushButton("REFRESH ADAPTERS")
        refresh_btn.clicked.connect(self.refresh_adapters)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Adapter Selection Card
        adapter_frame = QFrame()
        adapter_frame.setObjectName("Card")
        ad_layout = QVBoxLayout(adapter_frame)
        ad_layout.setContentsMargins(18, 18, 18, 18)
        ad_layout.setSpacing(14)

        ad_title = QLabel("NETWORK ADAPTER MAC SPOOFER")
        ad_title.setObjectName("CardTitle")
        ad_layout.addWidget(ad_title)

        select_row = QHBoxLayout()
        select_row.addWidget(QLabel("Target Interface:"))
        self.adapter_combo = QComboBox()
        self.adapter_combo.setStyleSheet(
            "background-color: #161619; color: #f0f0f5; border: 1px solid #2a2a32; "
            "padding: 8px 12px; border-radius: 6px; min-width: 200px;"
        )
        self.adapter_combo.currentIndexChanged.connect(self.on_adapter_selected)
        select_row.addWidget(self.adapter_combo)

        select_row.addStretch()

        self.spoof_mac_btn = QPushButton("RANDOMIZE MAC ADDRESS")
        self.spoof_mac_btn.setObjectName("AccentButton")
        self.spoof_mac_btn.clicked.connect(self.on_spoof_mac)
        select_row.addWidget(self.spoof_mac_btn)

        ad_layout.addLayout(select_row)

        self.mac_info_label = QLabel("Current MAC: --- | Status: ---")
        self.mac_info_label.setStyleSheet("color: #00ff66; font-family: monospace; font-size: 13px;")
        ad_layout.addWidget(self.mac_info_label)

        layout.addWidget(adapter_frame)

        # System Identifiers Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        # Hostname Card
        self.host_card = StatusCard(
            "SYSTEM HOSTNAME",
            "Checking...",
            "Dynamic OEM name via hostnamectl",
            "ACTIVE",
            "SECURE"
        )
        grid.addWidget(self.host_card, 0, 0)

        # Machine-ID Card
        self.mid_card = StatusCard(
            "SYSTEM MACHINE-ID",
            "Checking...",
            "/etc/machine-id uniqueness",
            "ACTIVE",
            "SECURE"
        )
        grid.addWidget(self.mid_card, 0, 1)

        layout.addLayout(grid)

        # Identity Action Buttons
        actions_frame = QFrame()
        actions_frame.setObjectName("Card")
        act_layout = QHBoxLayout(actions_frame)
        act_layout.setContentsMargins(16, 16, 16, 16)
        act_layout.setSpacing(12)

        host_btn = QPushButton("RANDOMIZE HOSTNAME")
        host_btn.clicked.connect(self.on_randomize_hostname)
        act_layout.addWidget(host_btn)

        mid_btn = QPushButton("RE-SEED MACHINE-ID")
        mid_btn.clicked.connect(self.on_reseed_machine_id)
        act_layout.addWidget(mid_btn)

        utc_btn = QPushButton("LOCK TIMEZONE TO UTC")
        utc_btn.clicked.connect(SpooferEngine.set_utc_timezone)
        act_layout.addWidget(utc_btn)

        act_layout.addStretch()
        layout.addWidget(actions_frame)

        layout.addStretch()

        self.interfaces = []
        self.refresh_adapters()
        self.update_system_ids()

    def refresh_adapters(self):
        self.interfaces = SpooferEngine.get_network_interfaces()
        self.adapter_combo.clear()
        for iface in self.interfaces:
            self.adapter_combo.addItem(f"{iface['name']} ({iface['mac']})", iface['name'])

    def on_adapter_selected(self, index):
        if 0 <= index < len(self.interfaces):
            iface = self.interfaces[index]
            self.mac_info_label.setText(f"Interface: {iface['name']} | Current MAC: {iface['mac']} | State: {iface['state']}")

    def on_spoof_mac(self):
        curr_iface = self.adapter_combo.currentData()
        if curr_iface:
            SpooferEngine.randomize_mac(curr_iface)
            self.refresh_adapters()

    def update_system_ids(self):
        try:
            import socket
            self.host_card.set_value(socket.gethostname())
        except Exception:
            self.host_card.set_value("Unknown")

        try:
            with open("/etc/machine-id", "r") as f:
                mid = f.read().strip()
                self.mid_card.set_value(f"{mid[:12]}...")
        except Exception:
            self.mid_card.set_value("N/A")

    def on_randomize_hostname(self):
        ok, res = SpooferEngine.randomize_hostname()
        if ok:
            self.host_card.set_value(res)

    def on_reseed_machine_id(self):
        ok, res = SpooferEngine.reseed_machine_id()
        if ok:
            self.mid_card.set_value(f"{res[:12]}...")

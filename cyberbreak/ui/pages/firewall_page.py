from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.ui.widgets.status_card import StatusCard

class FirewallPage(QWidget):
    """Netfilter and iptables profiles and VPN killswitch manager."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("HARDENED FIREWALL & KILLSWITCH PROFILES")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Linux Netfilter iptables rule enforcement and VPN leak containment")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        layout.addLayout(header)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.fw_card = StatusCard(
            "FIREWALL STATE",
            "Default Policy",
            "Standard workstation packet filtering",
            "ACTIVE",
            "SECURE"
        )
        grid.addWidget(self.fw_card, 0, 0)

        self.vpn_card = StatusCard(
            "VPN KILLSWITCH",
            "Standby",
            "Strict tunnel isolation mode",
            "STANDBY",
            "WARN"
        )
        grid.addWidget(self.vpn_card, 0, 1)

        layout.addLayout(grid)

        # Profile Selection Frame
        frame = QFrame()
        frame.setObjectName("Card")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(18, 18, 18, 18)
        f_layout.setSpacing(14)

        f_title = QLabel("SELECT FIREWALL PROFILE:")
        f_title.setObjectName("CardTitle")
        f_layout.addWidget(f_title)

        # Strict profile
        p1_row = QHBoxLayout()
        p1_info = QVBoxLayout()
        p1_lbl = QLabel("Strict Workstation Shield")
        p1_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        p1_sub = QLabel("Drops all unrequested incoming packets. Allows normal outbound traffic. Blocks all IPv6.")
        p1_sub.setObjectName("HeaderSubtitle")
        p1_info.addWidget(p1_lbl)
        p1_info.addWidget(p1_sub)
        p1_row.addLayout(p1_info)
        p1_row.addStretch()

        p1_btn = QPushButton("APPLY STRICT PROFILE")
        p1_btn.clicked.connect(self.on_apply_strict)
        p1_row.addWidget(p1_btn)
        f_layout.addLayout(p1_row)

        f_layout.addWidget(self.create_divider())

        # VPN Killswitch profile
        p2_row = QHBoxLayout()
        p2_info = QVBoxLayout()
        p2_lbl = QLabel("VPN-Only Killswitch (Zero Raw Leakage)")
        p2_lbl.setStyleSheet("font-weight: 600; color: #00ff66;")
        p2_sub = QLabel("Blocks ALL traffic on eth0/wlan0. Only allows encrypted tunnel interfaces (tun+, wg+, proton+).")
        p2_sub.setObjectName("HeaderSubtitle")
        p2_info.addWidget(p2_lbl)
        p2_info.addWidget(p2_sub)
        p2_row.addLayout(p2_info)
        p2_row.addStretch()

        p2_btn = QPushButton("ARM VPN KILLSWITCH")
        p2_btn.setObjectName("AccentButton")
        p2_btn.clicked.connect(self.on_apply_vpn)
        p2_row.addWidget(p2_btn)
        f_layout.addLayout(p2_row)

        f_layout.addWidget(self.create_divider())

        # Proton VPN dedicated killswitch
        proton_row = QHBoxLayout()
        proton_info = QVBoxLayout()
        proton_lbl = QLabel("Proton VPN Dedicated Killswitch")
        proton_lbl.setStyleSheet("font-weight: 600; color: #00ddff;")
        proton_sub = QLabel("Locks down traffic strictly to Proton VPN interfaces (proton+, pvpn+) and WireGuard/OpenVPN ports.")
        proton_sub.setObjectName("HeaderSubtitle")
        proton_info.addWidget(proton_lbl)
        proton_info.addWidget(proton_sub)
        proton_row.addLayout(proton_info)
        proton_row.addStretch()

        proton_btn = QPushButton("ARM PROTON KILLSWITCH")
        proton_btn.setStyleSheet("border-color: #00ddff; color: #00ddff; font-weight: 700;")
        proton_btn.clicked.connect(self.on_apply_proton)
        proton_row.addWidget(proton_btn)
        f_layout.addLayout(proton_row)

        f_layout.addWidget(self.create_divider())

        # Reset profile
        p3_row = QHBoxLayout()
        p3_info = QVBoxLayout()
        p3_lbl = QLabel("Restore Default Policies")
        p3_lbl.setStyleSheet("font-weight: 600; color: #8a8a95;")
        p3_sub = QLabel("Flushes custom iptables rules and sets default ACCEPT.")
        p3_sub.setObjectName("HeaderSubtitle")
        p3_info.addWidget(p3_lbl)
        p3_info.addWidget(p3_sub)
        p3_row.addLayout(p3_info)
        p3_row.addStretch()

        p3_btn = QPushButton("RESET FIREWALL")
        p3_btn.clicked.connect(self.on_reset)
        p3_row.addWidget(p3_btn)
        f_layout.addLayout(p3_row)

        layout.addWidget(frame)
        layout.addStretch()

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #242429;")
        return line

    def on_apply_strict(self):
        ok, res = FirewallController.apply_strict_profile()
        if ok:
            self.fw_card.set_value("Strict Mode")
            self.fw_card.set_pill("HARDENED", "SECURE")
            self.vpn_card.set_value("Standby")
            self.vpn_card.set_pill("STANDBY", "WARN")

    def on_apply_vpn(self):
        ok, res = FirewallController.apply_vpn_killswitch()
        if ok:
            self.fw_card.set_value("Killswitch Active")
            self.fw_card.set_pill("ISOLATED", "SECURE")
            self.vpn_card.set_value("Armed (tun+/wg+/proton+)")
            self.vpn_card.set_pill("ARMED", "SECURE")

    def on_apply_proton(self):
        ok, res = FirewallController.apply_protonvpn_killswitch()
        if ok:
            self.fw_card.set_value("Proton Killswitch")
            self.fw_card.set_pill("PROTECTED", "SECURE")
            self.vpn_card.set_value("Proton VPN Locked")
            self.vpn_card.set_pill("PROTON ARMED", "SECURE")

    def on_reset(self):
        FirewallController.reset_firewall()
        self.fw_card.set_value("Default Policy")
        self.fw_card.set_pill("STANDARD", "WARN")
        self.vpn_card.set_value("Inactive")
        self.vpn_card.set_pill("OFF", "WARN")

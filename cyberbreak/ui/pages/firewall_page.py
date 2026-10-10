from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.core.port_auditor import PortAuditor
from cyberbreak.ui.widgets.status_card import StatusCard

class FirewallPage(QWidget):
    """
    Netfilter and iptables profiles, VPN killswitch manager, and live kernel rules inspector.
    Engineered by lilami only.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("HARDENED FIREWALL & KILLSWITCH PROFILES // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Linux Netfilter iptables rule enforcement, VPN leak containment & live rule inspector")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.btn_refresh_rules = QPushButton("REFRESH FIREWALL RULES")
        self.btn_refresh_rules.setObjectName("OutlineButton")
        self.btn_refresh_rules.clicked.connect(self.refresh_rules_table)
        header.addWidget(self.btn_refresh_rules)

        layout.addLayout(header)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(14)

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
        f_layout.setContentsMargins(16, 16, 16, 16)
        f_layout.setSpacing(12)

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
        p1_btn.setObjectName("CyanButton")
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
        proton_btn.setObjectName("SecondaryButton")
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
        p3_btn.setObjectName("OutlineButton")
        p3_btn.clicked.connect(self.on_reset)
        p3_row.addWidget(p3_btn)
        f_layout.addLayout(p3_row)

        layout.addWidget(frame)

        # Active Rules Inspector Frame
        rules_frame = QFrame()
        rules_frame.setObjectName("Card")
        r_layout = QVBoxLayout(rules_frame)
        r_layout.setContentsMargins(16, 16, 16, 16)
        r_layout.setSpacing(10)

        r_title = QLabel("LIVE NETFILTER / IPTABLES KERNEL RULES INSPECTOR:")
        r_title.setObjectName("CardTitle")
        r_layout.addWidget(r_title)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(8)
        self.rules_table.setHorizontalHeaderLabels([
            "CHAIN", "NUM", "TARGET", "PROTO", "SOURCE", "DESTINATION", "PACKETS", "BYTES"
        ])
        for c in range(8):
            self.rules_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.rules_table.setStyleSheet("""
            QTableWidget {
                background-color: #121217;
                color: #e5e5ec;
                border: 1px solid #202028;
                border-radius: 6px;
                gridline-color: #1a1a24;
            }
            QHeaderView::section {
                background-color: #16161f;
                color: #00ff66;
                padding: 6px;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid #202028;
            }
        """)
        r_layout.addWidget(self.rules_table)

        layout.addWidget(rules_frame)

        self.refresh_rules_table()

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #242429;")
        return line

    def refresh_rules_table(self):
        rules = PortAuditor.get_active_iptables_rules()
        self.rules_table.setRowCount(len(rules))
        for row, r in enumerate(rules):
            self.rules_table.setItem(row, 0, QTableWidgetItem(r.get("chain", "")))
            self.rules_table.setItem(row, 1, QTableWidgetItem(r.get("num", "")))

            target_item = QTableWidgetItem(r.get("target", ""))
            if r.get("target") == "DROP":
                target_item.setForeground(Qt.GlobalColor.red)
            elif r.get("target") == "ACCEPT":
                target_item.setForeground(Qt.GlobalColor.green)
            self.rules_table.setItem(row, 2, target_item)

            self.rules_table.setItem(row, 3, QTableWidgetItem(r.get("proto", "")))
            self.rules_table.setItem(row, 4, QTableWidgetItem(r.get("source", "")))
            self.rules_table.setItem(row, 5, QTableWidgetItem(r.get("dest", "")))
            self.rules_table.setItem(row, 6, QTableWidgetItem(r.get("pkts", "")))
            self.rules_table.setItem(row, 7, QTableWidgetItem(r.get("bytes", "")))

        if len(rules) == 0:
            self.rules_table.setRowCount(1)
            self.rules_table.setItem(0, 0, QTableWidgetItem("INPUT/OUTPUT"))
            self.rules_table.setItem(0, 1, QTableWidgetItem("1"))
            self.rules_table.setItem(0, 2, QTableWidgetItem("DEFAULT"))
            self.rules_table.setItem(0, 3, QTableWidgetItem("ALL"))
            self.rules_table.setItem(0, 4, QTableWidgetItem("0.0.0.0/0"))
            self.rules_table.setItem(0, 5, QTableWidgetItem("0.0.0.0/0"))
            self.rules_table.setItem(0, 6, QTableWidgetItem("0"))
            self.rules_table.setItem(0, 7, QTableWidgetItem("0"))

    def on_apply_strict(self):
        ok, res = FirewallController.apply_strict_profile()
        if ok:
            self.fw_card.set_value("Strict Mode")
            self.fw_card.set_pill("HARDENED", "SECURE")
            self.vpn_card.set_value("Standby")
            self.vpn_card.set_pill("STANDBY", "WARN")
        self.refresh_rules_table()

    def on_apply_vpn(self):
        ok, res = FirewallController.apply_vpn_killswitch()
        if ok:
            self.fw_card.set_value("Killswitch Active")
            self.fw_card.set_pill("ISOLATED", "SECURE")
            self.vpn_card.set_value("Armed (tun+/wg+/proton+)")
            self.vpn_card.set_pill("ARMED", "SECURE")
        self.refresh_rules_table()

    def on_apply_proton(self):
        ok, res = FirewallController.apply_protonvpn_killswitch()
        if ok:
            self.fw_card.set_value("Proton Killswitch")
            self.fw_card.set_pill("PROTECTED", "SECURE")
            self.vpn_card.set_value("Proton VPN Locked")
            self.vpn_card.set_pill("PROTON ARMED", "SECURE")
        self.refresh_rules_table()

    def on_reset(self):
        FirewallController.reset_firewall()
        self.fw_card.set_value("Default Policy")
        self.fw_card.set_pill("STANDARD", "WARN")
        self.vpn_card.set_value("Inactive")
        self.vpn_card.set_pill("OFF", "WARN")
        self.refresh_rules_table()

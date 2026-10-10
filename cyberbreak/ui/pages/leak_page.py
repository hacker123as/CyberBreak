from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.ui.widgets.status_card import StatusCard

class LeakWorker(QThread):
    finished_results = pyqtSignal(dict)

    def run(self):
        ident = NetworkAuditor.get_external_identity()
        gw = NetworkAuditor.check_default_gateway()
        dns = NetworkAuditor.check_dns_resolvers()
        ipv6 = NetworkAuditor.check_ipv6_exposure()
        self.finished_results.emit({
            "ident": ident,
            "gw": gw,
            "dns": dns,
            "ipv6": ipv6
        })

class LeakPage(QWidget):
    """Deep socket audit, routing table examination, and DNS leak sensor."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("COMPREHENSIVE LEAK & ROUTING AUDITOR")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Zero mock data: real socket inspections, route parsing, and resolver audits")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.probe_btn = QPushButton("RUN AUDIT PROBE")
        self.probe_btn.setObjectName("AccentButton")
        self.probe_btn.clicked.connect(self.run_probe)
        header.addWidget(self.probe_btn)

        layout.addLayout(header)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_ip = StatusCard("PUBLIC IP / ASN", "Probing...", "External endpoint query", "", "WARN")
        grid.addWidget(self.card_ip, 0, 0)

        self.card_gw = StatusCard("GATEWAY ROUTE", "Probing...", "Parsing /proc/net/route", "", "WARN")
        grid.addWidget(self.card_gw, 0, 1)

        self.card_dns = StatusCard("ACTIVE DNS RESOLVERS", "Probing...", "/etc/resolv.conf inspection", "", "WARN")
        grid.addWidget(self.card_dns, 1, 0)

        self.card_ipv6 = StatusCard("RAW IPV6 STATUS", "Probing...", "AF_INET6 socket bind test", "", "WARN")
        grid.addWidget(self.card_ipv6, 1, 1)

        layout.addLayout(grid)

        # Detail Frame
        detail_frame = QFrame()
        detail_frame.setObjectName("Card")
        d_layout = QVBoxLayout(detail_frame)
        d_layout.setContentsMargins(16, 16, 16, 16)
        d_layout.setSpacing(10)

        d_title = QLabel("AUDIT LOG & TECHNICAL DETAILS:")
        d_title.setObjectName("CardTitle")
        d_layout.addWidget(d_title)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet(
            "background-color: #121215; color: #a0a0ab; border: 1px solid #242428; "
            "font-family: monospace; font-size: 11px; padding: 8px;"
        )
        self.detail_text.setFixedHeight(140)
        d_layout.addWidget(self.detail_text)

        layout.addWidget(detail_frame)
        layout.addStretch()

        self.run_probe()

    def run_probe(self):
        self.probe_btn.setEnabled(False)
        self.probe_btn.setText("PROBING NETWORK...")
        self.worker = LeakWorker()
        self.worker.finished_results.connect(self.on_probe_done)
        self.worker.start()

    def on_probe_done(self, data: dict):
        self.probe_btn.setEnabled(True)
        self.probe_btn.setText("RUN AUDIT PROBE")

        ident = data.get("ident", {})
        gw = data.get("gw", {})
        dns = data.get("dns", [])
        ipv6 = data.get("ipv6", {})

        # IP Card
        ip = ident.get("ip", "Unknown")
        isp = ident.get("isp", "Unknown")
        self.card_ip.set_value(ip)
        self.card_ip.subtitle_label.setText(f"{isp} • {ident.get('city', '')}, {ident.get('country', '')}")
        self.card_ip.set_pill("RESOLVED", "SECURE" if ident.get("is_mullvad") else "WARN")

        # Gateway Card
        iface = gw.get("interface", "Unknown")
        is_tun = gw.get("is_tunnel", False)
        self.card_gw.set_value(iface)
        if is_tun:
            self.card_gw.subtitle_label.setText(f"Default gateway {gw.get('gateway_ip')} via encrypted tunnel")
            self.card_gw.set_pill("TUNNEL SECURE", "SECURE")
        else:
            self.card_gw.subtitle_label.setText(f"WARNING: Direct bypass via unencrypted NIC {iface}")
            self.card_gw.set_pill("BYPASS DETECTED", "DANGER")

        # DNS Card
        dns_str = ", ".join(dns) if dns else "None detected"
        self.card_dns.set_value(f"{len(dns)} Nameservers")
        self.card_dns.subtitle_label.setText(dns_str)
        self.card_dns.set_pill("CHECKED", "SECURE")

        # IPv6 Card
        if ipv6.get("has_global_ipv6"):
            self.card_ipv6.set_value("LEAK DETECTED")
            self.card_ipv6.subtitle_label.setText("Routable global IPv6 detected in system")
            self.card_ipv6.set_pill("DANGER", "DANGER")
        else:
            self.card_ipv6.set_value("NO LEAK")
            self.card_ipv6.subtitle_label.setText("No external IPv6 traffic exposure")
            self.card_ipv6.set_pill("SECURE", "SECURE")

        # Detail report
        report = (
            f"=== LEAK AUDIT REPORT ===\n"
            f"External IP:       {ip}\n"
            f"ISP / ASN:         {isp}\n"
            f"Country:           {ident.get('country')}\n"
            f"Default Route:     {iface} -> {gw.get('gateway_ip')} (Tunnel: {is_tun})\n"
            f"Nameservers:       {dns_str}\n"
            f"IPv6 Status:       Supported={ipv6.get('ipv6_supported')}, GlobalLeak={ipv6.get('has_global_ipv6')}\n"
        )
        self.detail_text.setText(report)

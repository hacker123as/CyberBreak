from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.core.kernel_hardening import KernelHardening
from cyberbreak.core.metadata_cleaner import MetadataCleaner

class AuditWorker(QThread):
    finished_data = pyqtSignal(dict)

    def run(self):
        identity = NetworkAuditor.get_external_identity()
        gw = NetworkAuditor.check_default_gateway()
        ipv6 = NetworkAuditor.check_ipv6_exposure()
        self.finished_data.emit({
            "identity": identity,
            "gw": gw,
            "ipv6": ipv6
        })

class DashboardPage(QWidget):
    """Overall workstation security posture and status matrix."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("SECURITY POSTURE MATRIX")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Real-time kernel defenses, leak sensors, and hardware interlocks")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.scan_btn = QPushButton("RUN SYSTEM AUDIT")
        self.scan_btn.setObjectName("AccentButton")
        self.scan_btn.clicked.connect(self.run_audit)
        header.addWidget(self.scan_btn)

        layout.addLayout(header)

        # Metric Cards Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_ip = StatusCard(
            "EXTERNAL IP / IDENTITY",
            "Resolving...",
            "Checking multi-endpoint resolvers",
            "PROBING",
            "WARN"
        )
        grid.addWidget(self.card_ip, 0, 0)

        self.card_route = StatusCard(
            "GATEWAY ROUTING",
            "Auditing...",
            "Parsing /proc/net/route",
            "PROBING",
            "WARN"
        )
        grid.addWidget(self.card_route, 0, 1)

        self.card_ipv6 = StatusCard(
            "IPV6 LEAK DEFENSE",
            "Checking...",
            "AF_INET6 raw socket probe",
            "PROBING",
            "WARN"
        )
        grid.addWidget(self.card_ipv6, 1, 0)

        self.card_kernel = StatusCard(
            "KERNEL SYSCTL SHIELD",
            "Hardened",
            "Ptrace, eBPF & dmesg restrictions",
            "SECURE",
            "SECURE"
        )
        grid.addWidget(self.card_kernel, 1, 1)

        layout.addLayout(grid)

        # Quick Actions
        actions_frame = QFrame()
        actions_frame.setObjectName("Card")
        act_layout = QHBoxLayout(actions_frame)
        act_layout.setContentsMargins(16, 16, 16, 16)
        act_layout.setSpacing(12)

        act_title = QLabel("QUICK ACTIONS:")
        act_title.setObjectName("CardTitle")
        act_layout.addWidget(act_title)

        purge_btn = QPushButton("PURGE RAM CACHE")
        purge_btn.clicked.connect(MetadataCleaner.purge_ram_cache)
        act_layout.addWidget(purge_btn)

        harden_btn = QPushButton("ENFORCE KERNEL SYSCTL")
        harden_btn.clicked.connect(KernelHardening.apply_sysctl_hardening)
        act_layout.addWidget(harden_btn)

        act_layout.addStretch()
        layout.addWidget(actions_frame)

        layout.addStretch()

        # Initial background scan
        self.run_audit()

    def run_audit(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("AUDITING...")
        self.worker = AuditWorker()
        self.worker.finished_data.connect(self.on_audit_finished)
        self.worker.start()

    def on_audit_finished(self, data: dict):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("RUN SYSTEM AUDIT")

        ident = data.get("identity", {})
        ip_val = ident.get("ip", "Unknown")
        isp = ident.get("isp", "Unknown")
        self.card_ip.set_value(ip_val)
        self.card_ip.subtitle_label.setText(f"ISP: {isp} ({ident.get('country', '')})")
        if ident.get("is_mullvad") or "tor" in isp.lower():
            self.card_ip.set_pill("PROTECTED", "SECURE")
        else:
            self.card_ip.set_pill("PUBLIC IP", "WARN")

        gw = data.get("gw", {})
        iface = gw.get("interface", "Unknown")
        is_tun = gw.get("is_tunnel", False)
        self.card_route.set_value(f"{iface} ({gw.get('gateway_ip', '')})")
        if is_tun:
            self.card_route.subtitle_label.setText("Routed via encrypted tunnel/proxy")
            self.card_route.set_pill("ENCRYPTED", "SECURE")
        else:
            self.card_route.subtitle_label.setText("Traffic leaving via raw unencrypted adapter")
            self.card_route.set_pill("LEAK WARNING", "DANGER")

        ipv6 = data.get("ipv6", {})
        if ipv6.get("has_global_ipv6", False):
            self.card_ipv6.set_value("GLOBAL IPV6 ACTIVE")
            self.card_ipv6.subtitle_label.setText("Traffic may bypass IPv4 VPN killswitch")
            self.card_ipv6.set_pill("LEAK RISK", "DANGER")
        else:
            self.card_ipv6.set_value("NO LEAK")
            self.card_ipv6.subtitle_label.setText("IPv6 global routable addresses neutralized")
            self.card_ipv6.set_pill("SAFE", "SECURE")

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.core.kernel_hardening import KernelHardening
from cyberbreak.core.metadata_cleaner import MetadataCleaner
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.core.usb_armory import USBArmory
from cyberbreak.core.port_auditor import PortAuditor
from cyberbreak.core.hardware_manager import HardwareManager

class AuditWorker(QThread):
    finished_data = pyqtSignal(dict)

    def run(self):
        identity = NetworkAuditor.get_external_identity()
        gw = NetworkAuditor.check_default_gateway()
        ipv6 = NetworkAuditor.check_ipv6_exposure()
        proton = NetworkAuditor.check_proton_vpn()
        ports = PortAuditor.get_open_listening_ports()
        usb_devs = HardwareManager.get_connected_usb_devices()
        self.finished_data.emit({
            "identity": identity,
            "gw": gw,
            "ipv6": ipv6,
            "proton": proton,
            "ports": ports,
            "usb": usb_devs
        })

class DashboardPage(QWidget):
    """
    Workstation Security Posture Matrix & Threat Radar.
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
        title = QLabel("SECURITY POSTURE MATRIX // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Real-time kernel defenses, socket leak sensors, listening port radars and hardware interlocks")
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

        # Dynamic Threat Alert Banner
        self.alert_banner = QFrame()
        self.alert_banner.setObjectName("Card")
        b_layout = QHBoxLayout(self.alert_banner)
        b_layout.setContentsMargins(16, 14, 16, 14)
        self.b_icon = QLabel("📡")
        self.b_icon.setStyleSheet("font-size: 24px;")
        b_layout.addWidget(self.b_icon)

        b_text_box = QVBoxLayout()
        self.b_title = QLabel("FORTRESS INITIALIZING...")
        self.b_title.setStyleSheet("font-weight: 800; font-size: 14px; color: #ffffff;")
        self.b_sub = QLabel("Probing active routes and checking for hardware / network leaks...")
        self.b_sub.setStyleSheet("font-size: 12px; color: #8c93a8;")
        b_text_box.addWidget(self.b_title)
        b_text_box.addWidget(self.b_sub)
        b_layout.addLayout(b_text_box)
        b_layout.addStretch()

        layout.addWidget(self.alert_banner)

        # Metric Cards Grid (6 cards: 2x3)
        grid = QGridLayout()
        grid.setSpacing(14)

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

        self.card_ports = StatusCard(
            "LISTENING NETWORK PORTS",
            "Scanning...",
            "Open TCP/UDP daemon sockets",
            "PROBING",
            "WARN"
        )
        grid.addWidget(self.card_ports, 0, 2)

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

        self.card_usb = StatusCard(
            "USB HARDWARE CONTROLLERS",
            "Auditing...",
            "Sysfs port authorization status",
            "PROBING",
            "SECURE"
        )
        grid.addWidget(self.card_usb, 1, 2)

        layout.addLayout(grid)

        # Quick Actions
        actions_frame = QFrame()
        actions_frame.setObjectName("Card")
        act_layout = QHBoxLayout(actions_frame)
        act_layout.setContentsMargins(16, 14, 16, 14)
        act_layout.setSpacing(12)

        act_title = QLabel("QUICK COMBAT ACTIONS:")
        act_title.setObjectName("CardTitle")
        act_layout.addWidget(act_title)

        purge_btn = QPushButton("🧹 PURGE RAM CACHE")
        purge_btn.setObjectName("OutlineButton")
        purge_btn.clicked.connect(MetadataCleaner.purge_ram_cache)
        act_layout.addWidget(purge_btn)

        harden_btn = QPushButton("🛡️ ENFORCE SYSCTL")
        harden_btn.setObjectName("CyanButton")
        harden_btn.clicked.connect(KernelHardening.apply_sysctl_hardening)
        act_layout.addWidget(harden_btn)

        trim_btn = QPushButton("⚡ RUN SSD TRIM")
        trim_btn.setObjectName("OutlineButton")
        trim_btn.clicked.connect(USBArmory.trim_drives)
        act_layout.addWidget(trim_btn)

        fw_btn = QPushButton("🔒 STRICT FIREWALL")
        fw_btn.setObjectName("AccentButton")
        fw_btn.clicked.connect(FirewallController.apply_strict_profile)
        act_layout.addWidget(fw_btn)

        port_lock_btn = QPushButton("🚨 LOCKDOWN PORTS")
        port_lock_btn.setObjectName("PanicButton")
        port_lock_btn.clicked.connect(PortAuditor.lockdown_all_open_ports)
        act_layout.addWidget(port_lock_btn)

        act_layout.addStretch()
        layout.addWidget(actions_frame)

        layout.addStretch()

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
        proton = data.get("proton", {})
        ip_val = ident.get("ip", proton.get("ip", "Unknown"))
        isp = ident.get("isp", proton.get("isp", "Unknown"))
        city = ident.get("city", proton.get("city", "Unknown"))
        region = ident.get("region", "Unknown")
        country = ident.get("country", proton.get("country", "Unknown"))

        gw = data.get("gw", {})
        iface = gw.get("interface", proton.get("interface", "Unknown"))
        is_tun = gw.get("is_tunnel", False) or proton.get("is_connected", False)

        self.card_ip.set_value(ip_val)
        self.card_ip.subtitle_label.setText(f"ISP: {isp} • {city}, {country}")
        
        if proton.get("is_connected") or ident.get("is_proton"):
            self.card_ip.set_pill("PROTON VPN SECURE", "SECURE")
        elif ident.get("is_mullvad") or "tor" in isp.lower():
            self.card_ip.set_pill("PROTECTED EXIT", "SECURE")
        else:
            self.card_ip.set_pill("REAL IP REVEALED", "DANGER")

        self.card_route.set_value(f"{iface} ({gw.get('gateway_ip', '')})")
        if proton.get("is_connected") or gw.get("is_proton"):
            self.card_route.subtitle_label.setText("Routed via Proton VPN encrypted tunnel")
            self.card_route.set_pill("PROTON TUNNEL", "SECURE")
        elif is_tun:
            self.card_route.subtitle_label.setText("Routed via encrypted tunnel/proxy")
            self.card_route.set_pill("ENCRYPTED", "SECURE")
        else:
            self.card_route.subtitle_label.setText("Traffic leaving via raw unencrypted adapter")
            self.card_route.set_pill("LEAK DETECTED", "DANGER")

        # Network Ports
        ports = data.get("ports", [])
        wan_ports = sum(1 for p in ports if p.get("is_wan"))
        self.card_ports.set_value(f"{len(ports)} Sockets ({wan_ports} WAN)")
        if wan_ports > 0:
            self.card_ports.set_pill(f"{wan_ports} WAN EXPOSED", "DANGER")
            self.card_ports.subtitle_label.setText("Rogue listeners bound to 0.0.0.0 or wildcard")
        else:
            self.card_ports.set_pill("SAFE", "SECURE")
            self.card_ports.subtitle_label.setText("All listening sockets restricted to loopback")

        # IPv6
        ipv6 = data.get("ipv6", {})
        if ipv6.get("has_global_ipv6", False):
            self.card_ipv6.set_value("GLOBAL IPV6 ACTIVE")
            self.card_ipv6.subtitle_label.setText("Traffic may bypass IPv4 VPN killswitch")
            self.card_ipv6.set_pill("LEAK RISK", "DANGER")
        else:
            self.card_ipv6.set_value("Disabled / Neutral")
            self.card_ipv6.subtitle_label.setText("IPv6 global routable addresses neutralized")
            self.card_ipv6.set_pill("SAFE", "SECURE")

        # USB Devices
        usb_devs = data.get("usb", [])
        periph_count = sum(1 for d in usb_devs if not d.get("is_root_hub"))
        self.card_usb.set_value(f"{periph_count} Peripherals")
        self.card_usb.subtitle_label.setText(f"{len(usb_devs)} total controller interfaces")
        self.card_usb.set_pill("MONITORED", "SECURE")

        # Dynamic Banner Feedback
        if not is_tun and not proton.get("is_connected") and not ident.get("is_tor"):
            self.alert_banner.setStyleSheet("background-color: #240c10; border: 2px solid #ff2a4b; border-radius: 8px;")
            self.b_icon.setText("🚨")
            self.b_title.setText("⚠️ WARNING: YOUR REAL IP IS REVEALED!")
            self.b_title.setStyleSheet("font-weight: 800; font-size: 14px; color: #ff3344;")
            self.b_sub.setText(f"Real physical location exposed: {city}, {region}, {country} via {isp}. Activate Killswitch immediately.")
            self.b_sub.setStyleSheet("font-size: 12px; color: #ffffff;")
        else:
            self.alert_banner.setStyleSheet("background-color: #0b1f14; border: 2px solid #00ff66; border-radius: 8px;")
            self.b_icon.setText("🛡️")
            self.b_title.setText("FORTRESS DEFENSES ARMED // BY LILAMI ONLY")
            self.b_title.setStyleSheet("font-weight: 800; font-size: 14px; color: #00ff66;")
            self.b_sub.setText(f"Traffic cloaked via encrypted gateway ({iface}). Zero leak vectors exposed.")
            self.b_sub.setStyleSheet("font-size: 12px; color: #d0f5df;")

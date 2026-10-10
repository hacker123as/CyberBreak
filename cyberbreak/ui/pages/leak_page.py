from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.ui.widgets.status_card import StatusCard

class LeakWorker(QThread):
    finished_results = pyqtSignal(dict)

    def run(self):
        ident = NetworkAuditor.get_external_identity()
        gw = NetworkAuditor.check_default_gateway()
        dns = NetworkAuditor.check_dns_resolvers()
        ipv6 = NetworkAuditor.check_ipv6_exposure()
        proton = NetworkAuditor.check_proton_vpn()
        self.finished_results.emit({
            "ident": ident,
            "gw": gw,
            "dns": dns,
            "ipv6": ipv6,
            "proton": proton
        })

class LeakPage(QWidget):
    """
    Military-grade socket audit, IP exposure radar, and DNS/IPv6 leak sensor.
    Engineered by lilami.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("COMPREHENSIVE LEAK & ROUTING AUDITOR // By lilami")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Deep socket inspection, ISP fingerprinting, physical city/state detection & route analysis")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.probe_btn = QPushButton("RUN LIVE AUDIT PROBE")
        self.probe_btn.setObjectName("AccentButton")
        self.probe_btn.clicked.connect(self.run_probe)
        header.addWidget(self.probe_btn)

        layout.addLayout(header)

        # Dynamic Giant Status Banner
        self.banner_frame = QFrame()
        self.banner_frame.setObjectName("Card")
        self.banner_layout = QHBoxLayout(self.banner_frame)
        self.banner_layout.setContentsMargins(18, 16, 18, 16)
        self.banner_layout.setSpacing(14)

        self.banner_icon = QLabel("📡")
        self.banner_icon.setStyleSheet("font-size: 26px;")
        self.banner_layout.addWidget(self.banner_icon)

        banner_text_box = QVBoxLayout()
        self.banner_title = QLabel("PROBING SYSTEM FOR IP & ROUTING LEAKS...")
        self.banner_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff;")
        self.banner_subtitle = QLabel("Querying network sockets, route tables, and external endpoints...")
        self.banner_subtitle.setStyleSheet("font-size: 12px; color: #8c92a6;")
        banner_text_box.addWidget(self.banner_title)
        banner_text_box.addWidget(self.banner_subtitle)
        self.banner_layout.addLayout(banner_text_box)

        self.banner_layout.addStretch()

        self.seal_btn = QPushButton("🔒 SEAL LEAKS NOW")
        self.seal_btn.setObjectName("PanicButton")
        self.seal_btn.setVisible(False)
        self.seal_btn.clicked.connect(self.seal_leaks_immediately)
        self.banner_layout.addWidget(self.seal_btn)

        layout.addWidget(self.banner_frame)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(14)

        self.card_ip = StatusCard("PUBLIC IP EXPOSURE", "Probing...", "External endpoint query", "", "WARN")
        grid.addWidget(self.card_ip, 0, 0)

        self.card_geo = StatusCard("GEOLOCATION INTEL", "Probing...", "City, State & Region", "", "WARN")
        grid.addWidget(self.card_geo, 0, 1)

        self.card_isp = StatusCard("ISP & CARRIER ASN", "Probing...", "Telecom route entity", "", "WARN")
        grid.addWidget(self.card_isp, 1, 0)

        self.card_gw = StatusCard("GATEWAY ROUTE", "Probing...", "/proc/net/route parser", "", "WARN")
        grid.addWidget(self.card_gw, 1, 1)

        self.card_dns = StatusCard("ACTIVE DNS RESOLVERS", "Probing...", "/etc/resolv.conf query", "", "WARN")
        grid.addWidget(self.card_dns, 2, 0)

        self.card_ipv6 = StatusCard("RAW IPV6 EXPOSURE", "Probing...", "AF_INET6 socket bind test", "", "WARN")
        grid.addWidget(self.card_ipv6, 2, 1)

        layout.addLayout(grid)

        # Technical Detail Log Frame
        detail_frame = QFrame()
        detail_frame.setObjectName("Card")
        d_layout = QVBoxLayout(detail_frame)
        d_layout.setContentsMargins(16, 14, 16, 14)
        d_layout.setSpacing(8)

        d_title = QLabel("FORENSIC NETWORK AUDIT LOG:")
        d_title.setObjectName("CardTitle")
        d_layout.addWidget(d_title)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet(
            "background-color: #0d0e14; color: #a4abbd; border: 1px solid #232635; "
            "font-family: monospace; font-size: 11px; padding: 8px; border-radius: 6px;"
        )
        self.detail_text.setFixedHeight(120)
        d_layout.addWidget(self.detail_text)

        layout.addWidget(detail_frame)

        self.run_probe()

    def run_probe(self):
        self.probe_btn.setEnabled(False)
        self.probe_btn.setText("PROBING NETWORK...")
        self.banner_title.setText("AUDITING NETWORK PRIVACY & SCANNING FOR LEAKS...")
        self.banner_subtitle.setText("Performing socket binds, route table audits, and external geo lookups...")
        self.banner_frame.setStyleSheet("background-color: #13141b; border: 1px solid #242736;")
        self.seal_btn.setVisible(False)

        self.worker = LeakWorker()
        self.worker.finished_results.connect(self.on_probe_done)
        self.worker.start()

    def on_probe_done(self, data: dict):
        self.probe_btn.setEnabled(True)
        self.probe_btn.setText("RUN LIVE AUDIT PROBE")

        ident = data.get("ident", {})
        gw = data.get("gw", {})
        dns = data.get("dns", [])
        ipv6 = data.get("ipv6", {})
        proton = data.get("proton", {})

        ip = ident.get("ip", proton.get("ip", "Unknown"))
        isp = ident.get("isp", proton.get("isp", "Unknown"))
        city = ident.get("city", proton.get("city", "Unknown"))
        region = ident.get("region", "Unknown")
        country = ident.get("country", proton.get("country", "Unknown"))
        postal = ident.get("postal", "Unknown")
        asn = ident.get("asn", "Unknown")

        is_tunnel = gw.get("is_tunnel", False) or proton.get("is_connected", False)
        is_leak = ident.get("is_leak", True) and not is_tunnel

        # IP Card
        self.card_ip.set_value(ip)
        self.card_ip.subtitle_label.setText(f"{country} ({ident.get('timezone', 'UTC')})")
        if proton.get("is_connected") or ident.get("is_proton"):
            self.card_ip.set_pill("PROTON VPN SECURED", "SECURE")
        elif ident.get("is_mullvad"):
            self.card_ip.set_pill("MULLVAD SECURED", "SECURE")
        elif ident.get("is_tor"):
            self.card_ip.set_pill("TOR EXIT SECURED", "SECURE")
        else:
            self.card_ip.set_pill("REAL IP EXPOSED", "DANGER")

        # Geo Card
        geo_str = f"{city}, {region}" if region != "Unknown" else city
        self.card_geo.set_value(geo_str[:22])
        self.card_geo.subtitle_label.setText(f"Postal: {postal} • Country: {country}")
        if is_leak:
            self.card_geo.set_pill("COORDINATES EXPOSED", "DANGER")
        else:
            self.card_geo.set_pill("CLOAKED EXIT", "SECURE")

        # ISP Card
        self.card_isp.set_value(isp[:22])
        self.card_isp.subtitle_label.setText(f"ASN: {asn}")
        if is_leak:
            self.card_isp.set_pill("RESIDENTIAL ISP", "DANGER")
        else:
            self.card_isp.set_pill("ENCRYPTED TRANSIT", "SECURE")

        # Gateway Card
        iface = gw.get("interface", proton.get("interface", "Unknown"))
        self.card_gw.set_value(iface)
        if proton.get("is_connected") or gw.get("is_proton"):
            self.card_gw.subtitle_label.setText(f"Default gateway via Proton VPN tunnel ({iface})")
            self.card_gw.set_pill("PROTON TUNNEL", "SECURE")
        elif is_tunnel:
            self.card_gw.subtitle_label.setText(f"Default route {gw.get('gateway_ip')} via encrypted tunnel")
            self.card_gw.set_pill("TUNNEL ACTIVE", "SECURE")
        else:
            self.card_gw.subtitle_label.setText(f"Direct bypass on unencrypted NIC {iface}")
            self.card_gw.set_pill("DIRECT BYPASS", "DANGER")

        # DNS Card
        if dns:
            dns_txt = ", ".join(dns[:2])
            self.card_dns.set_value(dns_txt)
            if any(d in ("10.", "172.", "192.168.", "127.0.0.1", "10.2.0.1") for d in dns):
                self.card_dns.subtitle_label.setText("Private tunnel DNS nameserver")
                self.card_dns.set_pill("SECURE DNS", "SECURE")
            else:
                self.card_dns.subtitle_label.setText(f"Upstream public resolvers: {dns_txt}")
                self.card_dns.set_pill("POTENTIAL DNS LEAK", "WARN")
        else:
            self.card_dns.set_value("No Resolvers")
            self.card_dns.subtitle_label.setText("DNS queries currently unreachable")
            self.card_dns.set_pill("ISOLATED", "WARN")

        # IPv6 Card
        if ipv6.get("has_global_ipv6"):
            self.card_ipv6.set_value("LEAKING")
            self.card_ipv6.subtitle_label.setText(f"Global IPv6 active on: {', '.join(ipv6.get('addresses', []))}")
            self.card_ipv6.set_pill("IPV6 LEAK DETECTED", "DANGER")
        else:
            self.card_ipv6.set_value("Disabled / Neutral")
            self.card_ipv6.subtitle_label.setText("No global scope IPv6 leaks found in kernel")
            self.card_ipv6.set_pill("IPV6 NEUTRALIZED", "SECURE")

        # Update Giant Banner
        if is_leak:
            self.banner_frame.setStyleSheet(
                "background-color: #240c10; border: 2px solid #ff2a4b; border-radius: 8px;"
            )
            self.banner_icon.setText("🚨")
            self.banner_title.setText("⚠️ WARNING: YOUR REAL IP IS REVEALED!")
            self.banner_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #ff3344;")
            self.banner_subtitle.setText(
                f"Your real IP ({ip}), ISP ({isp}), and physical location (City: {city}, State: {region}, Country: {country}) "
                "are exposed! Remote servers can identify and track your workstation."
            )
            self.banner_subtitle.setStyleSheet("font-size: 12px; color: #ffffff;")
            self.seal_btn.setVisible(True)
        else:
            self.banner_frame.setStyleSheet(
                "background-color: #0b1f14; border: 2px solid #00ff66; border-radius: 8px;"
            )
            self.banner_icon.setText("🛡️")
            self.banner_title.setText("FORTRESS SHIELD ACTIVE: IP & TRAFFIC ENCRYPTED")
            self.banner_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #00ff66;")
            self.banner_subtitle.setText(
                f"Workstation protected via encrypted tunnel. Exit node: {country} ({city}). Zero IP/DNS/IPv6 leaks revealed."
            )
            self.banner_subtitle.setStyleSheet("font-size: 12px; color: #d0f5df;")
            self.seal_btn.setVisible(False)

        # Log Details
        log_entries = [
            f"[AUDIT COMPLETE] Public IP: {ip}",
            f"[LOCATION] City: {city} | State/Region: {region} | Country: {country} | Postal: {postal}",
            f"[NETWORK] ISP: {isp} | ASN: {asn} | Interface: {iface}",
            f"[TUNNEL STATUS] Encrypted: {is_tunnel} | Leak Detected: {is_leak}",
            f"[NAMESERVERS] {dns}",
            f"[IPV6] Global Exposure: {ipv6.get('has_global_ipv6', False)}"
        ]
        self.detail_text.setText("\n".join(log_entries))

    def seal_leaks_immediately(self):
        self.seal_btn.setEnabled(False)
        self.seal_btn.setText("SEALING...")
        FirewallController.apply_vpn_only_firewall()
        self.run_probe()

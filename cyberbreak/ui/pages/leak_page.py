from PyQt6.QtWidgets import QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QTextEdit
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.ui.widgets.glass import GlassFrame, icon

class LeakWorker(QThread):
    finished_results = pyqtSignal(dict)

    def run(self):
        ident = NetworkAuditor.get_external_identity()
        gw = NetworkAuditor.check_default_gateway()
        dns = NetworkAuditor.check_dns_resolvers()
        ipv6 = NetworkAuditor.check_ipv6_exposure()
        proton = NetworkAuditor.check_proton_vpn()
        self.finished_results.emit({'ident': ident, 'gw': gw, 'dns': dns, 'ipv6': ipv6, 'proton': proton})

class LeakPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(8)
        title = QLabel('Network privacy')
        title.setObjectName('HeaderTitle')
        title.setWordWrap(True)
        subtitle = QLabel('Inspect your public identity, DNS resolvers, and network routes.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        self.probe_btn = QPushButton('Run privacy audit')
        self.probe_btn.setObjectName('AccentButton')
        self.probe_btn.clicked.connect(self.run_probe)
        header.addWidget(self.probe_btn)
        layout.addLayout(header)
        self.banner_frame = QFrame()
        self.banner_frame.setObjectName('Card')
        self.banner_layout = QHBoxLayout(self.banner_frame)
        self.banner_layout.setContentsMargins(22, 22, 22, 22)
        self.banner_layout.setSpacing(14)
        self.banner_icon = QLabel()
        self.banner_icon.setPixmap(icon('route', '#8fa8ff', 28).pixmap(28, 28))
        self.banner_icon.setFixedSize(36, 36)
        self.banner_layout.addWidget(self.banner_icon)
        banner_text_box = QVBoxLayout()
        self.banner_title = QLabel('Checking your network')
        self.banner_title.setObjectName('CardTitle')
        self.banner_subtitle = QLabel('Querying network sockets, route tables, and external endpoints...')
        self.banner_subtitle.setObjectName('HeaderSubtitle')
        self.banner_subtitle.setWordWrap(True)
        banner_text_box.addWidget(self.banner_title)
        banner_text_box.addWidget(self.banner_subtitle)
        self.banner_layout.addLayout(banner_text_box, 1)
        self.seal_btn = QPushButton('Enable VPN-only policy')
        self.seal_btn.setIcon(icon('shield'))
        self.seal_btn.setObjectName('PanicButton')
        self.seal_btn.setVisible(False)
        self.seal_btn.clicked.connect(self.seal_leaks_immediately)
        self.banner_layout.addWidget(self.seal_btn)
        layout.addWidget(self.banner_frame)
        grid = QGridLayout()
        grid.setSpacing(16)
        self.card_ip = StatusCard('Public IP exposure', 'Checking…', 'External endpoint query', '', 'WARN')
        grid.addWidget(self.card_ip, 0, 0)
        self.card_geo = StatusCard('Exit location', 'Checking…', 'City, State & Region', '', 'WARN')
        grid.addWidget(self.card_geo, 0, 1)
        self.card_isp = StatusCard('Network provider', 'Checking…', 'Telecom route entity', '', 'WARN')
        grid.addWidget(self.card_isp, 1, 0)
        self.card_gw = StatusCard('Gateway route', 'Checking…', '/proc/net/route parser', '', 'WARN')
        grid.addWidget(self.card_gw, 1, 1)
        self.card_dns = StatusCard('Active DNS resolvers', 'Checking…', '/etc/resolv.conf query', '', 'WARN')
        grid.addWidget(self.card_dns, 2, 0)
        self.card_ipv6 = StatusCard('IPv6 exposure', 'Checking…', 'AF_INET6 socket bind test', '', 'WARN')
        grid.addWidget(self.card_ipv6, 2, 1)
        layout.addLayout(grid)
        detail_frame = GlassFrame()
        detail_frame.setObjectName('GlassCard')
        d_layout = QVBoxLayout(detail_frame)
        d_layout.setContentsMargins(22, 22, 22, 22)
        d_layout.setSpacing(8)
        d_title = QLabel('Audit details')
        d_title.setObjectName('CardTitle')
        d_layout.addWidget(d_title)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setObjectName('Terminal')
        self.detail_text.setFixedHeight(120)
        d_layout.addWidget(self.detail_text)
        layout.addWidget(detail_frame)
        self.run_probe()

    def run_probe(self):
        self.probe_btn.setEnabled(False)
        self.probe_btn.setText('Running audit…')
        self.banner_title.setText('Checking your network')
        self.banner_subtitle.setText('Performing socket binds, route table audits, and external geo lookups...')
        self.banner_frame.setStyleSheet('QFrame#Card { background: rgba(255, 255, 255, 8); border: 1px solid rgba(255, 255, 255, 18); border-radius: 20px; }')
        self.seal_btn.setVisible(False)
        self.worker = LeakWorker()
        self.worker.finished_results.connect(self.on_probe_done)
        self.worker.start()

    def on_probe_done(self, data: dict):
        self.probe_btn.setEnabled(True)
        self.probe_btn.setText('Run privacy audit')
        ident = data.get('ident', {})
        gw = data.get('gw', {})
        dns = data.get('dns', [])
        ipv6 = data.get('ipv6', {})
        proton = data.get('proton', {})
        ip = ident.get('ip', proton.get('ip', 'Unknown'))
        isp = ident.get('isp', proton.get('isp', 'Unknown'))
        city = ident.get('city', proton.get('city', 'Unknown'))
        region = ident.get('region', 'Unknown')
        country = ident.get('country', proton.get('country', 'Unknown'))
        postal = ident.get('postal', 'Unknown')
        asn = ident.get('asn', 'Unknown')
        is_tunnel = gw.get('is_tunnel', False) or proton.get('is_connected', False)
        is_leak = ident.get('is_leak', True) and (not is_tunnel)
        self.card_ip.set_value(ip)
        self.card_ip.subtitle_label.setText(f"{country} ({ident.get('timezone', 'UTC')})")
        if proton.get('is_connected') or ident.get('is_proton'):
            self.card_ip.set_pill('Proton VPN secured', 'SECURE')
        elif ident.get('is_mullvad'):
            self.card_ip.set_pill('Mullvad secured', 'SECURE')
        elif ident.get('is_tor'):
            self.card_ip.set_pill('Tor exit secured', 'SECURE')
        else:
            self.card_ip.set_pill('Real IP exposed', 'DANGER')
        geo_str = f'{city}, {region}' if region != 'Unknown' else city
        self.card_geo.set_value(geo_str[:22])
        self.card_geo.subtitle_label.setText(f'Postal: {postal} • Country: {country}')
        if is_leak:
            self.card_geo.set_pill('Public location', 'DANGER')
        else:
            self.card_geo.set_pill('Tunnel exit', 'SECURE')
        self.card_isp.set_value(isp[:22])
        self.card_isp.subtitle_label.setText(f'ASN: {asn}')
        if is_leak:
            self.card_isp.set_pill('Residential ISP', 'DANGER')
        else:
            self.card_isp.set_pill('Tunnel route', 'SECURE')
        iface = gw.get('interface', proton.get('interface', 'Unknown'))
        self.card_gw.set_value(iface)
        if proton.get('is_connected') or gw.get('is_proton'):
            self.card_gw.subtitle_label.setText(f'Default gateway via Proton VPN tunnel ({iface})')
            self.card_gw.set_pill('Proton tunnel', 'SECURE')
        elif is_tunnel:
            self.card_gw.subtitle_label.setText(f"Default route {gw.get('gateway_ip')} via encrypted tunnel")
            self.card_gw.set_pill('Tunnel active', 'SECURE')
        else:
            self.card_gw.subtitle_label.setText(f'Direct bypass on unencrypted NIC {iface}')
            self.card_gw.set_pill('Direct bypass', 'DANGER')
        if dns:
            dns_txt = ', '.join(dns[:2])
            self.card_dns.set_value(dns_txt)
            if any((d in ('10.', '172.', '192.168.', '127.0.0.1', '10.2.0.1') for d in dns)):
                self.card_dns.subtitle_label.setText('Private tunnel DNS nameserver')
                self.card_dns.set_pill('Secure DNS', 'SECURE')
            else:
                self.card_dns.subtitle_label.setText(f'Upstream public resolvers: {dns_txt}')
                self.card_dns.set_pill('Potential DNS leak', 'WARN')
        else:
            self.card_dns.set_value('No Resolvers')
            self.card_dns.subtitle_label.setText('DNS queries currently unreachable')
            self.card_dns.set_pill('Isolated', 'WARN')
        if ipv6.get('has_global_ipv6'):
            self.card_ipv6.set_value('Leaking')
            self.card_ipv6.subtitle_label.setText(f"Global IPv6 active on: {', '.join(ipv6.get('addresses', []))}")
            self.card_ipv6.set_pill('IPv6 leak detected', 'DANGER')
        else:
            self.card_ipv6.set_value('Disabled / Neutral')
            self.card_ipv6.subtitle_label.setText('No global scope IPv6 leaks found in kernel')
            self.card_ipv6.set_pill('IPv6 neutralized', 'SECURE')
        if is_leak:
            self.banner_frame.setStyleSheet('QFrame#Card { background: rgba(255, 130, 148, 12); border: 1px solid rgba(255, 130, 148, 48); border-radius: 20px; }')
            self.banner_icon.setPixmap(icon('alert', '#ff8294', 28).pixmap(28, 28))
            self.banner_title.setText('Public identity exposed')
            self.banner_title.setObjectName('CardTitle')
            self.banner_subtitle.setText(f'Public IP {ip} is visible on a direct route. Provider: {isp}. Reported location: {city}, {country}.')
            self.banner_subtitle.setObjectName('HeaderSubtitle')
            self.banner_subtitle.setWordWrap(True)
            self.seal_btn.setVisible(True)
        else:
            self.banner_frame.setStyleSheet('QFrame#Card { background: rgba(101, 219, 197, 10); border: 1px solid rgba(101, 219, 197, 42); border-radius: 20px; }')
            self.banner_icon.setPixmap(icon('shield', '#65dbc5', 28).pixmap(28, 28))
            self.banner_title.setText('Encrypted route detected')
            self.banner_title.setObjectName('CardTitle')
            self.banner_subtitle.setText(f'An encrypted route is active. Exit location: {city}, {country}. Review DNS and IPv6 findings below.')
            self.banner_subtitle.setObjectName('HeaderSubtitle')
            self.banner_subtitle.setWordWrap(True)
            self.seal_btn.setVisible(False)
        log_entries = [f'[AUDIT COMPLETE] Public IP: {ip}', f'[LOCATION] City: {city} | State/Region: {region} | Country: {country} | Postal: {postal}', f'[NETWORK] ISP: {isp} | ASN: {asn} | Interface: {iface}', f'[TUNNEL STATUS] Encrypted: {is_tunnel} | Leak Detected: {is_leak}', f'[NAMESERVERS] {dns}', f"[IPV6] Global Exposure: {ipv6.get('has_global_ipv6', False)}"]
        self.detail_text.setText('\n'.join(log_entries))

    def seal_leaks_immediately(self):
        self.seal_btn.setEnabled(False)
        self.seal_btn.setText('Applying policy…')
        FirewallController.apply_vpn_only_firewall()
        self.run_probe()

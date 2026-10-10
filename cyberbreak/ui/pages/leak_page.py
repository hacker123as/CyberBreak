import ipaddress
from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QTextEdit
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.ui.widgets.glass import GlassFrame, icon
from cyberbreak.ui.widgets.status_card import StatusCard


class LeakWorker(QThread):
    finished_results = pyqtSignal(dict)

    def run(self):
        data = {'errors': []}
        probes = (
            ('ident', NetworkAuditor.get_external_identity),
            ('gw', NetworkAuditor.check_default_gateway),
            ('dns', NetworkAuditor.check_dns_resolvers),
            ('ipv6', NetworkAuditor.check_ipv6_exposure),
        )
        for key, probe in probes:
            if self.isInterruptionRequested():
                return
            try:
                data[key] = probe()
            except Exception as error:
                data['errors'].append(f'{key}: {error}')
        if not self.isInterruptionRequested():
            try:
                data['proton'] = NetworkAuditor.check_proton_vpn(data.get('ident', {}), data.get('gw', {}))
            except Exception as error:
                data['errors'].append(f'proton: {error}')
            self.finished_results.emit(data)


class FirewallPolicyWorker(QThread):
    result = pyqtSignal(bool, str)

    def run(self):
        try:
            ok, message = FirewallController.apply_vpn_killswitch()
            self.result.emit(ok, message)
        except Exception as error:
            self.result.emit(False, str(error))


class LeakPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.policy_worker = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)
        header = QHBoxLayout()
        headings = QVBoxLayout()
        title = QLabel('Network privacy')
        title.setObjectName('HeaderTitle')
        subtitle = QLabel('Inspect the actual route, public exit address and local DNS configuration.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        headings.addWidget(title)
        headings.addWidget(subtitle)
        header.addLayout(headings, 1)
        self.probe_btn = QPushButton('Run privacy audit')
        self.probe_btn.setObjectName('AccentButton')
        self.probe_btn.setIcon(icon('refresh', '#ffffff'))
        self.probe_btn.clicked.connect(self.run_probe)
        header.addWidget(self.probe_btn)
        layout.addLayout(header)
        self.banner_frame = GlassFrame()
        self.banner_layout = QHBoxLayout(self.banner_frame)
        self.banner_layout.setContentsMargins(22, 22, 22, 22)
        self.banner_icon = QLabel()
        self.banner_icon.setFixedSize(36, 36)
        self.banner_icon.setPixmap(icon('route', '#8fa8ff', 28).pixmap(28, 28))
        self.banner_layout.addWidget(self.banner_icon)
        copy = QVBoxLayout()
        self.banner_title = QLabel('Checking your network')
        self.banner_title.setObjectName('CardTitle')
        self.banner_subtitle = QLabel('Reading local routes and querying the public exit address.')
        self.banner_subtitle.setObjectName('HeaderSubtitle')
        self.banner_subtitle.setWordWrap(True)
        copy.addWidget(self.banner_title)
        copy.addWidget(self.banner_subtitle)
        self.banner_layout.addLayout(copy, 1)
        self.seal_btn = QPushButton('Apply VPN-only policy')
        self.seal_btn.setObjectName('WarningButton')
        self.seal_btn.setIcon(icon('shield'))
        self.seal_btn.clicked.connect(self.seal_leaks_immediately)
        self.seal_btn.hide()
        self.banner_layout.addWidget(self.seal_btn)
        layout.addWidget(self.banner_frame)
        grid = QGridLayout()
        grid.setSpacing(16)
        definitions = (
            ('card_ip', 'Public exit IP', 'globe'), ('card_geo', 'Exit location', 'globe'),
            ('card_isp', 'Reported provider', 'layers'), ('card_gw', 'Gateway route', 'route'),
            ('card_dns', 'Configured DNS', 'activity'), ('card_ipv6', 'IPv6 route', 'route'),
        )
        for index, (name, title, glyph) in enumerate(definitions):
            card = StatusCard(title, 'Checking…', '', 'Not verified', 'WARN', icon_name=glyph)
            setattr(self, name, card)
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        frame = GlassFrame()
        details = QVBoxLayout(frame)
        details.setContentsMargins(20, 18, 20, 18)
        label = QLabel('Audit evidence')
        label.setObjectName('CardTitle')
        details.addWidget(label)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setObjectName('Terminal')
        self.detail_text.setMinimumHeight(160)
        self.detail_text.setMaximumHeight(230)
        details.addWidget(self.detail_text)
        layout.addWidget(frame)
        self.run_probe()

    def run_probe(self):
        if getattr(self.window(), '_closing', False) or (self.worker is not None and self.worker.isRunning()):
            return
        self.probe_btn.setEnabled(False)
        self.probe_btn.setText('Running audit…')
        self.banner_title.setText('Checking your network')
        self.banner_subtitle.setText('Reading policy-aware routes, active interfaces and the public exit address.')
        self.worker = LeakWorker(self)
        self.worker.finished_results.connect(self.on_probe_done)
        self.worker.finished.connect(self.release_worker)
        self.worker.start()

    def release_worker(self):
        worker = self.sender()
        if self.worker is worker:
            self.worker = None
        if self.policy_worker is worker:
            self.policy_worker = None
        worker.deleteLater()

    @staticmethod
    def known(value):
        return value is not None and str(value).strip().casefold() not in ('', 'unknown', 'none', 'n/a')

    def unavailable(self, card, reason):
        card.set_value('Unavailable')
        card.subtitle_label.setText(reason)
        card.set_pill('Not verified', 'WARN')

    def on_probe_done(self, data):
        self.probe_btn.setEnabled(True)
        self.probe_btn.setText('Run privacy audit')
        ident, gw = data.get('ident', {}), data.get('gw', {})
        ipv6, proton = data.get('ipv6', {}), data.get('proton', {})
        dns = data.get('dns', [])
        tunnel_verified = bool(gw.get('route_verified') and gw.get('is_tunnel'))
        route_known = bool(gw.get('available'))
        ip_known = bool(ident.get('available') and self.known(ident.get('ip')))
        if ip_known:
            self.card_ip.set_value(ident['ip'])
            self.card_ip.subtitle_label.setText('Every visited website can see this public exit IP.')
            self.card_ip.set_pill('Tunnel route observed' if tunnel_verified else 'Public IP visible', 'SECURE' if tunnel_verified else 'WARN')
        else:
            self.unavailable(self.card_ip, 'The identity endpoints did not return a valid public address.')
        location = ', '.join(str(ident.get(key)) for key in ('city', 'region', 'country') if self.known(ident.get(key)))
        if ip_known and location:
            self.card_geo.set_value(location)
            self.card_geo.subtitle_label.setText('Approximate IP-based exit location; GPS permission is separate.')
            self.card_geo.set_pill('Reported location', 'WARN')
        else:
            self.unavailable(self.card_geo, 'No IP-based location was reported.')
        if ip_known and self.known(ident.get('isp')):
            self.card_isp.set_value(ident['isp'])
            self.card_isp.subtitle_label.setText(f"ASN: {ident.get('asn', 'Unknown')}. Provider ownership is not verified by a label.")
            self.card_isp.set_pill('Provider indicator', 'WARN')
        else:
            self.unavailable(self.card_isp, 'No provider information was reported.')
        if route_known:
            self.card_gw.set_value(gw.get('interface', 'Unknown'))
            self.card_gw.subtitle_label.setText('Policy lookup used two destinations and checked active interface state.' if gw.get('policy_routing_checked') else 'Fallback route table data; routing policy has not been verified.')
            self.card_gw.set_pill('Tunnel route verified' if tunnel_verified else 'Direct / unverified route', 'SECURE' if tunnel_verified else 'WARN')
        else:
            self.unavailable(self.card_gw, 'Local routing data is unavailable on this host.')
        if dns:
            self.card_dns.set_value(', '.join(dns))
            local = []
            for resolver in dns:
                try:
                    address = ipaddress.ip_address(resolver)
                    local.append(address.is_private or address.is_loopback)
                except ValueError:
                    local.append(False)
            self.card_dns.subtitle_label.setText('Local/private resolver addresses. This alone does not establish DNS routing or encryption.' if all(local) else 'Resolver addresses alone do not establish whether DNS follows the VPN.')
            self.card_dns.set_pill('Configuration read', 'WARN')
        else:
            self.unavailable(self.card_dns, 'No resolver configuration was available; this does not establish isolation.')
        if not ipv6.get('available'):
            self.unavailable(self.card_ipv6, 'IPv6 address or route evidence is unavailable.')
        elif ipv6.get('has_global_ipv6'):
            self.card_ipv6.set_value('Global IPv6 active')
            if ipv6.get('route_verified') and ipv6.get('status') == 'tunnel_routed':
                self.card_ipv6.set_pill('Tunnel route verified', 'SECURE')
                self.card_ipv6.subtitle_label.setText('The sampled IPv6 route uses an active tunnel.')
            else:
                self.card_ipv6.set_pill('Review IPv6 routing', 'WARN')
                self.card_ipv6.subtitle_label.setText('A global address does not by itself prove a leak. Verify its selected route.')
        else:
            self.card_ipv6.set_value('No global address')
            self.card_ipv6.subtitle_label.setText('No global IPv6 address found in the local interface data.')
            self.card_ipv6.set_pill('Address data checked', 'SECURE')
        self.banner_icon.setPixmap(icon('shield' if tunnel_verified else 'route', '#65dbc5' if tunnel_verified else '#8fa8ff', 28).pixmap(28, 28))
        if tunnel_verified:
            self.banner_title.setText('Active tunnel route verified')
            self.banner_subtitle.setText('The sampled IPv4 routes use an active tunnel. The public exit IP is still visible to websites; browser fingerprints need separate controls.')
        elif route_known:
            self.banner_title.setText('Tunnel routing is not verified')
            self.banner_subtitle.setText('A direct, mixed or fallback route was observed. Connect Proton VPN and check again before opening the private browser.')
        else:
            self.banner_title.setText('Network evidence is unavailable')
            self.banner_subtitle.setText('No protection claim can be made from missing routing data.')
        self.seal_btn.setVisible(route_known and not tunnel_verified)
        self.seal_btn.setEnabled(True)
        self.seal_btn.setText('Apply VPN-only policy')
        evidence = {
            'public_identity': ident, 'ipv4_route': gw, 'dns_resolvers': dns,
            'ipv6': ipv6, 'proton': proton, 'errors': data.get('errors', []),
        }
        import json
        self.detail_text.setPlainText(json.dumps(evidence, indent=2))
        for card in (self.card_ip, self.card_geo, self.card_isp, self.card_gw, self.card_dns, self.card_ipv6):
            card.subtitle_label.setToolTip(card.subtitle_label.text())

    def seal_leaks_immediately(self):
        if self.policy_worker is not None and self.policy_worker.isRunning():
            return
        self.seal_btn.setEnabled(False)
        self.seal_btn.setText('Applying policy…')
        self.policy_worker = FirewallPolicyWorker(self)
        self.policy_worker.result.connect(self.on_policy_result)
        self.policy_worker.finished.connect(self.release_worker)
        self.policy_worker.start()

    def on_policy_result(self, success, message):
        if success:
            self.run_probe()
        else:
            self.seal_btn.setEnabled(True)
            self.seal_btn.setText('Apply VPN-only policy')
            self.banner_title.setText('Firewall policy was not applied')
            self.banner_subtitle.setText(message or 'The privileged helper did not confirm the change.')

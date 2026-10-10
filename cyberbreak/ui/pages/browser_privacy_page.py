import json
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)
from cyberbreak.core.browser_privacy import BrowserPrivacyManager, PROFILE_SETTINGS
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.ui.widgets.glass import GlassFrame, icon
from cyberbreak.ui.widgets.private_browser import BrowserGuard, CHECKER_URL, WEBENGINE_AVAILABLE
from cyberbreak.ui.widgets.status_card import StatusCard


class BrowserRouteWorker(QThread):
    result = pyqtSignal(dict)

    def run(self):
        try:
            route = NetworkAuditor.check_default_gateway()
            route['ipv6'] = NetworkAuditor.check_ipv6_exposure()
            self.result.emit(route)
        except Exception as error:
            self.result.emit({'available': False, 'route_verified': False, 'error': str(error)})


class BrowserPrivacyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._closing = False
        self._pending_url = None
        self._pending_firefox = False
        self._epoch = 0
        self._route = {}
        self._last_report = {}
        self.manager = BrowserPrivacyManager()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(20)
        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Browser privacy')
        title.setObjectName('HeaderTitle')
        subtitle = QLabel('A private workspace that limits what websites can read.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        heading.addLayout(title_box, 1)
        self.route_button = QPushButton('Check VPN route')
        self.route_button.setObjectName('OutlineButton')
        self.route_button.setIcon(icon('route'))
        self.route_button.clicked.connect(self.check_route)
        heading.addWidget(self.route_button)
        layout.addLayout(heading)
        metrics = QGridLayout()
        metrics.setSpacing(14)
        self.route_card = StatusCard('VPN route', 'Not checked', 'Connect Proton VPN, then verify the local route.', 'Required', 'WARN', icon_name='route')
        self.session_card = StatusCard('Browser policy', 'Strict', 'Cookies, WebGL and canvas extraction blocked.', 'Private session', 'SECURE', icon_name='shield')
        self.request_card = StatusCard('Third-party requests', '0 blocked', 'Only requests to the current site are allowed.', '', 'WARN', icon_name='activity')
        metrics.addWidget(self.route_card, 0, 0)
        metrics.addWidget(self.session_card, 0, 1)
        metrics.addWidget(self.request_card, 0, 2)
        layout.addLayout(metrics)
        note = QLabel('Protection applies inside this workspace. Websites still see your VPN exit IP. Keep Proton’s native kill switch enabled; browser route checks do not replace it.')
        note.setObjectName('HeaderSubtitle')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.build_browser(), 'Private browser')
        self.tabs.addTab(self.build_report(), 'Protection report')
        self.tabs.addTab(self.build_firefox(), 'Firefox profile')
        layout.addWidget(self.tabs)
        self.timer = QTimer(self)
        self.timer.setInterval(15000)
        self.timer.timeout.connect(self.check_route)
        QTimer.singleShot(0, self.check_route)

    def build_browser(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 18, 16, 16)
        layout.setSpacing(12)
        actions = QHBoxLayout()
        self.checker_button = QPushButton('Open PixelDefence')
        self.checker_button.setObjectName('AccentButton')
        self.checker_button.setIcon(icon('globe', '#ffffff'))
        self.checker_button.clicked.connect(lambda: self.open_url(CHECKER_URL))
        actions.addWidget(self.checker_button)
        self.audit_button = QPushButton('Run browser checks')
        self.audit_button.setObjectName('CyanButton')
        self.audit_button.setIcon(icon('shield'))
        self.audit_button.clicked.connect(self.run_checks)
        actions.addWidget(self.audit_button)
        actions.addStretch()
        self.reset_button = QPushButton('New session')
        self.reset_button.setObjectName('OutlineButton')
        self.reset_button.setIcon(icon('refresh'))
        self.reset_button.clicked.connect(self.reset_session)
        actions.addWidget(self.reset_button)
        layout.addLayout(actions)
        address_row = QHBoxLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText('Enter an HTTPS address')
        self.address.setAccessibleName('Private browser address')
        self.address.returnPressed.connect(lambda: self.open_url(self.address.text()))
        address_row.addWidget(self.address, 1)
        go = QPushButton('Go')
        go.setIcon(icon('arrow'))
        go.clicked.connect(lambda: self.open_url(self.address.text()))
        address_row.addWidget(go)
        layout.addLayout(address_row)
        self.browser = BrowserGuard()
        self.browser.setMinimumHeight(540)
        self.browser.set_network_enabled(False)
        self.browser.audit_result.connect(self.on_audit)
        self.browser.navigation_changed.connect(self.on_navigation)
        self.browser.blocked_count_changed.connect(lambda count: self.request_card.set_value(f'{count} blocked'))
        self.browser.loading_changed.connect(self.on_loading)
        layout.addWidget(self.browser, 1)
        self.feedback = QLabel('Browsing is paused until an active VPN route is verified.')
        self.feedback.setObjectName('HeaderSubtitle')
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        if not WEBENGINE_AVAILABLE:
            self.session_card.set_value('Unavailable')
            self.session_card.set_pill('WebEngine missing', 'WARN')
            for button in (self.checker_button, self.audit_button, self.reset_button, go):
                button.setEnabled(False)
        return page

    def build_report(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        toolbar = QHBoxLayout()
        self.report_summary = QLabel('Run browser checks to verify the active session.')
        self.report_summary.setObjectName('CardTitle')
        self.report_summary.setWordWrap(True)
        toolbar.addWidget(self.report_summary, 1)
        export = QPushButton('Export report')
        export.setObjectName('OutlineButton')
        export.setIcon(icon('folder'))
        export.clicked.connect(self.export_report)
        toolbar.addWidget(export)
        layout.addLayout(toolbar)
        self.check_labels = {}
        grid = QGridLayout()
        grid.setSpacing(12)
        checks = (
            ('dnt', 'Do Not Track'), ('gpc', 'Global Privacy Control'),
            ('cookies', 'Cookie write / read'), ('webgl', 'WebGL access'),
            ('canvas', 'Canvas export'), ('canvas_readback', 'Canvas pixel readback'),
            ('battery', 'Battery API'), ('connection', 'Network information API'),
            ('webrtc', 'WebRTC connections'), ('workers', 'Background workers'),
        )
        for index, (key, title) in enumerate(checks):
            frame = GlassFrame()
            row = QHBoxLayout(frame)
            row.setContentsMargins(14, 14, 14, 14)
            label = QLabel(title)
            label.setWordWrap(True)
            row.addWidget(label, 1)
            state = QLabel('Not checked')
            state.setObjectName('StatusPillWarning')
            row.addWidget(state)
            self.check_labels[key] = state
            grid.addWidget(frame, index // 2, index % 2)
        layout.addLayout(grid)
        self.report_text = QPlainTextEdit()
        self.report_text.setObjectName('Terminal')
        self.report_text.setReadOnly(True)
        self.report_text.setMinimumHeight(170)
        layout.addWidget(self.report_text)
        explanation = QLabel('These checks attempt the restricted APIs in the current page. PixelDefence awards IP points when its external geolocation request is blocked; that does not hide the connection’s exit IP from the visited site.')
        explanation.setObjectName('HeaderSubtitle')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        return page

    def build_firefox(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        description = QLabel('An optional, separate Firefox profile with real privacy preferences. The route is checked before launch; ongoing network protection depends on Proton’s native kill switch. Firefox may still produce a canvas hash that PixelDefence flags.')
        description.setObjectName('HeaderSubtitle')
        description.setWordWrap(True)
        layout.addWidget(description)
        self.firefox_status = QLabel()
        self.firefox_status.setObjectName('CardTitle')
        self.firefox_status.setWordWrap(True)
        layout.addWidget(self.firefox_status)
        for setting in PROFILE_SETTINGS:
            frame = GlassFrame()
            row = QVBoxLayout(frame)
            row.setContentsMargins(16, 12, 16, 12)
            row.setSpacing(4)
            title = QLabel(setting['label'])
            title.setObjectName('SettingTitle')
            detail = QLabel(setting['detail'])
            detail.setObjectName('HeaderSubtitle')
            detail.setWordWrap(True)
            row.addWidget(title)
            row.addWidget(detail)
            layout.addWidget(frame)
        actions = QHBoxLayout()
        prepare = QPushButton('Prepare profile')
        prepare.setObjectName('CyanButton')
        prepare.clicked.connect(lambda: self.profile_action('prepare'))
        actions.addWidget(prepare)
        self.firefox_launch = QPushButton('Launch Firefox')
        self.firefox_launch.setObjectName('AccentButton')
        self.firefox_launch.clicked.connect(lambda: self.profile_action('launch'))
        actions.addWidget(self.firefox_launch)
        reset = QPushButton('Reset managed settings')
        reset.setObjectName('OutlineButton')
        reset.clicked.connect(lambda: self.profile_action('reset'))
        actions.addWidget(reset)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()
        self.update_firefox_status()
        return page

    def check_route(self):
        if self._closing or getattr(self.window(), '_closing', False):
            return
        if self.worker is not None and self.worker.isRunning():
            return
        self.route_button.setEnabled(False)
        self.route_button.setText('Checking…')
        self.worker = BrowserRouteWorker(self)
        epoch = self._epoch
        self.worker.result.connect(lambda route: self.on_route(route) if epoch == self._epoch else None)
        self.worker.finished.connect(self.release_worker)
        self.worker.start()

    def release_worker(self):
        worker = self.sender()
        if self.worker is worker:
            self.worker = None
        if not self._closing:
            self.route_button.setEnabled(True)
            self.route_button.setText('Check VPN route')
        worker.deleteLater()

    def on_route(self, route):
        if self._closing or getattr(self.window(), '_closing', False):
            return
        self._route = route
        self.route_button.setEnabled(True)
        self.route_button.setText('Check VPN route')
        verified = self.route_is_verified(route)
        self.browser.set_network_enabled(verified)
        if verified:
            interface = route.get('interface', 'Tunnel')
            self.route_card.set_value(interface)
            self.route_card.set_pill('Route verified', 'SECURE')
            self.route_card.subtitle_label.setText('Sampled IPv4 routes use a tunnel; IPv6 is tunnel-routed or has no global address. Server ownership remains unverified.')
            self.feedback.setText('Strict browser ready. Only first-party HTTPS requests are allowed; cookies, media, workers and fingerprint readback are blocked.')
            if self._pending_url:
                url, self._pending_url = self._pending_url, None
                if not self.browser.navigate(url):
                    self.feedback.setText('Enter a valid HTTPS address without embedded credentials.')
                else:
                    self.timer.start()
            if self._pending_firefox:
                self._pending_firefox = False
                ok, message = self.manager.launch(CHECKER_URL)
                self.update_firefox_status()
                self.firefox_status.setText(message)
        else:
            self.route_card.set_value('Not verified')
            self.route_card.set_pill('Browsing paused', 'WARN')
            self.route_card.subtitle_label.setText('Connect Proton VPN and enable its kill switch, then check again.')
            self.feedback.setText('Browsing paused: an active VPN route could not be verified. No new browser web requests are allowed.')
            self._pending_url = None
            self._pending_firefox = False
        self.firefox_launch.setEnabled(verified and self.manager.inspect().get('available', False))

    @staticmethod
    def route_is_verified(route):
        ipv6 = route.get('ipv6', {})
        ipv6_safe = ipv6.get('available') is True and (
            ipv6.get('has_global_ipv6') is False or
            (ipv6.get('route_verified') is True and ipv6.get('status') == 'tunnel_routed')
        )
        return bool(route.get('route_verified') and route.get('is_tunnel') and ipv6_safe)

    def open_url(self, url):
        if not WEBENGINE_AVAILABLE or self._closing:
            return
        self._pending_url = url
        self.check_route()

    def on_navigation(self, url):
        self.address.setText('' if url == 'about:blank' else url)

    def on_loading(self, loading):
        self.audit_button.setEnabled(not loading and WEBENGINE_AVAILABLE)

    def run_checks(self):
        self.browser.run_local_audit()
        self.tabs.setCurrentIndex(1)

    def on_audit(self, result):
        self._last_report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'browser': result, 'vpn_route': self._route}
        passed = 0
        for key, label in self.check_labels.items():
            verified = result.get(key) is True
            passed += verified
            label.setText('Verified' if verified else 'Not verified')
            label.setObjectName('StatusPillSecure' if verified else 'StatusPillWarning')
            label.style().unpolish(label)
            label.style().polish(label)
        self.report_summary.setText(f'{passed} of {len(self.check_labels)} browser restrictions verified')
        self.report_text.setPlainText(json.dumps(self._last_report, indent=2))

    def reset_session(self):
        self._epoch += 1
        self._pending_url = None
        self._pending_firefox = False
        self.browser.set_network_enabled(False)
        self.browser.reset_session()
        self.timer.stop()
        self._route = {}
        self._last_report = {}
        self.address.clear()
        self.report_summary.setText('New private session. Run checks to verify it.')
        self.report_text.clear()
        for label in self.check_labels.values():
            label.setText('Not checked')
            label.setObjectName('StatusPillWarning')
            label.style().unpolish(label)
            label.style().polish(label)
        self.route_card.set_value('Not checked')
        self.route_card.set_pill('Required', 'WARN')
        self.feedback.setText('New session created. Check the VPN route before browsing.')
        self.firefox_launch.setEnabled(False)

    def update_firefox_status(self):
        state = self.manager.inspect()
        self.firefox_status.setText(state.get('error') or ('Firefox found · ' if state.get('available') else 'Firefox not installed · ') + ('Managed profile ready' if state.get('configured') else 'Profile not prepared'))
        self.firefox_launch.setEnabled(bool(state.get('available') and self.route_is_verified(self._route)))

    def profile_action(self, action):
        if action == 'launch':
            self._pending_firefox = True
            self.firefox_status.setText('Checking IPv4 and IPv6 routes before launching Firefox…')
            self.check_route()
            return
        elif action == 'prepare':
            ok, message = self.manager.prepare_profile()
        else:
            ok, message = self.manager.reset_profile()
        self.update_firefox_status()
        self.firefox_status.setText(message)
        self.firefox_status.setToolTip(message)

    def export_report(self):
        if not self._last_report:
            self.report_summary.setText('Run browser checks before exporting a report.')
            return
        filename, _ = QFileDialog.getSaveFileName(self, 'Export privacy report', 'cyberbreak-privacy.json', 'JSON files (*.json)')
        if filename:
            try:
                Path(filename).write_text(json.dumps(self._last_report, indent=2) + '\n', encoding='utf-8')
                self.report_summary.setText('Privacy report exported')
            except OSError as error:
                self.report_summary.setText(f'Export failed: {error}')

    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        self._epoch += 1
        self._pending_url = None
        self._pending_firefox = False
        self.timer.stop()
        self.browser.shutdown()

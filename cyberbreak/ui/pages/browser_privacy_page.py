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
from cyberbreak.ui.widgets.private_browser import (
    BrowserGuard, CHECKER_URL, WEBENGINE_AVAILABLE,
    format_search_or_url, StandaloneBrowserWindow,
)
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
        self._enforce_vpn_lock = False
        self.standalone_window = None
        self.manager = BrowserPrivacyManager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(18)

        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Browser Privacy & Zero-Tracking Engine')
        title.setObjectName('HeaderTitle')
        subtitle = QLabel('Titanium workspace blocking all cookies, canvas fingerprinting, WebGL, WebRTC, and tracking beacons.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        heading.addLayout(title_box, 1)

        self.vpn_lock_btn = QPushButton('VPN killswitch: OFF (Direct mode active)')
        self.vpn_lock_btn.setObjectName('OutlineButton')
        self.vpn_lock_btn.setIcon(icon('lock'))
        self.vpn_lock_btn.setToolTip('When OFF: allows zero-tracking browsing on any connection. When ON: blocks web requests unless VPN tunnel is verified.')
        self.vpn_lock_btn.clicked.connect(self.toggle_vpn_lock)
        heading.addWidget(self.vpn_lock_btn)

        self.route_button = QPushButton('Check VPN route')
        self.route_button.setObjectName('OutlineButton')
        self.route_button.setIcon(icon('route'))
        self.route_button.clicked.connect(self.check_route)
        heading.addWidget(self.route_button)
        layout.addLayout(heading)

        metrics = QGridLayout()
        metrics.setSpacing(14)
        self.route_card = StatusCard('Network Route', 'Direct connection', 'Zero-tracking shields active. Connect Proton VPN to mask ISP IP.', 'Direct mode', 'WARN', icon_name='route')
        self.session_card = StatusCard('Shield Policy', 'Titanium Strict', 'Cookies, canvas, WebGL readback, WebRTC & audio leaks denied.', 'Zero tracking', 'SECURE', icon_name='shield')
        self.request_card = StatusCard('Tracking Beacons', '0 blocked', 'Cross-origin trackers and advertising beacons intercepted.', '', 'WARN', icon_name='activity')
        metrics.addWidget(self.route_card, 0, 0)
        metrics.addWidget(self.session_card, 0, 1)
        metrics.addWidget(self.request_card, 0, 2)
        layout.addLayout(metrics)

        note = QLabel('Zero-tracking shields operate at the browser engine level. Websites cannot extract cookies, persistent storage, canvas hashes, or WebRTC IP addresses. External exit IP depends on your VPN or network connection.')
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Main Navigation Bar
        nav_row = QHBoxLayout()
        self.back_button = QPushButton()
        self.back_button.setIcon(icon('arrow-left'))
        self.back_button.setToolTip('Back')
        self.back_button.setFixedWidth(38)
        self.back_button.clicked.connect(self._browser_back)
        nav_row.addWidget(self.back_button)

        self.fwd_button = QPushButton()
        self.fwd_button.setIcon(icon('arrow-right'))
        self.fwd_button.setToolTip('Forward')
        self.fwd_button.setFixedWidth(38)
        self.fwd_button.clicked.connect(self._browser_forward)
        nav_row.addWidget(self.fwd_button)

        self.reload_button = QPushButton()
        self.reload_button.setIcon(icon('refresh'))
        self.reload_button.setToolTip('Reload')
        self.reload_button.setFixedWidth(38)
        self.reload_button.clicked.connect(self._browser_reload)
        nav_row.addWidget(self.reload_button)

        self.home_button = QPushButton('DuckDuckGo')
        self.home_button.setIcon(icon('home'))
        self.home_button.setToolTip('Go to DuckDuckGo Private Search')
        self.home_button.clicked.connect(lambda: self.open_url('https://duckduckgo.com'))
        nav_row.addWidget(self.home_button)

        self.checker_button = QPushButton('PixelDefence')
        self.checker_button.setObjectName('AccentButton')
        self.checker_button.setIcon(icon('globe', '#ffffff'))
        self.checker_button.setToolTip('Open PixelDefence Data Leak Test')
        self.checker_button.clicked.connect(lambda: self.open_url(CHECKER_URL))
        nav_row.addWidget(self.checker_button)

        self.audit_button = QPushButton('Run checks')
        self.audit_button.setObjectName('CyanButton')
        self.audit_button.setIcon(icon('shield'))
        self.audit_button.clicked.connect(self.run_checks)
        nav_row.addWidget(self.audit_button)

        self.standalone_button = QPushButton('Standalone window')
        self.standalone_button.setObjectName('OutlineButton')
        self.standalone_button.setIcon(icon('external-link'))
        self.standalone_button.setToolTip('Open Private Browser in a separate dedicated window')
        self.standalone_button.clicked.connect(self.open_standalone_window)
        nav_row.addWidget(self.standalone_button)

        nav_row.addStretch()

        self.reset_button = QPushButton('New session')
        self.reset_button.setObjectName('OutlineButton')
        self.reset_button.setIcon(icon('refresh'))
        self.reset_button.setToolTip('Wipe cookies, cache and restart clean private session')
        self.reset_button.clicked.connect(self.reset_session)
        nav_row.addWidget(self.reset_button)
        layout.addLayout(nav_row)

        # Address & Search Bar
        address_row = QHBoxLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText('Enter website address (e.g. duckduckgo.com, pixeldefence.com) or search query...')
        self.address.setAccessibleName('Private browser address')
        self.address.returnPressed.connect(lambda: self.open_url(self.address.text()))
        address_row.addWidget(self.address, 1)

        go = QPushButton('Go')
        go.setObjectName('AccentButton')
        go.setIcon(icon('arrow', '#ffffff'))
        go.clicked.connect(lambda: self.open_url(self.address.text()))
        address_row.addWidget(go)

        stop = QPushButton('Stop')
        stop.setObjectName('OutlineButton')
        stop.clicked.connect(self._browser_stop)
        address_row.addWidget(stop)
        layout.addLayout(address_row)

        # Quick privacy bookmark pills
        pills_row = QHBoxLayout()
        pills_row.setSpacing(8)
        pills_label = QLabel('Quick Launch:')
        pills_label.setObjectName('HeaderSubtitle')
        pills_row.addWidget(pills_label)

        bookmarks = [
            ('DuckDuckGo', 'https://duckduckgo.com'),
            ('PixelDefence Leak Test', CHECKER_URL),
            ('EFF Cover Your Tracks', 'https://coveryourtracks.eff.org/'),
            ('Brave Search', 'https://search.brave.com/'),
            ('IPleak.net', 'https://ipleak.net/'),
        ]
        for name, target in bookmarks:
            btn = QPushButton(name)
            btn.setObjectName('OutlineButton')
            btn.setStyleSheet('padding: 3px 10px; font-size: 11px;')
            btn.clicked.connect(lambda checked=False, t=target: self.open_url(t))
            pills_row.addWidget(btn)

        pills_row.addStretch()
        layout.addLayout(pills_row)

        # Browser Guard Frame
        self.browser = BrowserGuard()
        self.browser.setMinimumHeight(540)
        self.browser.set_network_enabled(True)
        self.browser.audit_result.connect(self.on_audit)
        self.browser.navigation_changed.connect(self.on_navigation)
        self.browser.blocked_count_changed.connect(lambda count: self.request_card.set_value(f'{count} blocked'))
        self.browser.loading_changed.connect(self.on_loading)
        layout.addWidget(self.browser, 1)

        self.feedback = QLabel('Zero-tracking browser active. First-party HTTPS requests permitted; all fingerprint APIs blocked.')
        self.feedback.setObjectName('HeaderSubtitle')
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)

        if not WEBENGINE_AVAILABLE:
            self.session_card.set_value('External Mode')
            self.session_card.set_pill('WebEngine missing', 'WARN')
            self.feedback.setText('PyQt6-WebEngine is not detected. Click "Open PixelDefence" or "Launch Firefox" to open external hardened browser.')
        return page

    def _browser_back(self):
        if hasattr(self, 'browser') and self.browser:
            self.browser.back()

    def _browser_forward(self):
        if hasattr(self, 'browser') and self.browser:
            self.browser.forward()

    def _browser_reload(self):
        if hasattr(self, 'browser') and self.browser:
            self.browser.reload()

    def _browser_stop(self):
        if hasattr(self, 'browser') and self.browser:
            self.browser.stop()

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
        description = QLabel('An optional, separate Firefox / LibreWolf profile configured with 49 Mozilla privacy directives, resisting canvas extraction and disabling telemetry. Operates in user space.')
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

    def toggle_vpn_lock(self):
        self._enforce_vpn_lock = not self._enforce_vpn_lock
        if self._enforce_vpn_lock:
            self.vpn_lock_btn.setText('VPN killswitch: ON (Enforced)')
            self.vpn_lock_btn.setObjectName('AccentButton')
            self.vpn_lock_btn.style().unpolish(self.vpn_lock_btn)
            self.vpn_lock_btn.style().polish(self.vpn_lock_btn)
            verified = self.route_is_verified(self._route)
            if not verified:
                self.browser.set_network_enabled(False)
                self.feedback.setText('VPN killswitch lock enabled: web requests paused until VPN tunnel is verified.')
                self.route_card.set_value('Lock enforced')
                self.route_card.set_pill('Browsing paused', 'WARN')
        else:
            self.vpn_lock_btn.setText('VPN killswitch: OFF (Direct mode active)')
            self.vpn_lock_btn.setObjectName('OutlineButton')
            self.vpn_lock_btn.style().unpolish(self.vpn_lock_btn)
            self.vpn_lock_btn.style().polish(self.vpn_lock_btn)
            self.browser.set_network_enabled(True)
            self.feedback.setText('VPN killswitch lock disabled: zero-tracking browsing active on any connection.')
            self.route_card.set_value('Direct connection')
            self.route_card.set_pill('Shields active', 'WARN')
        self.check_route()

    def open_standalone_window(self):
        if self.standalone_window is None:
            self.standalone_window = StandaloneBrowserWindow()
        current = self.address.text().strip() or "https://duckduckgo.com"
        self.standalone_window.show()
        self.standalone_window.raise_()
        self.standalone_window.activateWindow()
        self.standalone_window.navigate(current)

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
        if worker is not None:
            worker.deleteLater()

    def on_route(self, route):
        if self._closing or getattr(self.window(), '_closing', False):
            return
        self._route = route
        self.route_button.setEnabled(True)
        self.route_button.setText('Check VPN route')
        verified = self.route_is_verified(route)

        if verified:
            interface = route.get('interface', 'Tunnel')
            self.route_card.set_value(interface)
            self.route_card.set_pill('Tunnel verified', 'SECURE')
            self.route_card.subtitle_label.setText('Traffic is actively routed through verified VPN tunnel.')
            self.feedback.setText('Titanium browser ready. VPN route verified; all tracking beacons and fingerprint APIs blocked.')
            self.browser.set_network_enabled(True)
            if self._pending_url:
                url, self._pending_url = self._pending_url, None
                self.browser.navigate(url)
            if self._pending_firefox:
                self._pending_firefox = False
                ok, message = self.manager.launch(CHECKER_URL)
                self.update_firefox_status()
                self.firefox_status.setText(message)
        else:
            if self._enforce_vpn_lock:
                self.browser.set_network_enabled(False)
                self.route_card.set_value('Lock active')
                self.route_card.set_pill('Browsing paused', 'WARN')
                self.route_card.subtitle_label.setText('VPN killswitch lock is active. Connect Proton VPN or disable lock.')
                self.feedback.setText('Browsing paused by VPN killswitch lock. Disable lock or connect VPN.')
                self._pending_url = None
                self._pending_firefox = False
            else:
                self.browser.set_network_enabled(True)
                self.route_card.set_value('Direct connection')
                self.route_card.set_pill('Shields active', 'WARN')
                self.route_card.subtitle_label.setText('Direct route: zero-tracking shields active. Connect Proton VPN to mask ISP IP.')
                self.feedback.setText('Direct zero-tracking active. WebRTC, cookies, canvas, and fingerprinting blocked.')
                if self._pending_url:
                    url, self._pending_url = self._pending_url, None
                    self.browser.navigate(url)

        self.update_firefox_status()

    @staticmethod
    def route_is_verified(route):
        ipv6 = route.get('ipv6', {})
        ipv6_safe = ipv6.get('available') is True and (
            ipv6.get('has_global_ipv6') is False or
            (ipv6.get('route_verified') is True and ipv6.get('status') == 'tunnel_routed')
        )
        return bool(route.get('route_verified') and route.get('is_tunnel') and ipv6_safe)

    def open_url(self, text):
        if not text:
            return
        url = format_search_or_url(text)
        if not url:
            self.feedback.setText('Enter a valid HTTPS address or search term.')
            return

        if not WEBENGINE_AVAILABLE:
            self.feedback.setText('WebEngine missing on host: Launching URL in external hardened browser...')
            self.manager.launch(url)
            return

        if self._closing:
            return

        if self._enforce_vpn_lock and not self.route_is_verified(self._route):
            self._pending_url = url
            self.feedback.setText("VPN killswitch lock is active and route is unverified. Disable 'VPN Lock' to browse or connect Proton VPN.")
            self.check_route()
            return

        self.browser.set_network_enabled(True)
        if self.browser.navigate(url):
            self.feedback.setText(f'Loading {url} with titanium zero-tracking shields...')
            self.address.setText(url)
        else:
            self.feedback.setText('Failed to navigate to target address.')

    def on_navigation(self, url):
        self.address.setText('' if url == 'about:blank' else url)

    def on_loading(self, loading):
        self.audit_button.setEnabled(not loading and WEBENGINE_AVAILABLE)
        if loading:
            self.feedback.setText('Loading page securely with zero-tracking protections...')

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
        self.browser.reset_session()
        self.browser.set_network_enabled(not self._enforce_vpn_lock or self.route_is_verified(self._route))
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
        self.feedback.setText('New clean private session initialized. All cookies and ephemeral caches purged.')
        self.check_route()

    def update_firefox_status(self):
        state = self.manager.inspect()
        avail = state.get('available', False)
        configured = state.get('configured', False)
        name = Path(state.get('browser_path', 'firefox')).name if state.get('browser_path') else 'Firefox'
        self.firefox_status.setText(state.get('error') or (f'{name} ready · ' if avail else 'No browser installed · ') + ('Managed profile ready' if configured else 'Profile not prepared'))
        self.firefox_launch.setEnabled(bool(avail))

    def profile_action(self, action):
        if action == 'launch':
            if self._enforce_vpn_lock and not self.route_is_verified(self._route):
                self._pending_firefox = True
                self.firefox_status.setText('VPN lock is enforced. Verifying VPN route before launch...')
                self.check_route()
                return
            ok, message = self.manager.launch(CHECKER_URL)
            self.update_firefox_status()
            self.firefox_status.setText(message)
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
        if hasattr(self, 'browser') and self.browser:
            self.browser.shutdown()
        if self.standalone_window is not None:
            self.standalone_window.close()

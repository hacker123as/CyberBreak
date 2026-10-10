import os
import sys
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, QTimer, QRectF, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QRadialGradient, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSizePolicy, QLayout
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.ui.widgets.glass import GlassFrame, icon
from cyberbreak.core.network_auditor import NetworkAuditor
from cyberbreak.core.kernel_hardening import KernelHardening
from cyberbreak.core.metadata_cleaner import MetadataCleaner
from cyberbreak.core.firewall_controller import FirewallController
from cyberbreak.core.usb_armory import USBArmory
from cyberbreak.core.port_auditor import PortAuditor
from cyberbreak.core.hardware_manager import HardwareManager


class AuditWorker(QThread):
    finished_data = pyqtSignal(dict)
    progress = pyqtSignal(str, int)

    def run(self):
        data = {"errors": {}}
        probes = (
            ("identity", "Resolving your public identity", NetworkAuditor.get_external_identity, True),
            ("gw", "Reading the default route", NetworkAuditor.check_default_gateway, os.path.exists("/proc/net/route")),
            ("ipv6", "Checking IPv6 addresses", NetworkAuditor.check_ipv6_exposure, sys.platform.startswith("linux")),
            ("proton", "Checking VPN indicators", lambda: NetworkAuditor.check_proton_vpn(data.get("identity", {}), data.get("gw", {})), True),
            ("ports", "Inspecting listening sockets", PortAuditor.get_open_listening_ports, sys.platform.startswith("linux")),
            ("usb", "Reading connected hardware", HardwareManager.get_connected_usb_devices, os.path.isdir("/sys/bus/usb/devices")),
            ("kernel", "Comparing kernel settings", KernelHardening.audit_sysctl, sys.platform.startswith("linux")),
        )
        for index, (key, label, probe, supported) in enumerate(probes):
            if self.isInterruptionRequested():
                return
            self.progress.emit(label, index)
            try:
                if not supported:
                    raise OSError("Linux system data is unavailable on this host")
                result = probe()
                expected_type = list if key in ("ports", "usb") else dict
                if not isinstance(result, expected_type):
                    raise TypeError("The system probe returned an unexpected result")
                data[key] = result
            except Exception as error:
                data["errors"][key] = str(error)
        self.finished_data.emit(data)


class ActionWorker(QThread):
    result = pyqtSignal(bool, str)

    def __init__(self, action, parent=None):
        super().__init__(parent)
        self.action = action

    def run(self):
        try:
            result = self.action()
            if isinstance(result, tuple) and len(result) >= 2:
                self.result.emit(bool(result[0]), str(result[1]))
            else:
                self.result.emit(False, "The operation returned no completion status. Check the audit terminal.")
        except Exception as error:
            self.result.emit(False, str(error))


class AuditOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(168, 168)
        self.angle = 0
        self.active = False
        self.summary = "—"
        self.caption = "Awaiting audit"
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.advance)

    def advance(self):
        if self.window().property("reducedMotion"):
            self.timer.stop()
            return
        self.angle = (self.angle + 2) % 360
        self.update()

    def set_active(self, active):
        self.active = active
        if active:
            self.summary = "···"
            self.caption = "Reading signals"
            if not self.window().property("reducedMotion"):
                self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def set_summary(self, available):
        self.set_active(False)
        self.summary = f"{available}/6"
        self.caption = "Checks available"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QRadialGradient(84, 84, 78)
        glow.setColorAt(0, QColor(99, 135, 255, 34))
        glow.setColorAt(0.64, QColor(99, 135, 255, 15))
        glow.setColorAt(1, QColor(99, 135, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QRectF(4, 4, 160, 160))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(143, 168, 255, 22), 5))
        painter.drawEllipse(QRectF(15, 15, 138, 138))
        for index in range(6):
            color = QColor("#8fa8ff" if index % 2 == 0 else "#65dbc5")
            color.setAlpha(210 if self.active else 145)
            painter.setPen(QPen(color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(QRectF(15, 15, 138, 138), int((index * 60 + self.angle) * 16), 39 * 16)
        painter.setPen(QPen(QColor(143, 168, 255, 30), 1))
        painter.drawEllipse(QRectF(29, 29, 110, 110))
        icon("shield", "#8fa8ff", 24).paint(painter, 72, 42, 24, 24)
        painter.setPen(QColor("#f4f6ff"))
        font = QFont(self.font())
        font.setPixelSize(30)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRectF(32, 70, 104, 36), Qt.AlignmentFlag.AlignCenter, self.summary)
        font.setPixelSize(10)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#a4aec8"))
        painter.drawText(QRectF(22, 109, 124, 20), Qt.AlignmentFlag.AlignCenter, self.caption)


class ActionTile(GlassFrame):
    activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activated.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.activated.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hasFocus():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#8fa8ff"), 1.2))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 20, 20)


class DashboardPage(QWidget):
    audit_started = pyqtSignal()
    audit_completed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.action_worker = None
        self._columns = 3
        self._action_buttons = []
        self._cards = []

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(5)
        title = QLabel("Your security, at a glance.")
        title.setObjectName("HeaderTitle")
        title_box.addWidget(title)
        subtitle = QLabel("A clear view of your network, kernel and connected hardware.")
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        header.addSpacing(18)
        self.scan_btn = QPushButton("Run audit")
        self.scan_btn.setObjectName("AccentButton")
        self.scan_btn.setIcon(icon("refresh", "#f4f6ff", 16))
        self.scan_btn.setIconSize(QSize(16, 16))
        self.scan_btn.setMinimumHeight(42)
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.clicked.connect(self.run_audit)
        header.addWidget(self.scan_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header)

        self.alert_banner = GlassFrame()
        self.alert_banner.setObjectName("GlassCard")
        hero = QHBoxLayout(self.alert_banner)
        hero.setContentsMargins(28, 18, 22, 18)
        hero.setSpacing(24)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(10)
        self.audit_badge = QLabel("Audit in progress")
        self.audit_badge.setObjectName("StatusPillWarning")
        self.audit_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        hero_text.addWidget(self.audit_badge)
        self.b_title = QLabel("Let's take a closer look.")
        self.b_title.setStyleSheet("color: #f4f6ff; font-size: 24px; font-weight: 600; background: transparent; border: none;")
        self.b_title.setWordWrap(True)
        hero_text.addWidget(self.b_title)
        self.b_sub = QLabel("Reading the signals that matter. Results will appear below.")
        self.b_sub.setObjectName("HeaderSubtitle")
        self.b_sub.setTextFormat(Qt.TextFormat.PlainText)
        self.b_sub.setWordWrap(True)
        hero_text.addWidget(self.b_sub)
        self.last_scan = QLabel("Live system checks · No stored snapshots")
        self.last_scan.setStyleSheet("font-size: 11px; color: #8291b0; background: transparent; border: none;")
        hero_text.addSpacing(3)
        hero_text.addWidget(self.last_scan)
        hero.addLayout(hero_text, 1)
        self.orb = AuditOrb()
        hero.addWidget(self.orb)
        layout.addWidget(self.alert_banner)

        section = QHBoxLayout()
        section_title = QLabel("System overview")
        section_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f4f6ff;")
        section.addWidget(section_title)
        section.addStretch()
        section_note = QLabel("6 live signals")
        section_note.setObjectName("HeaderSubtitle")
        section_note.setStyleSheet("font-size: 11px; color: #8291b0;")
        section.addWidget(section_note)
        layout.addLayout(section)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        metrics = (
            ("card_ip", "Public identity", "Resolving…", "Your visible IP and provider", "globe"),
            ("card_route", "Network route", "Reading…", "Default gateway and tunnel", "route"),
            ("card_ports", "Listening ports", "Scanning…", "Services accepting connections", "activity"),
            ("card_ipv6", "IPv6 exposure", "Checking…", "Global addresses on this host", "layers"),
            ("card_kernel", "Kernel settings", "Checking…", "Read-only sysctl comparison", "cpu"),
            ("card_usb", "Connected hardware", "Reading…", "USB devices and authorization", "usb"),
        )
        for index, (attribute, title, value, subtitle, name) in enumerate(metrics):
            card = StatusCard(title, value, subtitle, "Checking", "WARN", icon_name=name)
            setattr(self, attribute, card)
            self._cards.append(card)
            self.grid.addWidget(card, index // 3, index % 3)
        for column in range(3):
            self.grid.setColumnStretch(column, 1)
        layout.addLayout(self.grid)

        actions_header = QHBoxLayout()
        actions_title = QLabel("Quick actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f4f6ff;")
        actions_header.addWidget(actions_title)
        actions_header.addStretch()
        actions_note = QLabel("Changes use the system helper")
        actions_note.setStyleSheet("font-size: 11px; color: #8291b0;")
        actions_header.addWidget(actions_note)
        layout.addLayout(actions_header)

        self.actions_grid = QGridLayout()
        self.actions_grid.setSpacing(12)
        self._actions = []
        actions = (
            ("Ghost this device", "Randomize hardware identity & fingerprints under VPN shield", "ghost", self.on_ghost_device, False),
            ("Purge RAM cache", "Release cached system memory", "layers", MetadataCleaner.purge_ram_cache, False),
            ("Harden kernel", "Apply recommended sysctl values", "shield", KernelHardening.apply_sysctl_hardening, False),
            ("Trim storage", "Discard unused SSD blocks", "usb", USBArmory.trim_drives, False),
            ("Strict firewall", "Apply the restrictive network profile", "lock", FirewallController.apply_strict_profile, False),
            ("Lock listening ports", "Block ports and stop their processes", "alert", PortAuditor.lockdown_all_open_ports, True),
        )
        for index, (title, subtitle, name, callback, danger) in enumerate(actions):
            tile = self.make_action(title, subtitle, name, callback, danger)
            self._actions.append(tile)
            self.actions_grid.addWidget(tile, index // 3, index % 3)
        for column in range(3):
            self.actions_grid.setColumnStretch(column, 1)
        layout.addLayout(self.actions_grid)

        self.action_feedback = QLabel()
        self.action_feedback.setTextFormat(Qt.TextFormat.PlainText)
        self.action_feedback.setWordWrap(True)
        self.action_feedback.setVisible(False)
        layout.addWidget(self.action_feedback)
        layout.addStretch()
        QTimer.singleShot(0, self.run_audit)

    def make_action(self, title, subtitle, name, callback, danger):
        frame = ActionTile()
        frame.setObjectName("GlassCard")
        frame.setAccessibleName(title)
        frame.setAccessibleDescription(subtitle)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 16, 15, 16)
        layout.setSpacing(12)
        color = "#ff8294" if danger else "#8fa8ff"
        glyph = QLabel()
        glyph.setPixmap(icon(name, color, 19).pixmap(19, 19))
        glyph.setFixedSize(28, 28)
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(glyph)
        copy = QVBoxLayout()
        copy.setSpacing(4)
        button = QPushButton(title)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setObjectName("DashboardAction")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(f"QPushButton {{ text-align: left; background: transparent; border: none; padding: 0; color: {'#ffadb9' if danger else '#f4f6ff'}; font-size: 12px; font-weight: 600; }} QPushButton:hover {{ color: {color}; }} QPushButton:disabled {{ color: #8291b0; }} QPushButton:focus {{ border-bottom: 1px solid {color}; }}")
        button.setToolTip(title)
        if title == "Ghost this device":
            button.clicked.connect(lambda checked=False: self.on_ghost_device())
        else:
            button.clicked.connect(lambda checked=False, action=callback, label=title, control=button: self.run_action(action, label, control))
        frame.activated.connect(button.click)
        self._action_buttons.append(button)
        copy.addWidget(button)
        description = QLabel(subtitle)
        description.setObjectName("HeaderSubtitle")
        description.setWordWrap(True)
        description.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        description.setStyleSheet("font-size: 10px; color: #8291b0; background: transparent; border: none;")
        copy.addWidget(description)
        layout.addLayout(copy, 1)
        arrow = QLabel()
        arrow.setPixmap(icon("arrow", "#8291b0", 14).pixmap(14, 14))
        layout.addWidget(arrow)
        return frame

    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = 2 if self.width() < 860 else 3
        if columns == self._columns:
            return
        self._columns = columns
        for grid, widgets in ((self.grid, self._cards), (self.actions_grid, self._actions)):
            for widget in widgets:
                grid.removeWidget(widget)
            for column in range(3):
                grid.setColumnStretch(column, 1 if column < columns else 0)
            for index, widget in enumerate(widgets):
                grid.addWidget(widget, index // columns, index % columns)

    def minimumSizeHint(self):
        return QSize(0, self.layout().minimumSize().height())

    def run_audit(self):
        if getattr(self.window(), "_closing", False):
            return
        if self.worker is not None and self.worker.isRunning():
            return
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Auditing…")
        self.audit_badge.setText("Audit in progress")
        self.audit_badge.setObjectName("StatusPillWarning")
        self.audit_badge.style().unpolish(self.audit_badge)
        self.audit_badge.style().polish(self.audit_badge)
        self.b_title.setText("Reading your system.")
        self.b_sub.setText("Collecting live network, kernel and hardware signals.")
        self.orb.set_active(True)
        self.audit_started.emit()
        self.worker = AuditWorker(self)
        self.worker.progress.connect(self.on_audit_progress)
        self.worker.finished_data.connect(self.on_audit_finished)
        self.worker.finished.connect(self.release_audit_worker)
        self.worker.start()

    def release_audit_worker(self):
        worker = self.sender()
        if self.worker is worker:
            self.worker = None
        worker.deleteLater()

    def on_audit_progress(self, label, step):
        self.b_sub.setText(f"{label}…")
        self.last_scan.setText(f"Probe {step + 1} of 7 · Live system checks")

    @staticmethod
    def known(value):
        return value is not None and str(value).strip().lower() not in ("", "unknown", "none", "n/a")

    def unavailable(self, card, reason):
        card.set_value("Unavailable")
        card.subtitle_label.setText(reason)
        card.subtitle_label.setToolTip(reason)
        card.set_pill("Not verified", "WARN")

    def on_audit_finished(self, data: dict):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Run audit")
        errors = data.get("errors", {})
        ident = data.get("identity", {})
        proton = data.get("proton", {})
        gw = data.get("gw", {})
        ip = ident.get("ip") if self.known(ident.get("ip")) else proton.get("ip", "Unknown")
        isp = ident.get("isp") if self.known(ident.get("isp")) else proton.get("isp", "Unknown")
        city = ident.get("city", "")
        country = ident.get("country", "")
        location = ", ".join(str(value) for value in (city, country) if self.known(value))
        tunnel = bool(gw.get("is_tunnel") and gw.get("route_verified"))
        available = 0
        review = 0

        if "identity" in errors or ident.get("available") is False or not self.known(ip):
            self.unavailable(self.card_ip, errors.get("identity", "The public IP endpoint could not be reached."))
        else:
            available += 1
            self.card_ip.set_value(str(ip))
            self.card_ip.subtitle_label.setText(" · ".join(str(value) for value in (isp, location) if self.known(value)) or "Location details unavailable")
            self.card_ip.set_pill("Exit IP visible", "WARN")

        iface = gw.get("interface", "Unknown")
        if not self.known(iface):
            iface = proton.get("interface", "Unknown")
        if "gw" in errors or gw.get("available") is False or not self.known(iface):
            self.unavailable(self.card_route, errors.get("gw", "No default route was available to inspect."))
        else:
            available += 1
            self.card_route.set_value(str(iface))
            gateway = gw.get("gateway_ip", "Unknown")
            self.card_route.subtitle_label.setText(f"Gateway {gateway}" if self.known(gateway) else "Gateway address unavailable")
            self.card_route.set_pill("Tunnel route verified" if tunnel else "Route unverified", "SECURE" if tunnel else "WARN")
            if not tunnel:
                review += 1

        ports = data.get("ports", [])
        if "ports" in errors or "ports" not in data:
            self.unavailable(self.card_ports, errors.get("ports", "Listening socket data was not returned by the probe."))
        else:
            available += 1
            wildcard = sum(1 for port in ports if port.get("is_wan"))
            self.card_ports.set_value(f"{len(ports)} listening")
            self.card_ports.subtitle_label.setText(f"{wildcard} bound to wildcard addresses" if wildcard else "No wildcard-bound listeners detected")
            self.card_ports.set_pill("Review bindings" if wildcard else "No wildcard bind", "WARN" if wildcard else "SECURE")
            review += bool(wildcard)

        ipv6 = data.get("ipv6", {})
        if "ipv6" in errors or "ipv6" not in data or ipv6.get("available") is False:
            self.unavailable(self.card_ipv6, errors.get("ipv6", "IPv6 address data was not returned by the probe."))
        else:
            available += 1
            global_ipv6 = bool(ipv6.get("has_global_ipv6"))
            self.card_ipv6.set_value("Global address" if global_ipv6 else "No global address")
            ipv6_tunnel = bool(ipv6.get("route_verified") and ipv6.get("status") == "tunnel_routed")
            self.card_ipv6.subtitle_label.setText("The sampled IPv6 route uses an active tunnel" if ipv6_tunnel else "Check that IPv6 follows your intended route" if global_ipv6 else "No global IPv6 address found by this probe")
            self.card_ipv6.set_pill("Tunnel route verified" if ipv6_tunnel else "Review routing" if global_ipv6 else "Checked", "WARN" if global_ipv6 and not ipv6_tunnel else "SECURE")
            review += global_ipv6 and not ipv6_tunnel

        kernel = data.get("kernel", {})
        checked = [value for value in kernel.values() if self.known(value.get("current"))]
        if "kernel" in errors or not checked:
            self.unavailable(self.card_kernel, errors.get("kernel", "Kernel settings could not be read on this host."))
        else:
            available += 1
            matched = sum(value.get("current") == value.get("target") for value in checked)
            total = len(kernel)
            self.card_kernel.set_value(f"{matched} of {total} matched")
            self.card_kernel.subtitle_label.setText(f"{len(checked)} settings read against recommended values")
            complete = matched == total
            self.card_kernel.set_pill("Targets matched" if complete else "Review settings", "SECURE" if complete else "WARN")
            review += not complete

        devices = data.get("usb", [])
        if "usb" in errors or "usb" not in data:
            self.unavailable(self.card_usb, errors.get("usb", "USB inventory data was not returned by the probe."))
        else:
            available += 1
            peripherals = [device for device in devices if not device.get("is_root_hub")]
            blocked = sum(not device.get("authorized", True) for device in peripherals)
            self.card_usb.set_value(f"{len(peripherals)} device{'s' if len(peripherals) != 1 else ''}")
            self.card_usb.subtitle_label.setText(f"{blocked} blocked · {len(devices)} controller entries")
            self.card_usb.set_pill("Inventory checked", "SECURE")

        for card in self._cards:
            card.subtitle_label.setToolTip(card.subtitle_label.text())
        self.orb.set_summary(available)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_scan.setText(f"Last checked at {timestamp} · Run another audit to refresh")
        if available == 0:
            title = "System checks are unavailable."
            subtitle = "This host did not provide the data needed for an audit. See each signal below."
            badge = "Results unavailable"
        elif review:
            title = "A few things to review."
            subtitle = f"{review} signal{'s' if review != 1 else ''} need a closer look. Check the details before choosing an action."
            badge = "Review suggested"
        elif available < 6:
            title = "Your latest results are ready."
            subtitle = f"{available} of 6 checks returned data. Unavailable signals remain unverified."
            badge = "Partial audit"
        else:
            title = "Your latest results are ready."
            subtitle = "All six checks returned data. This snapshot reflects the signals shown below."
            badge = "Audit complete"
        self.b_title.setText(title)
        self.b_sub.setText(subtitle)
        self.audit_badge.setText(badge)
        self.audit_badge.setObjectName("StatusPillSecure" if available == 6 and not review else "StatusPillWarning")
        self.audit_badge.style().unpolish(self.audit_badge)
        self.audit_badge.style().polish(self.audit_badge)
        self.audit_completed.emit(f"Audit checked at {timestamp} · {available}/6 signals available")

    def run_action(self, callback, title, button):
        if self.action_worker is not None and self.action_worker.isRunning():
            return
        for control in self._action_buttons:
            control.setEnabled(False)
        for frame in self._actions:
            frame.setEnabled(False)
        self.action_feedback.setVisible(True)
        self.action_feedback.setStyleSheet("padding: 12px 16px; background: rgba(143, 168, 255, 12); border: 1px solid rgba(143, 168, 255, 25); border-radius: 12px; color: #a4aec8; font-size: 12px;")
        self.action_feedback.setText(f"{title} is running…")
        self.action_worker = ActionWorker(callback, self)
        self.action_worker.result.connect(lambda success, message: self.on_action_finished(title, success, message))
        self.action_worker.finished.connect(self.release_action_worker)
        self.action_worker.start()

    def release_action_worker(self):
        worker = self.sender()
        if self.action_worker is worker:
            self.action_worker = None
        worker.deleteLater()

    def on_action_finished(self, title, success, message):
        for button in self._action_buttons:
            button.setEnabled(True)
        for frame in self._actions:
            frame.setEnabled(True)
        color = "#65dbc5" if success else "#ff8294"
        self.action_feedback.setStyleSheet(f"padding: 12px 16px; background: rgba(143, 168, 255, 10); border: 1px solid rgba(143, 168, 255, 25); border-radius: 12px; color: {color}; font-size: 12px;")
        self.action_feedback.setText(f"{title}: {message or ('Completed' if success else 'Operation failed')}")
        self.action_feedback.setToolTip(message)
        if success:
            self.run_audit()

    def on_ghost_device(self):
        from cyberbreak.ui.widgets.ghost_dialog import run_ghost_workflow
        run_ghost_workflow(self, on_complete_callback=self.run_audit)

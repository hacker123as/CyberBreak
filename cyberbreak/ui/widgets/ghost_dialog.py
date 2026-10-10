import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor
from cyberbreak.core.spoofer_engine import SpooferEngine
from cyberbreak.ui.widgets.glass import GlassFrame, icon


class GhostWorker(QThread):
    finished_result = pyqtSignal(bool, str, dict)
    progress_status = pyqtSignal(str)

    def __init__(self, ignore_vpn: bool = False, parent=None):
        super().__init__(parent)
        self.ignore_vpn = ignore_vpn

    def run(self):
        self.progress_status.emit("Verifying VPN tunnel shield...")
        self.progress_status.emit("Executing deep hardware & fingerprint transformation...")
        ok, status, details = SpooferEngine.ghost_device(ignore_vpn=self.ignore_vpn)
        self.finished_result.emit(ok, status, details)


class GhostConfirmDialog(QDialog):
    def __init__(self, vpn_active: bool, vpn_interface: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ghost This Device — Confirmation")
        self.setFixedSize(540, 420)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.proceed = False
        self.ignore_vpn = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        frame = GlassFrame(self)
        frame.setObjectName("GlassCard")
        frame.setStyleSheet(
            "QFrame#GlassCard { background: #0c1220; border: 1px solid #1e293b; border-radius: 16px; }"
        )
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(24, 24, 24, 24)
        f_layout.setSpacing(16)

        # Header with Ghost Icon
        h_box = QHBoxLayout()
        ghost_lbl = QLabel()
        ghost_lbl.setPixmap(icon("ghost", "#00e676", 32).pixmap(32, 32))
        h_box.addWidget(ghost_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Ghost This Device")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #f4f6ff;")
        title_box.addWidget(title)

        subtitle = QLabel("Deep Hardware & Fingerprint Transformation")
        subtitle.setStyleSheet("font-size: 12px; color: #8fa8ff;")
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box, 1)
        f_layout.addLayout(h_box)

        # VPN Status Box
        vpn_box = QFrame()
        vpn_box.setStyleSheet(
            "background: rgba(16, 24, 39, 0.85); border: 1px solid "
            + ("#00e676" if vpn_active else "#ff9800")
            + "; border-radius: 10px; padding: 12px;"
        )
        v_layout = QVBoxLayout(vpn_box)
        v_layout.setSpacing(6)

        v_head = QHBoxLayout()
        v_status = QLabel("✓ VPN SHIELD ACTIVE" if vpn_active else "⚠️ VPN CONNECTION REQUIRED")
        v_status.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {'#00e676' if vpn_active else '#ffb74d'};"
        )
        v_head.addWidget(v_status)
        v_head.addStretch()
        if vpn_active and vpn_interface:
            v_iface = QLabel(f"Interface: {vpn_interface}")
            v_iface.setStyleSheet("font-size: 11px; color: #94a3b8;")
            v_head.addWidget(v_iface)
        v_layout.addLayout(v_head)

        if vpn_active:
            v_desc = QLabel(
                "Your internet traffic is routed through a secure VPN tunnel. "
                "Hardware transformations (MAC, hostname, machine-id) will execute safely "
                "behind your encrypted connection so ISP and network sensors cannot link old and new identities."
            )
        else:
            v_desc = QLabel(
                "We strongly require an active VPN connection before ghosting this device! "
                "Routing through a VPN ensures that local routers, ISP sensors, and network gateways "
                "cannot detect your hardware transformation in progress or correlate your identities."
            )
        v_desc.setStyleSheet("font-size: 11px; color: #cbd5e1; line-height: 1.4;")
        v_desc.setWordWrap(True)
        v_layout.addWidget(v_desc)
        f_layout.addWidget(vpn_box)

        # Action Summary
        actions_lbl = QLabel(
            "<b>The ghosting sequence will immediately:</b><br>"
            "• Randomize MAC addresses across all network interfaces<br>"
            "• Generate and assign a fresh random system hostname<br>"
            "• Reseed /etc/machine-id and D-Bus identifiers with cryptographic entropy<br>"
            "• Lock system timezone to UTC to defeat browser clock fingerprinting<br>"
            "• Flush local DNS caches, ARP neighbor tables, and drop memory pagecache"
        )
        actions_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.5;")
        actions_lbl.setTextFormat(Qt.TextFormat.RichText)
        f_layout.addWidget(actions_lbl)

        f_layout.addStretch()

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("OutlineButton")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        if not vpn_active:
            override_btn = QPushButton("Override & Ghost Anyway")
            override_btn.setObjectName("PanicButton")
            override_btn.setMinimumHeight(38)
            override_btn.clicked.connect(self.on_override)
            btn_box.addWidget(override_btn)
        else:
            ghost_btn = QPushButton("👻 Start Ghosting Sequence")
            ghost_btn.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #00b0ff); "
                "color: #030712; font-weight: 700; font-size: 13px; border-radius: 8px; border: none; padding: 10px 18px; } "
                "QPushButton:hover { background: #00e676; }"
            )
            ghost_btn.setMinimumHeight(38)
            ghost_btn.clicked.connect(self.on_ghost)
            btn_box.addWidget(ghost_btn)

        f_layout.addLayout(btn_box)
        layout.addWidget(frame)

    def on_ghost(self):
        self.proceed = True
        self.ignore_vpn = False
        self.accept()

    def on_override(self):
        self.proceed = True
        self.ignore_vpn = True
        self.accept()


class GhostCelebrationDialog(QDialog):
    def __init__(self, details: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Device is Now Ghost")
        self.setFixedSize(560, 520)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        frame = GlassFrame(self)
        frame.setObjectName("GlassCard")
        frame.setStyleSheet(
            "QFrame#GlassCard { background: #0b1326; border: 2px solid #00e676; border-radius: 18px; }"
        )
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(28, 28, 28, 28)
        f_layout.setSpacing(18)

        # Header
        h_box = QHBoxLayout()
        ghost_lbl = QLabel()
        ghost_lbl.setPixmap(icon("ghost", "#00e676", 36).pixmap(36, 36))
        h_box.addWidget(ghost_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("YOUR DEVICE IS NOW GHOST!")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #00e676; letter-spacing: 0.5px;")
        title_box.addWidget(title)

        subtitle = QLabel("All fingerprint data and hardware identifiers have been randomized.")
        subtitle.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box, 1)
        f_layout.addLayout(h_box)

        # Details list
        hostname = details.get("hostname", "Randomized")
        machine_id = details.get("machine_id", "Reseeded")
        timezone = details.get("timezone", "UTC")
        mac_dict = details.get("mac_addresses", {})

        mac_summary = []
        if isinstance(mac_dict, dict):
            for iface, mac in list(mac_dict.items())[:3]:
                mac_summary.append(f"<b>{iface}</b>: <font color='#00e676'>{mac}</font>")
        mac_str = "<br>• ".join(mac_summary) if mac_summary else "All active adapters randomized"

        info_box = QFrame()
        info_box.setStyleSheet(
            "background: rgba(15, 23, 42, 0.75); border: 1px solid #1e293b; border-radius: 12px; padding: 14px;"
        )
        i_layout = QVBoxLayout(info_box)
        i_layout.setSpacing(8)

        details_html = (
            f"<div style='font-size: 12px; color: #f1f5f9; line-height: 1.5;'>"
            f"✓ <b>New Hostname:</b> <font color='#38bdf8'>{hostname}</font><br>"
            f"✓ <b>New Machine-ID:</b> <font color='#a78bfa'>{str(machine_id)[:16]}...</font><br>"
            f"✓ <b>Timezone:</b> <font color='#34d399'>{timezone}</font><br>"
            f"✓ <b>MAC Addresses:</b><br>• {mac_str}<br>"
            f"✓ <b>System Caches:</b> <font color='#00e676'>RAM pagecache dropped · DNS cache cleared</font>"
            f"</div>"
        )
        lbl_details = QLabel(details_html)
        lbl_details.setTextFormat(Qt.TextFormat.RichText)
        lbl_details.setWordWrap(True)
        i_layout.addWidget(lbl_details)
        f_layout.addWidget(info_box)

        # Prominent Notification Callout (The requested user text!)
        notice_box = QFrame()
        notice_box.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 230, 118, 0.15), stop:1 rgba(0, 176, 255, 0.15)); "
            "border: 1px solid #00e676; border-radius: 10px; padding: 14px;"
        )
        n_layout = QVBoxLayout(notice_box)
        n_layout.setSpacing(6)

        n_title = QLabel("💡 YOU CAN NOW TURN OFF YOUR VPN IF DESIRED")
        n_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #00e676;")
        n_layout.addWidget(n_title)

        n_msg = QLabel(
            "We used the VPN during the ghosting sequence so that nothing on the network detects "
            "your device is now a ghost. All your persistent hardware identifiers, network addresses, "
            "and memory caches have been transformed into completely fresh pseudo-random entropy."
        )
        n_msg.setStyleSheet("font-size: 11px; color: #e2e8f0; line-height: 1.4;")
        n_msg.setWordWrap(True)
        n_layout.addWidget(n_msg)
        f_layout.addWidget(notice_box)

        f_layout.addStretch()

        # Close button
        btn_close = QPushButton("Done (Close)")
        btn_close.setStyleSheet(
            "QPushButton { background: #00e676; color: #030712; font-weight: 700; font-size: 13px; "
            "border-radius: 8px; border: none; padding: 10px; } "
            "QPushButton:hover { background: #00c853; }"
        )
        btn_close.setMinimumHeight(40)
        btn_close.clicked.connect(self.accept)
        f_layout.addWidget(btn_close)

        layout.addWidget(frame)


def run_ghost_workflow(parent_widget, on_complete_callback=None):
    vpn_active, vpn_iface = SpooferEngine.check_vpn_active()
    confirm = GhostConfirmDialog(vpn_active, vpn_iface, parent_widget)
    if confirm.exec() != QDialog.DialogCode.Accepted or not confirm.proceed:
        return

    # Create worker
    worker = GhostWorker(ignore_vpn=confirm.ignore_vpn, parent=parent_widget)

    def on_finished(ok: bool, status: str, details: dict):
        worker.deleteLater()
        if ok and status == "GHOST_SUCCESS":
            dlg = GhostCelebrationDialog(details, parent_widget)
            dlg.exec()
            if on_complete_callback:
                on_complete_callback()
        elif status == "VPN_REQUIRED":
            # Re-trigger with warning
            run_ghost_workflow(parent_widget, on_complete_callback)

    worker.finished_result.connect(on_finished)
    worker.start()

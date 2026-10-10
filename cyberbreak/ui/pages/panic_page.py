from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from cyberbreak.core.isolation import SystemIsolation
from cyberbreak.ui.widgets.nuke_dialog import NukeDialog
from cyberbreak.ui.widgets.status_card import StatusCard

class PanicPage(QWidget):
    """Emergency isolation switch and master crypto-nuke panic center."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("EMERGENCY DEFENSE & PANIC CENTER // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Dual-Action Panic System: Sub-50ms Network Blackout and Master Cryptographic Nuke")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        layout.addLayout(header)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.iso_card = StatusCard(
            "ISOLATION SYSTEM",
            "Disarmed",
            "Sub-50ms radio and socket blackout",
            "STANDBY",
            "SECURE"
        )
        grid.addWidget(self.iso_card, 0, 0)

        self.nuke_card = StatusCard(
            "CRYPTO-NUKE SYSTEM",
            "Locked",
            "Password-gated LUKS keyslot obliterator",
            "ARMED",
            "DANGER"
        )
        grid.addWidget(self.nuke_card, 0, 1)

        layout.addLayout(grid)

        # Action 1 Frame: ISOLATE NOW
        iso_frame = QFrame()
        iso_frame.setObjectName("Card")
        i_layout = QVBoxLayout(iso_frame)
        i_layout.setContentsMargins(20, 20, 20, 20)
        i_layout.setSpacing(12)

        i_title = QLabel("ACTION 1: EMERGENCY ISOLATION (KILL IT ALL - NETWORK BLACKOUT)")
        i_title.setObjectName("CardTitle")
        i_layout.addWidget(i_title)

        i_desc = QLabel(
            "Instantly severs all network communication in under 50 milliseconds:\n"
            "• Executes kernel rfkill block all (Wi-Fi, Bluetooth, WWAN disabled)\n"
            "• Shuts down NetworkManager (nmcli networking off) and drops all physical NICs\n"
            "• Flushes iptables/ip6tables and sets unconditional DROP policies\n"
            "• Terminates active browsers, VPNs, Tor, SSH, and messenger processes (pkill -9)"
        )
        i_desc.setObjectName("HeaderSubtitle")
        i_desc.setStyleSheet("color: #a0a0ab; line-height: 1.4;")
        i_layout.addWidget(i_desc)

        i_btn_row = QHBoxLayout()
        self.isolate_btn = QPushButton("ISOLATE SYSTEM NOW")
        self.isolate_btn.setObjectName("PanicButton")
        self.isolate_btn.setStyleSheet(
            "background-color: #ff3344; color: #ffffff; font-weight: 800; "
            "padding: 12px 24px; font-size: 13px; border-radius: 6px;"
        )
        self.isolate_btn.clicked.connect(self.on_isolate)
        i_btn_row.addWidget(self.isolate_btn)
        i_btn_row.addStretch()
        i_layout.addLayout(i_btn_row)

        layout.addWidget(iso_frame)

        # Action 2 Frame: NUKE SYSTEM
        nuke_frame = QFrame()
        nuke_frame.setObjectName("Card")
        n_layout = QVBoxLayout(nuke_frame)
        n_layout.setContentsMargins(20, 20, 20, 20)
        n_layout.setSpacing(12)

        n_title = QLabel("ACTION 2: MASTER PANIC NUKE (DRIVE OBLITERATION)")
        n_title.setObjectName("CardTitle")
        n_title.setStyleSheet("color: #ff3344; font-weight: 800;")
        n_layout.addWidget(n_title)

        n_desc = QLabel(
            "Permanent anti-forensic cryptographic destruction (Password-Protected):\n"
            "• Obliterates LUKS keyslots and headers via cryptsetup luksErase + random block rewrite in <100ms\n"
            "• Issues hardware NVMe/SSD blkdiscard NAND block purges across all drives\n"
            "• Zaps MBR/GPT partition tables via sgdisk\n"
            "• Triggers immediate intentional kernel crash panic (sysrq c) to defeat DRAM cold-boot forensic dumps\n"
            "REQUIRES EXPLICIT AUTHORIZATION PASSPHRASE."
        )
        n_desc.setObjectName("HeaderSubtitle")
        n_desc.setStyleSheet("color: #a0a0ab; line-height: 1.4;")
        n_layout.addWidget(n_desc)

        n_btn_row = QHBoxLayout()
        self.nuke_btn = QPushButton("OPEN MASTER NUKE CONSOLE")
        self.nuke_btn.setStyleSheet(
            "background-color: #2b1418; color: #ff3344; font-weight: 800; "
            "border: 2px solid #ff3344; padding: 12px 24px; font-size: 13px; border-radius: 6px;"
        )
        self.nuke_btn.clicked.connect(self.open_nuke_modal)
        n_btn_row.addWidget(self.nuke_btn)
        n_btn_row.addStretch()
        n_layout.addLayout(n_btn_row)

        layout.addWidget(nuke_frame)
        layout.addStretch()

    def on_isolate(self):
        SystemIsolation.trigger_instant_isolation()
        self.iso_card.set_value("SYSTEM ISOLATED")
        self.iso_card.set_pill("BLACKOUT", "DANGER")

    def open_nuke_modal(self):
        dlg = NukeDialog(self)
        dlg.exec()

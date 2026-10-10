from PyQt6.QtWidgets import QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QGridLayout
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from cyberbreak.core.spoofer_engine import SpooferEngine
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.ui.widgets.glass import GlassFrame, icon

class SpooferPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(8)
        title = QLabel('Device identity')
        title.setObjectName('HeaderTitle')
        title.setWordWrap(True)
        subtitle = QLabel('Manage network addresses, hostnames, machine IDs, and timezone.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        refresh_btn = QPushButton('Refresh adapters')
        refresh_btn.setIcon(icon('refresh'))
        refresh_btn.setObjectName('OutlineButton')
        refresh_btn.clicked.connect(self.refresh_adapters)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Ghost this device Hero Card
        ghost_frame = GlassFrame()
        ghost_frame.setObjectName('GlassCard')
        ghost_frame.setStyleSheet(
            "QFrame#GlassCard { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 230, 118, 0.08), stop:1 rgba(0, 176, 255, 0.05)); "
            "border: 1px solid rgba(0, 230, 118, 0.35); border-radius: 14px; }"
        )
        gh_layout = QHBoxLayout(ghost_frame)
        gh_layout.setContentsMargins(22, 18, 22, 18)
        gh_layout.setSpacing(18)

        gh_icon_lbl = QLabel()
        gh_icon_lbl.setPixmap(icon('ghost', '#00e676', 32).pixmap(32, 32))
        gh_layout.addWidget(gh_icon_lbl)

        gh_text = QVBoxLayout()
        gh_text.setSpacing(4)
        gh_title = QLabel('Ghost this device')
        gh_title.setStyleSheet('font-size: 17px; font-weight: 700; color: #f4f6ff;')
        gh_text.addWidget(gh_title)

        gh_desc = QLabel(
            'Complete hardware identity metamorphosis behind a VPN shield. '
            'Randomizes all MAC addresses, rotates system hostname, reseeds Machine-ID, '
            'locks timezone to UTC, and purges kernel memory residue.'
        )
        gh_desc.setStyleSheet('font-size: 11px; color: #94a3b8; line-height: 1.4;')
        gh_desc.setWordWrap(True)
        gh_text.addWidget(gh_desc)
        gh_layout.addLayout(gh_text, 1)

        self.btn_ghost = QPushButton('👻 Ghost this device')
        self.btn_ghost.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #00b0ff); "
            "color: #030712; font-weight: 700; font-size: 13px; border-radius: 8px; border: none; padding: 12px 22px; } "
            "QPushButton:hover { background: #00e676; }"
        )
        self.btn_ghost.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ghost.clicked.connect(self.on_ghost_device)
        gh_layout.addWidget(self.btn_ghost)

        layout.addWidget(ghost_frame)

        adapter_frame = GlassFrame()
        adapter_frame.setObjectName('GlassCard')
        ad_layout = QVBoxLayout(adapter_frame)
        ad_layout.setContentsMargins(22, 22, 22, 22)
        ad_layout.setSpacing(14)
        ad_title = QLabel('Network address')
        ad_title.setObjectName('CardTitle')
        ad_layout.addWidget(ad_title)
        select_row = QGridLayout()
        select_row.setHorizontalSpacing(12)
        select_row.setVerticalSpacing(12)
        select_row.setColumnStretch(1, 1)
        select_row.addWidget(QLabel('Network interface'), 0, 0)
        self.adapter_combo = QComboBox()
        self.adapter_combo.currentIndexChanged.connect(self.on_adapter_selected)
        self.adapter_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.adapter_combo.setMinimumContentsLength(16)
        select_row.addWidget(self.adapter_combo, 0, 1)
        self.spoof_mac_btn = QPushButton('Randomize address')
        self.spoof_mac_btn.setObjectName('AccentButton')
        self.spoof_mac_btn.clicked.connect(self.on_spoof_mac)
        select_row.addWidget(self.spoof_mac_btn, 1, 1, Qt.AlignmentFlag.AlignLeft)
        ad_layout.addLayout(select_row)
        self.mac_info_label = QLabel('Current MAC: --- | Status: ---')
        self.mac_info_label.setObjectName('MonoValue')
        self.mac_info_label.setWordWrap(True)
        ad_layout.addWidget(self.mac_info_label)
        layout.addWidget(adapter_frame)
        grid = QGridLayout()
        grid.setSpacing(16)
        self.host_card = StatusCard('System hostname', 'Checking…', 'Current system hostname', 'Local', 'WARN')
        grid.addWidget(self.host_card, 0, 0)
        self.mid_card = StatusCard('System machine-ID', 'Checking…', 'Local machine identifier', 'Local', 'WARN')
        grid.addWidget(self.mid_card, 0, 1)
        layout.addLayout(grid)
        actions_frame = GlassFrame()
        actions_frame.setObjectName('GlassCard')
        act_layout = QGridLayout(actions_frame)
        act_layout.setContentsMargins(22, 22, 22, 22)
        act_layout.setSpacing(12)
        host_btn = QPushButton('Randomize hostname')
        host_btn.setObjectName('CyanButton')
        host_btn.clicked.connect(self.on_randomize_hostname)
        act_layout.addWidget(host_btn, 0, 0)
        mid_btn = QPushButton('Renew machine ID')
        mid_btn.setObjectName('SecondaryButton')
        mid_btn.clicked.connect(self.on_reseed_machine_id)
        act_layout.addWidget(mid_btn, 0, 1)
        utc_btn = QPushButton('Use UTC timezone')
        utc_btn.setObjectName('OutlineButton')
        utc_btn.clicked.connect(SpooferEngine.set_utc_timezone)
        act_layout.addWidget(utc_btn, 1, 0, 1, 2)
        layout.addWidget(actions_frame)
        layout.addStretch()
        self.interfaces = []
        self.refresh_adapters()
        self.update_system_ids()

    def refresh_adapters(self):
        self.interfaces = SpooferEngine.get_network_interfaces()
        self.adapter_combo.clear()
        for iface in self.interfaces:
            self.adapter_combo.addItem(f"{iface['name']} ({iface['mac']})", iface['name'])

    def on_adapter_selected(self, index):
        if 0 <= index < len(self.interfaces):
            iface = self.interfaces[index]
            self.mac_info_label.setText(f"Interface: {iface['name']} | Current MAC: {iface['mac']} | State: {iface['state']}")

    def on_spoof_mac(self):
        curr_iface = self.adapter_combo.currentData()
        if curr_iface:
            SpooferEngine.randomize_mac(curr_iface)
            self.refresh_adapters()

    def update_system_ids(self):
        try:
            import socket
            self.host_card.set_value(socket.gethostname())
        except Exception:
            self.host_card.set_value('Unknown')
        try:
            with open('/etc/machine-id', 'r') as f:
                mid = f.read().strip()
                self.mid_card.set_value(f'{mid[:12]}...')
        except Exception:
            self.mid_card.set_value('Unavailable')

    def on_randomize_hostname(self):
        ok, res = SpooferEngine.randomize_hostname()
        if ok:
            self.host_card.set_value(res)

    def on_reseed_machine_id(self):
        ok, res = SpooferEngine.reseed_machine_id()
        if ok:
            self.mid_card.set_value(f'{res[:12]}...')

    def on_ghost_device(self):
        from cyberbreak.ui.widgets.ghost_dialog import run_ghost_workflow
        def on_complete():
            self.refresh_adapters()
            self.update_system_ids()
        run_ghost_workflow(self, on_complete_callback=on_complete)

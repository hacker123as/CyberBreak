from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.hardware_manager import HardwareManager
from cyberbreak.core.port_auditor import PortAuditor
from cyberbreak.ui.widgets.status_card import StatusCard

class ScanWorker(QThread):
    finished_data = pyqtSignal(dict)

    def run(self):
        usb_devs = HardwareManager.get_connected_usb_devices()
        ports = PortAuditor.get_open_listening_ports()
        self.finished_data.emit({
            "usb": usb_devs,
            "ports": ports
        })

class USBGuardPage(QWidget):
    """
    Hardware Defense, USB Port Lockdown, and Network Listening Socket Lockdown.
    Engineered by lilami only.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.usb_locked = False
        self.storage_blocked = False
        self.cam_disabled = False
        self.mic_muted = False
        self.bt_blocked = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("HARDWARE & PORT DEFENSE // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Deep USB port lockdown, live device tree, network listening socket killswitches & sensor interlocks")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.refresh_btn = QPushButton("REFRESH DEFENSES")
        self.refresh_btn.setObjectName("OutlineButton")
        self.refresh_btn.clicked.connect(self.run_full_scan)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #202028;
                background-color: #0d0d11;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #14141a;
                color: #8c93a8;
                padding: 10px 20px;
                font-weight: 700;
                font-size: 12px;
                border: 1px solid #202028;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #1a1a24;
                color: #00ff66;
                border-top: 2px solid #00ff66;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
        """)

        # 1. USB Tab
        self.usb_tab = QWidget()
        self.setup_usb_tab()
        self.tabs.addTab(self.usb_tab, "USB PORTS & HARDWARE LOCKDOWN")

        # 2. Network Ports Tab
        self.net_tab = QWidget()
        self.setup_net_tab()
        self.tabs.addTab(self.net_tab, "NETWORK OPEN PORTS LOCKDOWN")

        # 3. Sensor Interlocks Tab
        self.sensor_tab = QWidget()
        self.setup_sensor_tab()
        self.tabs.addTab(self.sensor_tab, "HARDWARE SENSOR KILLSWITCHES")

        layout.addWidget(self.tabs)

        self.run_full_scan()

    # -------------------------------------------------------------
    # TAB 1: USB PORTS & DEVICE DEFENSE
    # -------------------------------------------------------------
    def setup_usb_tab(self):
        tab_layout = QVBoxLayout(self.usb_tab)
        tab_layout.setContentsMargins(16, 16, 16, 16)
        tab_layout.setSpacing(14)

        # Status Cards Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_usb_state = StatusCard("USB PORT STATUS", "Authorized", "Sysfs auto-authorization", "DEFAULT", "WARN")
        grid.addWidget(self.card_usb_state, 0, 0)

        self.card_usb_count = StatusCard("CONNECTED USB DEVICES", "Probing...", "Physical controllers & hubs", "SCANNING", "SECURE")
        grid.addWidget(self.card_usb_count, 0, 1)

        self.card_storage_drv = StatusCard("MASS STORAGE DRIVER", "Active", "usb-storage & uas kernel modules", "UNBLOCKED", "WARN")
        grid.addWidget(self.card_storage_drv, 0, 2)

        tab_layout.addLayout(grid)

        # Controls Bar
        ctrl_bar = QHBoxLayout()
        self.btn_usb_lockdown = QPushButton("🔒 LOCKDOWN ALL USB PORTS")
        self.btn_usb_lockdown.setObjectName("CyanButton")
        self.btn_usb_lockdown.clicked.connect(self.toggle_usb_lockdown)
        ctrl_bar.addWidget(self.btn_usb_lockdown)

        self.btn_storage_block = QPushButton("💾 BLOCK USB STORAGE DRIVERS")
        self.btn_storage_block.setObjectName("SecondaryButton")
        self.btn_storage_block.clicked.connect(self.toggle_storage_driver)
        ctrl_bar.addWidget(self.btn_storage_block)

        ctrl_bar.addStretch()
        tab_layout.addLayout(ctrl_bar)

        # Devices Table
        tbl_label = QLabel("CONNECTED USB DEVICES & INDIVIDUAL PORT CONTROLS:")
        tbl_label.setObjectName("CardTitle")
        tab_layout.addWidget(tbl_label)

        self.usb_table = QTableWidget()
        self.usb_table.setColumnCount(7)
        self.usb_table.setHorizontalHeaderLabels([
            "PORT / BUS", "DEVICE NAME", "VENDOR:PRODUCT", "TYPE", "SPEED", "STATUS", "ACTION"
        ])
        self.usb_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.usb_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.usb_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.usb_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.usb_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.usb_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.usb_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.usb_table.setStyleSheet("""
            QTableWidget {
                background-color: #121217;
                color: #e5e5ec;
                border: 1px solid #202028;
                border-radius: 6px;
                gridline-color: #1a1a24;
            }
            QHeaderView::section {
                background-color: #16161f;
                color: #00ff66;
                padding: 6px;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid #202028;
            }
        """)
        tab_layout.addWidget(self.usb_table)

    # -------------------------------------------------------------
    # TAB 2: NETWORK OPEN PORTS LOCKDOWN
    # -------------------------------------------------------------
    def setup_net_tab(self):
        tab_layout = QVBoxLayout(self.net_tab)
        tab_layout.setContentsMargins(16, 16, 16, 16)
        tab_layout.setSpacing(14)

        # Status Cards Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_net_total = StatusCard("LISTENING SOCKETS", "Probing...", "Active TCP/UDP daemons", "SCANNING", "SECURE")
        grid.addWidget(self.card_net_total, 0, 0)

        self.card_net_exposed = StatusCard("WAN EXPOSED PORTS", "Probing...", "Bound to 0.0.0.0 or wildcard", "AUDITING", "WARN")
        grid.addWidget(self.card_net_exposed, 0, 1)

        self.card_net_policy = StatusCard("NETFILTER INBOUND", "Protected", "Inbound packet drop filter", "ACTIVE", "SECURE")
        grid.addWidget(self.card_net_policy, 0, 2)

        tab_layout.addLayout(grid)

        # Controls Bar
        ctrl_bar = QHBoxLayout()
        self.btn_ports_lockdown = QPushButton("🚨 LOCKDOWN ALL OPEN PORTS")
        self.btn_ports_lockdown.setObjectName("PanicButton")
        self.btn_ports_lockdown.clicked.connect(self.lockdown_all_network_ports)
        ctrl_bar.addWidget(self.btn_ports_lockdown)

        lbl_desc = QLabel("Drops inbound traffic on all listening ports via Netfilter rules and halts rogue daemons.")
        lbl_desc.setObjectName("HeaderSubtitle")
        ctrl_bar.addWidget(lbl_desc)

        ctrl_bar.addStretch()
        tab_layout.addLayout(ctrl_bar)

        # Ports Table
        tbl_label = QLabel("ACTIVE LISTENING NETWORK PORTS & DAEMONS:")
        tbl_label.setObjectName("CardTitle")
        tab_layout.addWidget(tbl_label)

        self.net_table = QTableWidget()
        self.net_table.setColumnCount(7)
        self.net_table.setHorizontalHeaderLabels([
            "PROTO", "PORT", "BIND ADDRESS", "PID", "SERVICE / PROCESS", "EXPOSURE RISK", "ACTION"
        ])
        self.net_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.net_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.net_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.net_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.net_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.net_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.net_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.net_table.setStyleSheet("""
            QTableWidget {
                background-color: #121217;
                color: #e5e5ec;
                border: 1px solid #202028;
                border-radius: 6px;
                gridline-color: #1a1a24;
            }
            QHeaderView::section {
                background-color: #16161f;
                color: #00ddff;
                padding: 6px;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid #202028;
            }
        """)
        tab_layout.addWidget(self.net_table)

    # -------------------------------------------------------------
    # TAB 3: HARDWARE SENSOR INTERLOCKS
    # -------------------------------------------------------------
    def setup_sensor_tab(self):
        tab_layout = QVBoxLayout(self.sensor_tab)
        tab_layout.setContentsMargins(16, 16, 16, 16)
        tab_layout.setSpacing(16)

        # Status Cards Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_cam = StatusCard("WEBCAM DRIVER", "Active", "Kernel uvcvideo driver", "UNLOCKED", "WARN")
        grid.addWidget(self.card_cam, 0, 0)

        self.card_mic = StatusCard("MICROPHONE CAPTURE", "Active", "Audio capture interface", "UNLOCKED", "WARN")
        grid.addWidget(self.card_mic, 0, 1)

        self.card_bt = StatusCard("BLUETOOTH RADIO", "Active", "rfkill hardware switch", "UNLOCKED", "WARN")
        grid.addWidget(self.card_bt, 0, 2)

        tab_layout.addLayout(grid)

        # Action Panel
        frame = QFrame()
        frame.setObjectName("Card")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(18, 18, 18, 18)
        f_layout.setSpacing(14)

        # Webcam
        cam_row = QHBoxLayout()
        c_info = QVBoxLayout()
        c_lbl = QLabel("Hardware Webcam Neutralizer")
        c_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        c_sub = QLabel("Unloads uvcvideo kernel module to physically disconnect /dev/video* hardware.")
        c_sub.setObjectName("HeaderSubtitle")
        c_info.addWidget(c_lbl)
        c_info.addWidget(c_sub)
        cam_row.addLayout(c_info)
        cam_row.addStretch()

        self.cam_btn = QPushButton("KILL WEBCAM DRIVER")
        self.cam_btn.setObjectName("PanicButton")
        self.cam_btn.clicked.connect(self.toggle_cam)
        cam_row.addWidget(self.cam_btn)
        f_layout.addLayout(cam_row)

        f_layout.addWidget(self.create_divider())

        # Mic
        mic_row = QHBoxLayout()
        m_info = QVBoxLayout()
        m_lbl = QLabel("Hardware Microphone Mute")
        m_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        m_sub = QLabel("Zeroes hardware audio capture gain in ALSA, PulseAudio, and PipeWire.")
        m_sub.setObjectName("HeaderSubtitle")
        m_info.addWidget(m_lbl)
        m_info.addWidget(m_sub)
        mic_row.addLayout(m_info)
        mic_row.addStretch()

        self.mic_btn = QPushButton("MUTE MICROPHONE")
        self.mic_btn.setObjectName("SecondaryButton")
        self.mic_btn.clicked.connect(self.toggle_mic)
        mic_row.addWidget(self.mic_btn)
        f_layout.addLayout(mic_row)

        f_layout.addWidget(self.create_divider())

        # Bluetooth
        bt_row = QHBoxLayout()
        b_info = QVBoxLayout()
        b_lbl = QLabel("Bluetooth Radio Killswitch")
        b_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        b_sub = QLabel("Blocks all physical Bluetooth transmitters at kernel rfkill controller layer.")
        b_sub.setObjectName("HeaderSubtitle")
        b_info.addWidget(b_lbl)
        b_info.addWidget(b_sub)
        bt_row.addLayout(b_info)
        bt_row.addStretch()

        self.bt_btn = QPushButton("BLOCK BLUETOOTH")
        self.bt_btn.setObjectName("CyanButton")
        self.bt_btn.clicked.connect(self.toggle_bt)
        bt_row.addWidget(self.bt_btn)
        f_layout.addLayout(bt_row)

        tab_layout.addWidget(frame)
        tab_layout.addStretch()

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #242429;")
        return line

    # -------------------------------------------------------------
    # SCAN & UPDATE LOGIC
    # -------------------------------------------------------------
    def run_full_scan(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("SCANNING...")
        self.worker = ScanWorker()
        self.worker.finished_data.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, data: dict):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("REFRESH DEFENSES")

        # 1. Update USB Tab
        usb_list = data.get("usb", [])
        self.card_usb_count.set_value(f"{len(usb_list)} Devices")
        self.card_usb_count.subtitle_label.setText(f"{sum(1 for d in usb_list if not d['is_root_hub'])} Peripherals connected")

        self.usb_table.setRowCount(len(usb_list))
        for row, dev in enumerate(usb_list):
            self.usb_table.setItem(row, 0, QTableWidgetItem(f"{dev['dev_id']} (Bus {dev['bus']})"))
            self.usb_table.setItem(row, 1, QTableWidgetItem(f"{dev['manufacturer']} {dev['product']}"))
            self.usb_table.setItem(row, 2, QTableWidgetItem(dev['vid_pid']))
            self.usb_table.setItem(row, 3, QTableWidgetItem(dev['type']))
            self.usb_table.setItem(row, 4, QTableWidgetItem(dev['speed']))

            status_item = QTableWidgetItem("AUTHORIZED" if dev["authorized"] else "BLOCKED")
            status_item.setForeground(Qt.GlobalColor.green if dev["authorized"] else Qt.GlobalColor.red)
            self.usb_table.setItem(row, 5, status_item)

            # Action button
            dev_id = dev["dev_id"]
            auth_now = dev["authorized"]
            btn = QPushButton("BLOCK" if auth_now else "AUTHORIZE")
            btn.setStyleSheet(
                "background-color: #ff2233; color: #fff; font-size: 10px; font-weight: 700; padding: 4px;"
                if auth_now else
                "background-color: #00ff66; color: #000; font-size: 10px; font-weight: 700; padding: 4px;"
            )
            btn.clicked.connect(lambda checked, d=dev_id, a=not auth_now: self.on_toggle_device_auth(d, a))
            self.usb_table.setCellWidget(row, 6, btn)

        # 2. Update Network Ports Tab
        ports_list = data.get("ports", [])
        wan_count = sum(1 for p in ports_list if p.get("is_wan"))
        self.card_net_total.set_value(f"{len(ports_list)} Open Sockets")
        self.card_net_total.subtitle_label.setText(f"{len(ports_list)} listening daemons detected")

        self.card_net_exposed.set_value(f"{wan_count} WAN Ports")
        if wan_count > 0:
            self.card_net_exposed.set_pill(f"{wan_count} EXPOSED", "DANGER")
            self.card_net_exposed.subtitle_label.setText("Ports bound to 0.0.0.0 or wildcard")
        else:
            self.card_net_exposed.set_pill("ISOLATED", "SECURE")
            self.card_net_exposed.subtitle_label.setText("Zero WAN listening ports detected")

        self.net_table.setRowCount(len(ports_list))
        for row, p in enumerate(ports_list):
            self.net_table.setItem(row, 0, QTableWidgetItem(p["proto"]))
            self.net_table.setItem(row, 1, QTableWidgetItem(str(p["port"])))
            self.net_table.setItem(row, 2, QTableWidgetItem(p["bind_ip"]))
            self.net_table.setItem(row, 3, QTableWidgetItem(str(p["pid"]) if p["pid"] else "-"))
            self.net_table.setItem(row, 4, QTableWidgetItem(p["process"]))

            risk_item = QTableWidgetItem(p["risk"])
            if p["is_wan"]:
                risk_item.setForeground(Qt.GlobalColor.red)
            else:
                risk_item.setForeground(Qt.GlobalColor.green)
            self.net_table.setItem(row, 5, risk_item)

            # Action button
            port_num = p["port"]
            proto_val = p["proto"]
            pid_val = p["pid"]
            btn_kill = QPushButton("KILL & DROP")
            btn_kill.setStyleSheet("background-color: #ff2233; color: #fff; font-size: 10px; font-weight: 700; padding: 4px;")
            btn_kill.clicked.connect(lambda checked, pt=port_num, pr=proto_val, pd=pid_val: self.on_lockdown_single_port(pt, pr, pd))
            self.net_table.setCellWidget(row, 6, btn_kill)

    # -------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------
    def toggle_usb_lockdown(self):
        self.usb_locked = not self.usb_locked
        HardwareManager.set_usb_lockdown(self.usb_locked)
        if self.usb_locked:
            self.card_usb_state.set_value("LOCKED")
            self.card_usb_state.set_pill("ARMED", "SECURE")
            self.btn_usb_lockdown.setText("🔓 RESTORE USB PORTS")
            self.btn_usb_lockdown.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.card_usb_state.set_value("Authorized")
            self.card_usb_state.set_pill("DEFAULT", "WARN")
            self.btn_usb_lockdown.setText("🔒 LOCKDOWN ALL USB PORTS")
            self.btn_usb_lockdown.setStyleSheet("")
        self.run_full_scan()

    def toggle_storage_driver(self):
        self.storage_blocked = not self.storage_blocked
        HardwareManager.set_usb_storage_lock(self.storage_blocked)
        if self.storage_blocked:
            self.card_storage_drv.set_value("BLOCKED")
            self.card_storage_drv.set_pill("ARMED", "SECURE")
            self.btn_storage_block.setText("💾 ALLOW STORAGE DRIVERS")
            self.btn_storage_block.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.card_storage_drv.set_value("Active")
            self.card_storage_drv.set_pill("UNBLOCKED", "WARN")
            self.btn_storage_block.setText("💾 BLOCK USB STORAGE DRIVERS")
            self.btn_storage_block.setStyleSheet("")

    def on_toggle_device_auth(self, dev_id: str, auth: bool):
        HardwareManager.set_device_authorization(dev_id, auth)
        self.run_full_scan()

    def on_lockdown_single_port(self, port: int, proto: str, pid: int):
        PortAuditor.lockdown_single_port(port, proto, pid)
        self.run_full_scan()

    def lockdown_all_network_ports(self):
        ok, res = PortAuditor.lockdown_all_open_ports()
        if ok:
            self.card_net_policy.set_value("LOCKED DOWN")
            self.card_net_policy.set_pill("ALL DROPPED", "SECURE")
        self.run_full_scan()

    def toggle_cam(self):
        self.cam_disabled = not self.cam_disabled
        HardwareManager.set_webcam_state(self.cam_disabled)
        if self.cam_disabled:
            self.card_cam.set_value("DRIVER KILLED")
            self.card_cam.set_pill("SAFE", "SECURE")
            self.cam_btn.setText("RESTORE WEBCAM")
            self.cam_btn.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.card_cam.set_value("Active")
            self.card_cam.set_pill("UNLOCKED", "WARN")
            self.cam_btn.setText("KILL WEBCAM DRIVER")
            self.cam_btn.setStyleSheet("")

    def toggle_mic(self):
        self.mic_muted = not self.mic_muted
        HardwareManager.set_microphone_mute(self.mic_muted)
        if self.mic_muted:
            self.card_mic.set_value("MUTED")
            self.card_mic.set_pill("MUTED", "SECURE")
            self.mic_btn.setText("UNMUTE MICROPHONE")
            self.mic_btn.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.card_mic.set_value("Active")
            self.card_mic.set_pill("UNLOCKED", "WARN")
            self.mic_btn.setText("MUTE MICROPHONE")
            self.mic_btn.setStyleSheet("")

    def toggle_bt(self):
        self.bt_blocked = not self.bt_blocked
        HardwareManager.set_bluetooth_state(self.bt_blocked)
        if self.bt_blocked:
            self.card_bt.set_value("RADIO BLOCKED")
            self.card_bt.set_pill("MUTED", "SECURE")
            self.bt_btn.setText("RESTORE BLUETOOTH")
            self.bt_btn.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.card_bt.set_value("Active")
            self.card_bt.set_pill("UNLOCKED", "WARN")
            self.bt_btn.setText("BLOCK BLUETOOTH")
            self.bt_btn.setStyleSheet("")

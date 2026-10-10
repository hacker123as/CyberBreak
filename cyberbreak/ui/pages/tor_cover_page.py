from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDateTime
from cyberbreak.core.tor_controller import TorController, DecoyTrafficGenerator
from cyberbreak.ui.widgets.status_card import StatusCard

class TorProbeWorker(QThread):
    finished_info = pyqtSignal(dict)

    def run(self):
        info = TorController.get_tor_info()
        self.finished_info.emit(info)

class TorCoverPage(QWidget):
    """
    Tor Control Port Interface, Real Circuit Radar, and Synthetic Cover Traffic Engine.
    Engineered by lilami only.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.decoy_engine = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("TOR CONTROLLER & CIRCUIT RADAR // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Live circuit topology inspection, authenticated IPC control socket & anti-timing decoy stream")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.refresh_btn = QPushButton("REFRESH CIRCUITS")
        self.refresh_btn.setObjectName("OutlineButton")
        self.refresh_btn.clicked.connect(self.run_tor_probe)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Status Cards Grid
        grid = QGridLayout()
        grid.setSpacing(14)

        self.card_daemon = StatusCard("TOR DAEMON STATUS", "Probing...", "Kernel systemd unit", "PROBING", "WARN")
        grid.addWidget(self.card_daemon, 0, 0)

        self.card_version = StatusCard("TOR CORE ENGINE", "Probing...", "Version & capabilities", "PROBING", "WARN")
        grid.addWidget(self.card_version, 0, 1)

        self.card_circuits = StatusCard("ACTIVE TOR CIRCUITS", "Probing...", "Established relay paths", "PROBING", "WARN")
        grid.addWidget(self.card_circuits, 1, 0)

        self.card_decoy = StatusCard("DECOY COVER TRAFFIC", "Inactive", "Synthetic HTTP packet bursts", "STOPPED", "WARN")
        grid.addWidget(self.card_decoy, 1, 1)

        layout.addLayout(grid)

        # Action Buttons Row
        action_bar = QHBoxLayout()
        self.newnym_btn = QPushButton("⚡ REQUEST NEW TOR IDENTITY (NEWNYM)")
        self.newnym_btn.setObjectName("AccentButton")
        self.newnym_btn.clicked.connect(self.on_newnym)
        action_bar.addWidget(self.newnym_btn)

        self.decoy_btn = QPushButton("📡 START COVER TRAFFIC GENERATOR")
        self.decoy_btn.setObjectName("CyanButton")
        self.decoy_btn.clicked.connect(self.on_toggle_decoy)
        action_bar.addWidget(self.decoy_btn)

        action_bar.addStretch()
        layout.addLayout(action_bar)

        # Active Circuits Matrix Frame
        circ_frame = QFrame()
        circ_frame.setObjectName("Card")
        c_layout = QVBoxLayout(circ_frame)
        c_layout.setContentsMargins(16, 16, 16, 16)
        c_layout.setSpacing(12)

        c_title = QLabel("ESTABLISHED TOR CIRCUITS & RELAY HOPS:")
        c_title.setObjectName("CardTitle")
        c_layout.addWidget(c_title)

        self.circ_table = QTableWidget()
        self.circ_table.setColumnCount(7)
        self.circ_table.setHorizontalHeaderLabels([
            "CIRCUIT ID", "STATUS", "GUARD RELAY", "MIDDLE RELAY", "EXIT NODE", "HOPS", "PURPOSE"
        ])
        self.circ_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.circ_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.circ_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.circ_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.circ_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.circ_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.circ_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.circ_table.setStyleSheet("""
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
        c_layout.addWidget(self.circ_table)

        layout.addWidget(circ_frame)

        # Live Decoy Activity Log Box
        decoy_frame = QFrame()
        decoy_frame.setObjectName("Card")
        d_layout = QVBoxLayout(decoy_frame)
        d_layout.setContentsMargins(16, 14, 16, 14)
        d_layout.setSpacing(10)

        d_title = QLabel("LIVE DECOY PACKET STREAM & TIMING DISRUPTION LOG:")
        d_title.setObjectName("CardTitle")
        d_layout.addWidget(d_title)

        self.decoy_log = QTextEdit()
        self.decoy_log.setReadOnly(True)
        self.decoy_log.setMaximumHeight(120)
        self.decoy_log.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d11;
                color: #00ff66;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #1a1a24;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        self.decoy_log.setPlainText("[SYSTEM] Decoy stream engine initialized. Ready to disrupt ISP packet correlation.\n")
        d_layout.addWidget(self.decoy_log)

        layout.addWidget(decoy_frame)

        self.run_tor_probe()

    def run_tor_probe(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("PROBING...")
        self.worker = TorProbeWorker()
        self.worker.finished_info.connect(self.on_tor_probe_finished)
        self.worker.start()

    def on_tor_probe_finished(self, info: dict):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("REFRESH CIRCUITS")

        is_running = info.get("running", False)
        ver = info.get("version", "N/A")
        circuits = info.get("circuits", [])

        if is_running:
            self.card_daemon.set_value("ACTIVE / ONLINE")
            self.card_daemon.set_pill("RUNNING", "SECURE")
            self.card_daemon.subtitle_label.setText("Tor daemon active and handling socks5")
        else:
            self.card_daemon.set_value("OFFLINE")
            self.card_daemon.set_pill("STOPPED", "WARN")
            self.card_daemon.subtitle_label.setText("Tor daemon service is not active")

        self.card_version.set_value(ver)
        self.card_version.set_pill("AUTHENTICATED", "SECURE")

        self.card_circuits.set_value(f"{len(circuits)} Established")
        self.card_circuits.subtitle_label.setText("Encrypted 3-hop onion routing paths")
        self.card_circuits.set_pill(f"{len(circuits)} CIRCUITS", "SECURE" if len(circuits) > 0 else "WARN")

        # Populate table
        self.circ_table.setRowCount(len(circuits))
        for row, c in enumerate(circuits):
            self.circ_table.setItem(row, 0, QTableWidgetItem(f"#{c.get('id', '')}"))

            st_item = QTableWidgetItem(c.get("status", "BUILT"))
            st_item.setForeground(Qt.GlobalColor.green if c.get("status") == "BUILT" else Qt.GlobalColor.yellow)
            self.circ_table.setItem(row, 1, st_item)

            self.circ_table.setItem(row, 2, QTableWidgetItem(c.get("guard", "---")))
            self.circ_table.setItem(row, 3, QTableWidgetItem(c.get("middle", "---")))

            exit_item = QTableWidgetItem(c.get("exit", "---"))
            exit_item.setForeground(Qt.GlobalColor.cyan)
            self.circ_table.setItem(row, 4, exit_item)

            self.circ_table.setItem(row, 5, QTableWidgetItem(f"{c.get('hops_count', '3')} Hops"))
            self.circ_table.setItem(row, 6, QTableWidgetItem(c.get("purpose", "GENERAL")))

        if len(circuits) == 0 and is_running:
            self.circ_table.setRowCount(1)
            self.circ_table.setItem(0, 0, QTableWidgetItem("-"))
            self.circ_table.setItem(0, 1, QTableWidgetItem("IDLE"))
            self.circ_table.setItem(0, 2, QTableWidgetItem("Awaiting onion traffic to construct circuits..."))
            for col in range(3, 7):
                self.circ_table.setItem(0, col, QTableWidgetItem("-"))

    def on_newnym(self):
        ok, res = TorController.signal_new_identity()
        if ok:
            self.card_circuits.set_value("Rebuilding...")
            self.card_circuits.set_pill("NEWNYM OK", "SECURE")
            self.log_decoy_event("Tor Control", 0, 0, "SIGNAL NEWNYM dispatched: All circuits renewing")
        else:
            self.card_circuits.set_value("Auth Error")
            self.card_circuits.set_pill("FAILED", "DANGER")
        self.run_tor_probe()

    def on_toggle_decoy(self):
        if not self.decoy_engine or not self.decoy_engine.running:
            self.decoy_engine = DecoyTrafficGenerator(log_callback=self.log_decoy_event)
            self.decoy_engine.start_generator()
            self.card_decoy.set_value("ACTIVE")
            self.card_decoy.set_pill("BURSTING", "SECURE")
            self.decoy_btn.setText("⏹️ STOP COVER TRAFFIC")
            self.decoy_btn.setStyleSheet("border-color: #ffaa00; color: #ffaa00;")
        else:
            self.decoy_engine.stop_generator()
            self.card_decoy.set_value("Inactive")
            self.card_decoy.set_pill("STOPPED", "WARN")
            self.decoy_btn.setText("📡 START COVER TRAFFIC GENERATOR")
            self.decoy_btn.setStyleSheet("")

    def log_decoy_event(self, target: str, size: int, latency: float, status: str):
        now = QDateTime.currentDateTime().toString("hh:mm:ss")
        line = f"[{now}] BURST -> {target} | {size} bytes | {latency}ms | {status}\n"
        self.decoy_log.append(line)

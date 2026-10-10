from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from cyberbreak.core.kernel_hardening import KernelHardening
from cyberbreak.core.executor import run_privileged, log

class HardeningPage(QWidget):
    """
    Kernel sysctl parameters and AppArmor enforcement matrix.
    Engineered by lilami only.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("KERNEL HARDENING & APPARMOR ENFORCER // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Enforce Kicksecure kernel parameters, YAMA ptrace lockdown, and AppArmor profiles")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.apply_btn = QPushButton("ENFORCE ALL SYSCTL")
        self.apply_btn.setObjectName("AccentButton")
        self.apply_btn.clicked.connect(self.on_apply_sysctl)
        header.addWidget(self.apply_btn)

        layout.addLayout(header)

        # AppArmor Card Frame
        aa_frame = QFrame()
        aa_frame.setObjectName("Card")
        aa_layout = QHBoxLayout(aa_frame)
        aa_layout.setContentsMargins(18, 18, 18, 18)
        aa_layout.setSpacing(14)

        aa_info = QVBoxLayout()
        aa_title = QLabel("APPARMOR MANDATORY ACCESS CONTROL")
        aa_title.setObjectName("CardTitle")
        self.aa_status_label = QLabel("Status: Probing active profiles...")
        self.aa_status_label.setObjectName("HeaderSubtitle")
        aa_info.addWidget(aa_title)
        aa_info.addWidget(self.aa_status_label)
        aa_layout.addLayout(aa_info)

        aa_layout.addStretch()

        enforce_aa_btn = QPushButton("ENFORCE ALL APPARMOR PROFILES")
        enforce_aa_btn.clicked.connect(self.on_enforce_aa)
        aa_layout.addWidget(enforce_aa_btn)

        layout.addWidget(aa_frame)

        # Sysctl Table Frame
        table_frame = QFrame()
        table_frame.setObjectName("Card")
        t_layout = QVBoxLayout(table_frame)
        t_layout.setContentsMargins(16, 16, 16, 16)
        t_layout.setSpacing(10)

        t_title = QLabel("KERNEL SYSCTL AUDIT & INDIVIDUAL PARAMETER CONTROLS:")
        t_title.setObjectName("CardTitle")
        t_layout.addWidget(t_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["PARAMETER", "CURRENT", "TARGET", "STATUS", "ACTION"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("""
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
        t_layout.addWidget(self.table)

        layout.addWidget(table_frame)

        self.refresh_matrix()

    def refresh_matrix(self):
        data = KernelHardening.audit_sysctl()
        self.table.setRowCount(len(data))
        for row, (key, info) in enumerate(data.items()):
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(info["current"]))
            self.table.setItem(row, 2, QTableWidgetItem(info["target"]))

            status_item = QTableWidgetItem(info["status"])
            if info["status"] == "SECURE":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 3, status_item)

            # Per-row enforce button
            btn = QPushButton("ENFORCE")
            btn.setStyleSheet("background-color: #00ff66; color: #000; font-size: 10px; font-weight: 700; padding: 4px;")
            param_key = key
            btn.clicked.connect(lambda checked, pk=param_key: self.on_enforce_single_sysctl(pk))
            self.table.setCellWidget(row, 4, btn)

        aa = KernelHardening.get_apparmor_status()
        self.aa_status_label.setText(aa["raw"][:120])

    def on_enforce_single_sysctl(self, key: str):
        target = KernelHardening.HARDENED_SYSCTL.get(key, "1")
        log(f"Enforcing single kernel parameter: {key}={target}", "KERN")
        KernelHardening.apply_sysctl_hardening()
        self.refresh_matrix()

    def on_apply_sysctl(self):
        KernelHardening.apply_sysctl_hardening()
        self.refresh_matrix()

    def on_enforce_aa(self):
        KernelHardening.enforce_all_apparmor()
        self.refresh_matrix()

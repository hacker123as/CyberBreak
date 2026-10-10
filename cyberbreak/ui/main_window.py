import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from cyberbreak.ui.styles import MAIN_STYLESHEET
from cyberbreak.ui.pages.dashboard_page import DashboardPage
from cyberbreak.ui.pages.leak_page import LeakPage
from cyberbreak.ui.pages.spoofer_page import SpooferPage
from cyberbreak.ui.pages.tor_cover_page import TorCoverPage
from cyberbreak.ui.pages.firewall_page import FirewallPage
from cyberbreak.ui.pages.usbguard_page import USBGuardPage
from cyberbreak.ui.pages.hardening_page import HardeningPage
from cyberbreak.ui.pages.metadata_page import MetadataPage
from cyberbreak.ui.pages.panic_page import PanicPage
from cyberbreak.ui.pages.desktop_page import DesktopPage
from cyberbreak.ui.pages.terminal_page import TerminalPage
from cyberbreak.core.clipboard_guard import ClipboardGuard

class MainWindow(QMainWindow):
    """CyberBreak Main Application Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberBreak - Hardened Security & Anti-Forensics Fortress")
        self.resize(1180, 760)
        self.setMinimumSize(1000, 650)

        # Apply dark modern stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        # Arm background clipboard memory guard (30-sec scrub)
        self.clipboard_guard = ClipboardGuard(timeout_seconds=30)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Left Sidebar Navigation
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("SidebarFrame")
        sidebar_frame.setFixedWidth(230)
        sidebar_frame.setStyleSheet("background-color: #161619; border-right: 1px solid #222227;")
        sb_layout = QVBoxLayout(sidebar_frame)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Branding Header
        brand_box = QFrame()
        brand_box.setStyleSheet("padding: 20px 16px 14px 16px; border-bottom: 1px solid #202025;")
        b_layout = QVBoxLayout(brand_box)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(4)

        brand_title = QLabel("CYBERBREAK")
        brand_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #00ff66; letter-spacing: 1px;")
        b_layout.addWidget(brand_title)

        brand_sub = QLabel("KICKSECURE FORTRESS")
        brand_sub.setStyleSheet("font-size: 10px; font-weight: 700; color: #70707c; letter-spacing: 1.5px;")
        b_layout.addWidget(brand_sub)

        sb_layout.addWidget(brand_box)

        # Sidebar List Widget
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("Sidebar")
        self.nav_list.setIconSize(QSize(18, 18))

        nav_items = [
            "Dashboard",
            "Leak Detector",
            "Hardware Spoofer",
            "Tor & Decoy Traffic",
            "Firewall & Profiles",
            "BadUSB & Hardware",
            "Kernel Hardening",
            "Metadata & Shredder",
            "Emergency Defense",
            "Desktop Integration",
            "Audit Terminal"
        ]

        for item_text in nav_items:
            list_item = QListWidgetItem(item_text)
            self.nav_list.addItem(list_item)

        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        sb_layout.addWidget(self.nav_list)

        # Sidebar Footer
        footer = QFrame()
        footer.setStyleSheet("padding: 12px 16px; border-top: 1px solid #202025;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(0, 0, 0, 0)
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #00ff66; font-size: 12px;")
        f_layout.addWidget(status_dot)
        status_txt = QLabel("System Guard Active")
        status_txt.setStyleSheet("color: #8c8c96; font-size: 11px; font-weight: 600;")
        f_layout.addWidget(status_txt)
        f_layout.addStretch()
        sb_layout.addWidget(footer)

        root_layout.addWidget(sidebar_frame)

        # Main Stacked Pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #121214;")

        # Instantiate all modular pages
        self.pages = [
            DashboardPage(),
            LeakPage(),
            SpooferPage(),
            TorCoverPage(),
            FirewallPage(),
            USBGuardPage(),
            HardeningPage(),
            MetadataPage(),
            PanicPage(),
            DesktopPage(),
            TerminalPage()
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        root_layout.addWidget(self.stack)

        # Select first tab by default
        self.nav_list.setCurrentRow(0)

    def on_nav_changed(self, row: int):
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)

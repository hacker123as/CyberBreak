from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from cyberbreak.core.desktop_integrator import DesktopIntegrator
from cyberbreak.ui.widgets.status_card import StatusCard

class DesktopPage(QWidget):
    """Linux FreeDesktop launcher and system application grid manager."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("NATIVE DESKTOP & APP GRID INTEGRATION // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Deploy CyberBreak into Linux application menus, desktop launchers, and system autostart")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        layout.addLayout(header)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.desk_card = StatusCard("DESKTOP LAUNCHER", "Checking...", "~/Desktop/cyberbreak.desktop", "", "WARN")
        grid.addWidget(self.desk_card, 0, 0)

        self.grid_card = StatusCard("APPLICATION GRID", "Checking...", "/usr/share/applications/ entry", "", "WARN")
        grid.addWidget(self.grid_card, 0, 1)

        self.auto_card = StatusCard("SYSTEM AUTOSTART", "Checking...", "~/.config/autostart/ entry", "", "WARN")
        grid.addWidget(self.auto_card, 1, 0)

        layout.addLayout(grid)

        # Management Frame
        frame = QFrame()
        frame.setObjectName("Card")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(18, 18, 18, 18)
        f_layout.setSpacing(14)

        f_title = QLabel("DESKTOP INTEGRATION ACTIONS:")
        f_title.setObjectName("CardTitle")
        f_layout.addWidget(f_title)

        # Add to Desktop
        d_row = QHBoxLayout()
        d_info = QVBoxLayout()
        d_lbl = QLabel("Place Shortcut on User Desktop")
        d_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        d_sub = QLabel("Generates executable, trusted ~/Desktop/cyberbreak.desktop with native icon.")
        d_sub.setObjectName("HeaderSubtitle")
        d_info.addWidget(d_lbl)
        d_info.addWidget(d_sub)
        d_row.addLayout(d_info)
        d_row.addStretch()

        d_btn = QPushButton("ADD TO DESKTOP")
        d_btn.setObjectName("AccentButton")
        d_btn.clicked.connect(self.on_add_desktop)
        d_row.addWidget(d_btn)
        f_layout.addLayout(d_row)

        f_layout.addWidget(self.create_divider())

        # Add to App Grid
        g_row = QHBoxLayout()
        g_info = QVBoxLayout()
        g_lbl = QLabel("Register into System Application Grid")
        g_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        g_sub = QLabel("Installs into Whisker Menu, Kicksecure Application Finder, GNOME Dash, and KDE Kickoff.")
        g_sub.setObjectName("HeaderSubtitle")
        g_info.addWidget(g_lbl)
        g_info.addWidget(g_sub)
        g_row.addLayout(g_info)
        g_row.addStretch()

        g_btn = QPushButton("REGISTER IN APP GRID")
        g_btn.clicked.connect(self.on_add_grid)
        g_row.addWidget(g_btn)
        f_layout.addLayout(g_row)

        f_layout.addWidget(self.create_divider())

        # Toggle Autostart
        a_row = QHBoxLayout()
        a_info = QVBoxLayout()
        a_lbl = QLabel("System Boot Autostart")
        a_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        a_sub = QLabel("Automatically launch CyberBreak protection suite upon user desktop login.")
        a_sub.setObjectName("HeaderSubtitle")
        a_info.addWidget(a_lbl)
        a_info.addWidget(a_sub)
        a_row.addLayout(a_info)
        a_row.addStretch()

        self.auto_btn = QPushButton("ENABLE AUTOSTART")
        self.auto_btn.clicked.connect(self.on_toggle_autostart)
        a_row.addWidget(self.auto_btn)
        f_layout.addLayout(a_row)

        layout.addWidget(frame)

        # Maintenance Note Frame
        maint_frame = QFrame()
        maint_frame.setObjectName("Card")
        m_layout = QVBoxLayout(maint_frame)
        m_layout.setContentsMargins(18, 18, 18, 18)
        m_layout.setSpacing(10)

        m_title = QLabel("ADMINISTRATIVE MAINTENANCE (SYSMAINT):")
        m_title.setObjectName("CardTitle")
        m_title.setStyleSheet("color: #00ff66; font-weight: 700;")
        m_layout.addWidget(m_title)

        m_desc = QLabel(
            "In accordance with Kicksecure's security architecture, system-wide packages, kernel policies, "
            "and helper authorizations are maintained through the administrative 'sysmaint' account.\n"
            "To perform system updates, reconfigure group authorizations, or reinstall security policies, run:\n"
            "  $ sudo bash /opt/cyberbreak/scripts/install.sh"
        )
        m_desc.setObjectName("HeaderSubtitle")
        m_desc.setStyleSheet("color: #a0a0ab; line-height: 1.4;")
        m_layout.addWidget(m_desc)

        layout.addWidget(maint_frame)
        layout.addStretch()

        self.refresh_status()

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #242429;")
        return line

    def refresh_status(self):
        st = DesktopIntegrator.get_status()
        if st["on_desktop"]:
            self.desk_card.set_value("Installed")
            self.desk_card.set_pill("ACTIVE", "SECURE")
        else:
            self.desk_card.set_value("Not Found")
            self.desk_card.set_pill("MISSING", "WARN")

        if st["in_app_grid"]:
            self.grid_card.set_value("Registered")
            self.grid_card.set_pill("ACTIVE", "SECURE")
        else:
            self.grid_card.set_value("Not Found")
            self.grid_card.set_pill("MISSING", "WARN")

        if st["autostart"]:
            self.auto_card.set_value("Enabled")
            self.auto_card.set_pill("ENABLED", "SECURE")
            self.auto_btn.setText("DISABLE AUTOSTART")
        else:
            self.auto_card.set_value("Disabled")
            self.auto_card.set_pill("OFF", "WARN")
            self.auto_btn.setText("ENABLE AUTOSTART")

    def on_add_desktop(self):
        DesktopIntegrator.install_to_desktop()
        self.refresh_status()

    def on_add_grid(self):
        DesktopIntegrator.install_to_app_grid()
        self.refresh_status()

    def on_toggle_autostart(self):
        st = DesktopIntegrator.get_status()
        DesktopIntegrator.toggle_autostart(not st["autostart"])
        self.refresh_status()

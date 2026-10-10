from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QCheckBox, QComboBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.settings_manager import SettingsManager
from cyberbreak.core.updater import Updater
from cyberbreak.ui.widgets.status_card import StatusCard

class UpdateCheckWorker(QThread):
    finished_signal = pyqtSignal(dict)

    def run(self):
        info = Updater.check_for_updates()
        self.finished_signal.emit(info)

class SettingsPage(QWidget):
    """
    Fortress Configuration, Defensive Automation Switches, and Live Update Engine.
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
        title = QLabel("CONTROL CENTER & SETTINGS // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Defensive automation toggles, persistence preferences, and live Git updater")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.save_btn = QPushButton("💾 SAVE PREFERENCES")
        self.save_btn.setObjectName("AccentButton")
        self.save_btn.clicked.connect(self.save_settings)
        header.addWidget(self.save_btn)

        layout.addLayout(header)

        # Top Status Cards
        grid = QGridLayout()
        grid.setSpacing(14)

        self.card_ver = StatusCard("VERSION STATUS", "v3.1.0", "Release channel: main", "STABLE", "SECURE")
        grid.addWidget(self.card_ver, 0, 0)

        self.card_commit = StatusCard("LOCAL COMMIT", Updater.get_local_commit(), "Git build hash", "", "WARN")
        grid.addWidget(self.card_commit, 0, 1)

        self.card_author = StatusCard("AUTHOR & ARCHITECT", "lilami only", "Exclusive architect", "LILAMI ONLY", "SECURE")
        grid.addWidget(self.card_author, 0, 2)

        layout.addLayout(grid)

        # Section 1: Defensive Automation Toggles
        toggles_frame = QFrame()
        toggles_frame.setObjectName("Card")
        t_layout = QVBoxLayout(toggles_frame)
        t_layout.setContentsMargins(18, 16, 18, 16)
        t_layout.setSpacing(12)

        t_title = QLabel("DEFENSIVE AUTOMATION SWITCHES:")
        t_title.setObjectName("CardTitle")
        t_layout.addWidget(t_title)

        t_grid = QGridLayout()
        t_grid.setSpacing(14)

        self.chk_killswitch = QCheckBox("Auto-Arm VPN Killswitch on System Boot")
        self.chk_mac = QCheckBox("Auto-Randomize Hardware MAC on Interface Connect")
        self.chk_leak_isolate = QCheckBox("Emergency Auto-Isolate on IP/DNS Leak Reveal")
        self.chk_badusb = QCheckBox("Strict BadUSB HID Injection Lockdown on Idle")
        self.chk_port_lockdown = QCheckBox("Auto-Lockdown Listening Ports on System Boot")
        self.chk_webcam = QCheckBox("Disable Webcam Kernel Module (uvcvideo) by Default")
        self.chk_sound = QCheckBox("Play High-Voltage Audio Alerts on Threat Detection")
        self.chk_auto_update = QCheckBox("Check for CyberBreak Updates on Launch")

        for chk in (self.chk_killswitch, self.chk_mac, self.chk_leak_isolate,
                    self.chk_badusb, self.chk_port_lockdown, self.chk_webcam,
                    self.chk_sound, self.chk_auto_update):
            chk.setStyleSheet("color: #e0e4f2; font-size: 13px; font-weight: 500;")

        t_grid.addWidget(self.chk_killswitch, 0, 0)
        t_grid.addWidget(self.chk_mac, 0, 1)
        t_grid.addWidget(self.chk_leak_isolate, 1, 0)
        t_grid.addWidget(self.chk_badusb, 1, 1)
        t_grid.addWidget(self.chk_port_lockdown, 2, 0)
        t_grid.addWidget(self.chk_webcam, 2, 1)
        t_grid.addWidget(self.chk_sound, 3, 0)
        t_grid.addWidget(self.chk_auto_update, 3, 1)

        t_layout.addLayout(t_grid)

        # Clipboard scrub interval row
        clip_row = QHBoxLayout()
        clip_row.addWidget(QLabel("Clipboard Memory Scrub Interval:"))
        self.clip_combo = QComboBox()
        self.clip_combo.addItem("15 Seconds", 15)
        self.clip_combo.addItem("30 Seconds (Default)", 30)
        self.clip_combo.addItem("60 Seconds", 60)
        self.clip_combo.addItem("120 Seconds", 120)
        clip_row.addWidget(self.clip_combo)
        clip_row.addStretch()
        t_layout.addLayout(clip_row)

        layout.addWidget(toggles_frame)

        # Section 2: Updater & Synchronization Frame
        update_frame = QFrame()
        update_frame.setObjectName("Card")
        u_layout = QVBoxLayout(update_frame)
        u_layout.setContentsMargins(18, 16, 18, 16)
        u_layout.setSpacing(12)

        u_title = QLabel("CYBERBREAK REPOSITORY SYNCHRONIZATION:")
        u_title.setObjectName("CardTitle")
        u_layout.addWidget(u_title)

        u_desc = QLabel(
            "Directly synchronizes CyberBreak with the official GitHub repository "
            "(https://github.com/hacker123as/CyberBreak.git). Pulls latest hardening signatures, "
            "rules, and privileged helper updates."
        )
        u_desc.setObjectName("HeaderSubtitle")
        u_layout.addWidget(u_desc)

        btn_row = QHBoxLayout()
        self.check_up_btn = QPushButton("🔍 CHECK FOR UPDATES")
        self.check_up_btn.setObjectName("CyanButton")
        self.check_up_btn.clicked.connect(self.check_updates)
        btn_row.addWidget(self.check_up_btn)

        self.apply_up_btn = QPushButton("⚡ APPLY LATEST UPDATE")
        self.apply_up_btn.setObjectName("AccentButton")
        self.apply_up_btn.clicked.connect(self.install_update)
        btn_row.addWidget(self.apply_up_btn)

        btn_row.addStretch()
        u_layout.addLayout(btn_row)

        self.up_log = QTextEdit()
        self.up_log.setReadOnly(True)
        self.up_log.setStyleSheet(
            "background-color: #0e0e13; color: #00ff66; font-family: monospace; "
            "font-size: 11px; border: 1px solid #1f1f28; border-radius: 6px; padding: 6px;"
        )
        self.up_log.setFixedHeight(75)
        u_layout.addWidget(self.up_log)

        layout.addWidget(update_frame)

        self.load_settings()

    def load_settings(self):
        cfg = SettingsManager.load()
        self.chk_killswitch.setChecked(bool(cfg.get("auto_killswitch_boot", False)))
        self.chk_mac.setChecked(bool(cfg.get("auto_randomize_mac", False)))
        self.chk_leak_isolate.setChecked(bool(cfg.get("auto_isolate_on_leak", False)))
        self.chk_badusb.setChecked(bool(cfg.get("strict_badusb", False)))
        self.chk_port_lockdown.setChecked(bool(cfg.get("auto_port_lockdown_boot", False)))
        self.chk_webcam.setChecked(bool(cfg.get("disable_webcam_boot", False)))
        self.chk_sound.setChecked(bool(cfg.get("sound_alerts", True)))
        self.chk_auto_update.setChecked(bool(cfg.get("auto_check_updates", True)))

        wipe_sec = cfg.get("clipboard_wipe_seconds", 30)
        idx = self.clip_combo.findData(wipe_sec)
        if idx >= 0:
            self.clip_combo.setCurrentIndex(idx)

    def save_settings(self):
        cfg = {
            "auto_killswitch_boot": self.chk_killswitch.isChecked(),
            "auto_randomize_mac": self.chk_mac.isChecked(),
            "auto_isolate_on_leak": self.chk_leak_isolate.isChecked(),
            "strict_badusb": self.chk_badusb.isChecked(),
            "auto_port_lockdown_boot": self.chk_port_lockdown.isChecked(),
            "disable_webcam_boot": self.chk_webcam.isChecked(),
            "sound_alerts": self.chk_sound.isChecked(),
            "auto_check_updates": self.chk_auto_update.isChecked(),
            "clipboard_wipe_seconds": self.clip_combo.currentData(),
            "created_by": "lilami only"
        }
        SettingsManager.save(cfg)
        QMessageBox.information(self, "Settings Saved", "Preferences and defensive automation rules saved successfully!")

    def check_updates(self):
        self.check_up_btn.setEnabled(False)
        self.check_up_btn.setText("CHECKING...")
        self.up_log.append("[UPDATER] Probing remote GitHub API for latest commits...")
        self.worker = UpdateCheckWorker()
        self.worker.finished_signal.connect(self._on_update_checked)
        self.worker.start()

    def _on_update_checked(self, info: dict):
        self.check_up_btn.setEnabled(True)
        self.check_up_btn.setText("🔍 CHECK FOR UPDATES")
        local_h = info.get("local_hash", "")
        remote_h = info.get("remote_hash", "")
        status = info.get("status", "")

        self.up_log.append(f"[UPDATER] Local: {local_h} | Remote: {remote_h} | Status: {status}")
        if info.get("message"):
            self.up_log.append(f"[UPDATER] Latest Commit: {info['message']} ({info.get('date', '')})")

        if info.get("update_available"):
            self.card_ver.set_pill("UPDATE READY", "DANGER")
            self.card_ver.set_value(f"Remote {remote_h}")
            QMessageBox.information(
                self, "Update Available",
                f"A new CyberBreak update is ready!\n\n"
                f"Remote Commit: {remote_h}\nMessage: {info.get('message')}\nDate: {info.get('date')}\n\n"
                f"Click 'APPLY LATEST UPDATE' to install."
            )
        else:
            self.card_ver.set_pill("UP TO DATE", "SECURE")
            self.card_ver.set_value(local_h)

    def install_update(self):
        ok, msg = Updater.apply_update()
        self.up_log.append(f"[UPDATER] Result: {msg}")
        if ok:
            QMessageBox.information(self, "Update Complete", msg)
        else:
            QMessageBox.information(self, "System Update Instructions", msg)

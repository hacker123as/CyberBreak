from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QComboBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.settings_manager import SettingsManager
from cyberbreak.core.updater import Updater
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.ui.widgets.glass import GlassFrame, ToggleSwitch, icon


class UpdateCheckWorker(QThread):
    finished_signal = pyqtSignal(dict)

    def run(self):
        self.finished_signal.emit(Updater.check_for_updates())


class SettingsPage(QWidget):
    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(8)
        title = QLabel("Settings")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Tune protection preferences and keep CyberBreak up to date.")
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        self.save_btn = QPushButton("Save preferences")
        self.save_btn.setIcon(icon("check", "#ffffff"))
        self.save_btn.setObjectName("AccentButton")
        self.save_btn.clicked.connect(self.save_settings)
        header.addWidget(self.save_btn, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.card_ver = StatusCard("Version", "v3.1.0", "Main release channel", "Stable", "SECURE")
        self.card_commit = StatusCard("Local build", Updater.get_local_commit(), "Git revision", "", "WARN")
        self.card_author = StatusCard("Maintainer", "lilami", "CyberBreak project", "", "SECURE")
        grid.addWidget(self.card_ver, 0, 0)
        grid.addWidget(self.card_commit, 0, 1)
        grid.addWidget(self.card_author, 0, 2)
        layout.addLayout(grid)

        automation_note = QLabel("Automation choices are stored as preferences. Automatic enforcement is not active in this release.")
        automation_note.setObjectName("HeaderSubtitle")
        automation_note.setWordWrap(True)
        layout.addWidget(automation_note)
        self.preferences_grid = QGridLayout()
        preferences = self.preferences_grid
        preferences.setSpacing(16)
        network, network_layout = self._section("Network & device protection")
        self.chk_killswitch = self._switch_row(network_layout, "VPN killswitch", "Arm traffic isolation when the system starts.")
        self.chk_mac = self._switch_row(network_layout, "Randomize MAC address", "Use a new hardware address when an interface connects.")
        self.chk_leak_isolate = self._switch_row(network_layout, "Isolate on a leak", "Disconnect automatically when an IP or DNS leak is detected.")
        self.chk_badusb = self._switch_row(network_layout, "Strict USB protection", "Lock HID injection access while the workstation is idle.")
        network_layout.addStretch()
        self.network_preferences = network
        preferences.addWidget(network, 0, 0)

        system, system_layout = self._section("System preferences")
        self.chk_port_lockdown = self._switch_row(system_layout, "Lock listening ports", "Apply port protection when the system starts.")
        self.chk_webcam = self._switch_row(system_layout, "Disable camera", "Keep the uvcvideo driver disabled at startup.")
        self.chk_sound = self._switch_row(system_layout, "Audio alerts", "Play a sound when a threat is detected.")
        self.chk_auto_update = self._switch_row(system_layout, "Check for updates", "Look for a new release when CyberBreak launches.")
        system_layout.addStretch()
        self.system_preferences = system
        preferences.addWidget(system, 1, 0)
        preferences.setColumnStretch(0, 1)
        preferences.setColumnStretch(1, 0)
        layout.addLayout(preferences)

        clipboard, clipboard_layout = self._section("Clipboard privacy")
        clipboard_row = QHBoxLayout()
        clipboard_info = QVBoxLayout()
        clipboard_info.setSpacing(6)
        clipboard_title = QLabel("Clear copied text automatically")
        clipboard_title.setObjectName("CardTitle")
        clipboard_subtitle = QLabel("Choose how long clipboard contents stay available.")
        clipboard_subtitle.setObjectName("HeaderSubtitle")
        clipboard_subtitle.setWordWrap(True)
        clipboard_info.addWidget(clipboard_title)
        clipboard_info.addWidget(clipboard_subtitle)
        clipboard_row.addLayout(clipboard_info, 1)
        self.clip_combo = QComboBox()
        self.clip_combo.addItem("15 seconds", 15)
        self.clip_combo.addItem("30 seconds", 30)
        self.clip_combo.addItem("1 minute", 60)
        self.clip_combo.addItem("2 minutes", 120)
        self.clip_combo.setMinimumWidth(170)
        clipboard_row.addWidget(self.clip_combo)
        clipboard_layout.addLayout(clipboard_row)
        layout.addWidget(clipboard)

        update_frame, update_layout = self._section("Software updates")
        update_description = QLabel("Check the official repository for new releases, rules, and helper updates.")
        update_description.setObjectName("HeaderSubtitle")
        update_description.setWordWrap(True)
        update_layout.addWidget(update_description)
        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        self.check_up_btn = QPushButton("Check for updates")
        self.check_up_btn.setIcon(icon("refresh"))
        self.check_up_btn.setObjectName("OutlineButton")
        self.check_up_btn.clicked.connect(self.check_updates)
        buttons.addWidget(self.check_up_btn)
        self.apply_up_btn = QPushButton("Apply update")
        self.apply_up_btn.setIcon(icon("arrow", "#ffffff"))
        self.apply_up_btn.setObjectName("AccentButton")
        self.apply_up_btn.clicked.connect(self.install_update)
        buttons.addWidget(self.apply_up_btn)
        buttons.addStretch()
        update_layout.addLayout(buttons)
        self.up_log = QTextEdit()
        self.up_log.setObjectName("Terminal")
        self.up_log.setReadOnly(True)
        self.up_log.setMinimumHeight(100)
        self.up_log.setMaximumHeight(150)
        update_layout.addWidget(self.up_log)
        layout.addWidget(update_frame)
        self._preferences_stacked = True
        self.load_settings()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "preferences_grid"):
            return
        stacked = self.width() < 840
        if stacked == self._preferences_stacked:
            return
        self.preferences_grid.removeWidget(self.system_preferences)
        self.preferences_grid.addWidget(self.system_preferences, 1 if stacked else 0, 0 if stacked else 1)
        self.preferences_grid.setColumnStretch(1, 0 if stacked else 1)
        self._preferences_stacked = stacked

    def _section(self, title):
        frame = GlassFrame()
        frame.setObjectName("GlassCard")
        section = QVBoxLayout(frame)
        section.setContentsMargins(22, 22, 22, 22)
        section.setSpacing(18)
        label = QLabel(title)
        label.setObjectName("CardTitle")
        section.addWidget(label)
        return frame, section

    def _switch_row(self, section, title, description):
        row = QHBoxLayout()
        row.setSpacing(16)
        details = QVBoxLayout()
        details.setSpacing(5)
        label = QLabel(title)
        label.setObjectName("SettingTitle")
        description_label = QLabel(description)
        description_label.setObjectName("HeaderSubtitle")
        description_label.setWordWrap(True)
        details.addWidget(label)
        details.addWidget(description_label)
        row.addLayout(details, 1)
        toggle = ToggleSwitch()
        toggle.setAccessibleName(title)
        toggle.setToolTip(description)
        row.addWidget(toggle, 0, Qt.AlignmentFlag.AlignVCenter)
        section.addLayout(row)
        return toggle

    def load_settings(self):
        cfg = SettingsManager.load()
        self.chk_killswitch.setChecked(bool(cfg.get('auto_killswitch_boot', False)))
        self.chk_mac.setChecked(bool(cfg.get('auto_randomize_mac', False)))
        self.chk_leak_isolate.setChecked(bool(cfg.get('auto_isolate_on_leak', False)))
        self.chk_badusb.setChecked(bool(cfg.get('strict_badusb', False)))
        self.chk_port_lockdown.setChecked(bool(cfg.get('auto_port_lockdown_boot', False)))
        self.chk_webcam.setChecked(bool(cfg.get('disable_webcam_boot', False)))
        self.chk_sound.setChecked(bool(cfg.get('sound_alerts', True)))
        self.chk_auto_update.setChecked(bool(cfg.get('auto_check_updates', True)))
        wipe_sec = cfg.get('clipboard_wipe_seconds', 30)
        idx = self.clip_combo.findData(wipe_sec)
        if idx >= 0:
            self.clip_combo.setCurrentIndex(idx)

    def save_settings(self):
        cfg = {'auto_killswitch_boot': self.chk_killswitch.isChecked(), 'auto_randomize_mac': self.chk_mac.isChecked(), 'auto_isolate_on_leak': self.chk_leak_isolate.isChecked(), 'strict_badusb': self.chk_badusb.isChecked(), 'auto_port_lockdown_boot': self.chk_port_lockdown.isChecked(), 'disable_webcam_boot': self.chk_webcam.isChecked(), 'sound_alerts': self.chk_sound.isChecked(), 'auto_check_updates': self.chk_auto_update.isChecked(), 'clipboard_wipe_seconds': self.clip_combo.currentData(), 'created_by': 'lilami only'}
        SettingsManager.save(cfg)
        self.settings_saved.emit(cfg)
        QMessageBox.information(self, 'Settings Saved', 'Your preferences have been saved.')

    def check_updates(self):
        self.check_up_btn.setEnabled(False)
        self.check_up_btn.setText('Checking…')
        self.up_log.append('[UPDATER] Probing remote GitHub API for latest commits...')
        self.worker = UpdateCheckWorker()
        self.worker.finished_signal.connect(self._on_update_checked)
        self.worker.start()

    def _on_update_checked(self, info: dict):
        self.check_up_btn.setEnabled(True)
        self.check_up_btn.setText('Check for updates')
        local_h = info.get('local_hash', '')
        remote_h = info.get('remote_hash', '')
        status = info.get('status', '')
        self.up_log.append(f'[UPDATER] Local: {local_h} | Remote: {remote_h} | Status: {status}')
        if info.get('message'):
            self.up_log.append(f"[UPDATER] Latest Commit: {info['message']} ({info.get('date', '')})")
        if info.get('update_available'):
            self.card_ver.set_pill('UPDATE READY', 'DANGER')
            self.card_ver.set_value(f'Remote {remote_h}')
            QMessageBox.information(self, 'Update Available', f"A new CyberBreak update is ready!\n\nRemote Commit: {remote_h}\nMessage: {info.get('message')}\nDate: {info.get('date')}\n\nClick 'Apply update' to install.")
        else:
            self.card_ver.set_pill('UP TO DATE', 'SECURE')
            self.card_ver.set_value(local_h)

    def install_update(self):
        ok, msg = Updater.apply_update()
        self.up_log.append(f'[UPDATER] Result: {msg}')
        if ok:
            QMessageBox.information(self, 'Update Complete', msg)
        else:
            QMessageBox.information(self, 'System Update Instructions', msg)

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QTabWidget, QComboBox, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.usb_armory import USBArmory
from cyberbreak.ui.widgets.status_card import StatusCard

class USBActionWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, action_func, *args):
        super().__init__()
        self.action_func = action_func
        self.args = args

    def run(self):
        try:
            ok, msg = self.action_func(*self.args)
            self.finished_signal.emit(ok, msg)
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class USBArmoryPage(QWidget):
    """
    USB & Storage Swiss Army Knife: LUKS2 Encoder/Decoder,
    Windows-Unreadable Stealth Storage, ISO Burner, Formatter & OS Backup.
    Engineered by lilami.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("USB & STORAGE ARMORY // By lilami")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("LUKS2 hardware vault encoder, Windows-unreadable stealth storage, ISO burner & OS backup")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self.refresh_btn = QPushButton("🔄 REFRESH STORAGE")
        self.refresh_btn.setObjectName("OutlineButton")
        self.refresh_btn.clicked.connect(self.refresh_all)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Quick Status Cards
        grid = QGridLayout()
        grid.setSpacing(14)

        self.card_devices = StatusCard("USB STORAGE DEVICES", "0 detected", "Removable block devices", "", "WARN")
        grid.addWidget(self.card_devices, 0, 0)

        self.card_vaults = StatusCard("REGISTERED VAULTS", "0 active", "LUKS2 cipher vaults", "", "WARN")
        grid.addWidget(self.card_vaults, 0, 1)

        self.card_keystore = StatusCard("APP KEYSTORE", "Protected", "~/.config/cyberbreak/vault_keys", "", "SECURE")
        grid.addWidget(self.card_keystore, 0, 2)

        layout.addLayout(grid)

        # Tab Widget for Armory Tools
        self.tabs = QTabWidget()

        # Tab 1: LUKS2 Encoder
        self.tabs.addTab(self._create_encoder_tab(), "🔐 USB Encoder (Vault)")
        # Tab 2: LUKS2 Decoder / Manager
        self.tabs.addTab(self._create_decoder_tab(), "🔓 Vault Decoder & Unlocker")
        # Tab 3: Formatter & Sanitizer
        self.tabs.addTab(self._create_formatter_tab(), "⚡ Formatter & Sanitizer")
        # Tab 4: ISO Flasher
        self.tabs.addTab(self._create_iso_tab(), "🔥 Live ISO Burner")
        # Tab 5: OS Backup
        self.tabs.addTab(self._create_backup_tab(), "💾 OS Backup to USB")
        # Tab 6: SSD TRIM
        self.tabs.addTab(self._create_trim_tab(), "🧹 Supercharged SSD TRIM")

        layout.addWidget(self.tabs)

        # Audit Output Log
        log_frame = QFrame()
        log_frame.setObjectName("Card")
        l_layout = QVBoxLayout(log_frame)
        l_layout.setContentsMargins(14, 12, 14, 12)
        l_layout.setSpacing(6)

        l_title = QLabel("STORAGE AUDIT & OPERATION LOG:")
        l_title.setObjectName("CardTitle")
        l_layout.addWidget(l_title)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(
            "background-color: #0c0d13; color: #00ff66; border: 1px solid #202331; "
            "font-family: monospace; font-size: 11px; padding: 6px; border-radius: 6px;"
        )
        self.log_box.setFixedHeight(85)
        l_layout.addWidget(self.log_box)

        layout.addWidget(log_frame)

        self.refresh_all()

    # --- TAB BUILDERS ---

    def _create_encoder_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        info = QLabel(
            "Creates a military-grade AES-XTS-512 LUKS2 encrypted volume on the target USB.\n"
            "• Encryption keys are generated with 512-bit entropy and saved strictly inside CyberBreak's app keystore.\n"
            "• Stealth Guarantee: When plugged into Windows, Windows sees NO readable partition, file table, or OS data—"
            "it is completely unreadable and unrecognized!"
        )
        info.setStyleSheet("color: #a0a6bd; font-size: 12px; line-height: 1.4;")
        lay.addWidget(info)

        form_grid = QGridLayout()
        form_grid.setSpacing(12)

        form_grid.addWidget(QLabel("Target USB Device:"), 0, 0)
        self.enc_dev_combo = QComboBox()
        form_grid.addWidget(self.enc_dev_combo, 0, 1)

        form_grid.addWidget(QLabel("Vault Label:"), 1, 0)
        self.enc_label_input = QLineEdit("CyberVault")
        form_grid.addWidget(self.enc_label_input, 1, 1)

        lay.addLayout(form_grid)

        self.enc_btn = QPushButton("🔒 ENCODE & ENCRYPT USB DRIVE")
        self.enc_btn.setObjectName("AccentButton")
        self.enc_btn.clicked.connect(self.on_encode_click)
        lay.addWidget(self.enc_btn)

        lay.addStretch()
        return w

    def _create_decoder_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        desc = QLabel("Registered encrypted vaults managed by CyberBreak keystore. Unlock or lock with 1-click:")
        desc.setStyleSheet("color: #9ba1b5; font-size: 12px;")
        lay.addWidget(desc)

        self.vault_table = QTableWidget()
        self.vault_table.setColumnCount(5)
        self.vault_table.setHorizontalHeaderLabels(["Vault ID", "Label", "Device", "Mount Path", "Status"])
        self.vault_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vault_table.setFixedHeight(160)
        lay.addWidget(self.vault_table)

        btn_row = QHBoxLayout()
        self.unlock_btn = QPushButton("🔓 UNLOCK & MOUNT VAULT")
        self.unlock_btn.setObjectName("AccentButton")
        self.unlock_btn.clicked.connect(self.on_unlock_click)
        btn_row.addWidget(self.unlock_btn)

        self.lock_btn = QPushButton("🔒 LOCK & SECURE VAULT")
        self.lock_btn.setObjectName("PanicButton")
        self.lock_btn.clicked.connect(self.on_lock_click)
        btn_row.addWidget(self.lock_btn)

        lay.addLayout(btn_row)
        lay.addStretch()
        return w

    def _create_formatter_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        form_grid = QGridLayout()
        form_grid.setSpacing(12)

        form_grid.addWidget(QLabel("Target Block Device:"), 0, 0)
        self.fmt_dev_combo = QComboBox()
        form_grid.addWidget(self.fmt_dev_combo, 0, 1)

        form_grid.addWidget(QLabel("Filesystem Format:"), 1, 0)
        self.fmt_type_combo = QComboBox()
        self.fmt_type_combo.addItems(["ext4", "btrfs", "vfat (FAT32)", "exfat"])
        form_grid.addWidget(self.fmt_type_combo, 1, 1)

        form_grid.addWidget(QLabel("Volume Label:"), 2, 0)
        self.fmt_label_input = QLineEdit("Storage")
        form_grid.addWidget(self.fmt_label_input, 2, 1)

        lay.addLayout(form_grid)

        btn_row = QHBoxLayout()
        self.fmt_btn = QPushButton("⚡ FORMAT DRIVE")
        self.fmt_btn.setObjectName("CyanButton")
        self.fmt_btn.clicked.connect(self.on_format_click)
        btn_row.addWidget(self.fmt_btn)

        self.wipe_btn = QPushButton("☣️ DOD ZERO-WIPE PARTITION TABLE")
        self.wipe_btn.setObjectName("PanicButton")
        self.wipe_btn.clicked.connect(self.on_wipe_click)
        btn_row.addWidget(self.wipe_btn)

        lay.addLayout(btn_row)
        lay.addStretch()
        return w

    def _create_iso_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        desc = QLabel("Burn Kicksecure, Whonix, Tails, Arch, or Debian ISO directly to raw USB flash drive:")
        desc.setStyleSheet("color: #9ba1b5; font-size: 12px;")
        lay.addWidget(desc)

        iso_row = QHBoxLayout()
        self.iso_path_input = QLineEdit()
        self.iso_path_input.setPlaceholderText("/path/to/distro.iso")
        iso_row.addWidget(self.iso_path_input)

        browse_btn = QPushButton("BROWSE ISO")
        browse_btn.setObjectName("OutlineButton")
        browse_btn.clicked.connect(self.on_browse_iso)
        iso_row.addWidget(browse_btn)
        lay.addLayout(iso_row)

        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel("Target USB Device:"))
        self.iso_dev_combo = QComboBox()
        dev_row.addWidget(self.iso_dev_combo)
        lay.addLayout(dev_row)

        self.burn_btn = QPushButton("🔥 BURN RAW ISO TO USB")
        self.burn_btn.setObjectName("PanicButton")
        self.burn_btn.clicked.connect(self.on_burn_iso_click)
        lay.addWidget(self.burn_btn)

        lay.addStretch()
        return w

    def _create_backup_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        desc = QLabel("Creates a compressed snapshot archive of your system session or essential configs onto USB:")
        desc.setStyleSheet("color: #9ba1b5; font-size: 12px;")
        lay.addWidget(desc)

        bk_grid = QGridLayout()
        bk_grid.setSpacing(12)

        bk_grid.addWidget(QLabel("Mounted USB Target:"), 0, 0)
        self.bk_dest_combo = QComboBox()
        bk_grid.addWidget(self.bk_dest_combo, 0, 1)

        bk_grid.addWidget(QLabel("Backup Scope:"), 1, 0)
        self.bk_scope_combo = QComboBox()
        self.bk_scope_combo.addItem("Home Directory (~/)", "home")
        self.bk_scope_combo.addItem("Essential Configs (/etc + /usr/local/bin + ~)", "full")
        bk_grid.addWidget(self.bk_scope_combo, 1, 1)

        lay.addLayout(bk_grid)

        self.bk_btn = QPushButton("📦 CREATE INSTANT USB BACKUP")
        self.bk_btn.setObjectName("AccentButton")
        self.bk_btn.clicked.connect(self.on_backup_click)
        lay.addWidget(self.bk_btn)

        lay.addStretch()
        return w

    def _create_trim_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        desc = QLabel(
            "Supercharged SSD TRIM Engine:\n"
            "Issues fstrim discard calls across all mounted flash storage, NVMe drives, and dm-crypt LUKS mappings.\n"
            "Purges discarded blocks from SSD flash controllers to restore maximum read/write performance."
        )
        desc.setStyleSheet("color: #a4abbd; font-size: 12px; line-height: 1.5;")
        lay.addWidget(desc)

        self.trim_btn = QPushButton("🧹 RUN HIGH-VOLTAGE DRIVE TRIM")
        self.trim_btn.setObjectName("CyanButton")
        self.trim_btn.clicked.connect(self.on_trim_click)
        lay.addWidget(self.trim_btn)

        lay.addStretch()
        return w

    # --- ACTIONS & LOGIC ---

    def refresh_all(self):
        self.log_box.append("[ARMORY] Refreshing storage hardware & vault registries...")
        devices = USBArmory.list_devices()
        usb_devs = [d for d in devices if d.get("is_usb")]

        self.card_devices.set_value(f"{len(usb_devs)} USB Drives")
        if usb_devs:
            self.card_devices.set_pill("HARDWARE READY", "SECURE")
            self.card_devices.subtitle_label.setText(", ".join([d['name'] for d in usb_devs]))
        else:
            self.card_devices.set_pill("NO USB INSERTED", "WARN")
            self.card_devices.subtitle_label.setText("Connect USB drive to arm")

        # Repopulate dropdowns
        for cb in (self.enc_dev_combo, self.fmt_dev_combo, self.iso_dev_combo):
            cb.clear()
            for d in devices:
                if not d.get("is_system"):
                    cb.addItem(f"{d['path']} ({d['model']} - {d['size_gb']} GB)", d['path'])

        # Repopulate backup dest combo
        self.bk_dest_combo.clear()
        mounts = []
        user = os.getenv("USER") or "user"
        for base in (f"/media/{user}", "/media", "/mnt"):
            if os.path.exists(base):
                for sub in os.listdir(base):
                    p = os.path.join(base, sub)
                    if os.path.isdir(p):
                        mounts.append(p)
        for m in mounts:
            self.bk_dest_combo.addItem(m, m)

        # Repopulate Vault table
        vaults = USBArmory.load_registry()
        self.card_vaults.set_value(f"{len(vaults)} Encrypted")
        self.vault_table.setRowCount(len(vaults))
        for row, v in enumerate(vaults):
            self.vault_table.setItem(row, 0, QTableWidgetItem(v.get("vault_id", "")))
            self.vault_table.setItem(row, 1, QTableWidgetItem(v.get("label", "")))
            self.vault_table.setItem(row, 2, QTableWidgetItem(v.get("device", "")))
            self.vault_table.setItem(row, 3, QTableWidgetItem(v.get("mount_dir", "")))
            is_mounted = os.path.ismount(v.get("mount_dir", ""))
            status = "MOUNTED" if is_mounted else "LOCKED"
            self.vault_table.setItem(row, 4, QTableWidgetItem(status))

    def on_encode_click(self):
        target_dev = self.enc_dev_combo.currentData()
        label = self.enc_label_input.text().strip() or "CyberVault"
        if not target_dev:
            QMessageBox.warning(self, "No Device", "Please select a target USB device.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Encoding",
            f"WARNING: All existing data on {target_dev} will be permanently erased and replaced with LUKS2 encryption.\n"
            f"The key will be saved inside CyberBreak's app keystore.\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.enc_btn.setEnabled(False)
        self.enc_btn.setText("ENCODING VAULT...")
        self.worker = USBActionWorker(USBArmory.encode_and_format_luks, target_dev, label)
        self.worker.finished_signal.connect(self._on_encode_done)
        self.worker.start()

    def _on_encode_done(self, ok: bool, msg: str):
        self.enc_btn.setEnabled(True)
        self.enc_btn.setText("🔒 ENCODE & ENCRYPT USB DRIVE")
        self.log_box.append(f"[ENCODER] {msg}")
        if ok:
            QMessageBox.information(self, "Vault Created", msg)
        else:
            QMessageBox.critical(self, "Encoding Failed", msg)
        self.refresh_all()

    def on_unlock_click(self):
        row = self.vault_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a vault in the table.")
            return
        v_id = self.vault_table.item(row, 0).text()
        self.log_box.append(f"[DECODER] Unlocking {v_id}...")
        ok, msg = USBArmory.unlock_vault(v_id)
        self.log_box.append(f"[DECODER] {msg}")
        self.refresh_all()

    def on_lock_click(self):
        row = self.vault_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a vault in the table.")
            return
        v_id = self.vault_table.item(row, 0).text()
        self.log_box.append(f"[DECODER] Locking {v_id}...")
        ok, msg = USBArmory.lock_vault(v_id)
        self.log_box.append(f"[DECODER] {msg}")
        self.refresh_all()

    def on_format_click(self):
        target_dev = self.fmt_dev_combo.currentData()
        raw_fstype = self.fmt_type_combo.currentText()
        fstype = raw_fstype.split()[0]
        label = self.fmt_label_input.text().strip() or "Storage"
        if not target_dev:
            return

        ok, msg = USBArmory.format_partition(target_dev, fstype, label)
        self.log_box.append(f"[FORMATTER] {msg}")
        self.refresh_all()

    def on_wipe_click(self):
        target_dev = self.fmt_dev_combo.currentData()
        if not target_dev:
            return
        ok, msg = USBArmory.wipe_drive(target_dev)
        self.log_box.append(f"[SANITIZER] {msg}")
        self.refresh_all()

    def on_browse_iso(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ISO Image", "", "Disk Images (*.iso *.img)")
        if path:
            self.iso_path_input.setText(path)

    def on_burn_iso_click(self):
        iso = self.iso_path_input.text().strip()
        dev = self.iso_dev_combo.currentData()
        if not iso or not dev:
            QMessageBox.warning(self, "Missing Arguments", "Please select an ISO file and target device.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Flashing",
            f"Are you sure you want to write {iso} to {dev}?\nALL DATA ON THE TARGET DRIVE WILL BE OVERWRITTEN.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.burn_btn.setEnabled(False)
        self.burn_btn.setText("BURNING ISO...")
        self.worker = USBActionWorker(USBArmory.flash_iso, iso, dev)
        self.worker.finished_signal.connect(lambda ok, msg: [
            self.burn_btn.setEnabled(True),
            self.burn_btn.setText("🔥 BURN RAW ISO TO USB"),
            self.log_box.append(f"[ISO FLASHER] {msg}"),
            self.refresh_all()
        ])
        self.worker.start()

    def on_backup_click(self):
        dest = self.bk_dest_combo.currentData()
        mode = self.bk_scope_combo.currentData()
        if not dest:
            QMessageBox.warning(self, "No Destination", "No mounted USB target found. Please mount a USB drive first.")
            return
        self.bk_btn.setEnabled(False)
        self.bk_btn.setText("CREATING BACKUP...")
        self.worker = USBActionWorker(USBArmory.backup_system_to_usb, dest, mode)
        self.worker.finished_signal.connect(lambda ok, msg: [
            self.bk_btn.setEnabled(True),
            self.bk_btn.setText("📦 CREATE INSTANT USB BACKUP"),
            self.log_box.append(f"[BACKUP] {msg}"),
            self.refresh_all()
        ])
        self.worker.start()

    def on_trim_click(self):
        self.trim_btn.setEnabled(False)
        self.trim_btn.setText("DISCARDING BLOCKS...")
        self.worker = USBActionWorker(USBArmory.trim_drives)
        self.worker.finished_signal.connect(lambda ok, msg: [
            self.trim_btn.setEnabled(True),
            self.trim_btn.setText("🧹 RUN HIGH-VOLTAGE DRIVE TRIM"),
            self.log_box.append(f"[TRIM] {msg}")
        ])
        self.worker.start()

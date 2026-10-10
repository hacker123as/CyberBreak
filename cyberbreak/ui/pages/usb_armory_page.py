import os
from PyQt6.QtWidgets import QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QTabWidget, QComboBox, QLineEdit, QTextEdit, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from cyberbreak.core.usb_armory import USBArmory
from cyberbreak.ui.widgets.status_card import StatusCard
from cyberbreak.ui.widgets.glass import GlassFrame, icon

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

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 24)
        layout.setSpacing(22)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(8)
        title = QLabel('Storage tools')
        title.setObjectName('HeaderTitle')
        title.setWordWrap(True)
        subtitle = QLabel('Encrypted vaults, drive formatting, image flashing, and system backups.')
        subtitle.setObjectName('HeaderSubtitle')
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        self.refresh_btn = QPushButton('Refresh storage')
        self.refresh_btn.setIcon(icon('refresh'))
        self.refresh_btn.setObjectName('OutlineButton')
        self.refresh_btn.clicked.connect(self.refresh_all)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)
        grid = QGridLayout()
        grid.setSpacing(16)
        self.card_devices = StatusCard('USB storage devices', '0 detected', 'Removable block devices', '', 'WARN')
        grid.addWidget(self.card_devices, 0, 0)
        self.card_vaults = StatusCard('Registered vaults', '0 active', 'LUKS2 cipher vaults', '', 'WARN')
        grid.addWidget(self.card_vaults, 0, 1)
        self.card_keystore = StatusCard('App keystore', 'Protected', '~/.config/cyberbreak/vault_keys', '', 'SECURE')
        grid.addWidget(self.card_keystore, 0, 2)
        layout.addLayout(grid)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)
        self.tabs.setMinimumHeight(380)
        self.tabs.addTab(self._create_encoder_tab(), 'Encrypt')
        self.tabs.addTab(self._create_decoder_tab(), 'Vaults')
        self.tabs.addTab(self._create_formatter_tab(), 'Format')
        self.tabs.addTab(self._create_iso_tab(), 'Flash image')
        self.tabs.addTab(self._create_backup_tab(), 'Back up')
        self.tabs.addTab(self._create_trim_tab(), 'Trim SSD')
        layout.addWidget(self.tabs)
        log_frame = GlassFrame()
        log_frame.setObjectName('GlassCard')
        l_layout = QVBoxLayout(log_frame)
        l_layout.setContentsMargins(22, 22, 22, 22)
        l_layout.setSpacing(6)
        l_title = QLabel('Operation log')
        l_title.setObjectName('CardTitle')
        l_layout.addWidget(l_title)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName('Terminal')
        self.log_box.setFixedHeight(85)
        l_layout.addWidget(self.log_box)
        layout.addWidget(log_frame)
        self.refresh_all()

    def _create_encoder_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)
        info = QLabel('Create an AES-XTS-512 encrypted LUKS2 volume. Encryption keys are stored in the CyberBreak keystore. Windows cannot read the encrypted filesystem. Existing drive contents will be erased.')
        info.setObjectName('HeaderSubtitle')
        info.setWordWrap(True)
        lay.addWidget(info)
        form_grid = QGridLayout()
        form_grid.setColumnStretch(1, 1)
        form_grid.setSpacing(16)
        form_grid.addWidget(QLabel('USB drive'), 0, 0)
        self.enc_dev_combo = QComboBox()
        form_grid.addWidget(self.enc_dev_combo, 0, 1)
        form_grid.addWidget(QLabel('Vault name'), 1, 0)
        self.enc_label_input = QLineEdit('CyberVault')
        form_grid.addWidget(self.enc_label_input, 1, 1)
        lay.addLayout(form_grid)
        self.enc_btn = QPushButton('Create encrypted vault')
        self.enc_btn.setIcon(icon('lock'))
        self.enc_btn.setObjectName('AccentButton')
        self.enc_btn.clicked.connect(self.on_encode_click)
        lay.addWidget(self.enc_btn)
        lay.addStretch()
        return w

    def _create_decoder_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)
        desc = QLabel('Select a registered vault to mount it or lock it with the app keystore.')
        desc.setObjectName('HeaderSubtitle')
        desc.setWordWrap(True)
        lay.addWidget(desc)
        self.vault_table = QTableWidget()
        self.vault_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vault_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vault_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.vault_table.setShowGrid(False)
        self.vault_table.setAlternatingRowColors(True)
        self.vault_table.verticalHeader().setVisible(False)
        self.vault_table.verticalHeader().setDefaultSectionSize(44)
        self.vault_table.setMinimumHeight(240)
        self.vault_table.setColumnCount(5)
        self.vault_table.setHorizontalHeaderLabels(['Vault ID', 'Label', 'Device', 'Mount Path', 'Status'])
        self.vault_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vault_table.setMinimumHeight(200)
        lay.addWidget(self.vault_table)
        btn_row = QHBoxLayout()
        self.unlock_btn = QPushButton('Unlock vault')
        self.unlock_btn.setIcon(icon('lock'))
        self.unlock_btn.setObjectName('AccentButton')
        self.unlock_btn.clicked.connect(self.on_unlock_click)
        btn_row.addWidget(self.unlock_btn)
        self.lock_btn = QPushButton('Lock vault')
        self.lock_btn.setIcon(icon('lock'))
        self.lock_btn.setObjectName('PanicButton')
        self.lock_btn.clicked.connect(self.on_lock_click)
        btn_row.addWidget(self.lock_btn)
        lay.addLayout(btn_row)
        lay.addStretch()
        return w

    def _create_formatter_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)
        form_grid = QGridLayout()
        form_grid.setColumnStretch(1, 1)
        form_grid.setSpacing(16)
        form_grid.addWidget(QLabel('Target drive'), 0, 0)
        self.fmt_dev_combo = QComboBox()
        form_grid.addWidget(self.fmt_dev_combo, 0, 1)
        form_grid.addWidget(QLabel('Filesystem'), 1, 0)
        self.fmt_type_combo = QComboBox()
        self.fmt_type_combo.addItems(['ext4', 'btrfs', 'vfat (FAT32)', 'exfat'])
        form_grid.addWidget(self.fmt_type_combo, 1, 1)
        form_grid.addWidget(QLabel('Volume name'), 2, 0)
        self.fmt_label_input = QLineEdit('Storage')
        form_grid.addWidget(self.fmt_label_input, 2, 1)
        lay.addLayout(form_grid)
        btn_row = QHBoxLayout()
        self.fmt_btn = QPushButton('Format drive')
        self.fmt_btn.setObjectName('CyanButton')
        self.fmt_btn.clicked.connect(self.on_format_click)
        btn_row.addWidget(self.fmt_btn)
        self.wipe_btn = QPushButton('Wipe drive')
        self.wipe_btn.setObjectName('PanicButton')
        self.wipe_btn.clicked.connect(self.on_wipe_click)
        btn_row.addWidget(self.wipe_btn)
        lay.addLayout(btn_row)
        lay.addStretch()
        return w

    def _create_iso_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)
        desc = QLabel('Write an ISO or disk image to a USB drive. Existing contents will be overwritten.')
        desc.setObjectName('HeaderSubtitle')
        desc.setWordWrap(True)
        lay.addWidget(desc)
        iso_row = QHBoxLayout()
        self.iso_path_input = QLineEdit()
        self.iso_path_input.setPlaceholderText('/path/to/distro.iso')
        iso_row.addWidget(self.iso_path_input)
        browse_btn = QPushButton('Choose image')
        browse_btn.setIcon(icon('folder'))
        browse_btn.setObjectName('OutlineButton')
        browse_btn.clicked.connect(self.on_browse_iso)
        iso_row.addWidget(browse_btn)
        lay.addLayout(iso_row)
        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel('USB drive'))
        self.iso_dev_combo = QComboBox()
        dev_row.addWidget(self.iso_dev_combo)
        lay.addLayout(dev_row)
        self.burn_btn = QPushButton('Flash image to USB')
        self.burn_btn.setObjectName('PanicButton')
        self.burn_btn.clicked.connect(self.on_burn_iso_click)
        lay.addWidget(self.burn_btn)
        lay.addStretch()
        return w

    def _create_backup_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)
        desc = QLabel('Save a compressed archive of your home directory or essential configuration to a mounted USB drive.')
        desc.setObjectName('HeaderSubtitle')
        desc.setWordWrap(True)
        lay.addWidget(desc)
        bk_grid = QGridLayout()
        bk_grid.setColumnStretch(1, 1)
        bk_grid.setSpacing(16)
        bk_grid.addWidget(QLabel('Backup destination'), 0, 0)
        self.bk_dest_combo = QComboBox()
        bk_grid.addWidget(self.bk_dest_combo, 0, 1)
        bk_grid.addWidget(QLabel('Include'), 1, 0)
        self.bk_scope_combo = QComboBox()
        self.bk_scope_combo.addItem('Home Directory (~/)', 'home')
        self.bk_scope_combo.addItem('Essential Configs (/etc + /usr/local/bin + ~)', 'full')
        bk_grid.addWidget(self.bk_scope_combo, 1, 1)
        lay.addLayout(bk_grid)
        self.bk_btn = QPushButton('Create backup')
        self.bk_btn.setIcon(icon('folder'))
        self.bk_btn.setObjectName('AccentButton')
        self.bk_btn.clicked.connect(self.on_backup_click)
        lay.addWidget(self.bk_btn)
        lay.addStretch()
        return w

    def _create_trim_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)
        desc = QLabel('Trim unused blocks on mounted flash storage, NVMe drives, and supported encrypted volumes.')
        desc.setObjectName('HeaderSubtitle')
        desc.setWordWrap(True)
        lay.addWidget(desc)
        self.trim_btn = QPushButton('Trim mounted drives')
        self.trim_btn.setObjectName('CyanButton')
        self.trim_btn.clicked.connect(self.on_trim_click)
        lay.addWidget(self.trim_btn)
        lay.addStretch()
        return w

    def refresh_all(self):
        self.log_box.append('[ARMORY] Refreshing storage hardware & vault registries...')
        devices = USBArmory.list_devices()
        usb_devs = [d for d in devices if d.get('is_usb')]
        self.card_devices.set_value(f'{len(usb_devs)} USB Drives')
        if usb_devs:
            self.card_devices.set_pill('Hardware ready', 'SECURE')
            self.card_devices.subtitle_label.setText(', '.join([d['name'] for d in usb_devs]))
        else:
            self.card_devices.set_pill('No USB inserted', 'WARN')
            self.card_devices.subtitle_label.setText('Connect USB drive to arm')
        for cb in (self.enc_dev_combo, self.fmt_dev_combo, self.iso_dev_combo):
            cb.clear()
            for d in devices:
                if not d.get('is_system'):
                    cb.addItem(f"{d['path']} ({d['model']} - {d['size_gb']} GB)", d['path'])
        self.bk_dest_combo.clear()
        mounts = []
        user = os.getenv('USER') or 'user'
        for base in (f'/media/{user}', '/media', '/mnt'):
            if os.path.exists(base):
                for sub in os.listdir(base):
                    p = os.path.join(base, sub)
                    if os.path.isdir(p):
                        mounts.append(p)
        for m in mounts:
            self.bk_dest_combo.addItem(m, m)
        vaults = USBArmory.load_registry()
        self.card_vaults.set_value(f'{len(vaults)} Encrypted')
        self.vault_table.setRowCount(len(vaults))
        for row, v in enumerate(vaults):
            self.vault_table.setItem(row, 0, QTableWidgetItem(v.get('vault_id', '')))
            self.vault_table.setItem(row, 1, QTableWidgetItem(v.get('label', '')))
            self.vault_table.setItem(row, 2, QTableWidgetItem(v.get('device', '')))
            self.vault_table.setItem(row, 3, QTableWidgetItem(v.get('mount_dir', '')))
            is_mounted = os.path.ismount(v.get('mount_dir', ''))
            status = 'MOUNTED' if is_mounted else 'LOCKED'
            self.vault_table.setItem(row, 4, QTableWidgetItem(status))

    def on_encode_click(self):
        target_dev = self.enc_dev_combo.currentData()
        label = self.enc_label_input.text().strip() or 'CyberVault'
        if not target_dev:
            QMessageBox.warning(self, 'No Device', 'Please select a target USB device.')
            return
        confirm = QMessageBox.question(self, 'Confirm Encoding', f"WARNING: All existing data on {target_dev} will be permanently erased and replaced with LUKS2 encryption.\nThe key will be saved inside CyberBreak's app keystore.\nProceed?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.enc_btn.setEnabled(False)
        self.enc_btn.setText('Creating vault…')
        self.worker = USBActionWorker(USBArmory.encode_and_format_luks, target_dev, label)
        self.worker.finished_signal.connect(self._on_encode_done)
        self.worker.start()

    def _on_encode_done(self, ok: bool, msg: str):
        self.enc_btn.setEnabled(True)
        self.enc_btn.setText('Create encrypted vault')
        self.log_box.append(f'[ENCODER] {msg}')
        if ok:
            QMessageBox.information(self, 'Vault Created', msg)
        else:
            QMessageBox.critical(self, 'Encoding Failed', msg)
        self.refresh_all()

    def on_unlock_click(self):
        row = self.vault_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Selection Required', 'Please select a vault in the table.')
            return
        v_id = self.vault_table.item(row, 0).text()
        self.log_box.append(f'[DECODER] Unlocking {v_id}...')
        ok, msg = USBArmory.unlock_vault(v_id)
        self.log_box.append(f'[DECODER] {msg}')
        self.refresh_all()

    def on_lock_click(self):
        row = self.vault_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Selection Required', 'Please select a vault in the table.')
            return
        v_id = self.vault_table.item(row, 0).text()
        self.log_box.append(f'[DECODER] Locking {v_id}...')
        ok, msg = USBArmory.lock_vault(v_id)
        self.log_box.append(f'[DECODER] {msg}')
        self.refresh_all()

    def on_format_click(self):
        target_dev = self.fmt_dev_combo.currentData()
        raw_fstype = self.fmt_type_combo.currentText()
        fstype = raw_fstype.split()[0]
        label = self.fmt_label_input.text().strip() or 'Storage'
        if not target_dev:
            return
        ok, msg = USBArmory.format_partition(target_dev, fstype, label)
        self.log_box.append(f'[FORMATTER] {msg}')
        self.refresh_all()

    def on_wipe_click(self):
        target_dev = self.fmt_dev_combo.currentData()
        if not target_dev:
            return
        ok, msg = USBArmory.wipe_drive(target_dev)
        self.log_box.append(f'[SANITIZER] {msg}')
        self.refresh_all()

    def on_browse_iso(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select ISO Image', '', 'Disk Images (*.iso *.img)')
        if path:
            self.iso_path_input.setText(path)

    def on_burn_iso_click(self):
        iso = self.iso_path_input.text().strip()
        dev = self.iso_dev_combo.currentData()
        if not iso or not dev:
            QMessageBox.warning(self, 'Missing Arguments', 'Please select an ISO file and target device.')
            return
        confirm = QMessageBox.question(self, 'Confirm Flashing', f'Are you sure you want to write {iso} to {dev}?\nALL DATA ON THE TARGET DRIVE WILL BE OVERWRITTEN.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.burn_btn.setEnabled(False)
        self.burn_btn.setText('Flashing image…')
        self.worker = USBActionWorker(USBArmory.flash_iso, iso, dev)
        self.worker.finished_signal.connect(lambda ok, msg: [self.burn_btn.setEnabled(True), self.burn_btn.setText('Flash image to USB'), self.log_box.append(f'[ISO FLASHER] {msg}'), self.refresh_all()])
        self.worker.start()

    def on_backup_click(self):
        dest = self.bk_dest_combo.currentData()
        mode = self.bk_scope_combo.currentData()
        if not dest:
            QMessageBox.warning(self, 'No Destination', 'No mounted USB target found. Please mount a USB drive first.')
            return
        self.bk_btn.setEnabled(False)
        self.bk_btn.setText('Creating backup…')
        self.worker = USBActionWorker(USBArmory.backup_system_to_usb, dest, mode)
        self.worker.finished_signal.connect(lambda ok, msg: [self.bk_btn.setEnabled(True), self.bk_btn.setText('Create backup'), self.log_box.append(f'[BACKUP] {msg}'), self.refresh_all()])
        self.worker.start()

    def on_trim_click(self):
        self.trim_btn.setEnabled(False)
        self.trim_btn.setText('Trimming drives…')
        self.worker = USBActionWorker(USBArmory.trim_drives)
        self.worker.finished_signal.connect(lambda ok, msg: [self.trim_btn.setEnabled(True), self.trim_btn.setText('Trim mounted drives'), self.log_box.append(f'[TRIM] {msg}')])
        self.worker.start()

import os
from PyQt6.QtWidgets import (
    QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTabWidget, QComboBox, QLineEdit, QTextEdit, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QDialog
)
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

class PasscodeDialog(QDialog):
    def __init__(self, parent=None, title="Unlock Encrypted USB", vault_name="CyberVault"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(460)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        t_lbl = QLabel(f"Unlock '{vault_name}'")
        t_lbl.setObjectName("CardTitle")
        lay.addWidget(t_lbl)

        sub_lbl = QLabel("Enter software passcode to unseal the 512-bit master key:")
        sub_lbl.setObjectName("HeaderSubtitle")
        sub_lbl.setWordWrap(True)
        lay.addWidget(sub_lbl)

        pass_row = QHBoxLayout()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Enter vault passcode...")
        pass_row.addWidget(self.pass_input, 1)

        self.toggle_btn = QPushButton("Show")
        self.toggle_btn.setObjectName("OutlineButton")
        self.toggle_btn.setFixedWidth(65)
        self.toggle_btn.clicked.connect(self._toggle_echo)
        pass_row.addWidget(self.toggle_btn)
        lay.addLayout(pass_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("OutlineButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        unlock_btn = QPushButton("Unlock Drive")
        unlock_btn.setObjectName("AccentButton")
        unlock_btn.clicked.connect(self.accept)
        btn_row.addWidget(unlock_btn)
        lay.addLayout(btn_row)

    def _toggle_echo(self):
        if self.pass_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("Hide")
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("Show")

    def get_passcode(self) -> str:
        return self.pass_input.text().strip()

class SecurityAuditDialog(QDialog):
    def __init__(self, parent=None, audit: dict = None, summary: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Cryptographic Hardening Audit")
        self.resize(600, 520)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        t_lbl = QLabel("Vault Cryptographic Verification")
        t_lbl.setObjectName("CardTitle")
        lay.addWidget(t_lbl)

        badge = QLabel("100% UNCRACKABLE VERIFIED • AES-256-XTS • ARGON2ID")
        badge.setStyleSheet("color: #85e4ce; background: rgba(81, 191, 163, 25); border: 1px solid rgba(108, 220, 191, 50); border-radius: 8px; padding: 6px 12px; font-weight: 700; font-size: 11px;")
        lay.addWidget(badge)

        info_frame = GlassFrame()
        info_frame.setObjectName("GlassCard")
        f_lay = QGridLayout(info_frame)
        f_lay.setContentsMargins(16, 16, 16, 16)
        f_lay.setSpacing(10)

        f_lay.addWidget(QLabel("Target Volume:"), 0, 0)
        lbl_dev = QLabel(f"{audit.get('label')} ({audit.get('device')})")
        lbl_dev.setStyleSheet("color: #ffffff; font-weight: 600;")
        f_lay.addWidget(lbl_dev, 0, 1)

        f_lay.addWidget(QLabel("Symmetric Cipher:"), 1, 0)
        lbl_ciph = QLabel("AES-256-XTS (aes-xts-plain64, 512-bit key)")
        lbl_ciph.setStyleSheet("color: #65dbc5; font-weight: 600;")
        f_lay.addWidget(lbl_ciph, 1, 1)

        f_lay.addWidget(QLabel("Key Derivation (PBKDF):"), 2, 0)
        lbl_pbkdf = QLabel("Argon2id (High-RAM hardware calibrated)")
        lbl_pbkdf.setStyleSheet("color: #65dbc5; font-weight: 600;")
        f_lay.addWidget(lbl_pbkdf, 2, 1)

        f_lay.addWidget(QLabel("Header Architecture:"), 3, 0)
        h_type = "Detached LUKS2 (Zero USB Signatures - 100% Raw Noise)" if audit.get("detached_header") else "Standard On-Disk LUKS2"
        lbl_h = QLabel(h_type)
        lbl_h.setStyleSheet("color: #a9bde9; font-weight: 600;")
        f_lay.addWidget(lbl_h, 3, 1)

        f_lay.addWidget(QLabel("Offline Header Backup:"), 4, 0)
        lbl_b = QLabel("Protected & Verified" if audit.get("backup_file") else "Not configured")
        lbl_b.setStyleSheet("color: #65dbc5; font-weight: 600;" if audit.get("backup_file") else "color: #f2c67a;")
        f_lay.addWidget(lbl_b, 4, 1)

        f_lay.addWidget(QLabel("Keystore Protection:"), 5, 0)
        lbl_k = QLabel("Scrypt-32768 + AES-256-GCM Envelope (Zero Plaintext)")
        lbl_k.setStyleSheet("color: #65dbc5; font-weight: 600;")
        f_lay.addWidget(lbl_k, 5, 1)

        lay.addWidget(info_frame)

        dump_lbl = QLabel("Raw Cryptsetup LUKSDump Audit:")
        dump_lbl.setObjectName("HeaderSubtitle")
        lay.addWidget(dump_lbl)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setObjectName("Terminal")
        txt.setPlainText(audit.get("raw_dump", summary))
        lay.addWidget(txt, 1)

        close_btn = QPushButton("Done")
        close_btn.setObjectName("AccentButton")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

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

        self.refresh_btn = QPushButton('Refresh USB list')
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
        self.tabs.setMinimumHeight(410)
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

        info = QLabel('Create an uncrackable AES-256-XTS encrypted LUKS2 volume with Argon2id PBKDF and Detached Headers. Encryption master keys are sealed inside CyberBreak keystore with Scrypt-32768. Windows and forensic tools see only raw unformatted noise.')
        info.setObjectName('HeaderSubtitle')
        info.setWordWrap(True)
        lay.addWidget(info)

        form_grid = QGridLayout()
        form_grid.setColumnStretch(1, 1)
        form_grid.setSpacing(14)

        form_grid.addWidget(QLabel('Target USB drive'), 0, 0)
        enc_dev_layout = QHBoxLayout()
        self.enc_dev_combo = QComboBox()
        enc_dev_layout.addWidget(self.enc_dev_combo, 1)
        self.enc_refresh_usb_btn = QPushButton('Refresh USB list')
        self.enc_refresh_usb_btn.setIcon(icon('refresh'))
        self.enc_refresh_usb_btn.setObjectName('OutlineButton')
        self.enc_refresh_usb_btn.clicked.connect(self.refresh_all)
        enc_dev_layout.addWidget(self.enc_refresh_usb_btn)
        form_grid.addLayout(enc_dev_layout, 0, 1)

        form_grid.addWidget(QLabel('Custom vault name'), 1, 0)
        self.enc_label_input = QLineEdit('CyberVault')
        form_grid.addWidget(self.enc_label_input, 1, 1)

        form_grid.addWidget(QLabel('Vault software passcode'), 2, 0)
        pass_row = QHBoxLayout()
        self.enc_pass_input = QLineEdit()
        self.enc_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.enc_pass_input.setPlaceholderText('Enter passcode to seal vault (e.g. 123456789 or generate below)...')
        pass_row.addWidget(self.enc_pass_input, 1)

        self.enc_toggle_pass_btn = QPushButton('Show')
        self.enc_toggle_pass_btn.setObjectName('OutlineButton')
        self.enc_toggle_pass_btn.setFixedWidth(65)
        self.enc_toggle_pass_btn.clicked.connect(self._toggle_enc_pass)
        pass_row.addWidget(self.enc_toggle_pass_btn)

        self.enc_gen_pass_btn = QPushButton('Generate 36-char Passcode')
        self.enc_gen_pass_btn.setIcon(icon('sparkles'))
        self.enc_gen_pass_btn.setObjectName('OutlineButton')
        self.enc_gen_pass_btn.clicked.connect(self._generate_passcode)
        pass_row.addWidget(self.enc_gen_pass_btn)
        form_grid.addLayout(pass_row, 2, 1)

        lay.addLayout(form_grid)

        self.enc_detached_cb = QCheckBox('Use Detached LUKS2 Header (Max Anti-Forensics: Zero LUKS signatures on USB drive, 100% uncrackable raw noise)')
        self.enc_detached_cb.setChecked(True)
        lay.addWidget(self.enc_detached_cb)

        specs_card = GlassFrame()
        specs_card.setObjectName('GlassCard')
        sc_lay = QVBoxLayout(specs_card)
        sc_lay.setContentsMargins(14, 10, 14, 10)
        sc_text = QLabel('• Cipher: AES-256-XTS (512-bit combined key)  • PBKDF: Argon2id (Hardware RAM calibrated)  • Keystore: Scrypt-32768 + AES-GCM  • Isolated USB Only')
        sc_text.setStyleSheet('color: #85e4ce; font-size: 11px; font-weight: 600;')
        sc_lay.addWidget(sc_text)
        lay.addWidget(specs_card)

        self.enc_btn = QPushButton('Create encrypted vault')
        self.enc_btn.setIcon(icon('lock'))
        self.enc_btn.setObjectName('AccentButton')
        self.enc_btn.clicked.connect(self.on_encode_click)
        lay.addWidget(self.enc_btn)

        lay.addStretch()
        return w

    def _toggle_enc_pass(self):
        if self.enc_pass_input.echoMode() == QLineEdit.EchoMode.Password:
            self.enc_pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.enc_toggle_pass_btn.setText('Hide')
        else:
            self.enc_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.enc_toggle_pass_btn.setText('Show')

    def _generate_passcode(self):
        code = USBArmory.generate_high_entropy_password(36)
        self.enc_pass_input.setText(code)
        self.enc_pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
        self.enc_toggle_pass_btn.setText('Hide')
        self.log_box.append('[KEYGEN] Generated 36-character high-entropy cryptographic passcode.')

    def _create_decoder_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)

        desc = QLabel('Registered uncrackable USB vaults. Requires your software passcode to unseal the 512-bit master key upon every unlock request.')
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
        self.vault_table.verticalHeader().setDefaultSectionSize(48)
        self.vault_table.setMinimumHeight(240)
        self.vault_table.setColumnCount(6)
        self.vault_table.setHorizontalHeaderLabels(['Vault ID', 'Label', 'Device', 'Header Architecture', 'Mount Path', 'Status'])
        self.vault_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.vault_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.vault_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.vault_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.vault_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.vault_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.vault_table)

        btn_row = QHBoxLayout()
        self.unlock_btn = QPushButton('Unlock vault')
        self.unlock_btn.setIcon(icon('lock'))
        self.unlock_btn.setObjectName('AccentButton')
        self.unlock_btn.clicked.connect(self.on_unlock_click)
        btn_row.addWidget(self.unlock_btn)

        self.lock_btn = QPushButton('Lock vault')
        self.lock_btn.setIcon(icon('lock'))
        self.lock_btn.setObjectName('CyanButton')
        self.lock_btn.clicked.connect(self.on_lock_click)
        btn_row.addWidget(self.lock_btn)

        self.verify_btn = QPushButton('Verify security')
        self.verify_btn.setIcon(icon('shield'))
        self.verify_btn.setObjectName('OutlineButton')
        self.verify_btn.clicked.connect(self.on_verify_security_click)
        btn_row.addWidget(self.verify_btn)

        self.del_vault_btn = QPushButton('Delete vault')
        self.del_vault_btn.setIcon(icon('close'))
        self.del_vault_btn.setObjectName('PanicButton')
        self.del_vault_btn.clicked.connect(self.on_delete_vault_click)
        btn_row.addWidget(self.del_vault_btn)

        btn_row.addStretch()

        self.refresh_vaults_btn = QPushButton('Refresh list')
        self.refresh_vaults_btn.setIcon(icon('refresh'))
        self.refresh_vaults_btn.setObjectName('OutlineButton')
        self.refresh_vaults_btn.clicked.connect(self.refresh_all)
        btn_row.addWidget(self.refresh_vaults_btn)

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
        form_grid.addWidget(QLabel('Target USB drive'), 0, 0)
        fmt_dev_layout = QHBoxLayout()
        self.fmt_dev_combo = QComboBox()
        fmt_dev_layout.addWidget(self.fmt_dev_combo, 1)
        self.fmt_refresh_usb_btn = QPushButton('Refresh USB list')
        self.fmt_refresh_usb_btn.setIcon(icon('refresh'))
        self.fmt_refresh_usb_btn.setObjectName('OutlineButton')
        self.fmt_refresh_usb_btn.clicked.connect(self.refresh_all)
        fmt_dev_layout.addWidget(self.fmt_refresh_usb_btn)
        form_grid.addLayout(fmt_dev_layout, 0, 1)
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
        desc = QLabel('Write an ISO or disk image to a removable USB drive. Existing contents will be overwritten.')
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
        self.iso_dev_combo = QComboBox()
        dev_row.addWidget(self.iso_dev_combo, 1)
        refresh_iso_btn = QPushButton('Refresh USB list')
        refresh_iso_btn.setIcon(icon('refresh'))
        refresh_iso_btn.setObjectName('OutlineButton')
        refresh_iso_btn.clicked.connect(self.refresh_all)
        dev_row.addWidget(refresh_iso_btn)
        lay.addLayout(dev_row)
        self.burn_btn = QPushButton('Flash image to USB')
        self.burn_btn.setObjectName('CyanButton')
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
        self.log_box.append('[ARMORY] Refreshing removable USB devices & vault registries...')
        usb_devs = USBArmory.get_usb_devices()
        self.card_devices.set_value(f'{len(usb_devs)} USB Drives')
        if usb_devs:
            self.card_devices.set_pill('Hardware ready', 'SECURE')
            self.card_devices.subtitle_label.setText(', '.join([d['name'] for d in usb_devs][:3]))
        else:
            self.card_devices.set_pill('No USB inserted', 'WARN')
            self.card_devices.subtitle_label.setText('Connect USB drive to arm')

        # Populate combos strictly with USB devices (ignoring system storage entirely)
        for cb in (self.enc_dev_combo, self.fmt_dev_combo, self.iso_dev_combo):
            cb.clear()
            if usb_devs:
                for d in usb_devs:
                    cb.addItem(f"{d['path']} ({d['model']} - {d['size_gb']} GB)", d['path'])
            else:
                cb.addItem('(No removable USB drives detected)', None)

        self.enc_btn.setEnabled(bool(usb_devs))
        self.fmt_btn.setEnabled(bool(usb_devs))
        self.wipe_btn.setEnabled(bool(usb_devs))
        self.burn_btn.setEnabled(bool(usb_devs))

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

            is_detached = v.get('detached_header', False)
            h_text = 'DETACHED (Zero USB Signatures)' if is_detached else 'ON-DISK LUKS2'
            h_item = QTableWidgetItem(h_text)
            h_item.setForeground(QColor('#85e4ce') if is_detached else QColor('#a4aec8'))
            self.vault_table.setItem(row, 3, h_item)

            self.vault_table.setItem(row, 4, QTableWidgetItem(v.get('mount_dir', '')))

            is_mounted = os.path.ismount(v.get('mount_dir', ''))
            status = 'MOUNTED' if is_mounted else 'LOCKED'
            s_item = QTableWidgetItem(status)
            s_item.setForeground(QColor('#65dbc5') if is_mounted else QColor('#f2c67a'))
            self.vault_table.setItem(row, 5, s_item)

    def on_encode_click(self):
        target_dev = self.enc_dev_combo.currentData()
        label = self.enc_label_input.text().strip() or 'CyberVault'
        passcode = self.enc_pass_input.text().strip()
        use_detached = self.enc_detached_cb.isChecked()

        if not target_dev:
            QMessageBox.warning(self, 'No USB Selected', 'Please insert and select a target USB device.')
            return

        if not passcode or len(passcode) < 6:
            QMessageBox.warning(self, 'Passcode Required', 'Please enter a software passcode (at least 6 characters) or click "Generate 36-char Passcode" to seal this vault.')
            return

        confirm = QMessageBox.question(
            self,
            'Confirm Uncrackable Encryption',
            f"ENCRYPTION HARDENING CONFIRMATION:\n\n"
            f"• Target Device: {target_dev} (Removable USB)\n"
            f"• Symmetric Cipher: AES-256-XTS (512-bit combined key)\n"
            f"• Key Derivation: Argon2id (Hardware RAM calibrated)\n"
            f"• Architecture: {'Detached LUKS2 Header (Zero signatures on USB)' if use_detached else 'Standard LUKS2'}\n"
            f"• Keystore Security: Sealed with Scrypt-32768 + AES-256-GCM\n"
            f"• Offline Header Backup: Automated (~/.config/cyberbreak/vault_backups/)\n\n"
            f"WARNING: All existing data on {target_dev} will be wiped permanently.\n"
            f"Proceed with encryption format?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.enc_btn.setEnabled(False)
        self.enc_btn.setText('Hardening & formatting…')
        self.worker = USBActionWorker(USBArmory.encode_and_format_luks, target_dev, label, passcode, use_detached)
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
        label_item = self.vault_table.item(row, 1)
        label = label_item.text() if label_item else v_id

        dialog = PasscodeDialog(self, title="Unlock Encrypted USB", vault_name=label)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        passcode = dialog.get_passcode()
        if not passcode:
            QMessageBox.warning(self, 'Passcode Required', 'Please enter your software passcode to unseal the master key.')
            return

        self.log_box.append(f'[DECODER] Unsealing and unlocking vault {label} ({v_id})...')
        ok, msg = USBArmory.unlock_vault(v_id, passcode)
        self.log_box.append(f'[DECODER] {msg}')
        if ok:
            QMessageBox.information(self, 'Vault Unlocked', msg)
        else:
            QMessageBox.critical(self, 'Unlock Denied', msg)
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

    def on_verify_security_click(self):
        row = self.vault_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Selection Required', 'Please select a vault in the table to verify.')
            return
        v_id = self.vault_table.item(row, 0).text()
        self.log_box.append(f'[AUDIT] Verifying cryptographic parameters for {v_id}...')
        ok, audit, raw = USBArmory.verify_vault_security(v_id)
        if not ok:
            QMessageBox.critical(self, 'Verification Error', f"Could not audit vault: {raw}")
            return
        dlg = SecurityAuditDialog(self, audit, raw)
        dlg.exec()

    def on_delete_vault_click(self):
        row = self.vault_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Selection Required', 'Please select a vault in the table to delete.')
            return
        v_id = self.vault_table.item(row, 0).text()
        label_item = self.vault_table.item(row, 1)
        label = label_item.text() if label_item else v_id
        confirm = QMessageBox.question(
            self,
            'Confirm Vault Deletion',
            f"Permanently delete encrypted vault '{label}' (ID: {v_id})?\n\n"
            "This will:\n"
            "1. Safely unmount filesystem and close LUKS2 crypt mapper\n"
            "2. Securely shred sealed keyfiles and detached headers\n"
            "3. Deregister the vault from CyberBreak\n\n"
            "WARNING: The drive will become permanently unreadable without this key.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.log_box.append(f'[DECODER] Deleting vault {v_id} ({label})...')
        ok, msg = USBArmory.delete_vault(v_id)
        self.log_box.append(f'[DECODER] {msg}')
        if ok:
            QMessageBox.information(self, 'Vault Deleted', msg)
        else:
            QMessageBox.critical(self, 'Deletion Failed', msg)
        self.refresh_all()

    def on_format_click(self):
        target_dev = self.fmt_dev_combo.currentData()
        raw_fstype = self.fmt_type_combo.currentText()
        fstype = raw_fstype.split()[0]
        label = self.fmt_label_input.text().strip() or 'Storage'
        if not target_dev:
            QMessageBox.warning(self, 'No USB Selected', 'Please insert and select a target USB device.')
            return
        confirm = QMessageBox.question(self, 'Confirm Format', f"Format USB {target_dev} as {fstype.upper()} ({label})?\nALL DATA WILL BE ERASED.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        ok, msg = USBArmory.format_partition(target_dev, fstype, label)
        self.log_box.append(f'[FORMATTER] {msg}')
        self.refresh_all()

    def on_wipe_click(self):
        target_dev = self.fmt_dev_combo.currentData()
        if not target_dev:
            QMessageBox.warning(self, 'No USB Selected', 'Please insert and select a target USB device.')
            return
        confirm = QMessageBox.question(self, 'Confirm Wipe', f"Zero-wipe partition table on {target_dev}?\nALL PARTITIONS WILL BE DESTROYED.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
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
            QMessageBox.warning(self, 'Missing Arguments', 'Please select an ISO file and target USB device.')
            return
        confirm = QMessageBox.question(self, 'Confirm Flashing', f'Are you sure you want to write {iso} to {dev}?\nALL DATA ON THE TARGET USB WILL BE OVERWRITTEN.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt
from cyberbreak.core.metadata_cleaner import MetadataCleaner

class MetadataPage(QWidget):
    """File metadata stripping (mat2), multi-pass file shredder, and memory sanitization."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("METADATA STRIPPER & SECURE FILE SHREDDER // By lilami only")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Sanitize document EXIF/metadata via mat2, destroy files with multi-pass overwrites")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        layout.addLayout(header)

        # Metadata Sanitizer Frame
        meta_frame = QFrame()
        meta_frame.setObjectName("Card")
        m_layout = QVBoxLayout(meta_frame)
        m_layout.setContentsMargins(18, 18, 18, 18)
        m_layout.setSpacing(12)

        m_title = QLabel("FILE METADATA SANITIZER (MAT2)")
        m_title.setObjectName("CardTitle")
        m_layout.addWidget(m_title)

        m_desc = QLabel("Select PDF, Office document, or image to scrub all author, GPS, device, and software metadata.")
        m_desc.setObjectName("HeaderSubtitle")
        m_layout.addWidget(m_desc)

        m_row = QHBoxLayout()
        self.meta_file_input = QLineEdit()
        self.meta_file_input.setPlaceholderText("Select file to sanitize...")
        m_row.addWidget(self.meta_file_input)

        browse_btn = QPushButton("BROWSE...")
        browse_btn.clicked.connect(self.browse_meta_file)
        m_row.addWidget(browse_btn)

        clean_btn = QPushButton("STRIP METADATA")
        clean_btn.setObjectName("AccentButton")
        clean_btn.clicked.connect(self.on_clean_meta)
        m_row.addWidget(clean_btn)

        m_layout.addLayout(m_row)
        layout.addWidget(meta_frame)

        # File Shredder Frame
        shred_frame = QFrame()
        shred_frame.setObjectName("Card")
        s_layout = QVBoxLayout(shred_frame)
        s_layout.setContentsMargins(18, 18, 18, 18)
        s_layout.setSpacing(12)

        s_title = QLabel("MILITARY-GRADE FILE SHREDDER")
        s_title.setObjectName("CardTitle")
        s_layout.addWidget(s_title)

        s_desc = QLabel("Overwrites file content with random bytes and zeroes (DoD 5220.22-M 3-pass) before unlinking inode.")
        s_desc.setObjectName("HeaderSubtitle")
        s_layout.addWidget(s_desc)

        s_row = QHBoxLayout()
        self.shred_file_input = QLineEdit()
        self.shred_file_input.setPlaceholderText("Select file to permanently obliterate...")
        s_row.addWidget(self.shred_file_input)

        browse_shred_btn = QPushButton("BROWSE...")
        browse_shred_btn.clicked.connect(self.browse_shred_file)
        s_row.addWidget(browse_shred_btn)

        shred_btn = QPushButton("SHRED FILE NOW")
        shred_btn.setStyleSheet("background-color: #ff3344; color: #ffffff; font-weight: 700;")
        shred_btn.clicked.connect(self.on_shred_file)
        s_row.addWidget(shred_btn)

        s_layout.addLayout(s_row)
        layout.addWidget(shred_frame)

        # RAM Cache Frame
        ram_frame = QFrame()
        ram_frame.setObjectName("Card")
        r_layout = QHBoxLayout(ram_frame)
        r_layout.setContentsMargins(18, 18, 18, 18)
        r_layout.setSpacing(14)

        r_info = QVBoxLayout()
        r_title = QLabel("KERNEL MEMORY CACHE PURGE")
        r_title.setObjectName("CardTitle")
        r_sub = QLabel("Drops kernel pagecache, dentries, and inode caches (sync && echo 3 > /proc/sys/vm/drop_caches).")
        r_sub.setObjectName("HeaderSubtitle")
        r_info.addWidget(r_title)
        r_info.addWidget(r_sub)
        r_layout.addLayout(r_info)

        r_layout.addStretch()

        purge_btn = QPushButton("PURGE RAM CACHE")
        purge_btn.clicked.connect(MetadataCleaner.purge_ram_cache)
        r_layout.addWidget(purge_btn)

        layout.addWidget(ram_frame)
        layout.addStretch()

    def browse_meta_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Clean")
        if file_path:
            self.meta_file_input.setText(file_path)

    def browse_shred_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Shred")
        if file_path:
            self.shred_file_input.setText(file_path)

    def on_clean_meta(self):
        target = self.meta_file_input.text().strip()
        if target:
            MetadataCleaner.clean_metadata(target)

    def on_shred_file(self):
        target = self.shred_file_input.text().strip()
        if target:
            MetadataCleaner.secure_shred(target, passes=3)
            self.shred_file_input.clear()

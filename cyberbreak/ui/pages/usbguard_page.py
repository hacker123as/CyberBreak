from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from cyberbreak.core.hardware_manager import HardwareManager
from cyberbreak.ui.widgets.status_card import StatusCard

class USBGuardPage(QWidget):
    """BadUSB defense, USB port lockdown, and hardware sensor interlocks."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.usb_locked = False
        self.cam_disabled = False
        self.mic_muted = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("HARDWARE DEFENSE & DEVICE INTERLOCK")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("BadUSB injection defense, USB port authorization, webcam driver kill, and mic mute")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        layout.addLayout(header)

        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.usb_card = StatusCard("USB PORT STATUS", "Authorized", "Sysfs auto-authorization", "DEFAULT", "WARN")
        grid.addWidget(self.usb_card, 0, 0)

        self.cam_card = StatusCard("WEBCAM DRIVER", "Active", "Kernel uvcvideo driver", "UNLOCKED", "WARN")
        grid.addWidget(self.cam_card, 0, 1)

        self.mic_card = StatusCard("MICROPHONE CAPTURE", "Active", "Audio capture interface", "UNLOCKED", "WARN")
        grid.addWidget(self.mic_card, 1, 0)

        layout.addLayout(grid)

        # Controls Frame
        frame = QFrame()
        frame.setObjectName("Card")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(18, 18, 18, 18)
        f_layout.setSpacing(14)

        f_title = QLabel("HARDWARE INTERLOCK CONTROLS:")
        f_title.setObjectName("CardTitle")
        f_layout.addWidget(f_title)

        # USB row
        usb_row = QHBoxLayout()
        u_info = QVBoxLayout()
        u_lbl = QLabel("BadUSB / Rubber Ducky Lockdown")
        u_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        u_sub = QLabel("Blocks newly plugged USB devices from registering HID keyboard/mouse inputs.")
        u_sub.setObjectName("HeaderSubtitle")
        u_info.addWidget(u_lbl)
        u_info.addWidget(u_sub)
        usb_row.addLayout(u_info)
        usb_row.addStretch()

        self.usb_btn = QPushButton("LOCKDOWN USB PORTS")
        self.usb_btn.clicked.connect(self.toggle_usb)
        usb_row.addWidget(self.usb_btn)
        f_layout.addLayout(usb_row)

        f_layout.addWidget(self.create_divider())

        # Cam row
        cam_row = QHBoxLayout()
        c_info = QVBoxLayout()
        c_lbl = QLabel("Hardware Webcam Neutralizer")
        c_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        c_sub = QLabel("Unloads uvcvideo kernel driver at kernel level to disable /dev/video* devices.")
        c_sub.setObjectName("HeaderSubtitle")
        c_info.addWidget(c_lbl)
        c_info.addWidget(c_sub)
        cam_row.addLayout(c_info)
        cam_row.addStretch()

        self.cam_btn = QPushButton("KILL WEBCAM DRIVER")
        self.cam_btn.clicked.connect(self.toggle_cam)
        cam_row.addWidget(self.cam_btn)
        f_layout.addLayout(cam_row)

        f_layout.addWidget(self.create_divider())

        # Mic row
        mic_row = QHBoxLayout()
        m_info = QVBoxLayout()
        m_lbl = QLabel("Hardware Microphone Mute")
        m_lbl.setStyleSheet("font-weight: 600; color: #ffffff;")
        m_sub = QLabel("Zeroes hardware input capture gain in ALSA and PulseAudio/PipeWire.")
        m_sub.setObjectName("HeaderSubtitle")
        m_info.addWidget(m_lbl)
        m_info.addWidget(m_sub)
        mic_row.addLayout(m_info)
        mic_row.addStretch()

        self.mic_btn = QPushButton("MUTE MICROPHONE")
        self.mic_btn.clicked.connect(self.toggle_mic)
        mic_row.addWidget(self.mic_btn)
        f_layout.addLayout(mic_row)

        layout.addWidget(frame)
        layout.addStretch()

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #242429;")
        return line

    def toggle_usb(self):
        self.usb_locked = not self.usb_locked
        HardwareManager.set_usb_lockdown(self.usb_locked)
        if self.usb_locked:
            self.usb_card.set_value("LOCKED")
            self.usb_card.set_pill("ARMED", "SECURE")
            self.usb_btn.setText("UNLOCK USB PORTS")
            self.usb_btn.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.usb_card.set_value("Authorized")
            self.usb_card.set_pill("DEFAULT", "WARN")
            self.usb_btn.setText("LOCKDOWN USB PORTS")
            self.usb_btn.setStyleSheet("")

    def toggle_cam(self):
        self.cam_disabled = not self.cam_disabled
        HardwareManager.set_webcam_state(self.cam_disabled)
        if self.cam_disabled:
            self.cam_card.set_value("DRIVER KILLED")
            self.cam_card.set_pill("SAFE", "SECURE")
            self.cam_btn.setText("RESTORE WEBCAM")
            self.cam_btn.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.cam_card.set_value("Active")
            self.cam_card.set_pill("UNLOCKED", "WARN")
            self.cam_btn.setText("KILL WEBCAM DRIVER")
            self.cam_btn.setStyleSheet("")

    def toggle_mic(self):
        self.mic_muted = not self.mic_muted
        HardwareManager.set_microphone_mute(self.mic_muted)
        if self.mic_muted:
            self.mic_card.set_value("MUTED")
            self.mic_card.set_pill("MUTED", "SECURE")
            self.mic_btn.setText("UNMUTE MICROPHONE")
            self.mic_btn.setStyleSheet("border-color: #00ff66; color: #00ff66;")
        else:
            self.mic_card.set_value("Active")
            self.mic_card.set_pill("UNLOCKED", "WARN")
            self.mic_btn.setText("MUTE MICROPHONE")
            self.mic_btn.setStyleSheet("")

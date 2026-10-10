from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSettings, QSize, Qt, QThread, QTimer, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QKeySequence, QLinearGradient, QPainter, QPen, QShortcut
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QStyledItemDelegate, QStyle, QToolButton, QVBoxLayout, QWidget,
)
from cyberbreak import __version__
from cyberbreak.core.clipboard_guard import ClipboardGuard
from cyberbreak.core.settings_manager import SettingsManager
from cyberbreak.ui.styles import MAIN_STYLESHEET
from cyberbreak.ui.widgets.glass import AppCanvas, icon
from cyberbreak.ui.pages.dashboard_page import DashboardPage
from cyberbreak.ui.pages.leak_page import LeakPage
from cyberbreak.ui.pages.spoofer_page import SpooferPage
from cyberbreak.ui.pages.tor_cover_page import TorCoverPage
from cyberbreak.ui.pages.firewall_page import FirewallPage
from cyberbreak.ui.pages.usbguard_page import USBGuardPage
from cyberbreak.ui.pages.usb_armory_page import USBArmoryPage
from cyberbreak.ui.pages.hardening_page import HardeningPage
from cyberbreak.ui.pages.metadata_page import MetadataPage
from cyberbreak.ui.pages.settings_page import SettingsPage
from cyberbreak.ui.pages.panic_page import PanicPage
from cyberbreak.ui.pages.desktop_page import DesktopPage
from cyberbreak.ui.pages.terminal_page import TerminalPage


TOOLS = (
    ("Overview", "Your network, kernel and hardware at a glance", "grid", DashboardPage),
    ("Network privacy", "Public identity, DNS, IPv6 and routing", "globe", LeakPage),
    ("Device identity", "Network adapters and system identifiers", "layers", SpooferPage),
    ("Tor & traffic", "Circuit inspection and background traffic", "route", TorCoverPage),
    ("Firewall", "Connection profiles and active rules", "shield", FirewallPage),
    ("Hardware & ports", "USB authorization, sensors and sockets", "cpu", USBGuardPage),
    ("USB & storage", "Encrypted vaults, ISO images and backups", "usb", USBArmoryPage),
    ("Kernel hardening", "System parameters and AppArmor profiles", "lock", HardeningPage),
    ("Metadata & files", "File metadata and removal tools", "folder", MetadataPage),
    ("Preferences", "App settings and repository updates", "settings", SettingsPage),
    ("Emergency", "Isolation and emergency controls", "alert", PanicPage),
    ("Desktop", "App shortcuts and session integration", "grid", DesktopPage),
    ("Audit terminal", "A live stream of application activity", "terminal", TerminalPage),
)


class NavigationDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(206, 64 if index.data(Qt.ItemDataRole.UserRole + 1) else 38)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(option.rect).adjusted(1, 1, -1, -1)
        group = index.data(Qt.ItemDataRole.UserRole + 1)
        font = QFont(option.font)
        if group:
            font.setPixelSize(9)
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.setPen(QColor("#7d8aa8"))
            painter.drawText(area.adjusted(12, 0, 0, -38), Qt.AlignmentFlag.AlignVCenter, group)
            area.setTop(area.top() + 26)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected:
            gradient = QLinearGradient(area.topLeft(), area.bottomRight())
            gradient.setColorAt(0, QColor(118, 157, 255, 45))
            gradient.setColorAt(1, QColor(149, 174, 244, 15))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor(169, 194, 255, 45), 1))
            painter.drawRoundedRect(area, 10, 10)
        elif hovered:
            painter.setBrush(QColor(193, 212, 255, 12))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(area, 10, 10)
        row = index.row()
        color = "#becfff" if selected else "#c691a7" if row == 10 else "#8596b9"
        icon(TOOLS[row][2], color, 18).paint(painter, int(area.x() + 12), int(area.center().y() - 9), 18, 18)
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.DemiBold if selected else QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#eef3ff" if selected else "#acbad6"))
        text_area = area.adjusted(42, 0, -18, 0)
        painter.drawText(text_area, Qt.AlignmentFlag.AlignVCenter, painter.fontMetrics().elidedText(index.data(), Qt.TextElideMode.ElideRight, int(text_area.width())))
        if selected:
            painter.setPen(QPen(QColor("#9eb8ff"), 1.5))
            x, y = area.right() - 12, area.center().y()
            painter.drawLine(int(x - 3), int(y - 3), int(x), int(y))
            painter.drawLine(int(x), int(y), int(x - 3), int(y + 3))
        painter.restore()


class PageTransition(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._opacity = 0.0
        self.pixmap = None
        self.animation = QPropertyAnimation(self, b"opacity", self)
        self.animation.setDuration(190)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self.hide)
        self.hide()

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    def reveal(self, pixmap):
        self.animation.stop()
        self.pixmap = pixmap
        self.setGeometry(self.parentWidget().rect())
        self.opacity = 1.0
        self.show()
        self.raise_()
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.start()

    def paintEvent(self, event):
        if self.pixmap is None:
            return
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        painter.drawPixmap(0, 0, self.pixmap)


class CommandPalette(QDialog):
    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("CommandPalette")
        self.setWindowTitle("Find a tool")
        self.setFixedSize(500, 470)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Where would you like to go?")
        self.search.setAccessibleName("Search tools")
        self.search.addAction(icon("search", "#9fb5e6"), QLineEdit.ActionPosition.LeadingPosition)
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.results = QListWidget()
        self.results.setObjectName("CommandResults")
        self.results.setIconSize(QSize(20, 20))
        layout.addWidget(self.results, 1)
        self.empty = QLabel("No matching tools. Try network, storage or settings.")
        self.empty.setObjectName("HeaderSubtitle")
        self.empty.setWordWrap(True)
        layout.addWidget(self.empty)
        hint = QLabel("↑ ↓ to browse    Enter to open    Esc to close")
        hint.setObjectName("Muted")
        layout.addWidget(hint)
        self.search.textChanged.connect(self.filter_tools)
        self.search.returnPressed.connect(self.open_selected)
        self.results.itemActivated.connect(self.open_selected)
        self.results.itemClicked.connect(self.open_selected)
        self._shortcuts = []
        for key, step in (("Down", 1), ("Up", -1)):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda delta=step: self.move_selection(delta))
            self._shortcuts.append(shortcut)
        self.filter_tools("")

    def filter_tools(self, query):
        self.results.clear()
        terms = query.casefold().split()
        for index, (title, description, symbol, _) in enumerate(TOOLS):
            searchable = f"{title} {description}".casefold()
            if all(term in searchable for term in terms):
                item = QListWidgetItem(icon(symbol, "#a7bfff"), title)
                item.setData(Qt.ItemDataRole.UserRole, index)
                item.setToolTip(description)
                self.results.addItem(item)
        self.results.setCurrentRow(0)
        self.empty.setVisible(self.results.count() == 0)

    def move_selection(self, step):
        if self.results.count():
            self.results.setCurrentRow((self.results.currentRow() + step) % self.results.count())

    def open_selected(self, *args):
        item = self.results.currentItem()
        if item:
            self.parentWidget().nav_list.setCurrentRow(item.data(Qt.ItemDataRole.UserRole))
            self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.search.clear()
        parent = self.parentWidget()
        self.move(parent.mapToGlobal(parent.rect().center()) - self.rect().center())
        self.search.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberBreak — Privacy, in your control")
        self.resize(1340, 920)
        self.setMinimumSize(1020, 700)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.preferences = QSettings("CyberBreak", "Interface")
        self.setProperty("reducedMotion", self.preferences.value("reducedMotion", False, type=bool))
        self._closing = False
        self._current_page = -1
        clipboard_seconds = SettingsManager.get("clipboard_wipe_seconds", 30)
        self.clipboard_guard = ClipboardGuard(timeout_seconds=clipboard_seconds if clipboard_seconds in (15, 30, 60, 120) else 30)
        canvas = AppCanvas()
        self.setCentralWidget(canvas)
        root = QHBoxLayout(canvas)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(18)
        self.sidebar = self.build_sidebar()
        root.addWidget(self.sidebar)
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(12)
        content.addWidget(self.build_topbar())
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pages = [None] * len(TOOLS)
        self.scrollers = []
        for _ in TOOLS:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.stack.addWidget(scroll)
            self.scrollers.append(scroll)
        content.addWidget(self.stack, 1)
        self.transition = PageTransition(self.stack)
        footer = QHBoxLayout()
        footer.setContentsMargins(22, 0, 22, 2)
        self.activity_label = QLabel("Ready for a fresh perspective")
        self.activity_label.setObjectName("Muted")
        footer.addWidget(self.activity_label, 1)
        shortcut_hint = QLabel("Ctrl K   Quick navigation")
        shortcut_hint.setObjectName("Muted")
        footer.addWidget(shortcut_hint)
        content.addLayout(footer)
        root.addLayout(content, 1)
        self.palette = CommandPalette(self)
        self.search_button.clicked.connect(self.palette.show)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self.palette.show)
        self.mount_page(12)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        self.nav_list.setCurrentRow(0)
        geometry = self.preferences.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def build_sidebar(self):
        frame = QFrame()
        frame.setObjectName("SidebarFrame")
        frame.setFixedWidth(234)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(13, 24, 13, 18)
        layout.setSpacing(8)
        brand = QHBoxLayout()
        brand.setContentsMargins(10, 0, 6, 0)
        brand.setSpacing(11)
        mark = QLabel()
        mark.setPixmap(icon("shield", "#b2c6ff", 27).pixmap(27, 27))
        mark.setFixedSize(43, 43)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet("background: rgba(140, 170, 255, 24); border: 1px solid rgba(181, 204, 255, 44); border-radius: 14px;")
        brand.addWidget(mark)
        names = QVBoxLayout()
        names.setSpacing(2)
        title = QLabel("CyberBreak")
        title.setObjectName("BrandTitle")
        names.addWidget(title)
        subtitle = QLabel("Privacy. In your control.")
        subtitle.setObjectName("BrandSubtitle")
        names.addWidget(subtitle)
        brand.addLayout(names)
        layout.addLayout(brand)
        layout.addSpacing(18)
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("Sidebar")
        self.nav_list.setMouseTracking(True)
        self.nav_list.setItemDelegate(NavigationDelegate(self.nav_list))
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setSpacing(2)
        groups = {0: "AT A GLANCE", 1: "PROTECTION", 9: "WORKSPACE"}
        for index, (title, description, _, _) in enumerate(TOOLS):
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setData(Qt.ItemDataRole.UserRole + 1, groups.get(index, ""))
            item.setToolTip(description)
            self.nav_list.addItem(item)
        layout.addWidget(self.nav_list, 1)
        local = QFrame()
        local.setObjectName("Card")
        footer = QVBoxLayout(local)
        footer.setContentsMargins(13, 12, 13, 12)
        footer.setSpacing(4)
        caption = QLabel("●  Local workstation")
        caption.setObjectName("StatusText")
        footer.addWidget(caption)
        build = QLabel(f"Built by lilami   ·   v{__version__}")
        build.setObjectName("Muted")
        footer.addWidget(build)
        layout.addWidget(local)
        return frame

    def build_topbar(self):
        frame = QFrame()
        frame.setObjectName("TopBar")
        frame.setFixedHeight(66)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 10, 14, 10)
        layout.setSpacing(14)
        self.breadcrumb = QLabel("Workspace / Overview")
        self.breadcrumb.setObjectName("Breadcrumb")
        layout.addWidget(self.breadcrumb, 1)
        self.search_button = QPushButton("Find a tool…     Ctrl K")
        self.search_button.setObjectName("SearchButton")
        self.search_button.setIcon(icon("search", "#95a4c2", 16))
        self.search_button.setFixedWidth(220)
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.setToolTip("Search all 13 tools (Ctrl+K)")
        layout.addWidget(self.search_button)
        self.motion_button = QToolButton()
        self.motion_button.setObjectName("MotionButton")
        self.motion_button.setIcon(icon("sparkles", "#b1c3ee", 18))
        self.motion_button.setCheckable(True)
        self.motion_button.setChecked(bool(self.property("reducedMotion")))
        self.motion_button.setAccessibleName("Reduce motion")
        self.motion_button.setToolTip("Reduce motion")
        self.motion_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.motion_button.toggled.connect(self.set_reduced_motion)
        layout.addWidget(self.motion_button)
        return frame

    def on_nav_changed(self, index):
        if self._closing or not 0 <= index < len(TOOLS):
            return
        previous = self.stack.currentWidget().grab() if self._current_page >= 0 and not self.property("reducedMotion") and self.isVisible() else None
        self.mount_page(index)
        self.stack.setCurrentIndex(index)
        self._current_page = index
        self.breadcrumb.setText(f"Workspace / {TOOLS[index][0]}")
        if index != 0:
            self.activity_label.setText(TOOLS[index][1])
        if previous is not None:
            self.transition.reveal(previous)
        else:
            self.transition.animation.stop()
            self.transition.hide()

    def mount_page(self, index):
        if self.pages[index] is not None:
            return
        page = TOOLS[index][3]()
        self.pages[index] = page
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 8, 22, 0)
        layout.addWidget(page)
        self.scrollers[index].setWidget(container)
        if index == 0:
            page.audit_started.connect(lambda: self.activity_label.setText("Audit in progress · Reading live system signals"))
            page.audit_completed.connect(self.activity_label.setText)
        elif index == 9:
            page.settings_saved.connect(self.apply_preferences)
        for button in page.findChildren(QPushButton):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        for label in page.findChildren(QLabel):
            if label.objectName() in ("HeaderSubtitle", "HeaderTitle"):
                label.setWordWrap(True)

    def apply_preferences(self, settings):
        interval = settings.get("clipboard_wipe_seconds", 30)
        self.clipboard_guard.timeout_seconds = interval if interval in (15, 30, 60, 120) else 30
        if self.clipboard_guard.timer.isActive():
            self.clipboard_guard.timer.start(self.clipboard_guard.timeout_seconds * 1000)

    def set_reduced_motion(self, enabled):
        self.setProperty("reducedMotion", enabled)
        self.preferences.setValue("reducedMotion", enabled)
        self.motion_button.setToolTip("Reduced motion is on" if enabled else "Reduce motion")
        self.transition.animation.stop()
        self.transition.hide()
        dashboard = self.pages[0]
        if dashboard is not None:
            orb = getattr(dashboard, "orb", None)
            if orb is not None:
                if enabled:
                    orb.timer.stop()
                elif orb.active:
                    orb.timer.start()
        self.activity_label.setText("Reduced motion enabled" if enabled else "Smooth motion enabled")

    def closeEvent(self, event):
        self._closing = True
        self.preferences.setValue("geometry", self.saveGeometry())
        running = []
        for page in self.pages:
            if page is None:
                continue
            for timer in page.findChildren(QTimer):
                timer.stop()
            threads = page.findChildren(QThread) + [value for value in vars(page).values() if isinstance(value, QThread)]
            for thread in threads:
                if thread.isRunning():
                    thread.requestInterruption()
                    running.append(thread)
        if running:
            self._closing = True
            self.setEnabled(False)
            self.activity_label.setText("Finishing active tasks before closing…")
            event.ignore()
            QTimer.singleShot(120, self.close)
        else:
            event.accept()

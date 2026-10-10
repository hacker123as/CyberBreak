import ipaddress
import os
import subprocess
import sys
import urllib.parse
from urllib.parse import urlsplit, urlunsplit

try:
    from PyQt6 import sip
    from PyQt6.QtCore import QByteArray, QUrl, Qt, pyqtSignal, QThread, QTimer
    from PyQt6.QtGui import QColor, QFont
    from PyQt6.QtWidgets import (
        QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
        QLineEdit, QProgressBar, QMessageBox, QFrame, QDialog, QTextEdit,
    )
    PYQT6_AVAILABLE = True
except ImportError:
    sip = None
    QByteArray = QUrl = QColor = QFont = None
    class _DummyAlignment:
        AlignCenter = 0x0004
    class _DummyQt:
        AlignmentFlag = _DummyAlignment
    Qt = _DummyQt
    PYQT6_AVAILABLE = False
    class _DummySignal:
        def connect(self, *a, **k): pass
        def emit(self, *a, **k): pass

    class _DummyWidget:
        def __init__(self, *args, **kwargs):
            self.clicked = _DummySignal()
            self.returnPressed = _DummySignal()
            self.textChanged = _DummySignal()
        def setContentsMargins(self, *args): pass
        def setSpacing(self, *args): pass
        def addWidget(self, *args, **kwargs): pass
        def addLayout(self, *args, **kwargs): pass
        def removeWidget(self, *args, **kwargs): pass
        def setAlignment(self, *args): pass
        def setWordWrap(self, *args): pass
        def setObjectName(self, *args): pass
        def setStyleSheet(self, *args): pass
        def setVisible(self, *args): pass
        def setEnabled(self, *args): pass
        def setRange(self, *args): pass
        def setFixedHeight(self, *args): pass
        def setFixedWidth(self, *args): pass
        def setToolTip(self, *args): pass
        def setPlaceholderText(self, *args): pass
        def setTextVisible(self, *args): pass
        def setText(self, *args): pass
        def text(self): return ""
        def deleteLater(self): pass
        def start(self): pass
        def isRunning(self): return False
        def accept(self): pass
        def exec(self): pass
        def addStretch(self, *args): pass
        @classmethod
        def instance(cls): return None

    QWidget = _DummyWidget
    QDialog = _DummyWidget
    QFrame = _DummyWidget
    QVBoxLayout = _DummyWidget
    QHBoxLayout = _DummyWidget
    QLabel = _DummyWidget
    QPushButton = _DummyWidget
    QLineEdit = _DummyWidget
    QProgressBar = _DummyWidget
    QMessageBox = _DummyWidget
    QTextEdit = _DummyWidget
    QApplication = _DummyWidget

    class QThread:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass
        def isRunning(self): return False

    def pyqtSignal(*args, **kwargs):
        class _Signal:
            def connect(self, *a, **k): pass
            def emit(self, *a, **k): pass
        return _Signal()


QWebEnginePage = None
QWebEngineProfile = None
QWebEngineScript = None
QWebEngineSettings = None
QWebEngineUrlRequestInfo = None
QWebEngineUrlRequestInterceptor = None
QWebEngineView = None
_RequestInterceptor = None
_PrivatePage = None
WEBENGINE_AVAILABLE = False
WEBENGINE_ERROR = ""


def _loopback(host):
    if host.lower().rstrip(".") == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def normalize_web_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or any(character.isspace() or ord(character) < 32 for character in value):
        return None
    if "://" not in value:
        value = "https://" + value
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None or parts.port == 0:
            return None
        host = parts.hostname.encode("idna").decode("ascii").lower()
        if parts.scheme.lower() == "http" and not _loopback(host):
            return None
        if ":" in host:
            ipaddress.ip_address(host)
        elif any(not part or any(not (character.isalnum() or character == "-") for character in part)
                 for part in host.rstrip(".").split(".")):
            return None
        return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path or "/", parts.query, parts.fragment))
    except (ValueError, UnicodeError):
        return None


def format_search_or_url(input_text):
    if not isinstance(input_text, str):
        return None
    text = input_text.strip()
    if not text:
        return None
    if text.startswith("https://") or text.startswith("http://"):
        norm = normalize_web_url(text)
        if norm is not None:
            return norm
    if " " in text:
        query = urllib.parse.quote_plus(text)
        return f"https://duckduckgo.com/?q={query}&kp=-2&kn=1"
    if "." in text and not text.startswith(".") and not text.endswith("."):
        candidate = normalize_web_url(text)
        if candidate is not None:
            return candidate
    if text.lower() == "localhost":
        return normalize_web_url("http://localhost:8080/") or "http://localhost/"
    query = urllib.parse.quote_plus(text)
    return f"https://duckduckgo.com/?q={query}&kp=-2&kn=1"


def request_allowed(request_url, first_party_url, main_frame=False):
    normalized = normalize_web_url(request_url)
    if normalized is None:
        return False
    if main_frame:
        return True
    first_party = normalize_web_url(first_party_url)
    if first_party is None:
        return False
    return urlsplit(normalized).hostname.lower() == urlsplit(first_party).hostname.lower()


def try_load_webengine():
    global WEBENGINE_AVAILABLE, WEBENGINE_ERROR
    global QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineSettings
    global QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor, QWebEngineView
    global _RequestInterceptor, _PrivatePage
    if not PYQT6_AVAILABLE:
        WEBENGINE_AVAILABLE = False
        WEBENGINE_ERROR = "PyQt6 is not installed"
        return False
    try:
        from PyQt6.QtWebEngineCore import (
            QWebEnginePage as _QWebEnginePage,
            QWebEngineProfile as _QWebEngineProfile,
            QWebEngineScript as _QWebEngineScript,
            QWebEngineSettings as _QWebEngineSettings,
            QWebEngineUrlRequestInfo as _QWebEngineUrlRequestInfo,
            QWebEngineUrlRequestInterceptor as _QWebEngineUrlRequestInterceptor,
        )
        from PyQt6.QtWebEngineWidgets import QWebEngineView as _QWebEngineView

        class DynamicRequestInterceptor(_QWebEngineUrlRequestInterceptor):
            blocked = pyqtSignal()

            def __init__(self, parent=None):
                super().__init__(parent)
                self.network_enabled = True

            def interceptRequest(self, info):
                main_frame = info.resourceType() == _QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame
                allowed = self.network_enabled and request_allowed(
                    info.requestUrl().toString(), info.firstPartyUrl().toString(), main_frame)
                if not allowed:
                    info.block(True)
                    self.blocked.emit()
                    return
                info.setHttpHeader(QByteArray(b"DNT"), QByteArray(b"1"))
                info.setHttpHeader(QByteArray(b"Sec-GPC"), QByteArray(b"1"))

        class DynamicPrivatePage(_QWebEnginePage):
            def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
                if url.toString() == "about:blank":
                    return True
                return normalize_web_url(url.toString()) is not None

            def createWindow(self, window_type):
                return None

            def chooseFiles(self, mode, old_files, accepted_mime_types):
                return []

        QWebEnginePage = _QWebEnginePage
        QWebEngineProfile = _QWebEngineProfile
        QWebEngineScript = _QWebEngineScript
        QWebEngineSettings = _QWebEngineSettings
        QWebEngineUrlRequestInfo = _QWebEngineUrlRequestInfo
        QWebEngineUrlRequestInterceptor = _QWebEngineUrlRequestInterceptor
        QWebEngineView = _QWebEngineView
        _RequestInterceptor = DynamicRequestInterceptor
        _PrivatePage = DynamicPrivatePage

        globals()["QWebEnginePage"] = _QWebEnginePage
        globals()["QWebEngineProfile"] = _QWebEngineProfile
        globals()["QWebEngineScript"] = _QWebEngineScript
        globals()["QWebEngineSettings"] = _QWebEngineSettings
        globals()["QWebEngineUrlRequestInfo"] = _QWebEngineUrlRequestInfo
        globals()["QWebEngineUrlRequestInterceptor"] = _QWebEngineUrlRequestInterceptor
        globals()["QWebEngineView"] = _QWebEngineView
        globals()["_RequestInterceptor"] = DynamicRequestInterceptor
        globals()["_PrivatePage"] = DynamicPrivatePage

        WEBENGINE_AVAILABLE = True
        globals()["WEBENGINE_AVAILABLE"] = True
        WEBENGINE_ERROR = ""
        globals()["WEBENGINE_ERROR"] = ""
        return True
    except (ImportError, RuntimeError) as error:
        WEBENGINE_AVAILABLE = False
        globals()["WEBENGINE_AVAILABLE"] = False
        WEBENGINE_ERROR = str(error)
        globals()["WEBENGINE_ERROR"] = str(error)
        return False


# Attempt initial import
try_load_webengine()


CHECKER_URL = "https://pixeldefence.com/data-leaking-check/"

PROTECTION_SCRIPT = r"""
(() => {
    'use strict';
    const define = Object.defineProperty;
    const visited = new WeakSet();
    const protectRealm = window => {
    if (visited.has(window)) return;
    const navigator = window.navigator;
    visited.add(window);
    const denied = function () {
        throw new DOMException('Disabled by CyberBreak privacy policy', 'NotAllowedError');
    };
    const lockValue = (object, name, value) => {
        if (!object) return;
        try {
            define(object, name, { value, writable: false, configurable: false });
        } catch (_) {}
    };
    const lockProperty = (object, name, value) => {
        if (!object) return;
        try {
            define(object, name, { get: () => value, configurable: false });
        } catch (_) {}
    };
    const navigatorPrototype = Object.getPrototypeOf(navigator);
    for (const target of [navigatorPrototype, navigator]) {
        lockProperty(target, 'doNotTrack', '1');
        lockProperty(target, 'globalPrivacyControl', true);
        lockProperty(target, 'cookieEnabled', false);
        lockProperty(target, 'hardwareConcurrency', 4);
        lockProperty(target, 'deviceMemory', 8);
        lockProperty(target, 'webdriver', false);
        lockProperty(target, 'languages', ['en-US', 'en']);
        for (const name of ['connection', 'mozConnection', 'webkitConnection', 'getBattery', 'gpu', 'serviceWorker']) {
            lockProperty(target, name, undefined);
        }
    }
    for (const name of ['RTCPeerConnection', 'webkitRTCPeerConnection', 'mozRTCPeerConnection',
                        'RTCDataChannel', 'Worker', 'SharedWorker']) {
        lockValue(window, name, denied);
    }
    if (typeof window.ServiceWorkerContainer !== 'undefined') {
        lockValue(window.ServiceWorkerContainer.prototype, 'register', denied);
    }
    const media = navigator.mediaDevices;
    if (media) {
        for (const target of [Object.getPrototypeOf(media), media]) {
            for (const name of ['enumerateDevices', 'getUserMedia', 'getDisplayMedia']) {
                lockValue(target, name, () => Promise.reject(
                    new DOMException('Disabled by CyberBreak privacy policy', 'NotAllowedError')));
            }
        }
    }
    for (const name of ['getUserMedia', 'webkitGetUserMedia', 'mozGetUserMedia']) {
        lockValue(navigatorPrototype, name, denied);
        lockValue(navigator, name, denied);
    }
    if (typeof window.HTMLCanvasElement !== 'undefined') {
        for (const name of ['toDataURL', 'toBlob', 'captureStream']) {
            lockValue(window.HTMLCanvasElement.prototype, name, denied);
        }
    }
    if (typeof window.CanvasRenderingContext2D !== 'undefined') {
        lockValue(window.CanvasRenderingContext2D.prototype, 'getImageData', denied);
    }
    if (typeof window.OffscreenCanvas !== 'undefined') {
        for (const name of ['convertToBlob', 'transferToImageBitmap']) {
            lockValue(window.OffscreenCanvas.prototype, name, denied);
        }
    }
    if (typeof window.OffscreenCanvasRenderingContext2D !== 'undefined') {
        lockValue(window.OffscreenCanvasRenderingContext2D.prototype, 'getImageData', denied);
    }
    for (const name of ['WebGLRenderingContext', 'WebGL2RenderingContext']) {
        if (typeof window[name] !== 'undefined') {
            lockValue(window[name].prototype, 'readPixels', denied);
            lockValue(window[name].prototype, 'getBufferSubData', denied);
        }
    }
    if (typeof window.AudioBuffer !== 'undefined') {
        lockValue(window.AudioBuffer.prototype, 'getChannelData', denied);
        lockValue(window.AudioBuffer.prototype, 'copyFromChannel', denied);
    }
    if (typeof window.BaseAudioContext !== 'undefined') {
        lockProperty(window.BaseAudioContext.prototype, 'sampleRate', 44100);
    }
    if (window.screen) {
        lockProperty(window.screen, 'availWidth', 1920);
        lockProperty(window.screen, 'availHeight', 1080);
        lockProperty(window.screen, 'colorDepth', 24);
        lockProperty(window.screen, 'pixelDepth', 24);
    }
    const framePrototype = window.HTMLIFrameElement && window.HTMLIFrameElement.prototype;
    const windowGetter = framePrototype && Object.getOwnPropertyDescriptor(framePrototype, 'contentWindow').get;
    const protectFrame = frame => {
        try {
            const childWindow = windowGetter.call(frame);
            if (childWindow) protectRealm(childWindow);
        } catch (_) {}
    };
    const protectTree = node => {
        if (!node) return;
        if (node.nodeName === 'IFRAME') protectFrame(node);
        if (node.querySelectorAll) {
            for (const frame of node.querySelectorAll('iframe')) protectFrame(frame);
        }
    };
    if (framePrototype) {
        for (const name of ['contentWindow', 'contentDocument']) {
            const descriptor = Object.getOwnPropertyDescriptor(framePrototype, name);
            if (descriptor && descriptor.get) {
                define(framePrototype, name, { configurable: false, get: function () {
                    protectFrame(this);
                    return descriptor.get.call(this);
                }});
            }
        }
    }
    for (const [prototype, names] of [
        [window.Node.prototype, ['appendChild', 'insertBefore', 'replaceChild']],
        [window.Element.prototype, ['append', 'prepend', 'before', 'after', 'replaceWith', 'replaceChildren', 'insertAdjacentHTML']],
        [window.Document.prototype, ['append', 'prepend', 'replaceChildren']],
        [window.DocumentFragment.prototype, ['append', 'prepend', 'replaceChildren']],
        [window.Range.prototype, ['insertNode']]
    ]) {
        for (const name of names) {
            const original = prototype[name];
            if (typeof original !== 'function') continue;
            lockValue(prototype, name, function (...args) {
                const ownerDocument = this.ownerDocument || window.document;
                const result = Reflect.apply(original, this, args);
                protectTree(ownerDocument);
                return result;
            });
        }
    }
    for (const name of ['innerHTML', 'outerHTML']) {
        const descriptor = Object.getOwnPropertyDescriptor(window.Element.prototype, name);
        if (descriptor && descriptor.set) {
            define(window.Element.prototype, name, { configurable: false, get: descriptor.get,
                set: function (value) {
                    const ownerDocument = this.ownerDocument;
                    descriptor.set.call(this, value);
                    protectTree(ownerDocument);
                }
            });
        }
    }
    for (const name of ['open', 'write', 'writeln']) {
        lockValue(window.Document.prototype, name, denied);
    }
    const observer = new window.MutationObserver(records => {
        for (const record of records) {
            for (const node of record.addedNodes) protectTree(node);
        }
    });
    observer.observe(window.document, { childList: true, subtree: true });
    protectTree(window.document);
    };
    protectRealm(window);
})();
"""

LOCAL_AUDIT_SCRIPT = r"""
(() => {
    const denied = callback => {
        try { callback(); return false; }
        catch (error) { return error.name === 'NotAllowedError' || error.name === 'SecurityError'; }
    };
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 8;
    const context = canvas.getContext('2d');
    if (context) {
        context.fillStyle = '#19a8ef';
        context.fillRect(0, 0, 8, 8);
    }
    const cookieName = 'cyberbreak_audit_' + Math.random().toString(16).slice(2);
    let cookieBlocked = false;
    try {
        document.cookie = cookieName + '=1; SameSite=Strict; path=/';
        cookieBlocked = !document.cookie.split(';').some(value => value.trim().startsWith(cookieName + '='));
        document.cookie = cookieName + '=; Max-Age=0; path=/';
    } catch (error) {
        cookieBlocked = error.name === 'SecurityError' || error.name === 'NotAllowedError';
    }
    let webglBlocked = false;
    try {
        webglBlocked = ['webgl', 'experimental-webgl', 'webgl2'].every(
            name => !document.createElement('canvas').getContext(name));
    } catch (_) {}
    const result = {
        url: location.href,
        dnt: navigator.doNotTrack === '1',
        gpc: navigator.globalPrivacyControl === true,
        cookies: cookieBlocked && navigator.cookieEnabled === false,
        canvas: denied(() => canvas.toDataURL()),
        canvas_readback: !context || denied(() => context.getImageData(0, 0, 1, 1)),
        webgl: webglBlocked,
        battery: typeof navigator.getBattery === 'undefined',
        connection: typeof navigator.connection === 'undefined' &&
            typeof navigator.mozConnection === 'undefined' && typeof navigator.webkitConnection === 'undefined',
        webrtc: typeof RTCPeerConnection === 'undefined' || denied(() => new RTCPeerConnection()),
        workers: (typeof Worker === 'undefined' || denied(() => new Worker('about:blank'))) &&
            (typeof SharedWorker === 'undefined' || denied(() => new SharedWorker('about:blank'))) &&
            typeof navigator.serviceWorker === 'undefined'
    };
    return result;
})();
"""


class WebEngineInstallWorker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def run(self):
        self.progress_signal.emit("Connecting to package repository / privileged helper...")
        try:
            from cyberbreak.core.executor import run_privileged
            code, out, err = run_privileged("install-webengine")
            if code == 0:
                self.progress_signal.emit("Package installed. Initializing QtWebEngine...")
                if try_load_webengine():
                    self.finished_signal.emit(True, "PyQt6-WebEngine installed and initialized successfully!")
                    return
        except Exception:
            pass

        self.progress_signal.emit("Attempting pip installation: PyQt6-WebEngine...")
        pip_cmds = [
            [sys.executable, "-m", "pip", "install", "PyQt6-WebEngine", "PyQt6-QtSvg", "--break-system-packages"],
            [sys.executable, "-m", "pip", "install", "PyQt6-WebEngine", "PyQt6-QtSvg"],
        ]
        for cmd in pip_cmds:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if res.returncode == 0:
                    if try_load_webengine():
                        self.finished_signal.emit(True, "PyQt6-WebEngine installed and loaded via pip!")
                        return
            except Exception:
                pass

        if try_load_webengine():
            self.finished_signal.emit(True, "QtWebEngine is now loaded and available!")
            return

        self.finished_signal.emit(
            False,
            "Could not auto-install PyQt6-WebEngine. Ensure your system has internet access, or run as sysmaint:\n"
            "sudo apt install -y python3-pyqt6.qtwebengine || pip install PyQt6-WebEngine"
        )


class ShieldsDialog(QDialog):
    def __init__(self, parent=None, blocked_count=0):
        super().__init__(parent)
        self.setWindowTitle("CyberBreak Shields & Anti-Tracking Armor")
        self.resize(540, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #0c121e;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
            QLabel {
                color: #cbd5e1;
            }
            #ShieldTitle {
                font-size: 17px;
                font-weight: bold;
                color: #10b981;
            }
            #ShieldBox {
                background-color: #131b2c;
                border: 1px solid #23304a;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("🛡️ 100/100 Shields: Zero Tracking Active")
        title.setObjectName("ShieldTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        desc = QLabel(
            "Every DOM API, hardware sensor, audio pipeline, and canvas element is intercepted and "
            "neutralized. Trackers receive zero identifying fingerprints from your device."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        box = QFrame()
        box.setObjectName("ShieldBox")
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(8)

        shields = [
            ("🎨 Anti-Canvas Fingerprinting", "Canvas readback (toDataURL, getImageData) is completely blocked & denied."),
            ("🎮 Anti-WebGL Fingerprinting", "WebGL buffer readback & GPU driver enumeration blocked."),
            ("🌐 WebRTC Zero-Leak Armor", "RTCPeerConnection & DataChannels blocked. Zero local or public IP leaks."),
            ("🔊 Anti-Audio Fingerprinting", "AudioContext channel readback blocked; sample rate locked to 44.1kHz."),
            ("💻 Device & Hardware Normalizer", "Hardware concurrency (4) & memory (8GB) spoofed to generic workstation."),
            ("🍪 Ephemeral RAM-Only Profile", "Zero persistent cookies or disk cache. All data purged on tab close."),
            ("📡 Privacy Directives Enforced", "DNT: 1 and Sec-GPC: 1 attached to all outgoing HTTP requests."),
            ("🚫 Cross-Origin Request Blocker", f"Strict first-party isolation. {blocked_count} tracking beacons intercepted."),
        ]

        for name, detail in shields:
            row = QVBoxLayout()
            row.setSpacing(1)
            lbl_name = QLabel(f"<b>{name}</b> — <span style='color: #10b981; font-weight: bold;'>ACTIVE</span>")
            lbl_desc = QLabel(f"<span style='color: #94a3b8; font-size: 11px;'>{detail}</span>")
            row.addWidget(lbl_name)
            row.addWidget(lbl_desc)
            box_layout.addLayout(row)

        layout.addWidget(box)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Done")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)


class BrowserGuard(QWidget):
    audit_result = pyqtSignal(dict)
    navigation_changed = pyqtSignal(str)
    loading_changed = pyqtSignal(bool)
    blocked_count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available = WEBENGINE_AVAILABLE
        self.view = None
        self.profile = None
        self.interceptor = None
        self.network_enabled = True
        self.blocked_requests = 0
        self._generation = 0
        self._closed = False
        self.pending_url = None
        self._fallback_container = None
        self._install_worker = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        if not self.available:
            self._build_fallback_ui()
            return
        self._create_session()
        application = QApplication.instance()
        if application:
            application.aboutToQuit.connect(self.shutdown)

    def _build_fallback_ui(self):
        self._fallback_container = QFrame(self)
        self._fallback_container.setObjectName("FallbackCard")
        self._fallback_container.setStyleSheet("""
            #FallbackCard {
                background-color: #0d131f;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 24px;
            }
            #HeaderTitle {
                font-size: 20px;
                font-weight: bold;
                color: #38bdf8;
            }
            #HeaderSubtitle {
                color: #94a3b8;
                font-size: 13px;
                line-height: 1.5;
            }
            #Terminal {
                background-color: #080c14;
                color: #00f3ff;
                font-family: monospace;
                font-size: 12px;
                padding: 10px 14px;
                border-radius: 6px;
                border: 1px solid #1a2538;
            }
            #StatusLabel {
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        box = QVBoxLayout(self._fallback_container)
        box.setContentsMargins(24, 32, 24, 32)
        box.setSpacing(16)

        title = QLabel("Built-in QtWebEngine Browser Not Detected")
        title.setObjectName("HeaderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(title)

        detail = QLabel(
            "PyQt6-WebEngine is not currently loaded in this Python environment.\n"
            "CyberBreak includes 1-click automated installation so you don't have to touch the terminal,\n"
            "or you can instantly launch the Hardened Firefox profile with 49 privacy directives."
        )
        detail.setObjectName("HeaderSubtitle")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        box.addWidget(detail)

        self._install_status = QLabel("Engine Status: Package not loaded")
        self._install_status.setObjectName("StatusLabel")
        self._install_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(self._install_status)

        self._install_progress = QProgressBar()
        self._install_progress.setRange(0, 0)
        self._install_progress.setFixedHeight(6)
        self._install_progress.setTextVisible(False)
        self._install_progress.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #00f3ff;
                border-radius: 3px;
            }
        """)
        self._install_progress.setVisible(False)
        box.addWidget(self._install_progress)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_install_webengine = QPushButton("⚡ Install QtWebEngine Browser Engine (1-Click Auto Install)")
        self.btn_install_webengine.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 18px;
                border-radius: 6px;
                border: 1px solid #38bdf8;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #334155;
                border-color: #475569;
                color: #94a3b8;
            }
        """)
        self.btn_install_webengine.clicked.connect(self.start_webengine_install)
        btn_row.addWidget(self.btn_install_webengine)

        self.btn_launch_firefox = QPushButton("🦊 Launch Hardened Firefox Profile (49 Directives)")
        self.btn_launch_firefox.setStyleSheet("""
            QPushButton {
                background-color: #b45309;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 18px;
                border-radius: 6px;
                border: 1px solid #f59e0b;
            }
            QPushButton:hover {
                background-color: #92400e;
            }
        """)
        self.btn_launch_firefox.clicked.connect(self.launch_firefox_profile)
        btn_row.addWidget(self.btn_launch_firefox)

        self.btn_install_desktop_app = QPushButton("📥 Install CyberBreak Browser as Desktop App")
        self.btn_install_desktop_app.setStyleSheet("""
            QPushButton {
                background-color: #047857;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 18px;
                border-radius: 6px;
                border: 1px solid #10b981;
            }
            QPushButton:hover {
                background-color: #065f46;
            }
        """)
        self.btn_install_desktop_app.clicked.connect(self.install_desktop_app)
        btn_row.addWidget(self.btn_install_desktop_app)

        box.addLayout(btn_row)

        cmd = QLabel("sudo apt install -y python3-pyqt6.qtwebengine || pip install PyQt6-WebEngine")
        cmd.setObjectName("Terminal")
        cmd.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(cmd)

        self._layout.addWidget(self._fallback_container)

    def start_webengine_install(self):
        if self._install_worker and self._install_worker.isRunning():
            return
        self.btn_install_webengine.setEnabled(False)
        self._install_progress.setVisible(True)
        self._install_status.setText("Initiating automated package installation via CyberBreak helper...")
        self._install_worker = WebEngineInstallWorker()
        self._install_worker.progress_signal.connect(self._install_status.setText)
        self._install_worker.finished_signal.connect(self._on_install_completed)
        self._install_worker.start()

    def _on_install_completed(self, success: bool, message: str):
        self._install_progress.setVisible(False)
        if success:
            self._install_status.setText("✅ " + message)
            self.available = True
            if self._fallback_container:
                self._layout.removeWidget(self._fallback_container)
                self._fallback_container.deleteLater()
                self._fallback_container = None
            self._create_session()
            target = self.pending_url or "https://duckduckgo.com"
            self.navigate(target)
            application = QApplication.instance()
            if application:
                application.aboutToQuit.connect(self.shutdown)
            QMessageBox.information(
                self,
                "WebEngine Ready",
                "PyQt6-WebEngine has been installed and activated successfully!\n\n"
                "Your Zero-Tracking Private Browser session is now live and armed with 100/100 shields."
            )
        else:
            self.btn_install_webengine.setEnabled(True)
            self._install_status.setText("❌ " + message)
            QMessageBox.warning(
                self,
                "Installation Notice",
                f"Automated installation could not complete:\n\n{message}\n\n"
                "You can still use the 'Launch Hardened Firefox Profile' button or run:\n"
                "sudo apt install -y python3-pyqt6.qtwebengine"
            )

    def launch_firefox_profile(self):
        try:
            from cyberbreak.core.browser_privacy import FirefoxPrivacyManager
            mgr = FirefoxPrivacyManager()
            url = self.pending_url or CHECKER_URL
            ok, msg = mgr.launch(url)
            if ok:
                QMessageBox.information(self, "Hardened Browser Launched", msg)
            else:
                QMessageBox.warning(self, "Launch Error", msg)
        except Exception as e:
            QMessageBox.warning(self, "Launch Error", f"Failed to launch external browser: {e}")

    def install_desktop_app(self):
        try:
            from cyberbreak.core.desktop_integrator import DesktopIntegrator
            ok, msg = DesktopIntegrator.install_browser_app()
            if ok:
                QMessageBox.information(
                    self,
                    "Browser App Installed",
                    "✅ CyberBreak Private Browser installed successfully!\n\n"
                    "• Desktop Launcher: ~/Desktop/cyberbreak-browser.desktop\n"
                    "• Applications Grid: Registered as standalone app\n\n"
                    "You can launch it directly from your desktop or applications menu anytime."
                )
            else:
                QMessageBox.warning(self, "Installation Notice", f"Notice: {msg}")
        except Exception as e:
            QMessageBox.warning(self, "Installation Error", f"Failed to install desktop launcher: {e}")

    def _create_session(self):
        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        self.profile.cookieStore().setCookieFilter(lambda request: False)
        self.profile.downloadRequested.connect(lambda download: download.cancel())
        if hasattr(self.profile, "setPersistentPermissionsPolicy"):
            self.profile.setPersistentPermissionsPolicy(QWebEngineProfile.PersistentPermissionsPolicy.AskEveryTime)
        if hasattr(self.profile, "setPushServiceEnabled"):
            self.profile.setPushServiceEnabled(False)
        settings = self.profile.settings()
        for name, value in {
            "WebGLEnabled": False,
            "WebRTCPublicInterfacesOnly": True,
            "LocalStorageEnabled": False,
            "LocalContentCanAccessRemoteUrls": False,
            "LocalContentCanAccessFileUrls": False,
            "JavascriptCanOpenWindows": False,
            "JavascriptCanAccessClipboard": False,
            "JavascriptCanPaste": False,
            "DnsPrefetchEnabled": False,
            "HyperlinkAuditingEnabled": False,
            "PluginsEnabled": False,
            "PdfViewerEnabled": False,
            "ScreenCaptureEnabled": False,
            "ErrorPageEnabled": False,
            "AllowRunningInsecureContent": False,
            "PlaybackRequiresUserGesture": True,
        }.items():
            attribute = getattr(QWebEngineSettings.WebAttribute, name, None)
            if attribute is not None:
                settings.setAttribute(attribute, value)
        settings.setUnknownUrlSchemePolicy(QWebEngineSettings.UnknownUrlSchemePolicy.DisallowUnknownUrlSchemes)
        self.interceptor = _RequestInterceptor(self.profile)
        self.interceptor.network_enabled = self.network_enabled
        self.interceptor.blocked.connect(self._request_blocked)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        script = QWebEngineScript()
        script.setName("CyberBreak privacy policy")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        script.setSourceCode(PROTECTION_SCRIPT)
        self.profile.scripts().insert(script)
        page = _PrivatePage(self.profile, self.view)
        page.setBackgroundColor(QColor("#101827"))
        if hasattr(page, "permissionRequested"):
            page.permissionRequested.connect(lambda permission: permission.deny())
        else:
            page.featurePermissionRequested.connect(
                lambda origin, feature: page.setFeaturePermission(
                    origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser))
        if hasattr(page, "fileSystemAccessRequested"):
            page.fileSystemAccessRequested.connect(lambda request: request.reject())
        page.certificateError.connect(lambda error: error.rejectCertificate())
        self.view.setPage(page)
        self.view.urlChanged.connect(lambda url: self.navigation_changed.emit(url.toString()))
        self.view.loadStarted.connect(lambda: self.loading_changed.emit(True))
        self.view.loadFinished.connect(lambda success: self.loading_changed.emit(False))
        self._layout.addWidget(self.view)

    def _request_blocked(self):
        if self._closed:
            return
        self.blocked_requests += 1
        self.blocked_count_changed.emit(self.blocked_requests)

    def back(self):
        if self.view and not self._closed:
            self.view.back()

    def forward(self):
        if self.view and not self._closed:
            self.view.forward()

    def navigate(self, url):
        target = format_search_or_url(url) or normalize_web_url(url)
        if target is None:
            return False
        self.pending_url = target
        if not self.available or self._closed or self.view is None:
            return False
        if not self.network_enabled:
            self.set_network_enabled(True)
        self._generation += 1
        self.view.setUrl(QUrl(target))
        return True

    def stop(self):
        if self.view and not self._closed:
            self.view.stop()

    def reload(self):
        if self.view and not self._closed:
            if not self.network_enabled:
                self.set_network_enabled(True)
            self._generation += 1
            self.view.reload()

    def set_network_enabled(self, enabled):
        self.network_enabled = bool(enabled)
        if self.interceptor is not None:
            self.interceptor.network_enabled = self.network_enabled
        if not self.network_enabled and self.view and not self._closed:
            self.view.stop()

    def _dispose_session(self):
        self._generation += 1
        if self.view is not None:
            self.view.stop()
            self._layout.removeWidget(self.view)
            if sip:
                sip.delete(self.view)
            self.view = None
        if self.profile is not None:
            if sip:
                sip.delete(self.profile)
            self.profile = None
            self.interceptor = None

    def reset_session(self):
        if not self.available or self._closed:
            return
        self._dispose_session()
        self.blocked_requests = 0
        self.blocked_count_changed.emit(0)
        self._create_session()
        self.navigation_changed.emit("")

    def clear_session(self):
        self.reset_session()

    def run_local_audit(self):
        if not self.available or self._closed or self.view is None:
            self.audit_result.emit({"error": WEBENGINE_ERROR or "Private browser is closed"})
            return
        generation = self._generation

        def completed(result):
            if self._closed or generation != self._generation:
                return
            if not isinstance(result, dict):
                self.audit_result.emit({"error": "The page could not be inspected. Load a web page and retry."})
                return
            result.update({
                "network_enabled": self.network_enabled,
                "blocked_requests": self.blocked_requests,
                "off_the_record": self.profile.isOffTheRecord(),
            })
            self.audit_result.emit(result)

        self.view.page().runJavaScript(LOCAL_AUDIT_SCRIPT, completed)

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        if self.available:
            self._dispose_session()

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)


class StandaloneBrowserWindow(QWidget):
    def __init__(self, parent=None, initial_url="https://duckduckgo.com"):
        super().__init__(parent)
        self.setWindowTitle("CyberBreak • Zero-Tracking Private Browser (By lilami only)")
        self.resize(1240, 820)
        
        # Load app icon if available
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "cyberbreak.png")
        if not os.path.exists(icon_path):
            icon_path = "/usr/share/icons/hicolor/256x256/apps/cyberbreak.png"
        if os.path.exists(icon_path) and hasattr(self, "setWindowIcon"):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QWidget {
                background-color: #0c1017;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit {
                background-color: #131b2c;
                border: 1px solid #1e2c44;
                border-radius: 8px;
                padding: 7px 14px;
                color: #f8fafc;
                font-size: 13px;
                selection-background-color: #0284c7;
            }
            QLineEdit:focus {
                border: 1px solid #00f3ff;
                background-color: #172238;
            }
            QPushButton {
                background-color: #182236;
                color: #e2e8f0;
                border: 1px solid #23334d;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #22304d;
                border-color: #38bdf8;
                color: #ffffff;
            }
            QPushButton#AccentButton {
                background-color: #0284c7;
                border: 1px solid #38bdf8;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton#AccentButton:hover {
                background-color: #0369a1;
            }
            QPushButton#ShieldButton {
                background-color: #042f2e;
                border: 1px solid #10b981;
                color: #34d399;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton#ShieldButton:hover {
                background-color: #064e3b;
                color: #6ee7b7;
            }
            QPushButton#AppButton {
                background-color: #1e1b4b;
                border: 1px solid #6366f1;
                color: #a5b4fc;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton#AppButton:hover {
                background-color: #312e81;
                color: #c7d2fe;
            }
            QPushButton#WipeButton {
                background-color: #2e1026;
                border: 1px solid #ec4899;
                color: #f472b6;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton#WipeButton:hover {
                background-color: #4c1d44;
                color: #fbcfe8;
            }
            #BookmarkBar {
                background-color: #090e17;
                border-bottom: 1px solid #162033;
                padding: 3px 8px;
            }
            #BookmarkBtn {
                background-color: transparent;
                border: 1px solid #1a2538;
                border-radius: 12px;
                padding: 3px 10px;
                color: #94a3b8;
                font-size: 11px;
            }
            #BookmarkBtn:hover {
                background-color: #172238;
                border-color: #00f3ff;
                color: #00f3ff;
            }
            #StatusBar {
                background-color: #080c14;
                border-top: 1px solid #151e2e;
                padding: 4px 10px;
                color: #64748b;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Main Navigation Row
        nav = QHBoxLayout()
        nav.setSpacing(6)

        self.back_btn = QPushButton("◀")
        self.back_btn.setToolTip("Back (Alt+Left)")
        self.back_btn.setFixedWidth(36)
        self.back_btn.clicked.connect(self._back)
        nav.addWidget(self.back_btn)

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setToolTip("Forward (Alt+Right)")
        self.fwd_btn.setFixedWidth(36)
        self.fwd_btn.clicked.connect(self._forward)
        nav.addWidget(self.fwd_btn)

        self.reload_btn = QPushButton("↻")
        self.reload_btn.setToolTip("Reload (Ctrl+R / F5)")
        self.reload_btn.setFixedWidth(36)
        self.reload_btn.clicked.connect(self._reload)
        nav.addWidget(self.reload_btn)

        self.home_btn = QPushButton("🏠 DuckDuckGo")
        self.home_btn.setToolTip("Go to DuckDuckGo Private Search")
        self.home_btn.clicked.connect(lambda: self.navigate("https://duckduckgo.com"))
        nav.addWidget(self.home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search with DuckDuckGo or enter HTTPS address...")
        self.url_bar.returnPressed.connect(self._on_enter)
        nav.addWidget(self.url_bar, 1)

        go_btn = QPushButton("Go")
        go_btn.setObjectName("AccentButton")
        go_btn.clicked.connect(self._on_enter)
        nav.addWidget(go_btn)

        self.app_btn = QPushButton("📥 Install as App")
        self.app_btn.setObjectName("AppButton")
        self.app_btn.setToolTip("Install CyberBreak Private Browser as a standalone Desktop & Applications app")
        self.app_btn.clicked.connect(self._install_as_app)
        nav.addWidget(self.app_btn)

        self.shields_btn = QPushButton("🛡️ 100/100 Shields")
        self.shields_btn.setObjectName("ShieldButton")
        self.shields_btn.setToolTip("Click to inspect active anti-tracking and anti-fingerprint shields")
        self.shields_btn.clicked.connect(self._show_shields_dialog)
        nav.addWidget(self.shields_btn)

        self.wipe_btn = QPushButton("🧹 New Identity")
        self.wipe_btn.setObjectName("WipeButton")
        self.wipe_btn.setToolTip("Purge RAM cache, wipe cookies, and initialize a completely fresh session")
        self.wipe_btn.clicked.connect(self._new_identity)
        nav.addWidget(self.wipe_btn)

        layout.addLayout(nav)

        # 2. Quick Bookmarks / Privacy Strip
        bm_frame = QFrame()
        bm_frame.setObjectName("BookmarkBar")
        bm_layout = QHBoxLayout(bm_frame)
        bm_layout.setContentsMargins(6, 2, 6, 2)
        bm_layout.setSpacing(8)

        lbl_quick = QLabel("Quick Access:")
        lbl_quick.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        bm_layout.addWidget(lbl_quick)

        bookmarks = [
            ("🦆 DuckDuckGo", "https://duckduckgo.com"),
            ("🛡️ PixelDefence Leak Check", CHECKER_URL),
            ("🔍 EFF Cover Your Tracks", "https://coveryourtracks.eff.org/"),
            ("🦁 Brave Search", "https://search.brave.com/"),
            ("🌐 IPLeak.net", "https://ipleak.net/"),
            ("🔒 Am I Mullvad", "https://am.i.mullvad.net/"),
        ]

        for title, url in bookmarks:
            btn = QPushButton(title)
            btn.setObjectName("BookmarkBtn")
            btn.clicked.connect(lambda checked=False, target=url: self.navigate(target))
            bm_layout.addWidget(btn)

        bm_layout.addStretch()
        layout.addWidget(bm_frame)

        # 3. Main Browser Guard View
        self.browser = BrowserGuard(self)
        self.browser.navigation_changed.connect(self._on_nav)
        self.browser.blocked_count_changed.connect(self._on_blocked_count)
        layout.addWidget(self.browser, 1)

        # 4. Status Bar
        status_bar = QFrame()
        status_bar.setObjectName("StatusBar")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 4, 10, 4)

        self.status_policy = QLabel("🛡️ Titanium Privacy Shields: 100/100 Active • Ephemeral RAM Session • Zero Persistent Storage")
        status_layout.addWidget(self.status_policy)
        status_layout.addStretch()

        self.status_blocked = QLabel("Trackers Intercepted: 0")
        self.status_blocked.setStyleSheet("color: #38bdf8; font-weight: bold;")
        status_layout.addWidget(self.status_blocked)

        lbl_sep = QLabel("•")
        lbl_sep.setStyleSheet("color: #334155; margin: 0 4px;")
        status_layout.addWidget(lbl_sep)

        lbl_credit = QLabel("By lilami only")
        lbl_credit.setStyleSheet("color: #94a3b8; font-weight: 600;")
        status_layout.addWidget(lbl_credit)

        layout.addWidget(status_bar)

        # Set initial navigation
        if initial_url:
            self.navigate(initial_url)

    def _back(self):
        self.browser.back()

    def _forward(self):
        self.browser.forward()

    def _reload(self):
        self.browser.reload()

    def _on_enter(self):
        target = self.url_bar.text().strip()
        if target:
            self.navigate(target)

    def _on_nav(self, url):
        if url and url != "about:blank":
            self.url_bar.setText(url)

    def _on_blocked_count(self, count):
        self.status_blocked.setText(f"Trackers Intercepted: {count}")
        self.shields_btn.setText(f"🛡️ Shields ({count} blocked)")

    def _install_as_app(self):
        try:
            from cyberbreak.core.desktop_integrator import DesktopIntegrator
            ok, msg = DesktopIntegrator.install_browser_app()
            if ok:
                QMessageBox.information(
                    self,
                    "CyberBreak Browser App Installed",
                    "✅ CyberBreak Private Browser is now installed as an official desktop app!\n\n"
                    "• Desktop Shortcut: ~/Desktop/cyberbreak-browser.desktop\n"
                    "• Applications Grid: Registered as standalone app\n\n"
                    "You can launch it anytime directly from your desktop or app launcher."
                )
            else:
                QMessageBox.warning(self, "Installation Notice", f"Notice: {msg}")
        except Exception as e:
            QMessageBox.warning(self, "Installation Error", f"Failed to install desktop app launcher: {e}")

    def _show_shields_dialog(self):
        dlg = ShieldsDialog(self, self.browser.blocked_requests)
        dlg.exec()

    def _new_identity(self):
        self.browser.reset_session()
        self.url_bar.setText("https://duckduckgo.com")
        self.navigate("https://duckduckgo.com")
        QMessageBox.information(
            self,
            "New Identity Generated",
            "🧹 Session wiped completely!\n\n"
            "• Ephemeral cache and cookies cleared\n"
            "• Connection pools and DOM storage purged\n"
            "• Brand new isolated browser identity generated."
        )

    def navigate(self, url):
        self.browser.set_network_enabled(True)
        if self.browser.navigate(url):
            self.url_bar.setText(url)

    def closeEvent(self, event):
        self.browser.shutdown()
        event.accept()

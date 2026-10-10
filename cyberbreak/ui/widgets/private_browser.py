import ipaddress
import urllib.parse
from urllib.parse import urlsplit, urlunsplit

try:
    from PyQt6 import sip
    from PyQt6.QtCore import QByteArray, QUrl, Qt, pyqtSignal
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLineEdit
    PYQT6_AVAILABLE = True
except ImportError:
    sip = None
    QByteArray = QUrl = Qt = QColor = QApplication = QLabel = QVBoxLayout = None
    QHBoxLayout = QPushButton = QLineEdit = None
    PYQT6_AVAILABLE = False
    class QWidget:
        def __init__(self, *args, **kwargs): pass
    def pyqtSignal(*args, **kwargs):
        class _Signal:
            def connect(self, *a, **k): pass
            def emit(self, *a, **k): pass
        return _Signal()

try:
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 is not installed")
    from PyQt6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineScript,
        QWebEngineSettings,
        QWebEngineUrlRequestInfo,
        QWebEngineUrlRequestInterceptor,
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
    WEBENGINE_ERROR = ""
except (ImportError, RuntimeError) as error:
    WEBENGINE_AVAILABLE = False
    WEBENGINE_ERROR = str(error)


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


if WEBENGINE_AVAILABLE:
    class _RequestInterceptor(QWebEngineUrlRequestInterceptor):
        blocked = pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self.network_enabled = True

        def interceptRequest(self, info):
            main_frame = info.resourceType() == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame
            allowed = self.network_enabled and request_allowed(
                info.requestUrl().toString(), info.firstPartyUrl().toString(), main_frame)
            if not allowed:
                info.block(True)
                self.blocked.emit()
                return
            info.setHttpHeader(QByteArray(b"DNT"), QByteArray(b"1"))
            info.setHttpHeader(QByteArray(b"Sec-GPC"), QByteArray(b"1"))


    class _PrivatePage(QWebEnginePage):
        def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
            if url.toString() == "about:blank":
                return True
            return normalize_web_url(url.toString()) is not None

        def createWindow(self, window_type):
            return None

        def chooseFiles(self, mode, old_files, accepted_mime_types):
            return []


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
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        if not self.available:
            box = QVBoxLayout()
            box.setContentsMargins(20, 40, 20, 40)
            box.setSpacing(12)
            title = QLabel("Built-in QtWebEngine Not Detected")
            title.setObjectName("HeaderTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(title)
            detail = QLabel(
                "PyQt6-WebEngine is not currently loaded in this Python environment.\n"
                "You can launch the Hardened Firefox / External Browser profile with 49 privacy directives,\n"
                "or install PyQt6-WebEngine using the terminal command below."
            )
            detail.setObjectName("HeaderSubtitle")
            detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail.setWordWrap(True)
            box.addWidget(detail)
            cmd = QLabel("sudo apt install -y python3-pyqt6.qtwebengine || pip install PyQt6-WebEngine")
            cmd.setObjectName("Terminal")
            cmd.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(cmd)
            self._layout.addLayout(box)
            return
        self._create_session()
        application = QApplication.instance()
        if application:
            application.aboutToQuit.connect(self.shutdown)

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
        if not self.available or self._closed or target is None:
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
            sip.delete(self.view)
            self.view = None
        if self.profile is not None:
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
        self.resize(1180, 780)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        nav = QHBoxLayout()
        self.back_btn = QPushButton("◀")
        self.back_btn.setFixedWidth(36)
        self.back_btn.clicked.connect(self._back)
        nav.addWidget(self.back_btn)
        
        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setFixedWidth(36)
        self.fwd_btn.clicked.connect(self._forward)
        nav.addWidget(self.fwd_btn)
        
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setFixedWidth(36)
        self.reload_btn.clicked.connect(self._reload)
        nav.addWidget(self.reload_btn)
        
        self.home_btn = QPushButton("DuckDuckGo")
        self.home_btn.clicked.connect(lambda: self.navigate("https://duckduckgo.com"))
        nav.addWidget(self.home_btn)
        
        self.pixel_btn = QPushButton("PixelDefence")
        self.pixel_btn.clicked.connect(lambda: self.navigate(CHECKER_URL))
        nav.addWidget(self.pixel_btn)
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter HTTPS URL or search query...")
        self.url_bar.returnPressed.connect(self._on_enter)
        nav.addWidget(self.url_bar, 1)
        
        go_btn = QPushButton("Go")
        go_btn.setObjectName("AccentButton")
        go_btn.clicked.connect(self._on_enter)
        nav.addWidget(go_btn)
        
        layout.addLayout(nav)
        
        self.browser = BrowserGuard(self)
        self.browser.navigation_changed.connect(self._on_nav)
        layout.addWidget(self.browser, 1)
        
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
            
    def navigate(self, url):
        self.browser.set_network_enabled(True)
        if self.browser.navigate(url):
            self.url_bar.setText(url)
            
    def closeEvent(self, event):
        self.browser.shutdown()
        event.accept()

import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

try:
    from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer, Qt
    from PyQt6.QtWidgets import QApplication
    PYQT6_AVAILABLE = True
except ImportError:
    QCoreApplication = QEventLoop = QTimer = Qt = QApplication = None
    PYQT6_AVAILABLE = False

from cyberbreak.ui.widgets.private_browser import (
    BrowserGuard,
    WEBENGINE_AVAILABLE,
    WEBENGINE_ERROR,
    LOCAL_AUDIT_SCRIPT,
    normalize_web_url,
    request_allowed,
)


class UrlPolicyTests(unittest.TestCase):
    def test_https_normalization(self):
        self.assertEqual(normalize_web_url("example.com/privacy?q=1"), "https://example.com/privacy?q=1")
        self.assertEqual(normalize_web_url(" https://example.com "), "https://example.com/")
        self.assertEqual(normalize_web_url("http://127.0.0.1:8080/test"), "http://127.0.0.1:8080/test")
        self.assertEqual(normalize_web_url("http://[::1]:8080/test"), "http://[::1]:8080/test")

    def test_rejects_untrusted_schemes_credentials_and_invalid_urls(self):
        for value in ("", "javascript:alert(1)", "file:///C:/private", "data:text/html,x",
                      "http://example.com", "https://user:password@example.com", "https://example.com:99999",
                      "https://example.com:0", "https://example.com/path\nnext", "https:///path",
                      "ws://example.com", "wss://example.com", "https://example.com\\other"):
            with self.subTest(value=value):
                self.assertIsNone(normalize_web_url(value))

    def test_first_party_policy(self):
        self.assertTrue(request_allowed("https://example.com/app.js", "https://example.com/page"))
        self.assertFalse(request_allowed("https://cdn.example.com/app.js", "https://example.com/page"))
        self.assertFalse(request_allowed("https://tracker.test/pixel", "https://example.com/page"))
        self.assertFalse(request_allowed("https://example.com/app.js", "about:blank"))
        self.assertTrue(request_allowed("https://another.test/", "https://example.com/", main_frame=True))
        self.assertFalse(request_allowed("http://another.test/", "https://example.com/", main_frame=True))


@unittest.skipUnless(PYQT6_AVAILABLE and WEBENGINE_AVAILABLE, "QtWebEngine unavailable: " + str(WEBENGINE_ERROR))
class BrowserProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        cls.application = QApplication.instance() or QApplication(["CyberBreak browser tests"])
        cls.requests = []
        cls.request_lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                with cls.request_lock:
                    cls.requests.append((self.path, dict(self.headers)))
                if self.path == "/parser-frame":
                    body = b"""<!doctype html><iframe></iframe><script>
                    try {
                        const realm = window.frames[0];
                        const canvas = realm.document.createElement('canvas');
                        canvas.toDataURL();
                        window.parserFrameBlocked = false;
                    } catch (error) {
                        window.parserFrameBlocked = error.name === 'NotAllowedError';
                    }
                    </script>"""
                    content_type = "text/html"
                elif self.path.startswith("/page"):
                    body = f"""<!doctype html><html><head><script>
                    window.early = {{dnt: navigator.doNotTrack, cookies: navigator.cookieEnabled,
                        connection: typeof navigator.connection, battery: typeof navigator.getBattery}};
                    const canvas = document.createElement('canvas');
                    try {{ canvas.toDataURL(); window.early.canvas = false; }}
                    catch (error) {{ window.early.canvas = error.name === 'NotAllowedError'; }}
                    window.media = 'pending';
                    if (navigator.mediaDevices) {{
                        navigator.mediaDevices.enumerateDevices().then(() => window.media = false)
                            .catch(error => window.media = error.name === 'NotAllowedError');
                    }} else {{ window.media = true; }}
                    </script></head><body>Protected test page
                    <script src='/same-party.js'></script>
                    <img src='http://localhost:{cls.server.server_port}/third-party'>
                    </body></html>""".encode()
                    content_type = "text/html"
                elif self.path == "/same-party.js":
                    body = b"window.samePartyLoaded = true;"
                    content_type = "application/javascript"
                elif self.path == "/worker.js":
                    body = b"self.addEventListener('install', event => self.skipWaiting());"
                    content_type = "application/javascript"
                else:
                    body = b"blocked cross-origin content"
                    content_type = "text/plain"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Set-Cookie", "server_cookie=1; SameSite=Strict; Path=/")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    pass

            def log_message(self, format, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.daemon_threads = True
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(3)

    def setUp(self):
        with self.request_lock:
            self.requests.clear()
        self.guard = BrowserGuard()
        self.guard.resize(640, 480)
        self.guard.show()
        self._load("/page")

    def tearDown(self):
        self.guard.shutdown()
        self.guard.close()
        self.guard.deleteLater()
        self.application.processEvents()

    def _load(self, path):
        finished = []
        loop = QEventLoop()

        def completed(success):
            finished.append(success)
            loop.quit()

        self.guard.view.loadFinished.connect(completed)
        self.assertTrue(self.guard.navigate(self.base_url + path))
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        self.guard.view.loadFinished.disconnect(completed)
        self.assertEqual(finished, [True], "Local page did not load")

    def _evaluate(self, source, world=0):
        results = []
        loop = QEventLoop()

        def completed(value):
            results.append(value)
            loop.quit()

        self.guard.view.page().runJavaScript(source, world, completed)
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        self.assertTrue(results, "JavaScript evaluation timed out")
        return results[0]

    def test_protection_runs_before_page_scripts(self):
        result = self._evaluate("window.early")
        self.assertEqual(result, {"dnt": "1", "cookies": False, "connection": "undefined",
                                  "battery": "undefined", "canvas": True})
        self.assertIs(self._evaluate("window.media"), True)
        self.assertIs(self._evaluate("window.samePartyLoaded"), True)

    def test_cookie_rejection_headers_and_cross_origin_blocking(self):
        self.assertEqual(self._evaluate("document.cookie"), "")
        self.assertEqual(self._evaluate("document.cookie='client_cookie=1; path=/'; document.cookie"), "")
        self._load("/page?repeat=1")
        with self.request_lock:
            requests = list(self.requests)
        self.assertFalse(any(path == "/third-party" for path, headers in requests))
        self.assertTrue(any(path == "/same-party.js" for path, headers in requests))
        for path, headers in requests:
            with self.subTest(path=path):
                self.assertEqual(headers.get("DNT"), "1")
                self.assertEqual(headers.get("Sec-GPC"), "1")
                self.assertNotIn("Cookie", headers)
        self.assertGreaterEqual(self.guard.blocked_requests, 1)

    def test_audit_checks_actual_api_denial(self):
        results = []
        loop = QEventLoop()

        def completed(result):
            results.append(result)
            loop.quit()

        self.guard.audit_result.connect(completed)
        self.guard.run_local_audit()
        QTimer.singleShot(10000, loop.quit)
        loop.exec()
        self.assertTrue(results, "Local audit timed out")
        result = results[0]
        for key in ("dnt", "gpc", "cookies", "canvas", "canvas_readback", "webgl", "battery",
                    "connection", "webrtc", "workers", "off_the_record"):
            with self.subTest(key=key):
                self.assertIs(result.get(key), True)

    def test_subframe_privacy_policy(self):
        self._evaluate("const frame = document.createElement('iframe'); frame.src = '/page?iframe=1'; "
                       "document.body.appendChild(frame)")
        loop = QEventLoop()
        QTimer.singleShot(500, loop.quit)
        loop.exec()
        result = self._evaluate("document.querySelector('iframe').contentWindow.early")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["dnt"], "1")
        self.assertIs(result["canvas"], True)

    def test_fresh_blank_frame_cannot_export_canvas(self):
        result = self._evaluate("(() => { const frame = document.createElement('iframe'); "
                                "document.body.appendChild(frame); "
                                "const canvas = frame.contentDocument.createElement('canvas'); "
                                "try { canvas.toDataURL(); return false; } "
                                "catch (error) { return error.name === 'NotAllowedError'; } })()")
        self.assertIs(result, True)

    def test_document_parser_writes_are_denied(self):
        result = self._evaluate("(() => { const blocked = {}; "
                                "for (const name of ['open', 'write', 'writeln']) { "
                                "try { document[name]('<iframe></iframe>'); "
                                "const realm = window.frames[0]; "
                                "blocked[name] = !realm || !realm.document.createElement('canvas').toDataURL(); } "
                                "catch (error) { blocked[name] = error.name === 'NotAllowedError'; } "
                                "} return blocked; })()")
        self.assertEqual(result, {"open": True, "write": True, "writeln": True})

    def test_static_parser_frame_is_protected_before_inline_script(self):
        self._load("/parser-frame")
        self.assertIs(self._evaluate("window.parserFrameBlocked"), True)

    def test_webgl_audit_detects_reenabled_native_access(self):
        from PyQt6.QtWebEngineCore import QWebEngineSettings
        attribute = QWebEngineSettings.WebAttribute.WebGLEnabled
        self.guard.profile.settings().setAttribute(attribute, True)
        self._load("/page?webgl-control=1")
        available = self._evaluate("!!document.createElement('canvas').getContext('webgl')")
        if not available:
            self.skipTest("This test host cannot create a native WebGL context")
        result = self._evaluate(LOCAL_AUDIT_SCRIPT)
        self.assertIs(result["webgl"], False)

    def test_service_worker_registration_is_denied_by_native_cookie_policy(self):
        self.assertEqual(self._evaluate("typeof navigator.serviceWorker"), "undefined")
        self._evaluate("window.nativeWorkerResult = 'pending'; "
                       "Promise.resolve().then(() => navigator.serviceWorker.register('/worker.js'))"
                       ".then(() => window.nativeWorkerResult = 'registered')"
                       ".catch(error => window.nativeWorkerResult = {name: error.name, message: error.message})", world=1)
        loop = QEventLoop()
        QTimer.singleShot(500, loop.quit)
        loop.exec()
        result = self._evaluate("window.nativeWorkerResult", world=1)
        self.assertIsInstance(result, dict)
        self.assertIn(result["name"], ("SecurityError", "NotAllowedError", "NotSupportedError"),
                      "Service workers must be blocked in the native realm as well as page JavaScript")

    def test_reset_replaces_profile_and_network_revocation_clears_page(self):
        old_profile = self.guard.profile
        self._evaluate("window.secret = 'session data'")
        self.guard.reset_session()
        self.assertIsNot(old_profile, self.guard.profile)
        self.assertTrue(self.guard.profile.isOffTheRecord())
        self._load("/page?fresh=1")
        self.assertEqual(self._evaluate("typeof window.secret"), "undefined")
        self.guard.set_network_enabled(False)
        self.assertFalse(self.guard.navigate(self.base_url + "/page?forbidden=1"))
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()
        self.assertEqual(self.guard.view.url().toString(), "about:blank")
        with self.request_lock:
            self.assertFalse(any(path == "/page?forbidden=1" for path, headers in self.requests))
        self.guard.reset_session()
        self.assertFalse(self.guard.interceptor.network_enabled)


if __name__ == "__main__":
    unittest.main()

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QCheckBox, QFrame, QWidget


_PATHS = {
    "shield": '<path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6.5h14M5 17.5h14"/>',
    "route": '<circle cx="6" cy="5" r="2"/><circle cx="18" cy="19" r="2"/><path d="M6 7v7a4 4 0 0 0 4 4h2M18 17v-7a4 4 0 0 0-4-4h-2m-2-2 2 2-2 2m4 8-2 2 2 2"/>',
    "activity": '<path d="M2 12h5l3-8 4 16 3-8h5"/>',
    "usb": '<path d="M12 20V4m-3 3 3-3 3 3M12 15l-5-4V8m5 4 5-3V6"/><circle cx="12" cy="20" r="2"/><circle cx="7" cy="7" r="1"/><path d="M16 3h3v3h-3z"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="3"/><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 3v3m6-3v3M9 18v3m6-3v3M3 9h3m-3 6h3m12-6h3m-3 6h3"/>',
    "refresh": '<path d="M20 10a8 8 0 0 0-14-5L3 8m0-5v5h5M4 14a8 8 0 0 0 14 5l3-3m0 5v-5h-5"/>',
    "arrow": '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m7 9 3 3-3 3m6 0h4"/>',
    "sparkles": '<path d="m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3zM20 2v4m-2-2h4"/>',
    "layers": '<path d="m12 3 10 5-10 5L2 8zM3 12l9 5 9-5M3 16l9 5 9-5"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "alert": '<path d="m10.3 4-8 14a2 2 0 0 0 1.7 3h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0zM12 9v4m0 4h.01"/>',
    "settings": '<path d="m10 3-1 3-3 1-3-1-1 4 3 2v3l-1 3 3 3 3-2h3l3 2 3-3-1-3v-3l3-2-1-4-3 1-3-1-1-3z"/><circle cx="12" cy="12" r="3"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "moon": '<path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14z"/>',
    "close": '<path d="m6 6 12 12M6 18 18 6"/>',
}


def icon(name, color="#a4aec8", size=20):
    path = _PATHS.get(name, _PATHS["shield"])
    source = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(source.encode()).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


class AppCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppCanvas")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        base = QLinearGradient(0, 0, self.width(), self.height())
        base.setColorAt(0, QColor("#151b2b"))
        base.setColorAt(0.55, QColor("#0d1422"))
        base.setColorAt(1, QColor("#111725"))
        painter.fillRect(self.rect(), base)
        for x, y, radius, color in (
            (0.83, 0.03, 0.65, QColor(74, 99, 171, 70)),
            (0.98, 0.50, 0.50, QColor(58, 139, 151, 26)),
            (0.24, 0.94, 0.45, QColor(96, 75, 164, 35)),
        ):
            glow = QRadialGradient(self.width() * x, self.height() * y, self.width() * radius)
            glow.setColorAt(0, color)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillRect(self.rect(), glow)
        painter.setPen(QPen(QColor(171, 191, 238, 10), 1.0))
        for offset in (0, 36, 72):
            path = QPainterPath()
            path.moveTo(self.width() * 0.42, -20 - offset)
            path.cubicTo(self.width() * 0.72, self.height() * 0.15, self.width() * 0.66, self.height() * 0.80, self.width() + 90, self.height() * 0.96 + offset)
            painter.drawPath(path)


class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self._hover = 0.0
        self._animation = QPropertyAnimation(self, b"hover", self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    @pyqtProperty(float)
    def hover(self):
        return self._hover

    @hover.setter
    def hover(self, value):
        self._hover = value
        self.update()

    def _animate(self, value):
        self._animation.stop()
        if self.window().property("reducedMotion"):
            self.hover = value
            return
        self._animation.setStartValue(self._hover)
        self._animation.setEndValue(value)
        self._animation.start()

    def enterEvent(self, event):
        self._animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75)
        gradient = QLinearGradient(area.topLeft(), area.bottomRight())
        gradient.setColorAt(0, QColor(185, 206, 255, 17 + int(self._hover * 8)))
        gradient.setColorAt(0.45, QColor(177, 197, 240, 9 + int(self._hover * 5)))
        gradient.setColorAt(1, QColor(125, 144, 191, 6))
        painter.setBrush(gradient)
        border = QLinearGradient(area.topLeft(), area.bottomRight())
        border.setColorAt(0, QColor(205, 220, 255, 45 + int(self._hover * 20)))
        border.setColorAt(0.5, QColor(170, 194, 239, 14))
        border.setColorAt(1, QColor(177, 199, 234, 25))
        painter.setPen(QPen(border, 1.0))
        painter.drawRoundedRect(area, 20, 20)


class ToggleSwitch(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._position = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(34)
        self._animation = QPropertyAnimation(self, b"position", self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._toggle)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.update()

    def _toggle(self, checked):
        self._animation.stop()
        target = 1.0 if checked else 0.0
        if not self.isVisible() or self.window().property("reducedMotion"):
            self.position = target
            return
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(target)
        self._animation.start()

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 68, 36)

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(1.0 if self.isEnabled() else 0.45)
        track = QRectF(self.width() - 48, (self.height() - 26) / 2, 46, 26)
        off, on = QColor("#3d465c"), QColor("#7294ff")
        blend = QColor(*[round(a + (b - a) * self._position) for a, b in zip(off.getRgb()[:3], on.getRgb()[:3])])
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(blend)
        painter.drawRoundedRect(track, 13, 13)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f6f8ff"))
        painter.drawEllipse(QRectF(track.x() + 3 + 20 * self._position, track.y() + 3, 20, 20))
        painter.setPen(QColor("#e4e9f7"))
        text_rect = self.rect().adjusted(0, 0, -62, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight, text_rect.width()))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#b0c2ff"), 1.5))
            painter.drawRoundedRect(track.adjusted(-2, -2, 2, 2), 15, 15)

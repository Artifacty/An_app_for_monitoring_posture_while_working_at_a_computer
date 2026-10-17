"""Собственные виджеты: переключатель, плашка статуса, кольцо оценки, окно камеры, график."""
from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
)
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui import theme


class Card(QFrame):
    """Скруглённая карточка с вертикальной раскладкой."""

    def __init__(self, title: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(10)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("h2")
            self.body.addWidget(lbl)


class ToggleSwitch(QAbstractButton):
    """Переключатель вкл/выкл с анимацией."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(48, 28)
        self._pos = 0.0
        self._anim = QPropertyAnimation(self, b"position", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.toggled.connect(self._animate)

    def _get_pos(self) -> float:
        return self._pos

    def _set_pos(self, value: float) -> None:
        self._pos = value
        self.update()

    position = Property(float, _get_pos, _set_pos)

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def set_checked_silent(self, checked: bool) -> None:
        """Переключить без сигнала toggled."""
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        self._anim.stop()
        self._set_pos(1.0 if checked else 0.0)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        off, on = QColor(theme.BORDER), QColor(theme.ACCENT)
        t = self._pos
        track = QColor(
            int(off.red() + (on.red() - off.red()) * t),
            int(off.green() + (on.green() - off.green()) * t),
            int(off.blue() + (on.blue() - off.blue()) * t),
        )
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(self.rect(), self.height() / 2, self.height() / 2)
        d = self.height() - 8
        x = 4 + t * (self.width() - 8 - d)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QRectF(x, 4, d, d))


class StatusPill(QLabel):
    """Цветная плашка статуса."""

    _COLORS = {
        "off": (theme.MUTED, "#262b34"),
        "ok": (theme.ACCENT, "#16352d"),
        "warn": (theme.WARN, "#3a2f14"),
        "bad": (theme.BAD, "#3b1d1d"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_state("off", "Выключено")

    def set_state(self, kind: str, text: str) -> None:
        fg, bg = self._COLORS[kind]
        self.setText(f"●  {text}")
        self.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 14px;"
            f"padding: 6px 14px; font-weight: 600;"
        )


class ScoreRing(QWidget):
    """Кольцо с оценкой осанки 0..100. None = нет данных."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value: int | None = None
        self.setMinimumSize(150, 150)

    def set_value(self, value: int | None) -> None:
        self._value = value
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 20
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

        pen = QPen(QColor(theme.SURFACE_2), 12)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        if self._value is not None:
            v = max(0, min(100, self._value))
            color = theme.ACCENT if v >= 70 else theme.WARN if v >= 40 else theme.BAD
            pen.setColor(QColor(color))
            p.setPen(pen)
            p.drawArc(rect, 90 * 16, int(-v / 100 * 360 * 16))
            text = str(v)
        else:
            text = "—"

        p.setPen(QColor(theme.TEXT))
        font = QFont(self.font())
        font.setPixelSize(int(side * 0.28))
        font.setBold(True)
        p.setFont(font)
        p.drawText(rect, Qt.AlignCenter, text)


class MetricRow(QWidget):
    """Строка метрики: название слева, значение справа, полоска снизу."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        row = QHBoxLayout()
        self._name = QLabel(name)
        self._name.setObjectName("muted")
        self._value = QLabel("—")
        self._value.setAlignment(Qt.AlignRight)
        row.addWidget(self._name)
        row.addWidget(self._value)
        lay.addLayout(row)
        self._bar = _Bar()
        lay.addWidget(self._bar)

    def set_value(self, text: str, fraction: float | None = None, level: str = "ok") -> None:
        self._value.setText(text)
        self._bar.set_fraction(fraction, level)


class _Bar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._f: float | None = None
        self._level = "ok"

    def set_fraction(self, f: float | None, level: str) -> None:
        self._f, self._level = f, level
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.SURFACE_2))
        p.drawRoundedRect(self.rect(), 3, 3)
        if self._f is not None:
            color = {"ok": theme.ACCENT, "warn": theme.WARN, "bad": theme.BAD}[self._level]
            p.setBrush(QColor(color))
            w = self.width() * max(0.0, min(1.0, self._f))
            p.drawRoundedRect(QRectF(0, 0, w, self.height()), 3, 3)


class VideoView(QWidget):
    """Окно камеры: кадр, скелет и точки поверх, плашка LIVE и оверлей-текст.

    `connections` — пары индексов точек, которые соединяются линиями.
    Backend может задать свои (например, для 33 точек MediaPipe).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._image: QImage | None = None
        self._points: list[tuple[float, float]] = []
        self.connections: list[tuple[int, int]] = [(1, 0), (0, 2), (3, 4)]
        self._placeholder = "Камера выключена"
        self._overlay: str | None = None

    # --- API ----------------------------------------------------------
    def show_frame(self, image: QImage, points: list) -> None:
        self._image, self._points = image, points
        self.update()

    def show_idle(self, text: str = "Камера выключена") -> None:
        self._image, self._points = None, []
        self._placeholder = text
        self._overlay = None
        self.update()

    def set_overlay(self, text: str | None) -> None:
        """Крупный текст по центру (например, отсчёт при калибровке)."""
        self._overlay = text
        self.update()

    # --- отрисовка ----------------------------------------------------
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        outer = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        clip = QPainterPath()
        clip.addRoundedRect(outer, 16, 16)
        p.setClipPath(clip)
        p.fillRect(outer, QColor("#0d0f13"))

        if self._image is None:
            self._paint_placeholder(p, outer)
        else:
            iw, ih = self._image.width(), self._image.height()
            scale = min(outer.width() / iw, outer.height() / ih)
            w, h = iw * scale, ih * scale
            target = QRectF(
                outer.x() + (outer.width() - w) / 2,
                outer.y() + (outer.height() - h) / 2,
                w,
                h,
            )
            p.drawImage(target, self._image)
            self._paint_skeleton(p, target)
            self._paint_live_badge(p, outer)

        if self._overlay:
            p.fillRect(outer, QColor(0, 0, 0, 140))
            font = QFont(self.font())
            font.setPixelSize(96)
            font.setBold(True)
            p.setFont(font)
            p.setPen(QColor(theme.TEXT))
            p.drawText(outer, Qt.AlignCenter, self._overlay)

        p.setClipping(False)
        p.setPen(QPen(QColor(theme.BORDER), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(outer, 16, 16)

    def _paint_placeholder(self, p: QPainter, rect: QRectF) -> None:
        c = rect.center()
        p.setPen(QPen(QColor(theme.BORDER), 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(c + QPointF(0, -34), 26, 26)  # голова
        path = QPainterPath()
        path.moveTo(c.x() - 62, c.y() + 40)
        path.quadTo(c.x(), c.y() - 28, c.x() + 62, c.y() + 40)  # плечи
        p.drawPath(path)
        p.setPen(QColor(theme.MUTED))
        p.drawText(
            QRectF(rect.x(), c.y() + 56, rect.width(), 30), Qt.AlignHCenter, self._placeholder
        )

    def _paint_skeleton(self, p: QPainter, target: QRectF) -> None:
        pts = [
            QPointF(target.x() + x * target.width(), target.y() + y * target.height())
            for x, y in self._points
        ]
        line = QPen(QColor(theme.ACCENT), 3)
        line.setCapStyle(Qt.RoundCap)
        p.setPen(line)
        for a, b in self.connections:
            if a < len(pts) and b < len(pts):
                p.drawLine(pts[a], pts[b])
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.setBrush(QColor(theme.ACCENT))
        for pt in pts:
            p.drawEllipse(pt, 6, 6)

    def _paint_live_badge(self, p: QPainter, rect: QRectF) -> None:
        badge = QRectF(rect.x() + 14, rect.y() + 14, 64, 26)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(badge, 13, 13)
        p.setBrush(QColor(theme.BAD))
        p.drawEllipse(QPointF(badge.x() + 16, badge.center().y()), 4.5, 4.5)
        font = QFont(self.font())
        font.setPixelSize(12)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor("#ffffff"))
        p.drawText(badge.adjusted(26, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, "LIVE")


class BarChart(QWidget):
    """Простой столбчатый график. data = [(подпись, значение 0..100), ...]."""

    def __init__(self, data: list[tuple[str, float]] | None = None, parent=None):
        super().__init__(parent)
        self.data = data or []
        self.setMinimumHeight(220)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.data:
            return
        left, bottom, top = 34, 26, 8
        w, h = self.width() - left, self.height() - bottom - top

        p.setPen(QPen(QColor(theme.BORDER), 1))
        font = QFont(self.font())
        font.setPixelSize(11)
        p.setFont(font)
        for v in (0, 50, 100):
            y = top + h - v / 100 * h
            p.drawLine(QPointF(left, y), QPointF(self.width(), y))
            p.setPen(QColor(theme.MUTED))
            p.drawText(QRectF(0, y - 8, left - 6, 16), Qt.AlignRight | Qt.AlignVCenter, str(v))
            p.setPen(QPen(QColor(theme.BORDER), 1))

        slot = w / len(self.data)
        bar_w = min(38.0, slot * 0.55)
        p.setPen(Qt.NoPen)
        for i, (label, value) in enumerate(self.data):
            color = theme.ACCENT if value >= 70 else theme.WARN if value >= 40 else theme.BAD
            bh = max(0.0, min(100.0, value)) / 100 * h
            x = left + i * slot + (slot - bar_w) / 2
            p.setBrush(QColor(color))
            p.drawRoundedRect(QRectF(x, top + h - bh, bar_w, bh), 5, 5)
            p.setPen(QColor(theme.MUTED))
            p.drawText(
                QRectF(left + i * slot, self.height() - bottom + 4, slot, 18),
                Qt.AlignHCenter,
                label,
            )
            p.setPen(Qt.NoPen)

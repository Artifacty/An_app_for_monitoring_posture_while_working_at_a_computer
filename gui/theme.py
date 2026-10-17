"""Цвета и общий стиль (QSS) приложения. Меняйте палитру только здесь."""

BG = "#13161b"
SURFACE = "#1b1f26"
SURFACE_2 = "#232831"
BORDER = "#2c323d"
TEXT = "#e8ebf0"
MUTED = "#8b94a3"
ACCENT = "#35d0a0"
ACCENT_HOVER = "#4be0b1"
WARN = "#f2b84b"
BAD = "#ef5b5b"

FONT = '"Segoe UI", "Inter", "Roboto", "Noto Sans", sans-serif'


def build_stylesheet() -> str:
    return f"""
* {{ font-family: {FONT}; color: {TEXT}; font-size: 14px; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QStackedWidget, QWidget#page {{ background: transparent; }}

QLabel {{ background: transparent; }}
QLabel#h1 {{ font-size: 24px; font-weight: 700; }}
QLabel#h2 {{ font-size: 15px; font-weight: 600; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#small {{ color: {MUTED}; font-size: 12px; }}
QLabel#big {{ font-size: 28px; font-weight: 700; }}

/* ---------- боковая панель ---------- */
QFrame#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
QLabel#logo {{ font-size: 18px; font-weight: 700; }}
QPushButton[nav="true"] {{
    background: transparent; border: none; border-left: 3px solid transparent;
    border-radius: 0; text-align: left; padding: 12px 20px;
    color: {MUTED}; font-weight: 600;
}}
QPushButton[nav="true"]:hover {{ background: {SURFACE_2}; color: {TEXT}; }}
QPushButton[nav="true"]:checked {{
    background: {SURFACE_2}; color: {TEXT}; border-left: 3px solid {ACCENT};
}}

/* ---------- карточки ---------- */
QFrame#card {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
}}
QFrame#card QLabel {{ border: none; }}

/* ---------- кнопки ---------- */
QPushButton#primary {{
    background: {ACCENT}; color: #08201a; border: none; border-radius: 10px;
    padding: 11px 18px; font-weight: 700;
}}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primary:disabled {{ background: {SURFACE_2}; color: {MUTED}; }}
QPushButton#ghost {{
    background: transparent; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 10px 18px; font-weight: 600;
}}
QPushButton#ghost:hover {{ background: {SURFACE_2}; }}

/* ---------- настройки ---------- */
QSlider::groove:horizontal {{ height: 6px; background: {SURFACE_2}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {TEXT}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
}}
QCheckBox {{ spacing: 10px; }}
QCheckBox::indicator {{
    width: 20px; height: 20px; border-radius: 6px;
    border: 1px solid {BORDER}; background: {SURFACE_2};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 1px solid {ACCENT}; }}
QComboBox {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 12px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE_2}; selection-background-color: {ACCENT}; border: 1px solid {BORDER};
}}
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QMessageBox {{ background: {SURFACE}; }}
"""

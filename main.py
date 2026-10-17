import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Posture Guard")
    app.setStyle("Fusion")  # единый вид на Windows/macOS/Linux, QSS ложится предсказуемо
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

"""Application entry point for Currency Pair Analyzer."""

import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow


def main() -> None:
    """Create and run the PyQt application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

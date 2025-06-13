import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from .gui.mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-size: 10pt;}")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

    
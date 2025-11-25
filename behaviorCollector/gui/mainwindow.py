from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from scipy.io import loadmat
from .video_controller import Controller
from .behav_panel import BehavPanel, BehavViewer, pyqt_KEY_MAP
from .utils_gui import error2messagebox
from .config_menu import MenuBuilder
from .eeg_dialog import EEGDialog


class MainWindow(QMainWindow):
    
    main_window_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Behavior Detection Tool")
        self.setBaseSize(1000, 500)
        
        self._init_ui()
        self._init_menu()
        self._connect_signals()
        
        self.is_behav_saved = False
        self.eeg_dialog = None
        
    def _init_ui(self):
        layout = QHBoxLayout()
        
        l1 = QVBoxLayout()
        self.behav_viewer = BehavViewer()
        self.controller = Controller()
        l1.addWidget(self.behav_viewer)
        l1.addWidget(self.controller)
        layout.addLayout(l1, stretch=5)
        
        self.behav_control = BehavPanel()
        layout.addWidget(self.behav_control, stretch=5)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        self.controller.setFocusPolicy(Qt.StrongFocus)
        self.controller.setFocus()
    
    def _init_menu(self):
        self.menubar = MenuBuilder(self)
        
    def _connect_signals(self):
        self.behav_control.connect_controller(self.controller)
        self.behav_control.connect_behav_viewer(self.behav_viewer)
        self.behav_control.signal_saved.connect(self.behav_saved)
        self.behav_viewer.connect_controller(self.controller)
        self.main_window_closed.connect(self.controller.close_all_viewers)
        self.controller.connect_menubar(self.menubar)
        self.behav_control.connect_menubar(self.menubar)
        self.menubar.load_eeg_requested.connect(self.open_eeg)
        
    def behav_saved(self):
        self.is_behav_saved = True
        
    def closeEvent(self, event):
        if not self.is_behav_saved:
            reply = QMessageBox.question(
                self,
                "Confirm close",
                "The selected behavior is not saved yet. Do you want to close the application without saving?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        self.main_window_closed.emit()
        return super().closeEvent(event)

    @error2messagebox(to_warn=True)
    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_H, Qt.Key_J, Qt.Key_K, Qt.Key_L, Qt.Key_Space):
            self.controller.handle_key_input(event)
        elif key in pyqt_KEY_MAP:
            self.behav_control.handle_key_input(event)

    @error2messagebox(to_warn=True)
    def open_eeg(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open EEG File",
            "",
            "MAT Files (*.mat);;All Files (*.*)"
        )
        if not filepath:
            return

        eeg_data = loadmat(filepath)

        if "data" not in eeg_data or "times" not in eeg_data:
            raise ValueError("The selected MAT file does not contain required EEG fields: data, times.")

        if self.eeg_dialog is not None:
            try:
                self.eeg_dialog.close()
            except Exception:
                pass

        self.eeg_dialog = EEGDialog(eeg_data, controller=self.controller, parent=self)
        self.eeg_dialog.show()


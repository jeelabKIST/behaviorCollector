from PyQt5.QtWidgets import QAction, QMainWindow
from PyQt5.QtCore import pyqtSignal, QObject
from .keymap_viewer import ShortcutMapDialog


class MenuBuilder(QObject):
    load_video_requested    = pyqtSignal()
    load_eeg_requested      = pyqtSignal()
    load_header_requested   = pyqtSignal()
    load_behav_requested    = pyqtSignal()
    save_header_requested   = pyqtSignal()
    save_behav_requested    = pyqtSignal()
    export_epochs_requested = pyqtSignal()

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.parent = parent
        self.menubar = parent.menuBar()
        self._create_menu_bar()

    def _create_menu_bar(self):
        # File menu
        file_menu = self.menubar.addMenu("File")

        # Open Video
        open_video_action = QAction("Open Video", self.parent)
        open_video_action.triggered.connect(self.load_video_requested.emit)
        file_menu.addAction(open_video_action)

        # Open EEG
        open_eeg_action = QAction("Open EEG", self.parent)
        open_eeg_action.triggered.connect(self.load_eeg_requested.emit)
        file_menu.addAction(open_eeg_action)

        file_menu.addSeparator()

        # Load Header
        load_header_action = QAction("Load Behavior Header", self.parent)
        load_header_action.setShortcut("Ctrl+Shift+L")
        load_header_action.triggered.connect(self.load_header_requested.emit)
        file_menu.addAction(load_header_action)

        # Load Behavior
        load_behavior_action = QAction("Load Behavior", self.parent)
        load_behavior_action.setShortcut("Ctrl+L")
        load_behavior_action.triggered.connect(self.load_behav_requested.emit)
        file_menu.addAction(load_behavior_action)
        file_menu.addSeparator()

        # Save Header
        save_header_action = QAction("Save Behavior Header", self.parent)
        save_header_action.setShortcut("Ctrl+Shift+S")
        save_header_action.triggered.connect(self.save_header_requested.emit)
        file_menu.addAction(save_header_action)

        # Save Behavior
        save_behavior_action = QAction("Save Behavior", self.parent)
        save_behavior_action.setShortcut("Ctrl+S")
        save_behavior_action.triggered.connect(self.save_behav_requested.emit)
        file_menu.addAction(save_behavior_action)

        # Export Epochs
        export_epochs_action = QAction("Export Selected Behavior Epochs", self.parent)
        export_epochs_action.triggered.connect(self.export_epochs_requested.emit)
        file_menu.addAction(export_epochs_action)

        # Help menu
        help_menu = self.menubar.addMenu("Help")
        show_help_action = QAction("Show Help", self.parent)
        show_help_action.setShortcut("Ctrl+H")
        show_help_action.triggered.connect(self.show_shortcut_map)
        help_menu.addAction(show_help_action)
        
    def show_shortcut_map(self):
        dialog = ShortcutMapDialog(self.parent)
        dialog.exec_()
        
    def load_behavior_header(self):
        pass
    
        
        
    
    

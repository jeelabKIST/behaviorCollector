from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class ShortcutMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help shortcut keys")
        layout = QVBoxLayout()

        # Shortcut list
        shortcut_labels = [
                "--- Playback Controls ---",
                "Space : Play / Pause",
                "J : Decrease playback speed",
                "K : Increase playback speed",
                "H : Previous frame",
                "L : Next frame",
                "Shift + H : Jump back 10 seconds",
                "Shift + L : Jump forward 10 seconds",
                "Shift + J : Jump back 5 seconds",
                "Shift + K : Jump forward 5 seconds",
                "--- Behavior Annotation ---",
                "Q : Select time point for Behavior 1",
                "W : Select time point for Behavior 2",
                "E : Select time point for Behavior 3",
                "R : Select time point for Behavior 4",
                "T : Select time point for Behavior 5",
                "A : Select time point for Behavior 6",
                "S : Select time point for Behavior 7",
                "D : Select time point for Behavior 8",
                "F : Select time point for Behavior 9",
                "G : Select time point for Behavior 10",
                "1 : Select time point for Behavior 11",
                "2 : Select time point for Behavior 12",
                "3 : Select time point for Behavior 13",
                "4 : Select time point for Behavior 14",
                "5 : Select time point for Behavior 15",
                "6 : Select time point for Behavior 16",
                "7 : Select time point for Behavior 17",
                "8 : Select time point for Behavior 18",
                "--- Editing ---",
                "Z : Undo last selection",
                "X : Clear current selections"
                ]
        
        for key in shortcut_labels:
            label = QLabel(key)
            layout.addWidget(label)
            if key.startswith("---"):
                label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 4px;")
            label.setStyleSheet("font-family: monospace;")

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        
        
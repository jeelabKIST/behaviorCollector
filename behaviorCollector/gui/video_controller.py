from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QHBoxLayout, QFileDialog, QSlider, QLabel,
    QToolButton, QDoubleSpinBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import numpy as np
from functools import partial
from .video_viewer import VideoViewerWindow
from .config_menu import MenuBuilder


FPS_DEFAULT = 30
PENDING_TIME = 50
MOVE_LARGE = 10000 # 10 s
MOVE_SMALL = 5000  # 5s


class Controller(QWidget):
    
    # video_loaded = pyqtSignal(str)
    # video_closed = pyqtSignal(int)
    duration_updated = pyqtSignal(int)
    position_updated = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.viewers = []
        self._init_ui()
        self._init_timer()
        self.playing_state = False
        self.min_fps = FPS_DEFAULT
        # self._update_slider_value = True
        
    def _init_ui(self):
        
        layout = QVBoxLayout()
        
        l1 = QHBoxLayout()
        
        self.toggle_play_button = QToolButton()
        self.toggle_play_button.setText("▶")
        self.toggle_play_button.clicked.connect(self.toggle_play)
        self.next_scene = QToolButton()
        self.next_scene.setText("▶▶")
        self.next_scene.clicked.connect(partial(self.seek_relative, 100))
        self.prev_scene = QToolButton()
        self.prev_scene.setText("◀◀")
        self.prev_scene.clicked.connect(partial(self.seek_relative, -100))
        self.current_label = QLabel("Time: 0.000 s")
        
        self.speed_box = QDoubleSpinBox()
        self.speed_box.setValue(1)
        self.speed_box.setRange(0.1, 5)
        self.speed_box.setSingleStep(0.1)
        self.speed_box.valueChanged.connect(self._update_speed)
        
        # l1.addWidget(self.load_button)
        spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        l1.addItem(spacer)
        
        l1.addWidget(self.prev_scene)
        l1.addWidget(self.toggle_play_button)
        l1.addWidget(self.next_scene)
        
        spacer = QSpacerItem(2, 5, QSizePolicy.Expanding, QSizePolicy.Minimum)
        l1.addItem(spacer)
        l1.addWidget(QLabel("Play speed; x"))
        l1.addWidget(self.speed_box)
        
        l1.addWidget(self.current_label)
        layout.addLayout(l1)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.seek_slider)
        self._set_slider_style()
        layout.addWidget(self.slider)
        
        self.setLayout(layout)
        
    def _init_timer(self):
        self.seek_timer = QTimer()
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self._do_seek)
        self.pending_seek_ms = 0
        
    def connect_menubar(self, menubar: MenuBuilder):
        menubar.load_video_requested.connect(self.load_video)
        
    def load_video(self):
        video_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if video_path:
            viewer = VideoViewerWindow(video_path, len(self.viewers))
            viewer.show()
            
            self.viewers.append(viewer)
            viewer.closed.connect(self.closed_video)
            
            if self.num_video == 1:
                self._connect_viewer_signals(viewer)

            if viewer.fps < self.min_fps:
                self.min_fps = np.ceil(viewer.fps).astype(int)
                
    def closed_video(self, vid: int):
        self.viewers[vid] = None
        if vid == 0:
            for viewer in self.viewers:
                if viewer is not None:
                    self._connect_viewer_signals(viewer)
        # TODO: remove the viewer informations
        
    def close_all_viewers(self):
        for viewer in self.viewers:
            if viewer is not None:
                viewer.closed.disconnect(self.closed_video)
                viewer.close()
    
    def _connect_viewer_signals(self, viewer):
        viewer.media_player.durationChanged.connect(self.update_duration)
        viewer.media_player.positionChanged.connect(self.update_slider_position)
        self.update_duration(duration_ms=viewer.duration_ms)
            
    def update_duration(self, duration_ms: float=None):
        self.slider.setRange(0, duration_ms)
        self.duration_updated.emit(duration_ms)

    def update_slider_position(self, position_ms):
        self.slider.setValue(position_ms)
        self.current_label.setText(f"Time: {position_ms/1e3:.3f} s")
        self.position_updated.emit(position_ms)
        
    def seek_slider(self, position_ms):
        self.seek_timer.start(PENDING_TIME)
        
    def seek_relative(self, delta_ms):
        self.pending_seek_ms += delta_ms
        self.seek_timer.start(PENDING_TIME)
        
    def _do_seek(self):
        if self.pending_seek_ms != 0:
            new_pos = max(0, self.current + self.pending_seek_ms) # ms
            new_pos = min(new_pos, self.slider.maximum())
            for viewer in self.viewers:
                if viewer is not None:
                    viewer.update_position(position_ms=new_pos)
            self.pending_seek_ms = 0
            self.slider.setValue(new_pos)
        else:
            position_ms = self.slider.value()
            for viewer in self.viewers:
                if viewer is not None:
                    viewer.update_position(position_ms=position_ms)
                
    def update_position(self, time_ms):
        for viewer in self.viewers:
            if viewer is not None:
                viewer.update_position(position_ms=time_ms)
        self.slider.setValue(time_ms)
                
    def _update_speed(self, value):
        for viewer in self.viewers:
            if viewer is not None:
                viewer.setPlayrate(value)
            
    def update_speed_relative(self, dv):
        value = self.speed_box.value() + dv
        self.speed_box.setValue(value)
        for viewer in self.viewers:
            if viewer is not None:
                viewer.setPlayrate(value)
        
    def toggle_play(self):
        if self.playing_state:
            self.toggle_play_button.setText("▶")
            for viewer in self.viewers:
                if viewer is not None:
                    viewer.pause()
        else:
            self.toggle_play_button.setText("⏸")
            for viewer in self.viewers:
                if viewer is not None:
                    viewer.play()

        self.playing_state = not self.playing_state
            
    def handle_key_input(self, event):
        if self.num_video == 0:
            return
        
        key = event.key()
        modifiers = event.modifiers()
        
        if modifiers & Qt.ShiftModifier:
            if key == Qt.Key_H:
                self.seek_relative(-MOVE_LARGE)
            elif key == Qt.Key_L:
                self.seek_relative(MOVE_LARGE)
            elif key == Qt.Key_J:
                self.seek_relative(-MOVE_SMALL)
            elif key == Qt.Key_K:
                self.seek_relative(MOVE_SMALL)
        else:
            if key == Qt.Key_Space:
                self.toggle_play()
            elif key == Qt.Key_H:
                self.seek_relative(-int(1000/self.min_fps))
            elif key == Qt.Key_L:
                self.seek_relative(int(1000/self.min_fps))
            elif key == Qt.Key_J: # speed down
                self.update_speed_relative(-0.1)
            elif key == Qt.Key_K: # speed up
                self.update_speed_relative(0.1)
            else:
                raise ValueError(f"Key {key} not recognized in Controller")            
    
    @property   
    def current(self):
        if self.num_video == 0:
            return 0
        else:
            for viewer in self.viewers:
                if viewer is not None:
                    return viewer.media_player.position()
        
    @property
    def num_video(self):
        num = 0
        for viewer in self.viewers:
            if viewer is not None:
                num += 1
        return num
    
    @property
    def current_video_path(self):
        video_paths = []
        for viewer in self.viewers:
            if viewer is not None:
                video_paths.append(viewer.video_path)
        return video_paths
        
    def _set_slider_style(self):
        self.slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #bbb;
                    background: #eee;
                    height: 6px;
                    border-radius: 4px;
                }

                QSlider::sub-page:horizontal {
                    background: #409EFF; /* 진행된 부분 색 */
                    border: 1px solid #777;
                    height: 6px;
                    border-radius: 3px;
                }

                QSlider::add-page:horizontal {
                    background: #ccc;
                    border: 1px solid #777;
                    height: 6px;
                    border-radius: 3px;
                }

                QSlider::handle:horizontal {
                    background: white;
                    border: 1px solid #409EFF;
                    width: 14px;
                    height: 14px;
                    margin: -4px 0; /* 위아래로 중앙 정렬 */
                    border-radius: 7px;
                }
                """)
        self.slider.setFixedHeight(20)

    
        
    
            
    



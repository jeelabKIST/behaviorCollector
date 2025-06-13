import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QGraphicsView, QHBoxLayout, QSpacerItem, QSizePolicy,
    QGraphicsScene, QToolButton
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt5.QtCore import Qt, QUrl, QTimer, QRectF, QSizeF, QPointF, pyqtSignal



class VideoViewerWindow(QMainWindow):

    closed = pyqtSignal(int)
    
    def __init__(self, video_path, vid: int):
        super().__init__()
        self.setWindowTitle(f"{video_path} - Video Viewer")
        self.setMinimumSize(640, 640)
        self.setFocusPolicy(Qt.NoFocus)
        self.vid = vid
        
        self._init_video(video_path)
        self._init_ui()
    
    def _init_video(self, video_path):
        # read video information
        self._load_video_info(video_path) # fps, frame_count
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface) # load media player
        
        # QGraphicsScene setup
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1000, 1000)
        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignCenter)
        self.enable_zoom = False

        # Video item
        self.video_item = QGraphicsVideoItem()
        self.video_item.setSize(QSizeF(self.size()))  # initial size
        self.scene.addItem(self.video_item)
        
        # Connect media player
        self.media_player.setVideoOutput(self.video_item)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.media_player.positionChanged.connect(self.update_time_label)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
    
    def _init_ui(self):        
        layout = QVBoxLayout()
        
        l1 = QHBoxLayout()
        self.button_zoom = QToolButton()
        self.button_zoom.setCheckable(True)
        self.button_zoom.setText("🔍")
        self.button_zoom.clicked.connect(self._click_zoom_button)
        
        self.button_reset = QToolButton()
        self.button_reset.setText("🔄")
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        l1.addItem(spacer)
        l1.addWidget(self.button_zoom)
        l1.addWidget(self.button_reset)
        layout.addLayout(l1)
        
        layout.addWidget(self.view, stretch=10)
        
        self.time_label = QLabel("Time: 0.000 s / 0.000 s | Frame: 0")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label, stretch=1)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def _load_video_info(self, path):
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        self.fps = fps if fps > 1e-3 else 0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration_ms = int(frame_count/self.fps*1e3) if self.fps > 1e-3 else 0
        cap.release()
        
    def update_time_label(self, position_ms):
        seconds = position_ms / 1000
        frame_number = int(seconds * self.fps)
        self.time_label.setText(f"Time: {seconds:.3f} s / {self.duration_ms/1000:.3f} s | Frame: {frame_number}")

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            self.media_player.setPosition(0)
            self.media_player.pause()
            QTimer.singleShot(100, self._resize)

    def update_position(self, position_ms):
        self.media_player.setPosition(position_ms)
        QTimer.singleShot(100, self.media_player.pause)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize()
            
    def _resize(self):
        video_size = self.video_item.nativeSize()  # 실제 비디오 해상도
        if not video_size.isEmpty():
            self.video_item.setSize(video_size)
            self.scene.setSceneRect(QRectF(QPointF(0, 0), video_size))
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def play(self):
        self.media_player.play()
        
    def pause(self):
        self.media_player.pause()
    
    def setPlayrate(self, rate: float):
        self.media_player.setPlaybackRate(rate)
        
    def _click_zoom_button(self):
        if self.button_zoom.isChecked():
            self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            self.view.setDragMode(QGraphicsView.NoDrag)
    
    def wheelEvent(self, event):
        if not self.button_zoom.isChecked():
            return super().wheelEvent(event)
        
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.view.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.view.scale(zoom_out_factor, zoom_out_factor)
            
    def closeEvent(self, event):
        self.closed.emit(self.vid)
        super().closeEvent(event)
    
    
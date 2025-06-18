from PyQt5.QtWidgets import (
    QGraphicsLineItem, QGraphicsView, QGraphicsScene, QSizePolicy, QGraphicsTextItem,
    QHBoxLayout, QPushButton, QLabel
)
from PyQt5.QtGui import QPen, QColor, QFont, QPainter
from PyQt5.QtCore import Qt, QRectF, QLineF, pyqtSignal
from collections import defaultdict

from .behav_panel import pyqt_KEY_MAP
from .video_controller import Controller

NUM_TICKS = 5
MAX_KEY = len(pyqt_KEY_MAP) - 2


class BehavLine(QGraphicsLineItem):
    def __init__(self, key_id, color: str, time_ms_start, time_ms_end):
        super().__init__()
        self.key_id = key_id
        self.color = color
        self.time_ms_start = time_ms_start
        self.time_ms_end = time_ms_end
        self.rewind = None

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsLineItem.ItemIsSelectable)
        self.setPen(QPen(QColor(color), 2))
    
    def update_position(self, scene_width, scene_height, duration_ms):
        x1 = (self.time_ms_start / duration_ms) * scene_width
        x2 = (self.time_ms_end / duration_ms) * scene_width
        y = ((self.key_id + 1) / MAX_KEY) * scene_height  # 예시: key_id 기반 y 위치
        self.setLine(QLineF(x1, y, x2, y))
        
    def set_rewind_function(self, fn):
        self.rewind = fn # receives time_ms as input

    def mousePressEvent(self, event):
        if self.rewind is not None:
            self.rewind(self.time_ms_start)
            
            
class BehavViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setRenderHints(QPainter.Antialiasing)

        self.width = 20000
        self.max_show_ms = 10e3 # +-5 secs
        self.max_show = 100
        self.height = (MAX_KEY + 2)*4
        self.setSceneRect(0, 0, self.width, self.height)
        self.fitInView(QRectF(0, 0, self.max_show, self.height), Qt.IgnoreAspectRatio)
        
        self.lines = []
        self.num_items = defaultdict(int)
        self._init_ticks()
        self._init_line()
        self.duration_ms = 0
        
    def _init_line(self):
        self.l0 = QGraphicsLineItem(QLineF(0, 0, 0, self.height))
        pen = QPen(QColor("#000000"), 0.5)
        pen.setStyle(Qt.SolidLine)  # dotted, dashed 등도 가능
        self.l0.setPen(pen)
        self.scene.addItem(self.l0)
        
    def _init_ticks(self):
        self.ticks, self.tick_labels = [], []
        for n in range(NUM_TICKS):
            l = QGraphicsLineItem(QLineF(0, self.height, 0, self.height-1))
            pen = QPen(QColor("#000000"), 1)
            pen.setStyle(Qt.SolidLine)  # dotted, dashed 등도 가능
            l.setPen(pen)
            self.scene.addItem(l)
            self.ticks.append(l)
            
            text = QGraphicsTextItem("")
            text.setPos(0, self.height-2)
            text.setFont(QFont("Arial", 10))
            text.setFlag(QGraphicsTextItem.ItemIgnoresTransformations)
            
            self.scene.addItem(text)
            self.tick_labels.append(text)
            
    def _update_ticks(self, time_ms):
        if self.duration_ms == 0:
            return
        
        center_x = time_ms / self.duration_ms * self.width
        n0, dn = int(self.max_show / 2), int(self.max_show/4)
        dt = self.max_show_ms / (NUM_TICKS - 1)
        for n in range(NUM_TICKS):
            x = center_x - n0 + n*dn + 1
            if x < 0: continue
            self.ticks[n].setLine(QLineF(x, self.height-2, x, self.height-1))
            
            text = self.tick_labels[n]
            xp = int(x - text.boundingRect().width()/2) + self.max_show//8
            yp = self.height-6
            self.tick_labels[n].setPos(xp, yp)

            t = time_ms - self.max_show_ms/2 +  n*dt
            self.tick_labels[n].setPlainText(f"{t/1000:.2f}")
            
    def _update_line(self, time_ms):
        if self.duration_ms == 0:
            return
        center_x = time_ms / self.duration_ms * self.width
        self.l0.setLine(QLineF(center_x, 0, center_x, self.height))
 
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for line in self.lines:
            line.update_position(scene_width=self.width, scene_height=self.height, duration_ms=self.duration_ms)
        
    def clear_scene(self):
        self.scene.clear()

    def add_item(self, key_id, color, time_ms_start, time_ms_end):
        line = BehavLine(key_id, color, time_ms_start, time_ms_end)
        line.set_rewind_function(self.update_controller)
        
        self.scene.addItem(line)
        self.lines.append(line)
        line.update_position(scene_width=self.width, scene_height=self.height, duration_ms=self.duration_ms)
        self.num_items[key_id] += 1
        
    def delete_item(self, time_ms):
        for line in self.lines:
            if line.scene() == self.scene:
                if line.time_ms_start <= time_ms <= line.time_ms_end:
                    key_id = line.key_id
                    self.num_items[key_id] -= 1
                    self.scene.removeItem(line)
        
    def update_duration(self, duration_ms):
        self.duration_ms = duration_ms
        self.max_show = self.max_show_ms / self.duration_ms * self.width
        self.fitInView(QRectF(0, 0, self.max_show, self.height), Qt.IgnoreAspectRatio)
    
    def on_position_changed(self, time_ms: int):
        center_x = time_ms / self.duration_ms * self.width
        self.centerOn(center_x, self.height/2)
        self._update_ticks(time_ms)
        self._update_line(time_ms)
    
    def connect_controller(self, video_control_obj: Controller):
        video_control_obj.position_updated.connect(self.on_position_changed)
        self.update_controller = video_control_obj.update_position
        
        

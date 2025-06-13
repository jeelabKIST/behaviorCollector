
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QWidget,
    QHBoxLayout, QVBoxLayout, QComboBox, QPlainTextEdit,
    QFormLayout, QPushButton, QLineEdit, QLabel,
    QScrollArea, QGraphicsLineItem, QSizePolicy,
    QFileDialog, QGraphicsTextItem,
    QMessageBox
)

from PyQt5.QtCore import Qt, pyqtSignal, QLineF, QRectF
from PyQt5.QtGui import QPen, QColor, QKeySequence, QFont, QPainter

from collections import OrderedDict
from .video_controller import Controller
from .utils_gui import ColorPicker, tqdm_qt
from .config_menu import MenuBuilder

from ..processing.behav_container import BehavCollector, BEHAV_TYPES, EVENT, STATE
from ..processing.behav_extractor import BehavExtractor
import re


pyqt_KEY_MAP = OrderedDict({  
            Qt.Key_Q: 0,
            Qt.Key_W: 1,
            Qt.Key_E: 2,
            Qt.Key_R: 3,
            Qt.Key_T: 4,
            Qt.Key_A: 5,
            Qt.Key_S: 6,
            Qt.Key_D: 7,
            Qt.Key_F: 8,
            Qt.Key_G: 9,
            Qt.Key_Z: 10, # -> quit collecting
            Qt.Key_X: 11 # -> remove collecting
        })

MAX_KEY = len(pyqt_KEY_MAP) - 2
NUM_TICKS = 5


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
        self._init_ticks()
        self.duration_ms = 0
        
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
        
    def delete_item(self, time_ms):
        for line in self.lines:
            if line.time_ms_start <= time_ms <= line.time_ms_end:
                self.scene.removeItem(line)
        
    def update_duration(self, duration_ms):
        self.duration_ms = duration_ms
        self.max_show = self.max_show_ms / self.duration_ms * self.width
        self.fitInView(QRectF(0, 0, self.max_show, self.height), Qt.IgnoreAspectRatio)
    
    def on_position_changed(self, time_ms: int):
        center_x = time_ms / self.duration_ms * self.width
        self.centerOn(center_x, self.height/2)
        self._update_ticks(time_ms)
    
    def connect_controller(self, video_control_obj: Controller):
        video_control_obj.position_updated.connect(self.on_position_changed)
        self.update_controller = video_control_obj.update_position
        
        
class BehavItemRow(QPushButton):
    def __init__(self, behav_key, behav_name, behav_type, behav_color, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setLayout(QHBoxLayout())
        self.setFixedHeight(60)

        self.behav_name = behav_name
        self.behav_type = behav_type
        self.behav_key = behav_key
        
        self.label_name = QLabel(f"({self.behav_key}) {behav_name} [{behav_type}]")
        
        self.color_box = QLabel()
        self.color_box.setFixedSize(30, 20)
        self.color_box.setStyleSheet(f"background-color: {behav_color}; border: 1px solid black;")

        self.layout().addWidget(self.label_name)
        self.layout().addWidget(self.color_box)

        self.setCheckable(True)
        
    def modify_info(self, behav_name, behav_type, behav_color):
        self.label_name.setText(f"({self.behav_key}) {behav_name} [{behav_type}]")
        self.color_box.setStyleSheet(f"background-color: {behav_color}; border: 1px solid black;")


class BehavPanel(QWidget):
    
    signal_add_line = pyqtSignal(int, str, int, int) # key_id, color code, time_ms_start, time_ms_end
    signal_saved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.bcollector = None
        self.video_controller = None
        self.behav_viewer = None
        self.is_modifying = False
        self.duration_ms = 0
        self._reset_keep()
        
    def _init_ui(self):
        def _set_label(lb):
            label = QLabel(lb)
            return label
        
        layout = QHBoxLayout()
        
        layout_v = QVBoxLayout()
        
        layout_form = QFormLayout()
        self.text_name = QLineEdit()
        self.comb_type = QComboBox()
        self.color_picker = ColorPicker()
        self.button_add = QPushButton("Add Behavior")
        self.text_note = QPlainTextEdit()
        
        layout_form.addRow(_set_label("Behavior Name"), self.text_name)
        layout_form.addRow(_set_label("Behavior type"), self.comb_type)
        layout_form.addRow(_set_label("Color identifier"), self.color_picker)
        layout_form.addRow(_set_label("Note"), self.text_note)
        self._reset_input()
        
        self.comb_type.addItems(BEHAV_TYPES)
        self.button_add.clicked.connect(self._add_behav)
        
        layout_v.addLayout(layout_form)
        layout_v.addWidget(self.button_add)
        layout.addLayout(layout_v)
        
        layout_v2 = QVBoxLayout()
        self.label = QLabel("Behavior List")
        layout_v2.addWidget(self.label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_widget)
        layout_v2.addWidget(self.scroll_area, stretch=7)
        self.behav_rows = []
        
        layout.addLayout(layout_v2)
        self.setLayout(layout)
        
    def connect_menubar(self, menubar: MenuBuilder):
        menubar.load_header_requested.connect(self.load_behavior_header)
        menubar.load_behav_requested.connect(self.load_behavior)
        menubar.save_header_requested.connect(self.export_behavior_header)
        menubar.save_behav_requested.connect(self.export_behavior)
        menubar.export_epochs_requested.connect(self.export_epochs)
        
    def connect_controller(self, video_control_obj: Controller):
        self.video_controller = video_control_obj
        self.video_controller.video_loaded.connect(self.video_loaded)
        self.video_controller.video_closed.connect(self.video_closed)
        self.video_controller.duration_updated.connect(self._update_duration)
        
    def connect_behav_viewer(self, behave_viewer_obj: BehavViewer):
        self.behav_viewer = behave_viewer_obj
        
    def video_loaded(self, video_path: str):
        self.video_path = video_path
        if self.bcollector is None:
            self.bcollector = BehavCollector()
        self.bcollector.add_video_path(video_path)
        
    def video_closed(self, video_id: int):
        self.bcollector.delete_video_path(video_id)
    
    def _add_behav(self):
        if self.bcollector is None:
            raise ValueError("Please load the video first")
        
        name = self.text_name.text()
        type = self.comb_type.currentText()
        note = self.text_note.toPlainText()
        color_code = self.color_picker.color()
        color_hex = color_code.name()
        
        if name == "":
            raise ValueError("Behavior name cannot be empty")
        
        if bool(re.search(r'[\\/:*?"<>|]', name)):
            raise ValueError("Behavior name cannot contain special characters: \\ / : * ? \" < > |")
        
        if self.is_modifying:
            for bid, row in enumerate(self.behav_rows):
                if row.isChecked():
                    break
                
            self.bcollector.set_value(bid, "name", name)
            self.bcollector.set_value(bid, "type", type)
            self.bcollector.set_value(bid, "note", note)
            self.bcollector.set_value(bid, "color_code", color_hex)
            row.modify_info(type, name, color_hex)
            
            self.button_add.setText("Add Behavior")
            self.is_modifying = False
            row.setChecked(False)
            
        else:    
            bid = self.bcollector.num
            
            self.bcollector.add_behav(
                name=name,
                type=type,
                note=note,
                color_code=color_hex
            )
            
            key = list(pyqt_KEY_MAP.keys())[bid]
            key_str = QKeySequence(key).toString()

            row = BehavItemRow(
                key_str, name, type, color_hex
            )
            self.scroll_layout.addWidget(row)
            self.behav_rows.append(row)
            row.clicked.connect(self._modify_behav)
            
        self._reset_input()
        
    def _modify_behav(self):
        self.button_add.setText("Modify Behavior")
        self.is_modifying = True
        
        for bid, row in enumerate(self.behav_rows):
            if row.isChecked():
                break
        
        self.text_name.setText(self.bcollector.get_name(bid))
        self.comb_type.setCurrentText(self.bcollector.get_type(bid))
        self.text_note.setPlainText(self.bcollector.get_note(bid))
        self.color_picker.setColor(QColor(self.bcollector.get_color(bid)))
        
    def load_behavior(self):
        path_dir = QFileDialog.getExistingDirectory(self, "Select behavior directory")
        if path_dir:
            self.bcollector.load(path_dir)
        
        self._add_behav_set()
        for n in range(self.bcollector.num):
            # add behavior event
            for time_ms in self.bcollector.get_value(n, "time_ms"):
                self._add_behav_time(n, time_ms, add_to_collector=False)
                
    def load_behavior_header(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Behavior header",
                                                   "", "Behavior headers (*.json)")
        if file_path:
            self.bcollector = BehavCollector.load_header(file_path)
            self._add_behav_set()
            
    def export_behavior_header(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Behavior header", "", "Behavior headers (*.json)")
        if file_path:
            if self.bcollector.save_header(file_path):
                QMessageBox.information(self, "Success", "Behavior header saved successfully.")
    
    def export_behavior(self):
        path_dir = QFileDialog.getExistingDirectory(self, "Select behavior directory")
        if path_dir:
            if self.bcollector.save(path_dir):
                self.signal_saved.emit()
                QMessageBox.information(self, "Success", "Behavior data saved successfully.")
                
    def export_epochs(self):
        path_dir = QFileDialog.getExistingDirectory(self, "Select export directory")
        if path_dir:
            extractor = BehavExtractor(self.bcollector)
            if extractor.extract_epochs(path_dir, tqdm_fn=tqdm_qt):
                QMessageBox.information(self, "Success", "Behavior epochs exported successfully.")
        
    def _add_behav_set(self):
        for n in range(self.bcollector.num):
            # add behavior
            key = list(pyqt_KEY_MAP.keys())[n]
            key_str = QKeySequence(key).toString()
            
            row = BehavItemRow(
                key_str,
                self.bcollector.get_name(n),
                self.bcollector.get_type(n),
                self.bcollector.get_color(n)
            )
            
            self.scroll_layout.addWidget(row)
            self.behav_rows.append(row)
    
    def _reset_input(self):
        self.text_name.clear()
        self.text_note.clear()
        self.color_picker.setColor(QColor(255,255,255))
        
    def _add_behav_time(self, key_id, time_ms, add_to_collector=True):
        self.bcollector.add_behav_time(key_id, time_ms)
        if not isinstance(time_ms, list):
            _time_ms = [time_ms, time_ms+1]
        else:
            _time_ms = time_ms
        
        self.behav_viewer.add_item(key_id, 
            self.bcollector.get_color(key_id),
            _time_ms[0], _time_ms[1])
    
    def _keep_behav_time(self, key_id):
        if self.key_id_activate != -1 and self.key_id_activate != key_id:
            if key_id < self.bcollector.num:
                raise ValueError("Please add new behavior after saving the last selection")
        
        tp = self.bcollector.get_type(key_id)
        t0 = self.current
        if tp == EVENT:
            self._add_behav_time(key_id, t0)
        elif tp == STATE:
            if self.keep_time_ms != -1:
                self._add_behav_time(key_id, [self.keep_time_ms, t0])
                self._reset_keep()
                self.behav_rows[key_id].setChecked(False)
            else:
                self.keep_time_ms = t0
                self.key_id_activate = key_id
                self.behav_rows[key_id].setChecked(True)
        else:
            raise ValueError(f"Unexpected type {tp}")
    
    def handle_key_input(self, key):
        if key == Qt.Key_Z: # Undo
            self._reset_keep()
        elif key == Qt.Key_X:
            self._delete_behav(self.current)
        else:
            key_id = pyqt_KEY_MAP[key]
            self._keep_behav_time(key_id)
            
    def _reset_keep(self):
        self.keep_time_ms = -1
        self.key_id_activate = -1
        
    def _delete_behav(self, time_ms):
        for b in self.bcollector.behav_set:
            b.delete(time_ms)
        self.behav_viewer.delete_item(time_ms)        
        
    def _update_duration(self, duration_ms):
        self.duration_ms = duration_ms
        if self.behav_viewer is not None:
            self.behav_viewer.update_duration(duration_ms)
        
    @property
    def current(self):
        return self.video_controller.current
                
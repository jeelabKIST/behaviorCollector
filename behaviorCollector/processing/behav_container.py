from dataclasses import dataclass
from typing import Optional, List, Union
from collections import OrderedDict
import json
import os


EVENT = "Event"
STATE = "State"
BEHAV_TYPES = (EVENT, STATE)
PREFIX = "behav"


@dataclass
class BehavInfo:
    name: str
    id: int
    note: str
    type: str
    color_code: str # HEX color code
    video_path: List = None
    time_ms: str = None
    
    # def add_video_path(self, video_path: str):
    #     if self.video_path is None:
    #         self.video_path = []
    #     self.video_path.append(video_path)
        
    # def delete_video_path(self, video_id: int):
    #     self.video_path[video_id] = None
    
    def append(self, time_ms: Union[List, int]=None):
        if self.time_ms is None:
            self.time_ms = []
        
        if self.type == EVENT:
            if isinstance(time_ms, list):
                raise ValueError("Events cannot have multiple time_ms values")
            self.time_ms.append(time_ms)
        elif self.type == STATE:
            if isinstance(time_ms, float):
                raise ValueError("States needs a list of time_ms values")
            self.time_ms.append(time_ms)
            
    def delete(self, del_time_ms):
        for n, t in enumerate(self.time_ms):
            if self.type == EVENT:
                _tr = [t, t+1]
            else:
                _tr = t
            if del_time_ms >= _tr[0] and del_time_ms < _tr[1]:
                self.time_ms.pop(n)
                break
    
    def update_video_path(self, video_path: List[str]):
        self.video_path = video_path
            
    def save(self, path: str):
        file_name = os.path.join(path, f"{PREFIX}_{self.name}.json")
        if self.video_path is None:
            raise ValueError("Please define video_path before saving by calling update_video_path()")

        data = {
            "name": self.name,
            "id": self.id,
            "note": self.note,
            "type": self.type,
            "video_path": self.video_path,
            "color_code": self.color_code,
            "time_ms": self.time_ms if self.time_ms is not None else []
        }
        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def load(file_name: str):
        with open(file_name, 'r') as f:
            data = json.load(f)
        
        return BehavInfo(
            name=data["name"],
            id=data["id"],
            note=data.get("note", ""),
            type=data["type"],
            video_path=data["video_path"],
            color_code=data["color_code"],
            time_ms=data.get("time_ms", [])
        )
        
        
def is_valid_path(func):
    def wrapper(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    return wrapper
        

class BehavCollector:
    def __init__(self):
        self.behav_set = []
        self.video_path = []
        
    def update_video_path(self, video_path: List[str]):
        self.video_path = video_path
        for b in self.behav_set:
            b.update_video_path(video_path)
        
    # def add_video_path(self, video_path: str):
    #     self.video_path.append(video_path)
    #     for b in self.behav_set:
    #         b.add_video_path(video_path)
            
    # def delete_video_path(self, video_id: int):
    #     self.video_path[video_id] = None
    #     for b in self.behav_set:
    #         b.delete_video_path(video_id)
    
    @is_valid_path
    def add_behav_time(self, behav_id, time_ms):
        if self.num <= behav_id:
            return
        self.behav_set[behav_id].append(time_ms)

    def add_behav(self, name: str, note: str, type: str, color_code: str):
        # check first
        for b in self.behav_set:
            if name == b.name:
                raise ValueError(f"Behavior name {name} already exist")
        
        bid = len(self.behav_set)
        self.behav_set.append(
            BehavInfo(
                name=name,
                id=bid,
                note=note,
                type=type,
                color_code=color_code,
                video_path=self.video_path
            )
        )
        
    def delete_behav(self, behav_id):
        self.behav_set.pop(behav_id)
    
    @is_valid_path
    def save(self, path_dir: str):
        if any(os.scandir(path_dir)):
            raise ValueError(f"Directory {path_dir} is not empty")
        
        for behav in self.behav_set:
            behav.save(path_dir)
        return True
    
    @staticmethod
    def load(path_dir: str):
        # if self.num != 0:
        #     raise ValueError("Behavior alread loaded. Please create a new BehavCollector instance.")
        behav_collector = BehavCollector()
        behav_set =  [f for f in os.listdir(path_dir) if PREFIX in f and ".json" in f]
        
        for f in behav_set:
            behav_collector.behav_set.append(BehavInfo.load(os.path.join(path_dir, f)))
        behav_collector.behav_set = sorted(behav_collector.behav_set, key=lambda b: b.id)
        
        return behav_collector
    
    @is_valid_path
    def save_header(self, file_name: str):
        header = {
            "video_path": self.video_path,
            "behav_names": [b.name for b in self.behav_set],
            "types": [b.type for b in self.behav_set],
            "color_codes": [b.color_code for b in self.behav_set],
            "notes": [b.note for b in self.behav_set]
        }
        with open(file_name, "w") as f:
            json.dump(header, f, indent=4)
        
        return True
    
    @staticmethod
    def load_header(file_name: str):
        with open(file_name, 'r') as f:
            header = json.load(f)
        
        behav_collector = BehavCollector()

        for name, tp, c, note in zip(header["behav_names"], header["types"], header["color_codes"], header["notes"]):
            behav_collector.add_behav(
                name=name,
                type=tp,
                color_code=c,
                note=note
            )

        return behav_collector

    @property
    def num(self):
        return len(self.behav_set)
    
    def get_value(self, key_id, key):
        if self.num > key_id:
            return getattr(self.behav_set[key_id], key)
        else:
            raise ValueError(f"ID {key_id} is not defined yet")
        
    def set_value(self, key_id, key, value):
        assert self.num > key_id
        setattr(self.behav_set[key_id], key, value)
    
    def get_type(self, key_id):
        return self.get_value(key_id, "type")
    
    def get_color(self, key_id):
        return self.get_value(key_id, "color_code")
    
    def get_name(self, key_id):
        return self.get_value(key_id, "name")
    
    def get_note(self, key_id):
        return self.get_value(key_id, "note")
    


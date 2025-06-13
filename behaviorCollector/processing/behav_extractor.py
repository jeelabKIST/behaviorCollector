import cv2
import os
import warnings
from .behav_container import BehavCollector, EVENT, STATE
from tqdm import tqdm


FPS_WRITE = 10


class BehavExtractor:
    def __init__(self, bcollector: BehavCollector):
        self.bcollector = bcollector
        self.video_capture = [
            cv2.VideoCapture(path) for path in bcollector.video_path if path is not None
        ]
        
    def extract_epochs(self, path_dir: str, tqdm_fn=None):
        if any(os.scandir(path_dir)):
            warnings.warn(f"Directory {path_dir} is not empty")
            
        if tqdm_fn is None:
            tqdm_fn = tqdm
        
        for b in self.bcollector.behav_set:
            bar = tqdm_fn(total=len(b.time_ms), desc=f"Extracting {b.name} epochs")
            for n in range(len(b.time_ms)):
                try:
                    if b.type == STATE:
                        start_ms = b.time_ms[n][0]
                        end_ms = b.time_ms[n][1]
                        
                        # name_start time_end time (video_id)
                        prefix = os.path.join(path_dir, f"{b.name}_{start_ms//1000}_{end_ms//1000}")
                        self.extract_single_epoch(prefix, start_ms, end_ms)
                    elif b.type == EVENT:
                        start_ms = b.time_ms[n]
                        prefix = os.path.join(path_dir, f"{b.name}_{start_ms//1000}")
                        self.extract_single_event(prefix, start_ms)
                except Exception as e:
                    warnings.warn(f"Failed to extract epoch {n} for behavior {b.name}: {e}")
                bar.update()
            bar.close()
        
        return True
    
    def extract_single_epoch(self, prefix_video, start_ms: int, end_ms: int):
        for n, cap in enumerate(self.video_capture):
            if not cap.isOpened():
                raise ValueError("Video capture cannot be opened")
            
            writter = cv2.VideoWriter(
                f"{prefix_video}({n}).avi",
                cv2.VideoWriter_fourcc(*'XVID'),
                FPS_WRITE,
                (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            )
            
            cap.set(cv2.CAP_PROP_POS_MSEC, start_ms)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                current_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                if current_ms > end_ms:
                    break
                writter.write(frame)
            writter.release()

    def extract_single_event(self, perfix_event, start_ms: int):
        for n, cap in enumerate(self.video_capture):
            if not cap.isOpened():
                raise ValueError("Video capture cannot be opened")
            
            cap.set(cv2.CAP_PROP_POS_MSEC, start_ms)
            ret, frame = cap.read()
            if not ret:
                raise ValueError(f"Failed to read frame at {perfix_event} ms")
            
            cv2.imwrite(f"{perfix_event}({n}).jpg", frame)
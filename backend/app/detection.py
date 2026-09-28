from pathlib import Path
from ultralytics import YOLO

DEFAULT_MODEL = Path(__file__).resolve().parents[1] / 'models' / 'best.pt'

def load_model(model_path=None):
    path = Path(model_path or DEFAULT_MODEL)
    if not path.exists():
        raise FileNotFoundError(f'Trained YOLO model not found: {path}')
    return YOLO(str(path))

def track_frame(model, frame, conf=0.30):
    return model.track(frame, persist=True, conf=conf, verbose=False)

def extract_detections(result):
    names = result.names
    boxes = result.boxes
    out = []
    if boxes is None:
        return out
    ids = boxes.id.int().cpu().tolist() if boxes.id is not None else [None] * len(boxes)
    xyxy = boxes.xyxy.cpu().tolist()
    cls = boxes.cls.int().cpu().tolist()
    confs = boxes.conf.cpu().tolist()
    for i, b in enumerate(xyxy):
        x1, y1, x2, y2 = map(float, b)
        cid = int(cls[i])
        out.append({
            'track_id': ids[i],
            'class_id': cid,
            'vehicle_class': str(names[cid]),
            'confidence': float(confs[i]),
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'center_x': (x1+x2)/2,
            'center_y': (y1+y2)/2,
        })
    return out

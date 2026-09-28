from collections import defaultdict
from pathlib import Path
import json
import math
import pandas as pd
import numpy as np

VEHICLE_NAME_HINTS = ('car','bus','truck','suv','sedan','hatch','muv','lcv','van','vehicle','motor','bike','two','three','auto','rickshaw')
PERSON_NAMES = {'person','pedestrian'}

def is_vehicle(name):
    n = name.lower()
    return n not in PERSON_NAMES and any(x in n for x in VEHICLE_NAME_HINTS)

def zone(cx, cy, w, h):
    col = 'L' if cx < w/3 else ('C' if cx < 2*w/3 else 'R')
    row = 'T' if cy < h/3 else ('M' if cy < 2*h/3 else 'B')
    return row + col

def stopped_ratio(current, previous, threshold_px=2.0):
    if not current:
        return 0.0
    prev = previous or {}
    stopped = 0
    known = 0
    for d in current:
        tid = d.get('track_id')
        if tid is None or tid not in prev:
            continue
        known += 1
        ox, oy = prev[tid]
        if math.hypot(d['center_x']-ox, d['center_y']-oy) <= threshold_px:
            stopped += 1
    return stopped / known if known else 0.0

def density(count, width, height):
    area_mpx = max((width*height)/1_000_000, 0.1)
    return count / area_mpx

def congestion_level(dens, stopped):
    score = min(100.0, dens*1.8 + stopped*60)
    if score >= 70: return 'HIGH'
    if score >= 40: return 'MEDIUM'
    return 'LOW'

def make_heatmap(points, width, height, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    path = Path(path)
    if not points:
        return None
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    plt.figure(figsize=(10,6))
    plt.hist2d(xs, ys, bins=(32,18), range=[[0,width],[0,height]])
    plt.gca().invert_yaxis(); plt.xlabel('X'); plt.ylabel('Y'); plt.title('Traffic Movement Heatmap')
    plt.tight_layout(); plt.savefig(path, dpi=140); plt.close()
    return str(path)

def build_summary(events, congestion_rows, fps, width, height, out_dir, video_name, annotated_video, heatmap_path):
    duration = len(congestion_rows) / fps if fps else 0
    ids = {r['track_id'] for r in events if r.get('track_id') is not None}
    class_ids = defaultdict(set)
    for r in events:
        if r.get('track_id') is not None:
            class_ids[r['vehicle_class']].add(r['track_id'])
    avg_density = float(np.mean([r['density'] for r in congestion_rows])) if congestion_rows else 0
    avg_stopped = float(np.mean([r['stopped_ratio'] for r in congestion_rows])) if congestion_rows else 0
    congestion = congestion_level(avg_density, avg_stopped)
    flow = (len(ids)/duration*3600) if duration else 0
    summary = {
        'video_name': video_name, 'frames': len(congestion_rows), 'duration_s': duration,
        'total_vehicles': len(ids), 'vehicle_counts': {k: len(v) for k,v in class_ids.items()},
        'average_density': avg_density, 'congestion': congestion, 'flow_vph': flow,
        'annotated_video': annotated_video, 'heatmap': heatmap_path
    }
    p = Path(out_dir)/'summary.json'; p.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary

from pathlib import Path
import os

# FinalProtype/
PROJECT_DIR = Path(__file__).resolve().parents[2]

# Data
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
UPLOAD_DIR = DATA_DIR / "uploads"
HISTORY_DIR = DATA_DIR / "history"
OUTPUT_DIR = DATA_DIR / "outputs"

# Trained YOLO model
MODEL_DIR = PROJECT_DIR / "models"
MODEL_PATH = MODEL_DIR / "best.pt"

# Permanent demo video
VIDEO_CANDIDATES = [
    RAW_DIR / "traffic.mp4",
    RAW_DIR / "traffic.avi",
    RAW_DIR / "traffic.mov",
    RAW_DIR / "traffic.mkv",
    RAW_DIR / "traffic.webm",
]
DEMO_VIDEO = next((p for p in VIDEO_CANDIDATES if p.exists()), RAW_DIR / "traffic.mp4")

# SQLite database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + (DATA_DIR / "traffic.db").as_posix()
)

# Create required directories
for p in (
    RAW_DIR,
    UPLOAD_DIR,
    HISTORY_DIR,
    OUTPUT_DIR,
    MODEL_DIR,
):
    p.mkdir(parents=True, exist_ok=True)
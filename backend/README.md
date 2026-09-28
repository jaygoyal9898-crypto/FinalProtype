# AI Traffic Backend

## Folder setup

Put your trained model here:

`backend/models/best.pt`

Put the fixed traffic video here:

`backend/data/raw/traffic.mp4` (the supplied package also contains `traffic.avi` as a fallback)

The application does **not** require a browser upload. The dashboard automatically starts the configured video.

## Run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.api:app --reload
```

API: `http://127.0.0.1:8000`
Docs: `http://127.0.0.1:8000/docs`

## Live architecture

YOLO processes the fixed video in a background worker. Every few frames the backend updates:

- `live_frame.jpg`
- `live_state.json`
- `frame_stats.json`

The React dashboard reads those files through API endpoints, so the dashboard updates while YOLO is still processing instead of waiting for the final MP4.

If FFmpeg is installed, the backend also creates a browser-compatible H.264 `traffic_browser.mp4` after processing. The live dashboard does not depend on that MP4.

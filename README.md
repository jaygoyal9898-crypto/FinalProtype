# AI Traffic Decision Support — SQLite Final Prototype

This version requires **no PostgreSQL, Docker, pgAdmin, or database server**. SQLite is created automatically as `backend/data/traffic.db`.

## Included

- YOLO detection + tracking
- Vehicle-class counting
- Unique tracked-vehicle counting
- Density estimation
- Congestion estimation
- Traffic-flow estimate (vehicles/hour)
- Annotated YOLO video
- Traffic heatmap
- Drag-and-drop video upload
- Background video processing
- Current-analysis dashboard
- Analysis history stored in SQLite
- Permanent demo video
- FastAPI + Swagger
- Frontend with no Node/npm requirement

## 1. Put your model and demo video

Copy your trained model to:

`backend/models/best.pt`

Put your permanent demo video at:

`backend/data/raw/demo.mp4`

You can use any of your four traffic videos as `demo.mp4`. Other videos can be uploaded through the dashboard.

## 2. Create/activate the virtual environment

From the `backend` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you already have the working `.venv`, keep using it.

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

No PostgreSQL installation is required.

## 4. Test the ML pipeline

```powershell
python -m app.cli process
```

The generated analysis is stored under:

`backend/data/history/`

The SQLite database is:

`backend/data/traffic.db`

## 5. Start the API

```powershell
python -m uvicorn app.api:app --reload --port 8000
```

Open:

`http://127.0.0.1:8000/docs`

## 6. Start the frontend

Open a second PowerShell window:

```powershell
cd frontend
python -m http.server 5500
```

Then open:

`http://127.0.0.1:5500`

## Upload workflow

The dashboard permanently shows the demo video when available. Drag another traffic video into the upload panel. The backend saves it, runs YOLO detection/tracking, calculates vehicle counts, density, congestion and flow, creates a heatmap and stores the completed analysis in SQLite. The newest analysis replaces the active dashboard while previous analyses remain in history.

## Current scope

The yellow foundation is implemented. Passenger occupancy, advanced destination prediction, route-diversion prediction, Google Maps live-traffic integration and live CCTV are intentionally left for the later red-feature phase.

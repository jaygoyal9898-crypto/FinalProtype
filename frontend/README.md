# AI Traffic Frontend

## Run

```powershell
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend connects to `http://127.0.0.1:8000` by default. To change it, create `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

There is intentionally no video upload button. The backend uses `backend/data/raw/traffic.mp4` as the configured traffic source and starts YOLO automatically from the dashboard.

# ClipCutter 🎬✂

YouTube video trimmer & downloader — React frontend + Flask backend.

## Project structure

```
clipcutter/
├── frontend/               ← React app  (deploy to Vercel)
│   ├── src/
│   │   ├── App.js          ← Main UI component
│   │   ├── api.js          ← All backend API calls
│   │   └── index.js        ← React entry point
│   ├── public/index.html
│   ├── package.json
│   ├── vercel.json
│   ├── .env.development    ← Local API URL (http://localhost:5000)
│   └── .env.production     ← Production API URL (Railway)
│
├── backend/                ← Flask API  (deploy to Railway)
│   ├── server.py           ← All API routes
│   ├── requirements.txt
│   ├── Procfile            ← Railway start command
│   └── nixpacks.toml       ← Tells Railway to install ffmpeg
│
└── .gitignore
```

---

## Local development

### 1 — Backend

```bash
cd backend
pip install -r requirements.txt

# ffmpeg also needed:
# Ubuntu/Debian:  sudo apt install ffmpeg
# Mac:            brew install ffmpeg
# Windows:        https://ffmpeg.org/download.html  → add to PATH

python server.py
# → 🚀 Backend running at http://localhost:5000
```

### 2 — Frontend

```bash
cd frontend
npm install
npm start
# → App opens at http://localhost:3000
```

`frontend/.env.development` already points to `http://localhost:5000` — no changes needed for local dev.

---

## Deploy to production (free)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/clipcutter.git
git push -u origin main
```

### Step 2 — Deploy Backend to Railway

1. Go to **railway.app** → New Project → Deploy from GitHub
2. Select your repo → set **Root Directory** to `backend`
3. Railway auto-detects `nixpacks.toml` and installs Python + ffmpeg
4. Add environment variable:
   - `FRONTEND_URL` = `https://your-app.vercel.app`  ← (fill after Vercel deploy)
5. Click **Deploy** — Railway gives you a URL like `https://clipcutter-backend-xxxx.railway.app`

### Step 3 — Update frontend production URL

Edit `frontend/.env.production`:
```
REACT_APP_API_URL=https://clipcutter-backend-xxxx.railway.app
```

Commit and push:
```bash
git add frontend/.env.production
git commit -m "Set Railway backend URL"
git push
```

### Step 4 — Deploy Frontend to Vercel

1. Go to **vercel.com** → New Project → Import from GitHub
2. Set **Root Directory** to `frontend`
3. Vercel auto-detects React, sets build command to `npm run build`
4. Click **Deploy** — you get `https://clipcutter.vercel.app`

### Step 5 — Update Railway CORS

Go back to Railway → your backend service → Variables:
- Set `FRONTEND_URL` = `https://clipcutter.vercel.app`
- Railway auto-restarts the service

---

## API endpoints

| Method | Path         | Body                                                      | Returns              |
|--------|--------------|-----------------------------------------------------------|----------------------|
| GET    | `/api/health`| —                                                         | `{ ok: true }`       |
| POST   | `/api/info`  | `{ url }`                                                 | Video metadata + qualities |
| POST   | `/api/clip`  | `{ url, start, end, quality, format }`                    | MP4/MP3/WebM file    |

### `/api/clip` body example

```json
{
  "url":     "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "start":   "0:30",
  "end":     "1:15",
  "quality": "720",
  "format":  "mp4"
}
```

Limits: max 10 minutes per clip. Quality must be one returned by `/api/info`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Backend offline in header | Run `python server.py` locally or check Railway logs |
| `yt-dlp` fails on some videos | Update: `pip install -U yt-dlp` |
| ffmpeg not found on Railway | Check `nixpacks.toml` is in `backend/` folder |
| CORS error in browser | Add your Vercel URL to `FRONTEND_URL` env var on Railway |
| Quality not available | Select a lower quality — video may not have 1080p |

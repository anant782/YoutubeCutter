// All API calls live here.
// URL comes from .env files — never hardcoded.

const BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";

// ─── Health check ─────────────────────────────────────────────
export async function checkHealth() {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json(); // { ok: true, version: "1.0.0" }
}

// ─── Fetch video info ─────────────────────────────────────────
// Returns: { title, duration, thumbnail, channel, view_count, video_id, qualities }
export async function fetchVideoInfo(url) {
  const res = await fetch(`${BASE}/api/info`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ url }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);
  return data;
}

// ─── Download clip ────────────────────────────────────────────
// Streams the MP4/MP3/WebM directly into a browser download.
// onProgress(pct, msg) is called periodically during the fake progress animation.
export async function downloadClip({ url, start, end, quality, format }, onProgress) {
  // Fake progress steps while server processes
  const stages = [
    [10, "Video download ho raha hai..."],
    [30, "Video download ho raha hai..."],
    [55, `Clip trim ho rahi hai (${start} → ${end})...`],
    [75, `${quality}p ${format.toUpperCase()} encode ho raha hai...`],
    [90, "File ready ho rahi hai..."],
  ];

  let stageIdx = 0;
  const ticker = setInterval(() => {
    if (stageIdx < stages.length) {
      const [pct, msg] = stages[stageIdx++];
      onProgress(pct, msg);
    }
  }, 800);

  try {
    const res = await fetch(`${BASE}/api/clip`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url, start, end, quality, format }),
    });

    clearInterval(ticker);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Server error ${res.status}`);
    }

    onProgress(98, "File download ho rahi hai...");

    // Trigger browser file download
    const blob     = await res.blob();
    const dispo    = res.headers.get("content-disposition") || "";
    const fnMatch  = dispo.match(/filename="?([^"]+)"?/);
    const filename = fnMatch
      ? fnMatch[1]
      : `clip_${start.replace(":", "")}_${end.replace(":", "")}.${format}`;

    const link = document.createElement("a");
    link.href  = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);

    onProgress(100, "Download complete!");
  } catch (err) {
    clearInterval(ticker);
    throw err;
  }
}

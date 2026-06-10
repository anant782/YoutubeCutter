import { useState, useRef, useCallback, useEffect } from "react";
import { fetchVideoInfo, downloadClip, checkHealth } from "./api";

// ─── Constants ────────────────────────────────────────────────
const QUALITIES_ORDER = ["2160","1440","1080","720","480","360","240","144"];
const QUALITY_BADGE   = { "2160":"4K","1440":"2K","1080":"FHD","720":"HD" };
const FORMATS = [
  { id:"mp4",  label:"MP4",       icon:"🎬" },
  { id:"webm", label:"WebM",      icon:"🌐" },
  { id:"mp3",  label:"MP3 Audio", icon:"🎵" },
];

// ─── Helpers ──────────────────────────────────────────────────
const pad = n => String(Math.floor(n)).padStart(2, "0");

function secToStr(s) {
  const h   = Math.floor(s / 3600);
  const m   = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
}

function strToSec(str) {
  const parts = String(str).trim().split(":").map(Number);
  if (parts.some(isNaN)) return 0;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return parts[0] || 0;
}

function fmtViews(n) {
  if (!n) return "";
  if (n >= 1e9) return (n / 1e9).toFixed(1) + "B views";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M views";
  if (n >= 1e3) return (n / 1e3).toFixed(0) + "K views";
  return n + " views";
}

function estSize(quality, clipDur, fmt) {
  if (fmt === "mp3") {
    const kb = 128 * clipDur / 8;
    return kb > 1024 ? `~${(kb / 1024).toFixed(1)} MB` : `~${Math.round(kb)} KB`;
  }
  const kbps = { "2160":15000,"1440":8000,"1080":4000,"720":2000,"480":800,"360":400,"240":200,"144":100 };
  const kb   = (kbps[quality] || 1000) * clipDur / 8;
  return kb > 1024 ? `~${(kb / 1024).toFixed(1)} MB` : `~${Math.round(kb)} KB`;
}

// ─── Timeline component ───────────────────────────────────────
function Timeline({ totalSec, startSec, endSec, onChange }) {
  const ref  = useRef(null);
  const drag = useRef(null);

  const pct   = v => (totalSec > 0 ? (v / totalSec) * 100 : 0);
  const secAt = useCallback(clientX => {
    const r = ref.current.getBoundingClientRect();
    return Math.round(Math.max(0, Math.min(1, (clientX - r.left) / r.width)) * totalSec);
  }, [totalSec]);

  const onDown = (e, which) => {
    e.preventDefault();
    drag.current = which;
    const mv = ev => {
      const s = secAt(ev.clientX);
      if (drag.current === "s") onChange(Math.min(s, endSec - 1), endSec);
      else                       onChange(startSec, Math.max(s, startSec + 1));
    };
    const up = () => {
      drag.current = null;
      window.removeEventListener("mousemove", mv);
      window.removeEventListener("mouseup",   up);
    };
    window.addEventListener("mousemove", mv);
    window.addEventListener("mouseup",   up);
  };

  const sp = pct(startSec);
  const ep = pct(endSec);
  const bars = Array.from({ length: 60 }, (_, i) =>
    8 + Math.sin(i * 0.7) * 5 + Math.sin(i * 0.23 + 1) * 4
  );

  return (
    <div style={{ userSelect: "none" }}>
      <div
        ref={ref}
        onClick={e => {
          if (drag.current) return;
          const s = secAt(e.clientX);
          Math.abs(s - startSec) < Math.abs(s - endSec)
            ? onChange(Math.min(s, endSec - 1), endSec)
            : onChange(startSec, Math.max(s, startSec + 1));
        }}
        style={{ position:"relative", height:48, background:"#12122a", borderRadius:8, cursor:"pointer", border:"1px solid #23234a" }}
      >
        {bars.map((h, i) => (
          <div key={i} style={{
            position:"absolute", left:`${(i/60)*100}%`, bottom:"50%",
            transform:"translateY(50%)", width:"1.2%", height:h,
            background: ((i/60)*100 >= sp && (i/60)*100 <= ep) ? "#f97316" : "#23234a",
            borderRadius:2, transition:"background .08s",
          }}/>
        ))}
        <div style={{ position:"absolute", top:0, left:`${sp}%`, width:`${ep-sp}%`, height:"100%",
          background:"rgba(249,115,22,.13)", borderTop:"2px solid #f97316",
          borderBottom:"2px solid #f97316", pointerEvents:"none" }}/>
        {[["s", sp], ["e", ep]].map(([which, p]) => (
          <div key={which} onMouseDown={e => onDown(e, which)} style={{
            position:"absolute", left:`${p}%`, top:"50%", transform:"translate(-50%,-50%)",
            width:18, height:34, background:"#f97316", borderRadius:4, cursor:"ew-resize",
            zIndex:10, display:"flex", alignItems:"center", justifyContent:"center",
            boxShadow:"0 2px 10px rgba(249,115,22,.55)",
          }}>
            <div style={{ display:"flex", gap:2 }}>
              {[0, 1].map(k => <div key={k} style={{ width:2, height:14, background:"rgba(255,255,255,.75)", borderRadius:1 }}/>)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── TimeInput component ──────────────────────────────────────
function TimeInput({ label, value, onChange, max }) {
  const [edit, setEdit] = useState(false);
  const [raw,  setRaw]  = useState(value);

  useEffect(() => { if (!edit) setRaw(value); }, [value, edit]);

  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize:11, color:"#666", marginBottom:5, textTransform:"uppercase", letterSpacing:".06em" }}>{label}</div>
      <input
        value={edit ? raw : value}
        onFocus={() => { setEdit(true); setRaw(value); }}
        onChange={e => setRaw(e.target.value)}
        onBlur={() => { setEdit(false); onChange(Math.max(0, Math.min(strToSec(raw), max))); }}
        onKeyDown={e => e.key === "Enter" && e.target.blur()}
        style={{ width:"100%", background:"#12122a", border:"1.5px solid #23234a", borderRadius:8,
          padding:"10px 12px", color:"#fff", fontSize:18, fontWeight:700,
          fontFamily:"monospace", textAlign:"center", outline:"none", boxSizing:"border-box" }}
      />
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────
export default function App() {
  const [url,        setUrl]        = useState("");
  const [videoInfo,  setVideoInfo]  = useState(null);
  const [infoLoading,setInfoLoading]= useState(false);
  const [infoErr,    setInfoErr]    = useState("");
  const [startSec,   setStartSec]   = useState(0);
  const [endSec,     setEndSec]     = useState(30);
  const [quality,    setQuality]    = useState("720");
  const [format,     setFormat]     = useState("mp4");
  const [dlState,    setDlState]    = useState("idle"); // idle | loading | done | error
  const [dlMsg,      setDlMsg]      = useState("");
  const [progress,   setProgress]   = useState(0);
  const [backendOk,  setBackendOk]  = useState(null); // null = checking, true/false

  const totalSec = videoInfo?.duration || 300;
  const clipDur  = endSec - startSec;

  // Check backend on mount
  useEffect(() => {
    checkHealth()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  // Load video info
  const handleLoad = async () => {
    if (!url.trim()) { setInfoErr("YouTube URL daalo"); return; }
    setInfoLoading(true); setInfoErr(""); setVideoInfo(null); setDlState("idle");
    try {
      const data = await fetchVideoInfo(url);
      setVideoInfo(data);
      const dur = data.duration || 300;
      setStartSec(0);
      setEndSec(Math.min(30, dur));
      // Auto-select best available quality
      const avail = data.qualities || [];
      const best  = ["1080","720","480","360"].find(q => avail.includes(q)) || avail[0] || "720";
      setQuality(best);
    } catch (e) {
      setInfoErr(e.message);
    } finally {
      setInfoLoading(false);
    }
  };

  // Download clip
  const handleDownload = async () => {
    setDlState("loading"); setProgress(5); setDlMsg("Request bhej raha hai...");
    try {
      await downloadClip(
        { url, start: secToStr(startSec), end: secToStr(endSec), quality, format },
        (pct, msg) => { setProgress(pct); setDlMsg(msg); }
      );
      setDlState("done");
    } catch (e) {
      setDlState("error");
      setDlMsg(e.message);
    }
  };

  const isAvail = q => videoInfo?.qualities?.includes(q);

  // ── Render ────────────────────────────────────────────────
  return (
    <div style={{ minHeight:"100vh", background:"#0b0b18", color:"#fff",
      fontFamily:"'Inter',-apple-system,sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing:border-box }
        input::placeholder { color:#444 }
        input:focus { border-color:#f97316!important; box-shadow:0 0 0 3px rgba(249,115,22,.15) }
        button:hover:not(:disabled) { filter:brightness(1.1) }
        ::-webkit-scrollbar { width:5px }
        ::-webkit-scrollbar-track { background:#0b0b18 }
        ::-webkit-scrollbar-thumb { background:#23234a; border-radius:3px }
        @keyframes spin { to { transform:rotate(360deg) } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(10px) } to { opacity:1; transform:translateY(0) } }
        .card { animation: fadeUp .2s ease }
      `}</style>

      {/* ── Header ─────────────────────────────────────────── */}
      <div style={{ borderBottom:"1px solid #16163a", padding:"14px 24px",
        display:"flex", alignItems:"center", gap:10,
        position:"sticky", top:0, background:"rgba(11,11,24,.92)",
        backdropFilter:"blur(8px)", zIndex:100 }}>
        <div style={{ width:34, height:34, background:"#f97316", borderRadius:9,
          display:"flex", alignItems:"center", justifyContent:"center", fontSize:17, flexShrink:0 }}>✂</div>
        <div>
          <div style={{ fontWeight:700, fontSize:15, letterSpacing:"-.02em" }}>ClipCutter</div>
          <div style={{ fontSize:11, color:"#555" }}>YouTube video trimmer & downloader</div>
        </div>
        {/* Backend status indicator */}
        <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:6, fontSize:12,
          color: backendOk === null ? "#666" : backendOk ? "#22c55e" : "#ef4444" }}>
          <div style={{ width:7, height:7, borderRadius:"50%",
            background: backendOk === null ? "#666" : backendOk ? "#22c55e" : "#ef4444" }}/>
          {backendOk === null ? "Connecting..." : backendOk ? "Backend connected" : "Backend offline"}
        </div>
      </div>

      {/* Backend offline warning */}
      {backendOk === false && (
        <div style={{ background:"rgba(239,68,68,.1)", borderBottom:"1px solid rgba(239,68,68,.3)",
          padding:"10px 24px", fontSize:13, color:"#ef4444", textAlign:"center" }}>
          ⚠ Backend offline — <code style={{ fontSize:12 }}>python server.py</code> locally chalao ya Railway deploy karo
        </div>
      )}

      <div style={{ maxWidth:820, margin:"0 auto", padding:"28px 20px" }}>

        {/* ── URL Card ──────────────────────────────────────── */}
        <div className="card" style={{ background:"#12122a", borderRadius:14,
          border:"1px solid #1e1e42", padding:20, marginBottom:20 }}>
          <div style={{ fontSize:12, color:"#666", marginBottom:8,
            textTransform:"uppercase", letterSpacing:".06em" }}>YouTube URL</div>
          <div style={{ display:"flex", gap:10 }}>
            <div style={{ flex:1, display:"flex", alignItems:"center",
              background:"#0b0b18", border:"1.5px solid #23234a",
              borderRadius:10, padding:"0 14px" }}>
              <span style={{ marginRight:8, fontSize:15 }}>🔗</span>
              <input
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleLoad()}
                placeholder="https://www.youtube.com/watch?v=..."
                style={{ flex:1, background:"none", border:"none", color:"#fff",
                  fontSize:14, outline:"none", padding:"13px 0" }}
              />
              {url && (
                <button onClick={() => { setUrl(""); setVideoInfo(null); setDlState("idle"); }}
                  style={{ background:"none", border:"none", color:"#555",
                    cursor:"pointer", fontSize:20, padding:"0 2px", lineHeight:1 }}>×</button>
              )}
            </div>
            <button onClick={handleLoad} disabled={infoLoading || !url.trim()}
              style={{ background: infoLoading || !url.trim() ? "#23234a" : "#f97316",
                border:"none", borderRadius:10, padding:"0 22px",
                color: infoLoading || !url.trim() ? "#555" : "#fff",
                fontWeight:700, fontSize:14,
                cursor: infoLoading || !url.trim() ? "not-allowed" : "pointer",
                minWidth:110, transition:"background .2s",
                display:"flex", alignItems:"center", gap:6 }}>
              {infoLoading
                ? <><span style={{ display:"inline-block", animation:"spin 1s linear infinite" }}>⟳</span> Loading...</>
                : "▶  Load"}
            </button>
          </div>
          {infoErr && (
            <div style={{ marginTop:9, color:"#ef4444", fontSize:13 }}>⚠ {infoErr}</div>
          )}
        </div>

        {/* ── Video Info ────────────────────────────────────── */}
        {videoInfo && (
          <div className="card" style={{ display:"flex", gap:14, background:"#12122a",
            borderRadius:14, border:"1px solid #1e1e42", padding:16, marginBottom:20 }}>
            <img
              src={videoInfo.thumbnail || `https://img.youtube.com/vi/${videoInfo.video_id}/mqdefault.jpg`}
              alt="thumbnail"
              onError={e => { e.target.src = `https://img.youtube.com/vi/${videoInfo.video_id}/mqdefault.jpg`; }}
              style={{ width:140, height:79, objectFit:"cover", borderRadius:8,
                flexShrink:0, background:"#0b0b18" }}
            />
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontWeight:600, fontSize:14, marginBottom:4,
                overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                {videoInfo.title}
              </div>
              <div style={{ fontSize:12, color:"#666", marginBottom:10 }}>
                {videoInfo.channel}{videoInfo.view_count ? ` · ${fmtViews(videoInfo.view_count)}` : ""}
              </div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                <span style={{ background:"#0b0b18", border:"1px solid #23234a",
                  borderRadius:6, padding:"3px 10px", fontSize:11, color:"#888" }}>
                  ⏱ {secToStr(videoInfo.duration)}
                </span>
                <span style={{ background:"rgba(34,197,94,.1)", border:"1px solid rgba(34,197,94,.3)",
                  borderRadius:6, padding:"3px 10px", fontSize:11, color:"#22c55e" }}>
                  ✓ Ready to trim
                </span>
                {(videoInfo.qualities || []).slice(0, 3).map(q => (
                  <span key={q} style={{ background:"rgba(124,58,237,.1)", border:"1px solid rgba(124,58,237,.3)",
                    borderRadius:6, padding:"3px 8px", fontSize:11, color:"#a78bfa" }}>{q}p</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Trim Card ─────────────────────────────────────── */}
        {videoInfo && (
          <div className="card" style={{ background:"#12122a", borderRadius:14,
            border:"1px solid #1e1e42", padding:20, marginBottom:20 }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:16 }}>
              <span style={{ background:"#f97316", borderRadius:5, padding:"3px 9px",
                fontSize:11, fontWeight:700 }}>✂ TRIM</span>
              <span style={{ fontSize:13, color:"#666" }}>Handles drag karo ya time type karo</span>
            </div>
            <Timeline totalSec={totalSec} startSec={startSec} endSec={endSec}
              onChange={(s, e) => { setStartSec(s); setEndSec(e); }} />
            <div style={{ display:"flex", gap:16, marginTop:16, alignItems:"flex-end" }}>
              <TimeInput label="▶ Start" value={secToStr(startSec)}
                onChange={s => setStartSec(Math.min(s, endSec - 1))} max={totalSec} />
              <div style={{ paddingBottom:10, color:"#333", fontSize:22 }}>→</div>
              <TimeInput label="■ End" value={secToStr(endSec)}
                onChange={e => setEndSec(Math.max(e, startSec + 1))} max={totalSec} />
              <div style={{ paddingBottom:4, flex:"0 0 auto", textAlign:"right" }}>
                <div style={{ fontSize:10, color:"#555", marginBottom:3,
                  textTransform:"uppercase", letterSpacing:".06em" }}>Clip</div>
                <div style={{ fontSize:26, fontWeight:800, color:"#f97316",
                  fontFamily:"monospace", lineHeight:1 }}>{secToStr(clipDur)}</div>
              </div>
            </div>
            {/* Quick presets */}
            <div style={{ display:"flex", gap:7, marginTop:14, flexWrap:"wrap", alignItems:"center" }}>
              <span style={{ fontSize:12, color:"#555" }}>Quick:</span>
              {[
                ["Pehle 30s",   0,                          30],
                ["Pehle 1min",  0,                          60],
                ["Beech",       Math.floor(totalSec/2)-30,  Math.floor(totalSec/2)+30],
                ["Aakhri 30s",  Math.max(0, totalSec-30),   totalSec],
              ].map(([label, s, e]) => (
                <button key={label}
                  onClick={() => { setStartSec(Math.max(0, s)); setEndSec(Math.min(totalSec, e)); }}
                  style={{ background:"#0b0b18", border:"1px solid #23234a", borderRadius:6,
                    padding:"4px 10px", color:"#888", fontSize:12, cursor:"pointer" }}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Quality Card ──────────────────────────────────── */}
        {videoInfo && (
          <div className="card" style={{ background:"#12122a", borderRadius:14,
            border:"1px solid #1e1e42", padding:20, marginBottom:20 }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:14 }}>
              <span style={{ background:"#7c3aed", borderRadius:5, padding:"3px 9px",
                fontSize:11, fontWeight:700 }}>⚙ QUALITY</span>
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8, marginBottom:16 }}>
              {QUALITIES_ORDER.map(q => {
                const avail  = isAvail(q);
                const active = quality === q;
                const badge  = QUALITY_BADGE[q];
                return (
                  <button key={q} onClick={() => avail && setQuality(q)}
                    style={{ padding:"10px 6px", borderRadius:8, position:"relative",
                      border:  active ? "1.5px solid #f97316" : "1px solid #23234a",
                      background: active ? "rgba(249,115,22,.12)" : avail ? "#0b0b18" : "#0d0d1f",
                      color:   active ? "#f97316" : avail ? "#ccc" : "#333",
                      fontSize:13, fontWeight: active ? 700 : 400,
                      cursor:  avail ? "pointer" : "not-allowed", transition:"all .15s" }}>
                    {badge && (
                      <div style={{ position:"absolute", top:-1, right:-1,
                        background: active ? "#f97316" : avail ? "#7c3aed" : "#23234a",
                        color:"#fff", fontSize:9, padding:"1px 5px",
                        borderRadius:"0 6px 0 4px", fontWeight:700 }}>{badge}</div>
                    )}
                    {q}p
                    {!avail && <div style={{ fontSize:9, color:"#333", marginTop:2 }}>N/A</div>}
                  </button>
                );
              })}
            </div>
            <div style={{ fontSize:12, color:"#666", marginBottom:8 }}>Format</div>
            <div style={{ display:"flex", gap:8 }}>
              {FORMATS.map(({ id, label, icon }) => (
                <button key={id} onClick={() => setFormat(id)}
                  style={{ padding:"8px 14px", borderRadius:8,
                    border:  format === id ? "1.5px solid #f97316" : "1px solid #23234a",
                    background: format === id ? "rgba(249,115,22,.12)" : "#0b0b18",
                    color:   format === id ? "#f97316" : "#888",
                    fontSize:13, fontWeight: format === id ? 600 : 400,
                    cursor:"pointer", display:"flex", alignItems:"center", gap:6 }}>
                  <span>{icon}</span>{label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Download Card ─────────────────────────────────── */}
        {videoInfo && (
          <div className="card" style={{ background:"#12122a", borderRadius:14,
            border:"1px solid #1e1e42", padding:20 }}>
            {/* Summary chips */}
            <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:16 }}>
              {[
                ["⏱ Duration", secToStr(clipDur)],
                ["🎞 Quality",  quality + "p"],
                ["📦 Format",   format.toUpperCase()],
                ["💾 Est. size", estSize(quality, clipDur, format)],
              ].map(([k, v]) => (
                <div key={k} style={{ background:"#0b0b18", border:"1px solid #1e1e42",
                  borderRadius:8, padding:"9px 12px" }}>
                  <div style={{ fontSize:11, color:"#555", marginBottom:3 }}>{k}</div>
                  <div style={{ fontSize:13, fontWeight:700 }}>{v}</div>
                </div>
              ))}
            </div>

            {/* Progress bar */}
            {dlState === "loading" && (
              <div style={{ marginBottom:16 }}>
                <div style={{ display:"flex", justifyContent:"space-between",
                  fontSize:12, color:"#888", marginBottom:6 }}>
                  <span>{dlMsg}</span>
                  <span style={{ color:"#f97316", fontWeight:700 }}>{progress}%</span>
                </div>
                <div style={{ height:5, background:"#0b0b18", borderRadius:3,
                  overflow:"hidden", border:"1px solid #23234a" }}>
                  <div style={{ height:"100%", width:`${progress}%`,
                    background:"linear-gradient(90deg,#f97316,#fb923c)",
                    borderRadius:3, transition:"width .5s ease" }}/>
                </div>
              </div>
            )}

            {dlState === "done" && (
              <div style={{ background:"rgba(34,197,94,.1)", border:"1px solid rgba(34,197,94,.3)",
                borderRadius:8, padding:"10px 14px", marginBottom:14, color:"#22c55e", fontSize:13 }}>
                ✓ {dlMsg}
              </div>
            )}

            {dlState === "error" && (
              <div style={{ background:"rgba(239,68,68,.1)", border:"1px solid rgba(239,68,68,.3)",
                borderRadius:8, padding:"10px 14px", marginBottom:14, color:"#ef4444", fontSize:13 }}>
                ✗ Error: {dlMsg}
              </div>
            )}

            <button onClick={handleDownload} disabled={dlState === "loading"}
              style={{ width:"100%", padding:"14px", borderRadius:10, border:"none",
                background: dlState === "loading" ? "#23234a"
                           : dlState === "done"    ? "#22c55e"
                           : dlState === "error"   ? "#ef4444"
                                                   : "#f97316",
                color: dlState === "loading" ? "#555" : "#fff",
                fontSize:15, fontWeight:700,
                cursor: dlState === "loading" ? "not-allowed" : "pointer",
                display:"flex", alignItems:"center", justifyContent:"center",
                gap:8, transition:"background .2s", letterSpacing:"-.01em" }}>
              {dlState === "loading"
                ? <><span style={{ display:"inline-block", animation:"spin 1s linear infinite" }}>⟳</span>
                    Processing ({progress}%)...</>
                : dlState === "done"
                  ? "✓  Dobara download karo"
                  : dlState === "error"
                    ? "↺  Retry karo"
                    : `⬇  Download Clip — ${secToStr(clipDur)} · ${quality}p · ${format.toUpperCase()}`}
            </button>
            <div style={{ textAlign:"center", fontSize:11, color:"#444", marginTop:8 }}>
              yt-dlp + ffmpeg backend pe process hogi — file seedha browser me download hogi
            </div>
          </div>
        )}

        {/* ── Empty state ───────────────────────────────────── */}
        {!videoInfo && !infoLoading && (
          <div style={{ textAlign:"center", padding:"64px 0", color:"#333" }}>
            <div style={{ fontSize:52, marginBottom:14 }}>✂️</div>
            <div style={{ fontSize:18, fontWeight:700, color:"#555", marginBottom:6 }}>
              YouTube link paste karo upar
            </div>
            <div style={{ fontSize:14, marginBottom:28 }}>
              Video load hogi, timeline se trim karo, quality chuno, download karo
            </div>
            <div style={{ display:"flex", gap:10, justifyContent:"center", flexWrap:"wrap" }}>
              {["1️⃣ URL paste karo","2️⃣ Start & end set karo","3️⃣ Quality chuno","4️⃣ MP4 download karo"].map(s => (
                <div key={s} style={{ background:"#12122a", border:"1px solid #1e1e42",
                  borderRadius:8, padding:"8px 14px", fontSize:13, color:"#666" }}>{s}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

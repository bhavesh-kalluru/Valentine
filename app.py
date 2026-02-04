#!/usr/bin/env python3
import os
import re
from typing import Optional, Tuple

import requests
from flask import Flask, jsonify, request, render_template_string
from markupsafe import escape

APP_TITLE = "Valentine Ask"

def _env(name: str) -> str:
    return os.environ.get(name, "").strip()

OPENAI_API_KEY = _env("OPENAI_API_KEY")
PERPLEXITY_API_KEY = _env("PERPLEXITY_API_KEY")

OPENAI_MODEL = _env("OPENAI_MODEL") or "gpt-4.1-mini"
PERPLEXITY_MODEL = _env("PERPLEXITY_MODEL") or "sonar-pro"
HTTP_TIMEOUT = float(_env("HTTP_TIMEOUT") or "12")

app = Flask(__name__)


def normalize_name(raw: Optional[str]) -> str:
    # accepted safely (for optional personalization in prompts) but UI doesn't show it
    if not raw:
        return "Valentine"
    s = re.sub(r"\s+", " ", raw.strip())
    s = "".join(ch for ch in s if ch.isprintable())
    allowed = []
    for ch in s:
        if ch.isalnum() or ch in " .,'-–—_❤️❤💖💘💝💗💓💞💜🩷🫶":
            allowed.append(ch)
        elif ch.isspace():
            allowed.append(" ")
    s = "".join(allowed).strip()
    return (s[:40] if s else "Valentine")


def strip_author_and_citations(text: str) -> str:
    """Remove trailing author/source patterns like '— Author' and '[1]'."""
    s = (text or "").strip()
    s = re.sub(r"\s*\[\d+\]\s*$", "", s).strip()
    s = re.sub(r"\s*[\u2014\u2013\-]\s*[^.?!\n]{2,80}\s*$", "", s).strip()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_openai_output_text(resp_json: dict) -> str:
    if isinstance(resp_json, dict):
        if isinstance(resp_json.get("output_text"), str) and resp_json["output_text"].strip():
            return resp_json["output_text"].strip()
        output = resp_json.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                            t = c.get("text")
                            if isinstance(t, str) and t.strip():
                                return t.strip()
    return ""


def fetch_openai_quote(name: str) -> str:
    """Optional: OpenAI Responses API. Quote text only, no author."""
    if not OPENAI_API_KEY:
        return ""
    try:
        url = "https://api.openai.com/v1/responses"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        prompt = (
            "Return ONE romantic quote as ONE sentence.\n"
            "Return ONLY the quote text.\n"
            "Do NOT include any author name.\n"
            "Do NOT include sources/citations.\n"
            "No emojis.\n"
        )
        if name:
            prompt += f"(Context name: {name})"
        payload = {"model": OPENAI_MODEL, "input": prompt, "max_output_tokens": 90}
        r = requests.post(url, headers=headers, json=payload, timeout=HTTP_TIMEOUT)
        if r.status_code >= 400:
            return ""
        text = _extract_openai_output_text(r.json())
        return strip_author_and_citations(text)[:220]
    except Exception:
        return ""


def fetch_perplexity_quote() -> Tuple[str, Optional[str]]:
    """Optional: Perplexity chat completions. Quote text only, no author (best-effort)."""
    if not PERPLEXITY_API_KEY:
        return "", None
    try:
        url = "https://api.perplexity.ai/v2/chat/completions"
        headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {"role": "system", "content": "Return ONE romantic quote as ONE sentence. Quote text only. No author name. No citations. No emojis."},
                {"role": "user", "content": "Give a short romantic quote (1 sentence). Quote text only."},
            ],
            "max_tokens": 90,
            "temperature": 0.8,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=HTTP_TIMEOUT)
        if r.status_code >= 400:
            return "", None
        data = r.json()

        quote = ""
        citation = None

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message", {})
            if isinstance(msg, dict):
                quote = (msg.get("content") or "").strip()

        cits = data.get("citations")
        if isinstance(cits, list) and cits:
            citation = str(cits[0])

        quote = strip_author_and_citations(quote)[:220]
        return quote, citation
    except Exception:
        return "", None


PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>Valentine Ask</title>
  <style>
    :root{
      --bg1:#fff0f6; --bg2:#ffe8f1; --ink:#222; --muted:#5b5b5b;
      --yes:#ff4d6d; --yes2:#ff8fab; --card:rgba(255,255,255,.82);
      --shadow:0 10px 30px rgba(0,0,0,.12); --radius:22px;
    }
    *{box-sizing:border-box}
    html,body{height:100%}
    body{
      margin:0;
      font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,"Apple Color Emoji","Segoe UI Emoji";
      color:var(--ink);
      background: radial-gradient(1200px 800px at 20% 20%, #fff 0%, var(--bg1) 40%, var(--bg2) 100%);
      overflow:hidden;
    }
    .wrap{height:100%;display:grid;place-items:center;padding:18px}
    .card{
      width:min(560px,100%);
      background:var(--card);
      border:1px solid rgba(255,77,109,.18);
      box-shadow:var(--shadow);
      border-radius:var(--radius);
      padding:24px;
      backdrop-filter:blur(10px);
      position:relative;
      overflow:visible;
    }
    .floating{pointer-events:none;position:absolute;inset:-40px;opacity:.26;
      background:
        radial-gradient(circle at 15% 30%, rgba(255,77,109,.35), transparent 28%),
        radial-gradient(circle at 85% 25%, rgba(255,143,171,.40), transparent 26%),
        radial-gradient(circle at 30% 90%, rgba(255,77,109,.25), transparent 28%),
        radial-gradient(circle at 70% 85%, rgba(255,143,171,.30), transparent 24%);
    }
    .title{font-size:clamp(28px,5vw,44px);line-height:1.08;margin:0 0 10px;letter-spacing:-.02em}
    .subtitle{margin:0 0 18px;color:var(--muted);font-size:clamp(14px,2.2vw,16px)}
    .btn-row{display:flex;gap:14px;justify-content:center;align-items:center;margin-top:18px;flex-wrap:wrap}
    button{
      appearance:none;border:none;border-radius:999px;padding:18px 30px;
      font-weight:900;font-size:20px;cursor:pointer;user-select:none;touch-action:manipulation;
      min-width:160px; box-shadow:0 10px 18px rgba(0,0,0,.10);
      transition:transform .12s ease, filter .12s ease;
    }
    button:active{transform:scale(.98)}
    button:focus-visible{outline:4px solid rgba(255,77,109,.35);outline-offset:3px}
    .yes{background:linear-gradient(135deg,var(--yes) 0%,var(--yes2) 100%);color:#fff}
    .yes:hover{filter:brightness(1.03)}

    /* NO button fixed to viewport */
    .no{
      position:fixed;
      left:50%; top:68%;
      transform:translate(-50%,-50%);
      z-index:40;
      background:rgba(108,117,125,.14);
      border:2px solid rgba(108,117,125,.28);
      color:#3f4850;
      box-shadow:0 8px 14px rgba(0,0,0,.08);
    }

    /* Overlay + toy pop */
    .overlay{position:fixed;inset:0;display:none;place-items:center;background:rgba(255,240,246,.35);
      backdrop-filter:blur(6px);z-index:50}
    .overlay.show{display:grid}
    .toy{font-size:clamp(56px,10vw,92px);transform:scale(.2) rotate(-8deg);opacity:0;
      filter:drop-shadow(0 14px 14px rgba(0,0,0,.15))}
    .toy.pop{animation:pop .75s cubic-bezier(.2,.9,.2,1) forwards}
    @keyframes pop{0%{transform:scale(.2) rotate(-8deg);opacity:0}
      40%{transform:scale(1.15) rotate(6deg);opacity:1}
      70%{transform:scale(.96) rotate(-2deg)}
      100%{transform:scale(1) rotate(0deg);opacity:1}}

    /* Confetti canvas */
    #confetti{position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:60;display:none}
    #confetti.show{display:block}

    .result{display:none;margin-top:22px;text-align:center}
    .result.show{display:block}

    /* Quote only */
    .quote-wrap{
      margin-top:14px;
      text-align:center;
      padding:8px 10px;
    }
    .quote{
      font-size: clamp(18px, 3.2vw, 24px);
      font-weight: 900;
      font-style: italic;
      color:#333;
      line-height:1.35;
      margin:0;
    }

    .micro{margin-top:14px;font-size:12px;color:rgba(0,0,0,.45);text-align:center}
    .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}

    @media (prefers-reduced-motion: reduce){
      *{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
    }
  
    .quote-only .floating{opacity:.18}
    .quote-only #promptBlock{display:none}
    .quote-only #micro{display:none}
    .quote-only .card{padding:28px}
    .quote-only .quote-wrap{margin-top:0;padding:10px 6px}

  </style>
</head>
<body>
  <canvas id="confetti" aria-hidden="true"></canvas>

  <div class="overlay" id="overlay" aria-hidden="true">
    <div class="toy" id="toy" aria-label="Cute toy pop animation" role="img">🧸</div>
  </div>

  <div class="wrap">
    <div class="card" id="card">
      <div class="floating" aria-hidden="true"></div>

      <div id="promptBlock" aria-label="Prompt">
<h1 class="title">Could you be my Valentine?</h1>
      <p class="subtitle">Tap <strong>Yes</strong> to unlock a tiny celebration ✨</p>

      <div class="btn-row" aria-label="Valentine choice buttons">
        <button class="yes" id="yesBtn" aria-label="Yes">Yes</button>
      </div>
</div>

      <div class="result" id="result" aria-live="polite">
        <div class="quote-wrap" aria-label="Romantic quote">
          <p class="quote" id="quoteText"></p>
        </div>
      </div>

      <div class="micro" id="micro">Made with pure chaos + confetti.</div>
      <div class="sr-only" id="srStatus" aria-live="assertive"></div>
    </div>
  </div>

  <button class="no" id="noBtn" aria-label="No">No</button>

<script>
(() => {
  const fallbackName = {{ safe_name|tojson }};
  const qs = new URLSearchParams(window.location.search);
  const raw = (qs.get("name") || "").trim();
  const name = (raw || fallbackName || "Valentine").trim();

  const card = document.getElementById("card");
  const yesBtn = document.getElementById("yesBtn");
  const noBtn = document.getElementById("noBtn");
  const result = document.getElementById("result");
  const overlay = document.getElementById("overlay");
  const toy = document.getElementById("toy");
  const confettiCanvas = document.getElementById("confetti");
  const quoteTextEl = document.getElementById("quoteText");
  const srStatus = document.getElementById("srStatus");
  const promptBlock = document.getElementById("promptBlock");
  const micro = document.getElementById("micro");

  const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---- NO button evasion ----
  let attempts = 0;
  let locked = false;
  const state = { x: window.innerWidth * 0.5, y: window.innerHeight * 0.68 };

  function clamp(n, a, b) { return Math.max(a, Math.min(b, n)); }

  function setNoPos(x, y) {
    const rect = noBtn.getBoundingClientRect();
    const pad = 14;
    const maxX = window.innerWidth - rect.width - pad;
    const maxY = window.innerHeight - rect.height - pad;
    state.x = clamp(x, pad, Math.max(pad, maxX));
    state.y = clamp(y, pad, Math.max(pad, maxY));
    noBtn.style.left = state.x + "px";
    noBtn.style.top = state.y + "px";
    noBtn.style.transform = "translate(0,0)";
  }

  function placeNoNearCard() {
    const r = noBtn.getBoundingClientRect();
    const c = card.getBoundingClientRect();
    const x = c.left + c.width/2 - r.width/2;
    const y = c.top + Math.min(c.height * 0.68, c.height - r.height - 18);
    setNoPos(x, y);
  }

  function jumpAwayFrom(px, py, extra = 0) {
    if (locked) return;
    attempts++;

    const rect = noBtn.getBoundingClientRect();
    const cx = rect.left + rect.width/2;
    const cy = rect.top + rect.height/2;

    let dx = cx - px;
    let dy = cy - py;
    const dist = Math.max(1, Math.hypot(dx, dy));
    dx /= dist; dy /= dist;

    const base = 120 + attempts * 10 + extra;
    const jitter = 40 + Math.min(attempts, 20) * 3;

    const tx = cx + dx * base + (Math.random()-0.5) * jitter;
    const ty = cy + dy * base + (Math.random()-0.5) * jitter;

    setNoPos(tx - rect.width/2, ty - rect.height/2);

    if (attempts % 3 === 0) srStatus.textContent = "Nice try 😄";
  }

  function maybeEvade(px, py) {
    if (locked) return;
    const rect = noBtn.getBoundingClientRect();
    const cx = rect.left + rect.width/2;
    const cy = rect.top + rect.height/2;
    const dist = Math.hypot(cx - px, cy - py);
    const radius = 130 + Math.min(attempts, 20) * 6;
    if (dist < radius) jumpAwayFrom(px, py);
  }

  requestAnimationFrame(() => placeNoNearCard());

  window.addEventListener("pointermove", (e) => maybeEvade(e.clientX, e.clientY), {passive:true});
  window.addEventListener("touchmove", (e) => {
    if (!e.touches || !e.touches[0]) return;
    maybeEvade(e.touches[0].clientX, e.touches[0].clientY);
  }, {passive:true});

  noBtn.addEventListener("pointerenter", (e) => jumpAwayFrom(e.clientX, e.clientY, 60), {passive:true});
  noBtn.addEventListener("pointerdown", (e) => jumpAwayFrom(e.clientX, e.clientY, 90), {passive:true});
  noBtn.addEventListener("touchstart", (e) => {
    const t = e.touches && e.touches[0];
    jumpAwayFrom(t ? t.clientX : window.innerWidth/2, t ? t.clientY : window.innerHeight/2, 90);
  }, {passive:true});

  noBtn.addEventListener("click", (e) => {
    if (locked) return;
    e.preventDefault();
    e.stopPropagation();
    attempts += 3;
    noBtn.style.opacity = "0";
    noBtn.style.pointerEvents = "none";
    srStatus.textContent = "Nope 😅";
    setTimeout(() => {
      noBtn.style.opacity = "1";
      noBtn.style.pointerEvents = "auto";
      placeNoNearCard();
      jumpAwayFrom(window.innerWidth * Math.random(), window.innerHeight * Math.random(), 140);
    }, 220);
  });

  window.addEventListener("resize", () => {
    if (locked) return;
    placeNoNearCard();
  });

  // ---- YES flow ----
  function pickToyEmoji() {
    const toys = ["🧸","🦆","🤖","🐻"];
    return toys[Math.floor(Math.random() * toys.length)];
  }
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  async function playToyPop() {
    overlay.classList.add("show");
    toy.textContent = pickToyEmoji();
    toy.classList.remove("pop");
    void toy.offsetWidth;
    toy.classList.add("pop");
    await sleep(prefersReducedMotion ? 200 : 820);
  }

  function startConfetti(durationMs = 1800) {
    if (prefersReducedMotion) return Promise.resolve();

    const ctx = confettiCanvas.getContext("2d");
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    confettiCanvas.width = Math.floor(window.innerWidth * dpr);
    confettiCanvas.height = Math.floor(window.innerHeight * dpr);
    confettiCanvas.classList.add("show");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const pieces = [];
    const count = Math.floor(160 + Math.min(attempts, 20) * 6);

    for (let i = 0; i < count; i++) {
      pieces.push({
        x: Math.random() * window.innerWidth,
        y: -20 - Math.random() * 220,
        vx: (Math.random() - 0.5) * 7,
        vy: 2 + Math.random() * 7,
        r: 3 + Math.random() * 6,
        a: 1,
        rot: Math.random() * Math.PI * 2,
        vr: (Math.random() - 0.5) * 0.28,
        shape: Math.random() < 0.16 ? "heart" : "rect"
      });
    }

    let start = performance.now();
    return new Promise((resolve) => {
      function draw(t) {
        const elapsed = t - start;
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

        for (const p of pieces) {
          p.x += p.vx;
          p.y += p.vy;
          p.vy += 0.07;
          p.rot += p.vr;
          p.a = Math.max(0, 1 - elapsed / durationMs);

          ctx.save();
          ctx.globalAlpha = p.a;
          const hue = (p.x * 0.7 + p.y * 0.3 + elapsed * 0.05) % 360;
          ctx.fillStyle = `hsl(${hue}, 95%, 65%)`;

          ctx.translate(p.x, p.y);
          ctx.rotate(p.rot);

          if (p.shape === "heart") {
            const s = p.r;
            ctx.beginPath();
            ctx.moveTo(0, -s/2);
            ctx.bezierCurveTo(s, -s, s*1.4, s/2, 0, s*1.2);
            ctx.bezierCurveTo(-s*1.4, s/2, -s, -s, 0, -s/2);
            ctx.closePath();
            ctx.fill();
          } else {
            ctx.fillRect(-p.r, -p.r, p.r*2, p.r*2);
          }
          ctx.restore();
        }

        if (elapsed < durationMs) requestAnimationFrame(draw);
        else {
          confettiCanvas.classList.remove("show");
          resolve();
        }
      }
      requestAnimationFrame(draw);
    });
  }

  async function fetchYesData() {
    try {
      const r = await fetch("/api/yes", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({name})
      });
      if (!r.ok) throw new Error("bad status");
      return await r.json();
    } catch {
      return { quote: "In you, I found my favorite kind of forever." };
    }
  }

  function showResult(data) {
    // switch UI to "quote only"
    card.classList.add("quote-only");
    if (promptBlock) promptBlock.style.display = "none";
    if (micro) micro.style.display = "none";

    const quote = (data?.quote || "").toString().trim();
    quoteTextEl.textContent = quote || "In you, I found my favorite kind of forever.";
    result.classList.add("show");
    srStatus.textContent = "Celebration complete!";
  }

  async function onYes() {
    if (locked) return;
    locked = true;

    yesBtn.disabled = true;
    noBtn.style.display = "none";
    srStatus.textContent = "Yessss! Starting celebration.";

    await playToyPop();
    await startConfetti(1900);

    const data = await fetchYesData();
    overlay.classList.remove("show");
    showResult(data);
  }

  yesBtn.addEventListener("click", onYes);
})();
</script>
</body>
</html>
"""

@app.get("/")
def index():
    safe_name = escape(normalize_name(request.args.get("name", "")))
    return render_template_string(PAGE, safe_name=safe_name)


@app.post("/api/yes")
def api_yes():
    payload = request.get_json(silent=True) or {}
    name = normalize_name(payload.get("name"))

    quote = "In you, I found my favorite kind of forever."
    citation = None
    openai_line = ""

    oq = fetch_openai_quote(name)
    if oq:
        quote = oq
    else:
        pq, pc = fetch_perplexity_quote()
        if pq:
            quote = pq
        if pc:
            citation = pc

    quote = strip_author_and_citations(quote)
    return jsonify({"openai_line": openai_line, "quote": quote, "citation": citation})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

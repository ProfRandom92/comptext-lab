#!/usr/bin/env python3
"""
Generate a static, self-contained HTML cockpit from benchmark reports.
This is a lab-only visualization tool for synthetic data.
"""

import json
import html
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / "reports"
OUTPUT = REPORTS_DIR / "cockpit.html"

def load_json_safe(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def render():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    latest = load_json_safe(REPORTS_DIR / "latest.json") or {}
    divan = load_json_safe(REPORTS_DIR / "latest_divan.json")
    hf_verify = load_json_safe(REPORTS_DIR / "hyperfine_verify.json")
    hf_replay = load_json_safe(REPORTS_DIR / "hyperfine_replay.json")

    now = datetime.utcnow().isoformat() + "Z"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CompText Benchmarks Cockpit (Lab)</title>
<style>
:root {{ --bg:#0f172a; --card:#1e2937; --accent:#22d3ee; --text:#e2e8f0; --good:#4ade80; --bad:#f87171; }}
body {{ font-family: system-ui, sans-serif; background:var(--bg); color:var(--text); margin:0; padding:24px; }}
h1, h2 {{ color:var(--accent); }}
.card {{ background:var(--card); border-radius:12px; padding:16px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.3); }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ padding:8px 12px; text-align:left; border-bottom:1px solid #334155; }}
th {{ background:#0f172a; }}
.status-pass {{ color:var(--good); font-weight:600; }}
.status-fail {{ color:var(--bad); font-weight:600; }}
small {{ color:#64748b; }}
.note {{ font-size:0.9em; color:#94a3b8; border-left:3px solid #64748b; padding-left:8px; }}
</style>
</head>
<body>
<h1>CompText Benchmarks Cockpit <small>(Lab / Synthetic only)</small></h1>
<p class="note">
This dashboard is for internal development use only. All data is generated from synthetic fixtures.
No production, forensic, legal, or regulatory claims are made. Results are environment-specific.
</p>

<div class="card">
<h2>Run Summary</h2>
<pre>{html.escape(json.dumps(latest, indent=2, default=str))}</pre>
<p><small>Generated: {now}</small></p>
</div>

<div class="card">
<h2>Divan Micro-Benchmarks</h2>
"""
    if divan:
        html_content += f"<pre>{html.escape(json.dumps(divan, indent=2, default=str)[:3000])}</pre>"
    else:
        html_content += "<p>No latest_divan.json found.</p>"

    html_content += """
</div>

<div class="card">
<h2>Hyperfine CLI Benchmarks</h2>
<h3>Verify</h3>
"""
    if hf_verify:
        html_content += f"<pre>{html.escape(json.dumps(hf_verify, indent=2, default=str)[:2000])}</pre>"
    else:
        html_content += "<p>No hyperfine_verify.json</p>"

    html_content += "<h3>Replay</h3>"
    if hf_replay:
        html_content += f"<pre>{html.escape(json.dumps(hf_replay, indent=2, default=str)[:2000])}</pre>"
    else:
        html_content += "<p>No hyperfine_replay.json</p>"

    html_content += """
</div>

<div class="card">
<h2>Claim Hygiene Reminder</h2>
<ul>
<li>Synthetic SPARK-Style Fixture only</li>
<li>Deterministic packaging &amp; replay on synthetic data</li>
<li>Lab tooling — no production readiness or compliance claims</li>
<li>Human review required for any interpretation</li>
</ul>
</div>

</body>
</html>"""

    OUTPUT.write_text(html_content, encoding="utf-8")
    print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    render()

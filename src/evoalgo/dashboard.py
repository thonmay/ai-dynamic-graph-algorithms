# AI-assisted code: generated and revised with GLM-5.2
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Dashboard: static HTML generation from run data.

Emits a self-contained HTML file with embedded JSON data and client-side
JavaScript for: overview, generation replay slider, candidate detail,
failure reflections, and config view.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Dashboard:
    """Renders self-contained static HTML dashboards."""

    def __init__(self, run_dir: Path | str):
        self.run_dir = Path(run_dir)
        self.dashboard_dir = self.run_dir / "dashboard"
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

    def render(
        self,
        generation: int,
        config: dict[str, Any],
        generations_data: list[dict[str, Any]],
        run_id: str,
    ) -> Path:
        """Render a dashboard HTML file for the given generation.

        Args:
            generation: current generation number
            config: run config dict
            generations_data: list of generation state dicts (all committed)
            run_id: the run identifier

        Returns:
            Path to the written HTML file
        """
        html = self._build_html(generation, config, generations_data, run_id)
        path = self.dashboard_dir / f"gen{generation:04d}.html"
        path.write_text(html)
        logger.info("Dashboard written: %s", path)
        return path

    def _build_html(
        self,
        generation: int,
        config: dict[str, Any],
        generations_data: list[dict[str, Any]],
        run_id: str,
    ) -> str:
        # Prepare summary data
        all_candidates = []
        fitness_history = []

        for gen_data in generations_data:
            gen_num = gen_data.get("generation", 0)
            candidates = gen_data.get("candidates", [])
            best_fit = max((c.get("fitness", 0) for c in candidates), default=0)
            fitness_history.append({"gen": gen_num, "best": best_fit, "count": len(candidates)})
            for c in candidates:
                c["gen"] = gen_num
                all_candidates.append(c)

        best_fitness = max((c.get("fitness", 0) for c in all_candidates), default=0)
        passing = sum(1 for c in all_candidates if c.get("state") == "PASS")
        total = len(all_candidates)

        data_json = json.dumps({
            "run_id": run_id,
            "generation": generation,
            "config": config,
            "best_fitness": best_fitness,
            "passing": passing,
            "total_candidates": total,
            "fitness_history": fitness_history,
            "candidates": all_candidates,
        }, indent=2).replace("<", "\\u003c")  # no "</script>" from LLM text inside <script>

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>evoalgo - Run {run_id} - Gen {generation}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
  .header {{ background: #1a1a2e; color: #eee; padding: 16px 24px; }}
  .header h1 {{ margin: 0; font-size: 1.4em; }}
  .nav {{ display: flex; gap: 8px; padding: 8px 24px; background: #16213e; }}
  .nav button {{ padding: 8px 16px; border: none; background: #0f3460; color: #eee; cursor: pointer; border-radius: 4px; }}
  .nav button.active {{ background: #e94560; }}
  .content {{ padding: 24px; }}
  .view {{ display: none; }}
  .view.active {{ display: block; }}
  .card {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .metric {{ display: inline-block; margin-right: 32px; }}
  .metric .value {{ font-size: 2em; font-weight: bold; color: #0f3460; }}
  .metric .label {{ font-size: 0.85em; color: #666; text-transform: uppercase; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 0.9em; }}
  th {{ background: #f0f0f0; font-weight: 600; }}
  .state-PASS {{ color: #2e7d32; font-weight: bold; }}
  .state-FAIL {{ color: #c62828; }}
  .state-CRASH {{ color: #e65100; }}
  .state-NEW {{ color: #666; }}
  .state-DISCARDED {{ color: #999; text-decoration: line-through; }}
  #chart {{ width: 100%; height: 300px; }}
  pre {{ background: #f8f8f8; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 0.85em; }}
  .slider {{ width: 100%; }}
</style>
</head>
<body>
<div class="header">
  <h1>Evolutionary Graph Algorithm Discovery</h1>
  <div>Run: {run_id} | Generation: {generation} | {time.strftime('%Y-%m-%d %H:%M')}</div>
</div>
<div class="nav">
  <button class="active" onclick="showView('overview')">Overview</button>
  <button onclick="showView('replay')">Generation Replay</button>
  <button onclick="showView('candidates')">Candidates</button>
  <button onclick="showView('reflections')">Failure Reflections</button>
  <button onclick="showView('config')">Config</button>
</div>
<div class="content">

<div id="overview" class="view active">
  <div class="card">
    <div class="metric"><div class="value" id="m-best">--</div><div class="label">Best Fitness</div></div>
    <div class="metric"><div class="value" id="m-gen">--</div><div class="label">Generation</div></div>
    <div class="metric"><div class="value" id="m-passing">--</div><div class="label">Passing</div></div>
    <div class="metric"><div class="value" id="m-total">--</div><div class="label">Total Candidates</div></div>
  </div>
  <div class="card">
    <h3>Fitness Over Generations</h3>
    <svg id="chart"></svg>
  </div>
</div>

<div id="replay" class="view">
  <div class="card">
    <h3>Generation Replay</h3>
    <input type="range" class="slider" id="gen-slider" min="1" max="1" value="1" oninput="renderGen(this.value)">
    <div>Showing generation: <span id="gen-label">1</span></div>
  </div>
  <div class="card">
    <table id="gen-table"><thead>
      <tr><th>ID</th><th>State</th><th>Fitness</th><th>Work Ratio</th><th>Tests</th><th>Timeout</th><th>Parents</th></tr>
    </thead><tbody></tbody></table>
  </div>
</div>

<div id="candidates" class="view">
  <div class="card">
    <table id="cand-table"><thead>
      <tr><th>ID</th><th>Gen</th><th>State</th><th>Fitness</th><th>Work Ratio</th><th>Tests</th><th>Timeout</th><th>Error</th></tr>
    </thead><tbody></tbody></table>
  </div>
</div>

<div id="reflections" class="view">
  <div class="card" id="reflections-list"><p>No reflections available.</p></div>
</div>

<div id="config" class="view">
  <div class="card">
    <pre id="config-display"></pre>
  </div>
</div>

</div>

<script>
const DATA = {data_json};
// Candidate ids, errors and failing cases come from LLM-written code: escape
// everything that goes into innerHTML.
const esc = v => String(v ?? '').replace(/[&<>"']/g, ch => ({{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}})[ch]);

// Overview
document.getElementById('m-best').textContent = DATA.best_fitness.toFixed(2);
document.getElementById('m-gen').textContent = DATA.generation;
document.getElementById('m-passing').textContent = DATA.passing;
document.getElementById('m-total').textContent = DATA.total_candidates;

// Config
document.getElementById('config-display').textContent = JSON.stringify(DATA.config, null, 2);

// Fitness chart (simple SVG)
const history = DATA.fitness_history;
const svg = document.getElementById('chart');
if (history.length > 0) {{
  const w = svg.clientWidth || 800, h = 300, pad = 40;
  const maxGen = Math.max(...history.map(d => d.gen), 1);
  const xScale = i => pad + (i / Math.max(maxGen - 1, 1)) * (w - 2 * pad);
  const yScale = v => h - pad - v * (h - 2 * pad);
  let path = history.map((d, i) => (i === 0 ? 'M' : 'L') + xScale(d.gen) + ',' + yScale(d.best)).join(' ');
  svg.innerHTML = `<path d="${{path}}" fill="none" stroke="#0f3460" stroke-width="2"/>` +
    history.map(d => `<circle cx="${{xScale(d.gen)}}" cy="${{yScale(d.best)}}" r="3" fill="#e94560"/>`).join('') +
    `<text x="${{pad}}" y="20" fill="#666">Fitness</text>` +
    `<text x="${{w - pad}}" y="${{h - 5}}" text-anchor="end" fill="#666">Generation</text>`;
  svg.setAttribute('height', h);
}}

// Candidates table
const candTable = document.querySelector('#cand-table tbody');
DATA.candidates.forEach(c => {{
  candTable.innerHTML += `<tr>
    <td>${{esc(c.id)}}</td><td>${{esc(c.gen)}}</td>
    <td class="state-${{esc(c.state)}}">${{esc(c.state)}}</td>
    <td>${{c.fitness?.toFixed(2) ?? '--'}}</td>
    <td>${{c.work_ratio?.toFixed(2) ?? '--'}}</td>
    <td>${{esc(c.tests_passed)}}/${{esc(c.tests_total)}}</td>
    <td>${{c.timeout ? 'Y' : ''}}</td>
    <td>${{esc((c.error_message || '').substring(0, 60))}}</td>
  </tr>`;
}});

// Generation replay
const slider = document.getElementById('gen-slider');
slider.max = Math.max(...history.map(d => d.gen), 1);
slider.value = slider.max;
document.getElementById('gen-label').textContent = slider.value;

function renderGen(genNum) {{
  document.getElementById('gen-label').textContent = genNum;
  const tbody = document.querySelector('#gen-table tbody');
  tbody.innerHTML = '';
  DATA.candidates.filter(c => c.gen == genNum).forEach(c => {{
    tbody.innerHTML += `<tr>
      <td>${{esc(c.id)}}</td>
      <td class="state-${{esc(c.state)}}">${{esc(c.state)}}</td>
      <td>${{c.fitness?.toFixed(2) ?? '--'}}</td>
      <td>${{c.work_ratio?.toFixed(2) ?? '--'}}</td>
      <td>${{esc(c.tests_passed)}}/${{esc(c.tests_total)}}</td>
      <td>${{c.timeout ? 'Y' : ''}}</td>
      <td>${{esc((c.parent_ids || []).join(', '))}}</td>
    </tr>`;
  }});
}}
renderGen(slider.value);

// Reflections
const refList = document.getElementById('reflections-list');
const failed = DATA.candidates.filter(c => c.state === 'FAIL' && c.failing_case);
if (failed.length > 0) {{
  refList.innerHTML = '<h3>Failed Candidates with Failing Cases</h3>';
  failed.forEach(c => {{
    refList.innerHTML += `<div style="margin-bottom:12px;padding:8px;border-left:3px solid #e94560;">
      <strong>${{esc(c.id)}}</strong> (gen ${{esc(c.gen)}}, fitness ${{c.fitness?.toFixed(2)}})<br>
      <pre>${{esc(JSON.stringify(c.failing_case, null, 2))}}</pre>
    </div>`;
  }});
}}

function showView(name) {{
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}}
</script>
</body>
</html>"""

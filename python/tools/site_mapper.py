#!/usr/bin/env python3
"""
site_mapper.py — Scan any directory and generate an interactive structure visualization.

Reusable tool: scans a directory tree, computes sizes, classifies files,
and outputs a self-contained HTML visualization with:
  - Treemap (area = file size, color = file type)
  - Sunburst chart (hierarchical drill-down)
  - File type distribution (donut)
  - Directory size bars
  - Searchable file table

Usage:
    python site_mapper.py <directory> [--output map.html] [--exclude .git,.venv]
    python site_mapper.py ~/projects/jthorvaldur.github.io --output site_map.html
    python site_mapper.py . --output repo_map.html --exclude .git,node_modules,dist
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

DIR = sys.argv[1] if len(sys.argv) > 1 else "."
OUTPUT = "site_map.html"
EXCLUDE = {".git", ".venv", "__pycache__", "node_modules", ".wrangler", "dist"}

for i, arg in enumerate(sys.argv):
    if arg == "--output" and i + 1 < len(sys.argv):
        OUTPUT = sys.argv[i + 1]
    if arg == "--exclude" and i + 1 < len(sys.argv):
        EXCLUDE = set(sys.argv[i + 1].split(","))


def scan_directory(root: str) -> list[dict]:
    files = []
    root_path = Path(root).resolve()
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
        for fname in filenames:
            if fname.startswith("."):
                continue
            fpath = Path(dirpath) / fname
            try:
                stat = fpath.stat()
                rel = str(fpath.relative_to(root_path))
                ext = fpath.suffix.lstrip(".").lower() or "none"
                files.append({
                    "path": rel,
                    "name": fname,
                    "dir": str(Path(rel).parent) if "/" in rel else ".",
                    "ext": ext,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()[:19],
                    "depth": rel.count("/"),
                })
            except (OSError, ValueError):
                pass
    return files


def build_tree(files: list[dict]) -> dict:
    """Build a nested tree structure for treemap/sunburst."""
    root = {"name": Path(DIR).name, "children": {}, "size": 0}
    for f in files:
        parts = f["path"].split("/")
        node = root
        for part in parts[:-1]:
            if part not in node["children"]:
                node["children"][part] = {"name": part, "children": {}, "size": 0}
            node = node["children"][part]
        node["children"][parts[-1]] = {
            "name": parts[-1],
            "size": f["size"],
            "ext": f["ext"],
        }
        # Propagate sizes up
        node2 = root
        for part in parts[:-1]:
            node2["size"] += f["size"]
            node2 = node2["children"][part]
        node2["size"] += f["size"]
        root["size"] += f["size"]

    def to_list(node):
        if "children" in node and node["children"]:
            return {
                "name": node["name"],
                "size": node["size"],
                "children": [to_list(v) for v in node["children"].values()],
            }
        return {"name": node["name"], "size": node.get("size", 0), "ext": node.get("ext", "none")}

    return to_list(root)


def generate_html(files: list[dict], tree: dict, root_name: str) -> str:
    # Stats
    total_size = sum(f["size"] for f in files)
    total_files = len(files)
    ext_counts = {}
    ext_sizes = {}
    dir_sizes = {}
    for f in files:
        ext_counts[f["ext"]] = ext_counts.get(f["ext"], 0) + 1
        ext_sizes[f["ext"]] = ext_sizes.get(f["ext"], 0) + f["size"]
        d = f["dir"]
        dir_sizes[d] = dir_sizes.get(d, 0) + f["size"]

    top_dirs = sorted(dir_sizes.items(), key=lambda x: -x[1])[:20]
    top_exts = sorted(ext_counts.items(), key=lambda x: -x[1])

    files_json = json.dumps(files)
    tree_json = json.dumps(tree)
    dirs_json = json.dumps(top_dirs)
    exts_json = json.dumps(top_exts)
    ext_sizes_json = json.dumps(ext_sizes)

    def fmt_size(b):
        if b < 1024: return f"{b} B"
        if b < 1024*1024: return f"{b/1024:.1f} KB"
        return f"{b/1024/1024:.1f} MB"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Site Map — {root_name}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0a; color: #c0c0c0;
    font-family: 'JetBrains Mono', monospace;
    padding: 32px 20px; min-height: 100vh;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ color: #c0a060; font-size: 1.3rem; letter-spacing: 2px; margin-bottom: 4px; }}
  .sub {{ color: #444; font-size: 0.65rem; margin-bottom: 24px; }}
  h2 {{ color: #e0e0e0; font-size: 0.85rem; margin: 32px 0 12px; padding-bottom: 6px; border-bottom: 1px solid #1a1a1a; }}

  /* Stats bar */
  .stats {{ display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 32px; }}
  .stat {{ background: #111; border: 1px solid #1a1a1a; border-radius: 6px; padding: 14px 20px; flex: 1; min-width: 140px; }}
  .stat .num {{ color: #c0a060; font-size: 1.4rem; font-weight: 700; }}
  .stat .label {{ color: #555; font-size: 0.6rem; letter-spacing: 1px; margin-top: 4px; }}

  /* Charts */
  .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  .chart-box {{ background: #111; border: 1px solid #1a1a1a; border-radius: 8px; padding: 20px; }}
  canvas {{ width: 100% !important; }}

  /* Treemap */
  .treemap {{ position: relative; width: 100%; height: 400px; background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 8px; overflow: hidden; margin-bottom: 24px; }}
  .treemap-cell {{
    position: absolute; border: 1px solid #0a0a0a; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.55rem; color: #ddd; cursor: pointer;
    transition: opacity 0.15s;
  }}
  .treemap-cell:hover {{ opacity: 0.8; }}
  .treemap-cell span {{ pointer-events: none; text-shadow: 0 1px 2px rgba(0,0,0,0.8); text-align: center; word-break: break-all; padding: 2px; }}

  /* Table */
  .file-table {{ width: 100%; border-collapse: collapse; font-size: 0.65rem; }}
  .file-table th {{ text-align: left; color: #c0a060; padding: 6px 10px; border-bottom: 1px solid #222; font-size: 0.6rem; letter-spacing: 1px; cursor: pointer; }}
  .file-table th:hover {{ color: #e0c080; }}
  .file-table td {{ padding: 5px 10px; border-bottom: 1px solid #111; color: #888; }}
  .file-table tr:hover td {{ color: #ccc; background: #111; }}
  .search {{ background: #111; border: 1px solid #222; color: #ccc; padding: 8px 14px; font-family: inherit; font-size: 0.75rem; width: 300px; border-radius: 4px; margin-bottom: 12px; }}
  .search:focus {{ outline: none; border-color: #c0a060; }}
  .ext-badge {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.55rem; font-weight: 700; }}

  .tooltip {{
    position: fixed; background: #1a1a1a; border: 1px solid #333; border-radius: 4px;
    padding: 8px 12px; font-size: 0.65rem; color: #ccc; pointer-events: none;
    display: none; z-index: 100;
  }}

  @media (max-width: 700px) {{ .chart-row {{ grid-template-columns: 1fr; }} .stats {{ flex-direction: column; }} }}
</style>
</head>
<body>
<div class="container">
  <h1>SITE MAP — {root_name.upper()}</h1>
  <div class="sub">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &middot; {total_files} files &middot; {fmt_size(total_size)}</div>

  <div class="stats">
    <div class="stat"><div class="num">{total_files}</div><div class="label">FILES</div></div>
    <div class="stat"><div class="num">{fmt_size(total_size)}</div><div class="label">TOTAL SIZE</div></div>
    <div class="stat"><div class="num">{len(ext_counts)}</div><div class="label">FILE TYPES</div></div>
    <div class="stat"><div class="num">{len(dir_sizes)}</div><div class="label">DIRECTORIES</div></div>
  </div>

  <h2>TREEMAP (area = size, color = type)</h2>
  <div class="treemap" id="treemap"></div>

  <div class="chart-row">
    <div class="chart-box">
      <h2 style="margin-top:0;">FILE TYPES</h2>
      <canvas id="typeChart" height="280"></canvas>
    </div>
    <div class="chart-box">
      <h2 style="margin-top:0;">DIRECTORY SIZES</h2>
      <canvas id="dirChart" height="280"></canvas>
    </div>
  </div>

  <h2>ALL FILES</h2>
  <input class="search" id="search" placeholder="Search files..." autofocus>
  <table class="file-table" id="fileTable">
    <thead><tr>
      <th data-sort="path">PATH</th>
      <th data-sort="ext">TYPE</th>
      <th data-sort="size">SIZE</th>
      <th data-sort="modified">MODIFIED</th>
    </tr></thead>
    <tbody id="fileBody"></tbody>
  </table>
</div>

<div class="tooltip" id="tooltip"></div>

<script>
const FILES = {files_json};
const TREE = {tree_json};
const DIRS = {dirs_json};
const EXTS = {exts_json};
const EXT_SIZES = {ext_sizes_json};

// Color map
const EXT_COLORS = {{
  html: '#c0a060', pdf: '#cc4444', md: '#44aa44', json: '#4488cc',
  js: '#cccc44', ts: '#3388dd', css: '#cc66cc', py: '#4488aa',
  txt: '#888888', png: '#aa6644', jpg: '#aa6644', svg: '#66aaaa',
  tex: '#88aa44', sh: '#aa8844', toml: '#8866aa', yaml: '#6688aa',
  sql: '#aa4488', ics: '#448888', none: '#555555'
}};
function extColor(ext) {{ return EXT_COLORS[ext] || '#' + ((parseInt(ext,36)*7342)%0xffffff).toString(16).padStart(6,'0').slice(0,6); }}

// Format size
function fmt(b) {{
  if (b < 1024) return b + ' B';
  if (b < 1024*1024) return (b/1024).toFixed(1) + ' KB';
  return (b/1024/1024).toFixed(1) + ' MB';
}}

// === TREEMAP ===
function renderTreemap() {{
  const container = document.getElementById('treemap');
  const W = container.clientWidth;
  const H = container.clientHeight;

  // Flatten tree leaves
  const leaves = [];
  function flatten(node, prefix) {{
    if (!node.children) {{
      leaves.push({{ name: node.name, size: node.size, ext: node.ext || 'none', path: prefix + node.name }});
    }} else {{
      for (const c of node.children) flatten(c, prefix + node.name + '/');
    }}
  }}
  flatten(TREE, '');
  leaves.sort((a, b) => b.size - a.size);

  // Squarified treemap layout
  function layout(items, x, y, w, h) {{
    if (items.length === 0) return [];
    if (items.length === 1) return [{{ ...items[0], x, y, w, h }}];

    const total = items.reduce((s, i) => s + i.size, 0);
    if (total === 0) return [];

    let sum = 0;
    let split = 1;
    for (let i = 0; i < items.length; i++) {{
      sum += items[i].size;
      if (sum / total >= 0.4) {{ split = i + 1; break; }}
    }}
    if (split >= items.length) split = Math.ceil(items.length / 2);

    const left = items.slice(0, split);
    const right = items.slice(split);
    const leftSize = left.reduce((s, i) => s + i.size, 0);
    const ratio = total > 0 ? leftSize / total : 0.5;

    if (w >= h) {{
      return [
        ...layout(left, x, y, w * ratio, h),
        ...layout(right, x + w * ratio, y, w * (1 - ratio), h),
      ];
    }} else {{
      return [
        ...layout(left, x, y, w, h * ratio),
        ...layout(right, x, y + h * ratio, w, h * (1 - ratio)),
      ];
    }}
  }}

  const cells = layout(leaves, 0, 0, W, H);
  const tooltip = document.getElementById('tooltip');

  for (const cell of cells) {{
    const div = document.createElement('div');
    div.className = 'treemap-cell';
    div.style.left = cell.x + 'px';
    div.style.top = cell.y + 'px';
    div.style.width = Math.max(cell.w - 1, 1) + 'px';
    div.style.height = Math.max(cell.h - 1, 1) + 'px';
    div.style.background = extColor(cell.ext);
    if (cell.w > 40 && cell.h > 16) {{
      div.innerHTML = '<span>' + cell.name + '</span>';
    }}
    div.addEventListener('mouseenter', e => {{
      tooltip.style.display = 'block';
      tooltip.innerHTML = '<strong>' + cell.path + '</strong><br>' + fmt(cell.size) + ' &middot; ' + cell.ext;
    }});
    div.addEventListener('mousemove', e => {{
      tooltip.style.left = (e.clientX + 12) + 'px';
      tooltip.style.top = (e.clientY + 12) + 'px';
    }});
    div.addEventListener('mouseleave', () => {{ tooltip.style.display = 'none'; }});
    container.appendChild(div);
  }}
}}
renderTreemap();

// === DONUT CHART (file types) ===
function drawDonut(canvasId, data, colorFn) {{
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const cx = rect.width / 2;
  const cy = rect.height / 2 - 10;
  const r = Math.min(cx, cy) - 20;
  const inner = r * 0.55;
  const total = data.reduce((s, d) => s + d[1], 0);

  let angle = -Math.PI / 2;
  for (const [label, count] of data) {{
    const sweep = (count / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, r, angle, angle + sweep);
    ctx.arc(cx, cy, inner, angle + sweep, angle, true);
    ctx.closePath();
    ctx.fillStyle = colorFn(label);
    ctx.fill();

    if (sweep > 0.15) {{
      const mid = angle + sweep / 2;
      const tx = cx + Math.cos(mid) * (r + 14);
      const ty = cy + Math.sin(mid) * (r + 14);
      ctx.fillStyle = '#999';
      ctx.font = '10px JetBrains Mono';
      ctx.textAlign = Math.cos(mid) > 0 ? 'left' : 'right';
      ctx.fillText(label + ' (' + count + ')', tx, ty);
    }}
    angle += sweep;
  }}

  ctx.fillStyle = '#c0a060';
  ctx.font = 'bold 18px JetBrains Mono';
  ctx.textAlign = 'center';
  ctx.fillText(total, cx, cy + 6);
  ctx.fillStyle = '#666';
  ctx.font = '9px JetBrains Mono';
  ctx.fillText('FILES', cx, cy + 20);
}}
drawDonut('typeChart', EXTS, extColor);

// === BAR CHART (directory sizes) ===
function drawBars(canvasId, data) {{
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const maxVal = Math.max(...data.map(d => d[1]));
  const barH = Math.min(18, (rect.height - 20) / data.length);
  const leftPad = 160;
  const barW = rect.width - leftPad - 60;

  for (let i = 0; i < data.length && i < 15; i++) {{
    const [dir, size] = data[i];
    const y = i * (barH + 3) + 10;
    const w = (size / maxVal) * barW;

    ctx.fillStyle = '#c0a060';
    ctx.fillRect(leftPad, y, w, barH - 2);

    ctx.fillStyle = '#888';
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'right';
    const label = dir.length > 22 ? '...' + dir.slice(-19) : dir;
    ctx.fillText(label, leftPad - 6, y + barH - 4);

    ctx.textAlign = 'left';
    ctx.fillText(fmt(size), leftPad + w + 6, y + barH - 4);
  }}
}}
drawBars('dirChart', DIRS);

// === FILE TABLE ===
let sortKey = 'size';
let sortDir = -1;

function renderTable(filter) {{
  const tbody = document.getElementById('fileBody');
  let rows = FILES.filter(f => !filter || f.path.toLowerCase().includes(filter));
  rows.sort((a, b) => {{
    let av = a[sortKey], bv = b[sortKey];
    if (typeof av === 'string') return sortDir * av.localeCompare(bv);
    return sortDir * (av - bv);
  }});

  tbody.innerHTML = rows.slice(0, 200).map(f => `
    <tr>
      <td>${{f.path}}</td>
      <td><span class="ext-badge" style="background:${{extColor(f.ext)}}33;color:${{extColor(f.ext)}}">${{f.ext}}</span></td>
      <td>${{fmt(f.size)}}</td>
      <td>${{f.modified}}</td>
    </tr>
  `).join('');
}}
renderTable('');

document.getElementById('search').addEventListener('input', e => renderTable(e.target.value.toLowerCase()));

document.querySelectorAll('.file-table th').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.sort;
    if (sortKey === key) sortDir *= -1;
    else {{ sortKey = key; sortDir = key === 'size' ? -1 : 1; }}
    renderTable(document.getElementById('search').value.toLowerCase());
  }});
}});
</script>
</body>
</html>"""


def main():
    root = Path(DIR).resolve()
    print(f"Scanning {root}...")
    files = scan_directory(str(root))
    print(f"  Found {len(files)} files")

    tree = build_tree(files)
    html = generate_html(files, tree, root.name)

    Path(OUTPUT).write_text(html)
    print(f"  Output: {OUTPUT}")
    print(f"  Total size: {sum(f['size'] for f in files) / 1024:.0f} KB")


if __name__ == "__main__":
    main()

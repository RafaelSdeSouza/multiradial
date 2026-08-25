(function () {
  "use strict";

  const G = window.RadialPathsGeometry;
  const colours = ["#0072B2", "#D55E00", "#009E73", "#7B61A8"];
  const cividis = [
    [0.00, [0, 32, 76]],
    [0.25, [58, 75, 105]],
    [0.50, [124, 123, 120]],
    [0.75, [188, 174, 105]],
    [1.00, [254, 232, 56]],
  ];
  const state = {
    family: "elongated",
    centreCount: 2,
    resolution: 80,
    tracer: "brightness",
    tailWidth: 100,
    progress: 1,
    geometry: null,
    tracerData: null,
    scene: null,
    selectedIndex: null,
    draggingCentre: null,
    animation: null,
  };

  function colourAt(value) {
    const t = Math.max(0, Math.min(1, value));
    let lower = cividis[0];
    let upper = cividis[cividis.length - 1];
    for (let i = 1; i < cividis.length; i += 1) {
      if (t <= cividis[i][0]) { lower = cividis[i - 1]; upper = cividis[i]; break; }
    }
    const fraction = (t - lower[0]) / Math.max(upper[0] - lower[0], 1e-12);
    return lower[1].map((channel, i) => Math.round(channel + fraction * (upper[1][i] - channel)));
  }

  function distanceToSegment(x, y, ax, ay, bx, by) {
    const dx = bx - ax;
    const dy = by - ay;
    const length = dx * dx + dy * dy;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / Math.max(length, 1e-12)));
    return Math.hypot(x - (ax + t * dx), y - (ay + t * dy));
  }

  function polylineDistance(x, y, points) {
    let distance = Infinity;
    for (let i = 1; i < points.length; i += 1) {
      distance = Math.min(distance, distanceToSegment(x, y, ...points[i - 1], ...points[i]));
    }
    return distance;
  }

  function makeScene(family, resolution) {
    const height = resolution;
    const width = Math.round(resolution * 1.45);
    const support = new Uint8Array(width * height);
    const proposed = {
      circle: [[0.50, 0.43], [0.50, 0.58], [0.40, 0.50], [0.61, 0.50]],
      compact: [[0.49, 0.34], [0.51, 0.64], [0.35, 0.50], [0.66, 0.49]],
      elongated: [[0.48, 0.26], [0.55, 0.70], [0.45, 0.48], [0.60, 0.85]],
      folded: [[0.30, 0.24], [0.69, 0.31], [0.30, 0.70], [0.70, 0.73]],
      branched: [[0.75, 0.50], [0.23, 0.26], [0.23, 0.74], [0.50, 0.50]],
      perforated: [[0.50, 0.22], [0.50, 0.78], [0.26, 0.50], [0.74, 0.50]],
      merger: [[0.48, 0.29], [0.53, 0.61], [0.63, 0.82], [0.36, 0.47]],
    }[family];
    for (let row = 0; row < height; row += 1) {
      for (let column = 0; column < width; column += 1) {
        const x = column / (width - 1);
        const y = row / (height - 1);
        let inside = false;
        if (family === "circle") {
          inside = ((x - 0.5) / 0.34) ** 2 + ((y - 0.5) / 0.39) ** 2 <= 1;
        } else if (family === "compact") {
          inside = ((x - 0.49) / 0.35) ** 2 + ((y - 0.51) / 0.31) ** 2 <= 1;
          inside ||= ((x - 0.68) / 0.15) ** 2 + ((y - 0.38) / 0.17) ** 2 <= 1;
        } else if (family === "elongated") {
          const spine = [[0.20, 0.48], [0.38, 0.46], [0.56, 0.52], [0.73, 0.61], [0.90, 0.72]];
          const widthScale = state.tailWidth / 100;
          inside = polylineDistance(x, y, spine) <= 0.105 * widthScale || Math.hypot((x - 0.22) / 1.1, y - 0.48) <= 0.16 * widthScale;
        } else if (family === "folded") {
          const fold = [[0.22, 0.28], [0.67, 0.27], [0.76, 0.50], [0.67, 0.73], [0.27, 0.72], [0.25, 0.53]];
          inside = polylineDistance(x, y, fold) <= 0.105;
        } else if (family === "branched") {
          const trunk = polylineDistance(x, y, [[0.50, 0.82], [0.50, 0.50]]);
          const left = polylineDistance(x, y, [[0.50, 0.51], [0.25, 0.23]]);
          const right = polylineDistance(x, y, [[0.50, 0.51], [0.75, 0.22]]);
          inside = Math.min(trunk, left, right) <= 0.09;
        } else if (family === "perforated") {
          inside = ((x - 0.5) / 0.37) ** 2 + ((y - 0.5) / 0.36) ** 2 <= 1;
          inside &&= Math.hypot((x - 0.51) / 1.15, y - 0.49) >= 0.15;
        } else if (family === "merger") {
          inside = ((x - 0.31) / 0.22) ** 2 + ((y - 0.48) / 0.25) ** 2 <= 1;
          inside ||= ((x - 0.62) / 0.24) ** 2 + ((y - 0.53) / 0.27) ** 2 <= 1;
          inside ||= polylineDistance(x, y, [[0.31, 0.48], [0.62, 0.53], [0.87, 0.67]]) <= 0.07;
        }
        if (row === 0 || column === 0 || row === height - 1 || column === width - 1) inside = false;
        support[row * width + column] = inside ? 1 : 0;
      }
    }
    const centres = proposed.slice(0, state.centreCount).map(([y, x]) => nearestSupport(
      support, width, height, Math.round(y * (height - 1)), Math.round(x * (width - 1)),
    ));
    return { support, centres, width, height };
  }

  function nearestSupport(support, width, height, row, column) {
    let best = null;
    let bestDistance = Infinity;
    for (let rr = 0; rr < height; rr += 1) {
      for (let cc = 0; cc < width; cc += 1) {
        if (!support[rr * width + cc]) continue;
        const distance = (rr - row) ** 2 + (cc - column) ** 2;
        if (distance < bestDistance) { bestDistance = distance; best = [rr, cc]; }
      }
    }
    return best;
  }

  function tracer(scene, geometry) {
    const data = new Float64Array(scene.width * scene.height);
    data.fill(NaN);
    for (let row = 0; row < scene.height; row += 1) {
      for (let column = 0; column < scene.width; column += 1) {
        const idx = row * scene.width + column;
        if (!scene.support[idx]) continue;
        let value = 0;
        if (state.tracer === "brightness") {
          for (let centre = 0; centre < geometry.centres.length; centre += 1) {
            const [cy, cx] = geometry.centres[centre];
            value += (1 - centre * 0.12) * Math.exp(-Math.hypot(row - cy, column - cx) / (scene.height * 0.12));
          }
          value += 0.08 * column / scene.width;
        } else if (state.tracer === "colour") {
          value = 0.25 + 0.58 * column / scene.width + 0.08 * Math.sin(row / 7);
        } else {
          value = 0.65 - 0.40 * column / scene.width + 0.10 * Math.cos((row + column) / 9);
        }
        data[idx] = value;
      }
    }
    return data;
  }

  function reachedMask(geometry) {
    const reached = new Uint8Array(geometry.support.length);
    for (let idx = 0; idx < reached.length; idx += 1) {
      if (!geometry.support[idx]) continue;
      const label = geometry.labels[idx];
      reached[idx] = geometry.centreDistance[idx] <= state.progress * geometry.extents[label] + 1e-12 ? 1 : 0;
    }
    return reached;
  }

  function renderField(canvas, field, geometry, reached) {
    const ctx = canvas.getContext("2d");
    const image = ctx.createImageData(geometry.width, geometry.height);
    for (let idx = 0; idx < field.length; idx += 1) {
      const offset = idx * 4;
      if (!geometry.support[idx] || !Number.isFinite(field[idx])) {
        image.data[offset + 3] = 0;
        continue;
      }
      const rgb = reached[idx] ? colourAt(field[idx]) : [235, 238, 240];
      image.data[offset] = rgb[0];
      image.data[offset + 1] = rgb[1];
      image.data[offset + 2] = rgb[2];
      image.data[offset + 3] = 255;
    }
    const buffer = document.createElement("canvas");
    buffer.width = geometry.width;
    buffer.height = geometry.height;
    buffer.getContext("2d").putImageData(image, 0, 0);
    const rect = canvas.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(rect.width * scale));
    canvas.height = Math.max(1, Math.round(rect.height * scale));
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(buffer, 0, 0, rect.width, rect.height);
  }

  function contourSegments(field, geometry, level) {
    const segments = [];
    const width = geometry.width;
    const height = geometry.height;
    function crossing(a, b, ax, ay, bx, by) {
      if (!Number.isFinite(a) || !Number.isFinite(b) || (a < level) === (b < level)) return null;
      const t = (level - a) / (b - a);
      return [ax + t * (bx - ax), ay + t * (by - ay)];
    }
    for (let row = 0; row < height - 1; row += 1) {
      for (let column = 0; column < width - 1; column += 1) {
        const i00 = row * width + column;
        const i10 = i00 + 1;
        const i01 = i00 + width;
        const i11 = i01 + 1;
        const points = [
          crossing(field[i00], field[i10], column, row, column + 1, row),
          crossing(field[i10], field[i11], column + 1, row, column + 1, row + 1),
          crossing(field[i11], field[i01], column + 1, row + 1, column, row + 1),
          crossing(field[i01], field[i00], column, row + 1, column, row),
        ].filter(Boolean);
        if (points.length === 2) segments.push([points[0], points[1]]);
        if (points.length === 4) {
          segments.push([points[0], points[1]]);
          segments.push([points[2], points[3]]);
        }
      }
    }
    return segments;
  }

  function svgElement(name, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  }

  function renderOverlay(svg, field, geometry, includePath) {
    svg.replaceChildren();
    svg.setAttribute("viewBox", `0 0 ${geometry.width} ${geometry.height}`);
    const boundaryParts = [];
    for (let row = 0; row < geometry.height; row += 1) {
      for (let column = 0; column < geometry.width; column += 1) {
        const idx = row * geometry.width + column;
        if (!geometry.support[idx]) continue;
        const edges = [[-1, 0, column, row, column + 1, row], [1, 0, column, row + 1, column + 1, row + 1], [0, -1, column, row, column, row + 1], [0, 1, column + 1, row, column + 1, row + 1]];
        for (const [dr, dc, x1, y1, x2, y2] of edges) {
          const rr = row + dr;
          const cc = column + dc;
          if (rr < 0 || rr >= geometry.height || cc < 0 || cc >= geometry.width || !geometry.support[rr * geometry.width + cc]) {
            boundaryParts.push(`M${x1},${y1}L${x2},${y2}`);
          }
        }
      }
    }
    svg.appendChild(svgElement("path", { d: boundaryParts.join(""), class: "support-outline" }));
    for (const level of [0.25, 0.5, 0.75]) {
      const parts = contourSegments(field, geometry, level).map(segment => `M${segment[0][0]},${segment[0][1]}L${segment[1][0]},${segment[1][1]}`);
      svg.appendChild(svgElement("path", { d: parts.join(""), class: "field-contour" }));
    }
    if (state.progress > 0.002 && state.progress < 0.998) {
      const parts = contourSegments(geometry.rhoX, geometry, state.progress).map(segment => `M${segment[0][0]},${segment[0][1]}L${segment[1][0]},${segment[1][1]}`);
      svg.appendChild(svgElement("path", { d: parts.join(""), class: "wavefront-contour" }));
    }
    if (includePath && state.selectedIndex !== null) {
      const label = geometry.labels[state.selectedIndex];
      const path = G.shortestPath(geometry, label, state.selectedIndex);
      if (path.length) {
        const points = path.map(idx => `${(idx % geometry.width) + 0.5},${Math.floor(idx / geometry.width) + 0.5}`).join(" ");
        svg.appendChild(svgElement("polyline", { points, class: "shortest-path" }));
      }
      const row = Math.floor(state.selectedIndex / geometry.width);
      const column = state.selectedIndex % geometry.width;
      svg.appendChild(svgElement("rect", { x: column - 1, y: row - 1, width: 2.5, height: 2.5, class: "selected-pixel" }));
    }
    geometry.centres.forEach(([row, column], index) => {
      const halo = svgElement("circle", { cx: column + 0.5, cy: row + 0.5, r: 2.8, class: "centre-halo" });
      const marker = svgElement("circle", { cx: column + 0.5, cy: row + 0.5, r: 1.55, fill: colours[index], class: "centre-marker", "data-centre": index, tabindex: 0, role: "button", "aria-label": `Move supplied centre ${index + 1}` });
      svg.append(halo, marker);
    });
  }

  function renderProfile(data, geometry) {
    const svg = document.getElementById("profile-chart");
    const width = 540;
    const height = 210;
    const margin = { left: 48, right: 18, top: 18, bottom: 38 };
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.replaceChildren();
    const reached = reachedMask(geometry);
    const current = G.radialProfile(data, geometry, "rho_X", 30, 6, reached);
    const final = G.radialProfile(data, geometry, "rho_X", 30, 6, null);
    const all = final.medians.flat().filter(Number.isFinite);
    const min = Math.min(...all);
    const max = Math.max(...all);
    const x = value => margin.left + value * (width - margin.left - margin.right);
    const y = value => height - margin.bottom - (value - min) / Math.max(max - min, 1e-12) * (height - margin.top - margin.bottom);
    svg.appendChild(svgElement("path", { d: `M${margin.left},${height - margin.bottom}H${width - margin.right}M${margin.left},${margin.top}V${height - margin.bottom}`, class: "chart-axis" }));
    for (const value of [0, 0.5, 1]) {
      const label = svgElement("text", { x: x(value), y: height - 14, class: "chart-label", "text-anchor": "middle" });
      label.textContent = value.toFixed(1);
      svg.appendChild(label);
    }
    const xLabel = svgElement("text", { x: (margin.left + width - margin.right) / 2, y: height - 1, class: "chart-label", "text-anchor": "middle" });
    xLabel.textContent = "Normalized progression ρₓ";
    svg.appendChild(xLabel);
    function pathFor(values) {
      let path = "";
      let started = false;
      values.forEach((value, i) => {
        if (!Number.isFinite(value)) { started = false; return; }
        path += `${started ? "L" : "M"}${x(current.radius[i])},${y(value)}`;
        started = true;
      });
      return path;
    }
    final.medians.forEach(values => svg.appendChild(svgElement("path", { d: pathFor(values), class: "profile-final" })));
    current.medians.forEach((values, i) => svg.appendChild(svgElement("path", { d: pathFor(values), class: "profile-current", stroke: colours[i] })));
  }

  function updateInspection() {
    const g = state.geometry;
    const output = document.getElementById("inspection-values");
    if (state.selectedIndex === null || !g.support[state.selectedIndex]) {
      output.innerHTML = "<span>Select an in-support pixel to inspect its assigned centre and distances.</span>";
      return;
    }
    const idx = state.selectedIndex;
    const label = g.labels[idx];
    output.innerHTML = `
      <dl><div><dt>assigned centre</dt><dd style="color:${colours[label]}">Centre ${label + 1}</dd></div>
      <div><dt>d<sub>k</sub></dt><dd>${g.centreDistance[idx].toFixed(2)} px</dd></div>
      <div><dt>b</dt><dd>${g.boundaryDistance[idx].toFixed(2)} px</dd></div>
      <div><dt>ρ<sub>D</sub></dt><dd>${g.rhoD[idx].toFixed(3)}</dd></div>
      <div><dt>ρ<sub>X</sub></dt><dd>${g.rhoX[idx].toFixed(3)}</dd></div></dl>`;
  }

  function renderProgress() {
    const reached = reachedMask(state.geometry);
    renderField(document.getElementById("rho-d-canvas"), state.geometry.rhoD, state.geometry, reached);
    renderField(document.getElementById("rho-x-canvas"), state.geometry.rhoX, state.geometry, reached);
    renderOverlay(document.getElementById("rho-d-overlay"), state.geometry.rhoD, state.geometry, true);
    renderOverlay(document.getElementById("rho-x-overlay"), state.geometry.rhoX, state.geometry, false);
    renderProfile(state.tracerData, state.geometry);
    updateInspection();
    document.getElementById("progress-value").textContent = `${Math.round(state.progress * 100)}%`;
    document.getElementById("wave-progress").value = Math.round(state.progress * 100);
  }

  function render() {
    const scene = state.scene || makeScene(state.family, state.resolution);
    state.scene = scene;
    state.geometry = G.buildGeometry(scene.support, scene.width, scene.height, scene.centres);
    state.tracerData = tracer(scene, state.geometry);
    renderProgress();
  }

  function resetScene() {
    state.scene = makeScene(state.family, state.resolution);
    state.selectedIndex = null;
    state.progress = 1;
    render();
  }

  function updateTailControl() {
    const enabled = state.family === "elongated";
    const container = document.getElementById("tail-width-control");
    const input = document.getElementById("tail-width");
    input.disabled = !enabled;
    container.setAttribute("aria-disabled", enabled ? "false" : "true");
  }

  function pointFromEvent(svg, event) {
    const rect = svg.getBoundingClientRect();
    return [
      Math.round((event.clientY - rect.top) / rect.height * (state.scene.height - 1)),
      Math.round((event.clientX - rect.left) / rect.width * (state.scene.width - 1)),
    ];
  }

  function attachOverlayEvents(svg) {
    svg.addEventListener("pointerdown", event => {
      const marker = event.target.closest("[data-centre]");
      if (marker) {
        state.draggingCentre = Number(marker.dataset.centre);
        svg.setPointerCapture(event.pointerId);
        event.preventDefault();
        return;
      }
      const [row, column] = pointFromEvent(svg, event);
      const idx = row * state.scene.width + column;
      if (state.scene.support[idx]) { state.selectedIndex = idx; renderProgress(); }
    });
    svg.addEventListener("pointermove", event => {
      if (state.draggingCentre === null) return;
      const [row, column] = pointFromEvent(svg, event);
      const nearest = nearestSupport(state.scene.support, state.scene.width, state.scene.height, row, column);
      state.scene.centres[state.draggingCentre] = nearest;
      render();
    });
    svg.addEventListener("pointerup", event => {
      state.draggingCentre = null;
      if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
    });
  }

  function animate() {
    if (state.animation) cancelAnimationFrame(state.animation);
    state.progress = 0;
    const start = performance.now();
    const duration = 2400;
    function frame(now) {
      state.progress = Math.min(1, (now - start) / duration);
      renderProgress();
      if (state.progress < 1) state.animation = requestAnimationFrame(frame);
      else state.animation = null;
    }
    state.animation = requestAnimationFrame(frame);
  }

  document.getElementById("support-family").addEventListener("change", event => { state.family = event.target.value; updateTailControl(); resetScene(); });
  document.getElementById("tail-width").addEventListener("input", event => {
    state.tailWidth = Number(event.target.value);
    document.getElementById("tail-width-value").textContent = `${state.tailWidth}%`;
    resetScene();
  });
  document.getElementById("resolution").addEventListener("change", event => { state.resolution = Number(event.target.value); resetScene(); });
  document.getElementById("tracer").addEventListener("change", event => { state.tracer = event.target.value; state.tracerData = tracer(state.scene, state.geometry); renderProgress(); });
  document.getElementById("centre-count").addEventListener("click", event => {
    const button = event.target.closest("button[data-count]");
    if (!button) return;
    state.centreCount = Number(button.dataset.count);
    document.querySelectorAll("button[data-count]").forEach(item => item.setAttribute("aria-pressed", item === button ? "true" : "false"));
    resetScene();
  });
  document.getElementById("wave-progress").addEventListener("input", event => { state.progress = Number(event.target.value) / 100; renderProgress(); });
  document.getElementById("animate-wavefront").addEventListener("click", animate);
  attachOverlayEvents(document.getElementById("rho-d-overlay"));
  attachOverlayEvents(document.getElementById("rho-x-overlay"));
  window.addEventListener("resize", renderProgress);
  updateTailControl();
  resetScene();
})();

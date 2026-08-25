(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.RadialPathsGeometry = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const SQRT2 = Math.sqrt(2);
  const NEIGHBOURS = [
    [-1, -1, SQRT2], [-1, 0, 1], [-1, 1, SQRT2],
    [0, -1, 1], [0, 1, 1],
    [1, -1, SQRT2], [1, 0, 1], [1, 1, SQRT2],
  ];

  class MinHeap {
    constructor() { this.items = []; }
    push(item) {
      const items = this.items;
      items.push(item);
      let i = items.length - 1;
      while (i > 0) {
        const parent = (i - 1) >> 1;
        if (items[parent][0] <= item[0]) break;
        items[i] = items[parent];
        i = parent;
      }
      items[i] = item;
    }
    pop() {
      const items = this.items;
      if (!items.length) return null;
      const first = items[0];
      const last = items.pop();
      if (items.length) {
        let i = 0;
        while (true) {
          const left = i * 2 + 1;
          const right = left + 1;
          if (left >= items.length) break;
          let child = left;
          if (right < items.length && items[right][0] < items[left][0]) child = right;
          if (items[child][0] >= last[0]) break;
          items[i] = items[child];
          i = child;
        }
        items[i] = last;
      }
      return first;
    }
    get length() { return this.items.length; }
  }

  function indexOf(row, column, width) { return row * width + column; }

  function distanceFromSources(support, width, height, sources, withPredecessor = false) {
    const size = width * height;
    const distance = new Float64Array(size);
    distance.fill(Infinity);
    const predecessor = withPredecessor ? new Int32Array(size).fill(-1) : null;
    const heap = new MinHeap();
    for (const source of sources) {
      const idx = indexOf(source[0], source[1], width);
      if (!support[idx]) continue;
      distance[idx] = 0;
      heap.push([0, idx]);
    }
    while (heap.length) {
      const current = heap.pop();
      const currentDistance = current[0];
      const idx = current[1];
      if (currentDistance !== distance[idx]) continue;
      const row = Math.floor(idx / width);
      const column = idx - row * width;
      for (const [dr, dc, step] of NEIGHBOURS) {
        const rr = row + dr;
        const cc = column + dc;
        if (rr < 0 || rr >= height || cc < 0 || cc >= width) continue;
        const neighbour = indexOf(rr, cc, width);
        if (!support[neighbour]) continue;
        const candidate = currentDistance + step;
        if (candidate < distance[neighbour]) {
          distance[neighbour] = candidate;
          if (predecessor) predecessor[neighbour] = idx;
          heap.push([candidate, neighbour]);
        }
      }
    }
    for (let i = 0; i < size; i += 1) {
      if (!support[i]) distance[i] = NaN;
    }
    return { distance, predecessor };
  }

  function buildGeometry(supportInput, width, height, centresInput) {
    const support = Uint8Array.from(supportInput, value => value ? 1 : 0);
    const centres = centresInput.map(pair => [Math.round(pair[0]), Math.round(pair[1])]);
    if (!centres.length) throw new Error("at least one supplied centre is required");
    for (const [row, column] of centres) {
      if (row < 0 || row >= height || column < 0 || column >= width || !support[indexOf(row, column, width)]) {
        throw new Error("every supplied centre must lie on the support");
      }
    }
    const distances = centres.map(centre => distanceFromSources(support, width, height, [centre]).distance);
    const size = width * height;
    const labels = new Int16Array(size).fill(-1);
    const centreDistance = new Float64Array(size);
    centreDistance.fill(NaN);
    for (let idx = 0; idx < size; idx += 1) {
      if (!support[idx]) continue;
      let label = 0;
      let best = distances[0][idx];
      for (let centre = 1; centre < centres.length; centre += 1) {
        if (distances[centre][idx] < best) {
          best = distances[centre][idx];
          label = centre;
        }
      }
      labels[idx] = label;
      centreDistance[idx] = best;
    }

    const boundary = new Uint8Array(size);
    const boundarySources = [];
    for (let row = 0; row < height; row += 1) {
      for (let column = 0; column < width; column += 1) {
        const idx = indexOf(row, column, width);
        if (!support[idx]) continue;
        let isBoundary = false;
        for (let dr = -1; dr <= 1 && !isBoundary; dr += 1) {
          for (let dc = -1; dc <= 1; dc += 1) {
            const rr = row + dr;
            const cc = column + dc;
            if (rr < 0 || rr >= height || cc < 0 || cc >= width) continue;
            if (!support[indexOf(rr, cc, width)]) { isBoundary = true; break; }
          }
        }
        if (isBoundary) {
          boundary[idx] = 1;
          boundarySources.push([row, column]);
        }
      }
    }
    if (!boundarySources.length) throw new Error("support has no represented boundary");
    const boundaryDistance = distanceFromSources(support, width, height, boundarySources).distance;
    const rhoD = new Float64Array(size);
    const rhoX = new Float64Array(size);
    rhoD.fill(NaN);
    rhoX.fill(NaN);
    const extents = new Float64Array(centres.length);
    for (let idx = 0; idx < size; idx += 1) {
      if (!support[idx]) continue;
      const denominator = centreDistance[idx] + boundaryDistance[idx];
      rhoD[idx] = denominator > 0 ? centreDistance[idx] / denominator : NaN;
      const label = labels[idx];
      if (centreDistance[idx] > extents[label]) extents[label] = centreDistance[idx];
    }
    for (let idx = 0; idx < size; idx += 1) {
      if (!support[idx]) continue;
      const extent = extents[labels[idx]];
      rhoX[idx] = extent > 0 ? centreDistance[idx] / extent : 0;
    }
    return { width, height, support, centres, distances, labels, centreDistance, boundary, boundaryDistance, rhoD, rhoX, extents };
  }

  function shortestPath(geometry, centreIndex, targetIndex) {
    const result = distanceFromSources(
      geometry.support,
      geometry.width,
      geometry.height,
      [geometry.centres[centreIndex]],
      true,
    );
    if (!Number.isFinite(result.distance[targetIndex])) return [];
    const path = [];
    let idx = targetIndex;
    while (idx >= 0) {
      path.push(idx);
      if (result.distance[idx] === 0) break;
      idx = result.predecessor[idx];
    }
    return path.reverse();
  }

  function median(values) {
    if (!values.length) return NaN;
    values.sort((a, b) => a - b);
    const middle = Math.floor(values.length / 2);
    return values.length % 2 ? values[middle] : 0.5 * (values[middle - 1] + values[middle]);
  }

  function radialProfile(data, geometry, coordinateName, bins = 30, minPixels = 6, reached = null) {
    const coordinate = coordinateName === "rho_D" ? geometry.rhoD : geometry.rhoX;
    const values = Array.from({ length: geometry.centres.length }, () => Array.from({ length: bins }, () => []));
    for (let idx = 0; idx < geometry.support.length; idx += 1) {
      if (!geometry.support[idx] || !Number.isFinite(data[idx]) || !Number.isFinite(coordinate[idx])) continue;
      if (reached && !reached[idx]) continue;
      let bin = Math.floor(coordinate[idx] * bins);
      if (coordinate[idx] === 1) bin = bins - 1;
      if (bin < 0 || bin >= bins) continue;
      values[geometry.labels[idx]][bin].push(data[idx]);
    }
    const medians = values.map(row => row.map(sample => sample.length >= minPixels ? median(sample) : NaN));
    const counts = values.map(row => row.map(sample => sample.length));
    return { bins, radius: Array.from({ length: bins }, (_, i) => (i + 0.5) / bins), medians, counts };
  }

  return { buildGeometry, distanceFromSources, radialProfile, shortestPath };
});

// Utilidades puras sobre las marcas del FrameAnnotator (coordenadas en px del frame original).

export function lineLength(points) {
  if (points.length < 2) return null;
  const [a, b] = points;
  return Math.hypot(b.x - a.x, b.y - a.y);
}

export function rectFromPoints(points) {
  if (points.length < 2) return null;
  const [a, b] = points;
  const x = Math.floor(Math.min(a.x, b.x));
  const y = Math.floor(Math.min(a.y, b.y));
  const width = Math.ceil(Math.max(a.x, b.x)) - x;
  const height = Math.ceil(Math.max(a.y, b.y)) - y;
  return width > 0 && height > 0 ? { x, y, width, height } : null;
}

export function pointsFromRect(rect) {
  if (!rect) return [];
  return [
    { x: rect.x, y: rect.y },
    { x: rect.x + rect.width, y: rect.y + rect.height },
  ];
}

// Cuantos toques admite cada modo; polygon no tiene limite.
export function maxPointsFor(mode, maxPoints) {
  if (mode === 'line' || mode === 'rect') return 2;
  if (mode === 'points') return maxPoints ?? Infinity;
  return Infinity;
}

// Agrega un toque: al completar line/rect, el siguiente toque empieza una marca nueva.
export function addPoint(points, point, mode, maxPoints) {
  const limit = maxPointsFor(mode, maxPoints);
  if (points.length >= limit) {
    return mode === 'points' ? points : [point];
  }
  return [...points, point];
}

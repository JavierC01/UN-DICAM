// Calculo puro de escalas y marcas de eje para CurveChart.

export function validPairs(x = [], y = []) {
  const pairs = [];
  for (let i = 0; i < Math.min(x.length, y.length); i += 1) {
    if (Number.isFinite(x[i]) && Number.isFinite(y[i])) pairs.push([x[i], y[i]]);
  }
  return pairs;
}

export function extent(values) {
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    const pad = min === 0 ? 1 : Math.abs(min) * 0.1;
    min -= pad;
    max += pad;
  }
  return [min, max];
}

// Marcas "redondas" (1, 2, 2.5, 5 x 10^n) dentro del rango, con el paso mas cercano a (max - min) / count.
export function niceTicks(min, max, count = 4) {
  const step0 = (max - min) / count;
  const magnitude = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10]
    .map((m) => m * magnitude)
    .reduce((best, s) => (Math.abs(s - step0) < Math.abs(best - step0) ? s : best));
  const ticks = [];
  for (let t = Math.ceil(min / step) * step; t <= max + step * 1e-9; t += step) {
    ticks.push(Math.abs(t) < step * 1e-9 ? 0 : t);
  }
  return ticks;
}

export function formatTick(value) {
  if (value === 0) return '0';
  const abs = Math.abs(value);
  if (abs >= 1e5 || abs < 1e-3) return value.toExponential(1);
  return String(Number(value.toPrecision(3)));
}

const precise = value => Number(value.toPrecision(12));

export function fitWindow(window, domain) {
  if (![...window, ...domain].every(Number.isFinite) || domain[1] <= domain[0]) throw new RangeError('Invalid time window');
  const total = domain[1] - domain[0];
  const width = Math.min(total, Math.max(total / 1000, Math.abs(window[1] - window[0])));
  const start = Math.max(domain[0], Math.min(Math.min(...window), domain[1] - width));
  return [precise(start), precise(start + width)];
}

export function zoomWindow(window, domain, factor, anchor = (window[0] + window[1]) / 2) {
  if (!Number.isFinite(factor) || factor <= 0) throw new RangeError('Invalid zoom factor');
  return fitWindow([anchor - (anchor - window[0]) * factor, anchor + (window[1] - anchor) * factor], domain);
}

export function panWindow(window, domain, distance) {
  return fitWindow([window[0] + distance, window[1] + distance], domain);
}

export function valueAt(events, time) {
  return events.findLast(([at]) => at <= time)?.[1] ?? '?';
}

export function clipIntervals(events, window) {
  let start = window[0];
  let value = valueAt(events, start);
  const intervals = [];
  for (const [time, next] of events) {
    if (time <= window[0] || time >= window[1] || next === value) continue;
    intervals.push([start, time, value]);
    start = time;
    value = next;
  }
  if (start < window[1]) intervals.push([start, window[1], value]);
  return intervals;
}

export function activityBins(signals, domain, count = 32) {
  const bins = Array(count).fill(0);
  for (const { events } of signals) {
    events.forEach(([time, value], index) => {
      if (!index || value === events[index - 1][1] || time < domain[0] || time >= domain[1]) return;
      const bucket = Math.floor((time - domain[0]) / (domain[1] - domain[0]) * count);
      bins[Math.min(count - 1, bucket)]++;
    });
  }
  return bins;
}

export function formatTime(value, window) {
  const magnitude = Math.max(Math.abs(window[0]), Math.abs(window[1]));
  const [scale, unit] = magnitude < 1 ? [1000, 'ps'] : magnitude >= 1000 ? [0.001, 'μs'] : [1, 'ns'];
  return `${precise(value * scale)} ${unit}`;
}

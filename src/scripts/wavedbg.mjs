import { fitWindow, zoomWindow, panWindow, valueAt, clipIntervals, activityBins, formatTime } from '../lib/waveform.mjs';

const { cases } = JSON.parse(document.querySelector('#wave-data').textContent);
const workbench = document.querySelector('.wave-workbench');
const plot = document.querySelector('#wave-svg');
const overview = document.querySelector('#wave-overview-svg');
const plotStart = 150;
const plotEnd = 982;
const plotWidth = plotEnd - plotStart;
const rowHeight = 48;
let current = cases[0];
let stepIndex = 0;
let window = [...current.span];
let cursor = (window[0] + window[1]) / 2;
let selection;

const text = (selector, value) => { document.querySelector(selector).textContent = value; };
const unknown = value => /[xz?]/i.test(value.replace(/^0x/i, ''));
const sameWindow = (a, b) => a.every((value, index) => Math.abs(value - b[index]) < (current.span[1] - current.span[0]) * 1e-8);
const timeX = time => plotStart + (time - window[0]) / (window[1] - window[0]) * plotWidth;
const xTime = x => window[0] + (Math.max(plotStart, Math.min(plotEnd, x)) - plotStart) / plotWidth * (window[1] - window[0]);
const localX = (element, event, width) => (event.clientX - element.getBoundingClientRect().left) / element.getBoundingClientRect().width * width;

function svg(tag, attrs, value) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, String(value));
  if (value !== undefined) element.textContent = value;
  return element;
}

function displayValue(signal, value) {
  if (signal.width === 1 || unknown(value) || !/^[01]+$/.test(value)) return value;
  if (signal.id === 'credit') return String(parseInt(value, 2));
  return `0x${parseInt(value, 2).toString(16).toUpperCase().padStart(Math.ceil(signal.width / 4), '0')}`;
}

function renderPlot() {
  const height = 38 + current.signals.length * rowHeight;
  const active = new Set(current.steps[stepIndex].signals);
  plot.setAttribute('viewBox', `0 0 1000 ${height}`);
  plot.setAttribute('data-span', String(Number((window[1] - window[0]).toPrecision(12))));
  plot.setAttribute('data-start', String(window[0]));
  plot.setAttribute('data-end', String(window[1]));
  plot.setAttribute('aria-label', `${current.title}；${formatTime(window[0], current.span)} 至 ${formatTime(window[1], current.span)}；${current.signals.length} 条信号。数值在下方游标读值区列出。`);
  const elements = [];
  for (let index = 0; index <= 5; index++) {
    const x = plotStart + index / 5 * plotWidth;
    const time = window[0] + index / 5 * (window[1] - window[0]);
    elements.push(svg('line', { x1: x, x2: x, y1: 28, y2: height, class: 'wave-grid' }));
    elements.push(svg('text', { x, y: 16, class: 'wave-tick', 'text-anchor': index === 0 ? 'start' : index === 5 ? 'end' : 'middle' }, formatTime(time, current.span)));
  }
  current.signals.forEach((signal, index) => {
    const y = 30 + index * rowHeight;
    if (active.has(signal.id)) elements.push(svg('rect', { x: 0, y, width: 1000, height: rowHeight - 2, class: 'wave-track-bg' }));
    elements.push(svg('text', { x: 16, y: y + 18, class: 'wave-track-name' }, signal.label));
    elements.push(svg('text', { x: 16, y: y + 34, class: 'wave-track-role' }, signal.role));
    const group = svg('g', { opacity: active.has(signal.id) ? 1 : 0.5 });
    let previousY;
    for (const [start, end, value] of clipIntervals(signal.events, window)) {
      const left = timeX(start);
      const right = timeX(end);
      const isUnknown = unknown(value);
      if (signal.width === 1 && (value === '0' || value === '1')) {
        const level = y + (value === '1' ? 8 : 34);
        group.append(svg('path', { d: `${previousY !== undefined ? `M${left},${previousY}V${level}` : `M${left},${level}`}H${right}`, class: 'wave-line' }));
        previousY = level;
      } else {
        const inset = Math.min(4, (right - left) / 4);
        const shape = svg('path', { d: `M${left},${y + 21}L${left + inset},${y + 8}H${right - inset}L${right},${y + 21}L${right - inset},${y + 34}H${left + inset}Z`, class: `wave-bus${isUnknown ? ' wave-unknown' : ''}` });
        shape.append(svg('title', {}, `${signal.label} = ${value}`));
        group.append(shape);
        const label = displayValue(signal, value);
        if (right - left > label.length * 6.7 + 10) group.append(svg('text', { x: (left + right) / 2, y: y + 25, 'text-anchor': 'middle', class: `wave-bus-value${isUnknown ? ' wave-unknown-text' : ''}` }, label));
        previousY = undefined;
      }
    }
    elements.push(group);
  });
  elements.push(svg('line', { x1: timeX(cursor), x2: timeX(cursor), y1: 27, y2: height, class: 'wave-cursor-rule' }));
  plot.replaceChildren(...elements);
}

function renderWindow() {
  // The window end is excluded; reserve the last slider step for its preceding value.
  cursor = Math.max(window[0], Math.min(window[1] - (window[1] - window[0]) / 1000, cursor));
  text('#wave-range', `${formatTime(window[0], current.span)} — ${formatTime(window[1], current.span)}`);
  const ratio = (current.span[1] - current.span[0]) / (window[1] - window[0]);
  text('#wave-zoom-level', `${Number(ratio.toFixed(1))}× VIEW`);
  document.querySelectorAll('[data-wave-preset]').forEach(button => button.setAttribute('aria-pressed', String(sameWindow(window, current[button.dataset.wavePreset]))));
  renderPlot();
  const bins = activityBins(current.signals, current.span, 64);
  const max = Math.max(1, ...bins);
  const bars = bins.map((count, index) => svg('rect', { x: index * 12.5 + 1, y: 43 - count / max * 34, width: 9, height: Math.max(1, count / max * 34), rx: 1, class: 'wave-overview-bar' }));
  const scale = time => (time - current.span[0]) / (current.span[1] - current.span[0]) * 800;
  bars.push(svg('rect', { x: scale(window[0]), y: 2, width: scale(window[1]) - scale(window[0]), height: 44, rx: 2, class: 'wave-overview-window' }));
  overview.replaceChildren(...bars);
  text('#wave-domain-start', formatTime(current.span[0], current.span));
  text('#wave-domain-end', formatTime(current.span[1], current.span));
  text('#wave-cursor', formatTime(cursor, current.span));
  const slider = document.querySelector('#wave-cursor-slider');
  slider.value = String(Math.round((cursor - window[0]) / (window[1] - window[0]) * 1000));
  slider.setAttribute('aria-valuetext', formatTime(cursor, current.span));
  document.querySelector('#wave-values').replaceChildren(...current.signals.map(signal => {
    const raw = valueAt(signal.events, cursor);
    const item = document.createElement('span');
    const value = document.createElement('b');
    item.append(`${signal.label} `);
    value.textContent = displayValue(signal, raw);
    if (unknown(raw)) value.className = 'wave-value-unknown';
    item.title = `${signal.role} · 原始值 ${raw}`;
    item.append(value);
    return item;
  }));
}

function setWindow(next) {
  window = fitWindow(next, current.span);
  renderWindow();
}

function selectStep(index, moveWindow = true) {
  stepIndex = index;
  const step = current.steps[index];
  document.querySelectorAll('[data-wave-step]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.waveStep) === index)));
  document.querySelector('#wave-evidence').replaceChildren(...step.evidence.map(value => {
    const item = document.createElement('li');
    item.textContent = value;
    return item;
  }));
  if (moveWindow) {
    cursor = (step.window[0] + step.window[1]) / 2;
    setWindow(step.window);
  } else renderWindow();
}

function selectCase(id) {
  current = cases.find(item => item.id === id) || cases[0];
  window = [...current.span];
  cursor = (window[0] + window[1]) / 2;
  document.querySelectorAll('[data-wave-case]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.waveCase === current.id)));
  text('#wave-question', current.question);
  text('#wave-summary', current.summary);
  text('#wave-origin', current.origin_label);
  text('#wave-conclusion', current.conclusion);
  text('#wave-prompt', current.prompt);
  text('#wave-copy-status', '');
  document.querySelector('#wave-limitations').replaceChildren(...current.limitations.map(value => {
    const item = document.createElement('li');
    item.textContent = value;
    return item;
  }));
  document.querySelector('#wave-references').replaceChildren(...current.references.filter(reference => reference.path.startsWith('examples/')).map(reference => {
    const link = document.createElement('a');
    link.href = workbench.dataset.packageBase + reference.path;
    link.textContent = reference.description;
    return link;
  }));
  document.querySelector('#wave-steps').replaceChildren(...current.steps.map((step, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.waveStep = String(index);
    const number = document.createElement('span');
    number.className = 'wave-step-number';
    number.textContent = `0${index + 1}`;
    const copy = document.createElement('span');
    const title = document.createElement('span');
    title.className = 'wave-step-title';
    title.textContent = step.title;
    const summary = document.createElement('span');
    summary.className = 'wave-step-summary';
    summary.textContent = step.summary;
    copy.append(title, summary);
    button.append(number, copy);
    button.addEventListener('click', () => selectStep(index));
    return button;
  }));
  selectStep(0, false);
}

document.querySelectorAll('[data-wave-case]').forEach(button => button.addEventListener('click', () => selectCase(button.dataset.waveCase)));
document.querySelectorAll('[data-wave-preset]').forEach(button => button.addEventListener('click', () => setWindow(current[button.dataset.wavePreset])));
document.querySelectorAll('[data-wave-control]').forEach(button => button.addEventListener('click', () => {
  const control = button.dataset.waveControl;
  const span = window[1] - window[0];
  setWindow(control === 'in' || control === 'out' ? zoomWindow(window, current.span, control === 'in' ? 0.5 : 2) : panWindow(window, current.span, span * (control === 'left' ? -0.4 : 0.4)));
}));

plot.addEventListener('pointerdown', event => {
  if (event.button !== 0 || localX(plot, event, 1000) < plotStart) return;
  const x = Math.max(plotStart, Math.min(plotEnd, localX(plot, event, 1000)));
  selection = { start: x, clientX: event.clientX, pointer: event.pointerId };
  plot.setPointerCapture(event.pointerId);
});
plot.addEventListener('pointermove', event => {
  if (!selection || selection.pointer !== event.pointerId) return;
  plot.querySelector('.wave-selection')?.remove();
  const x = Math.max(plotStart, Math.min(plotEnd, localX(plot, event, 1000)));
  plot.append(svg('rect', { x: Math.min(x, selection.start), y: 28, width: Math.abs(x - selection.start), height: Number(plot.viewBox.baseVal.height) - 28, class: 'wave-selection' }));
});
plot.addEventListener('pointerup', event => {
  if (!selection || selection.pointer !== event.pointerId) return;
  const x = Math.max(plotStart, Math.min(plotEnd, localX(plot, event, 1000)));
  const start = selection.start;
  const dragged = Math.abs(event.clientX - selection.clientX) > 6;
  selection = undefined;
  plot.releasePointerCapture(event.pointerId);
  if (dragged) setWindow([xTime(Math.min(start, x)), xTime(Math.max(start, x))]);
  else { cursor = xTime(x); renderWindow(); }
});
plot.addEventListener('pointercancel', () => { selection = undefined; plot.querySelector('.wave-selection')?.remove(); });
plot.addEventListener('wheel', event => {
  if (!event.ctrlKey) return;
  event.preventDefault();
  setWindow(zoomWindow(window, current.span, event.deltaY > 0 ? 1.3 : 1 / 1.3, xTime(localX(plot, event, 1000))));
}, { passive: false });
overview.addEventListener('click', event => {
  const center = current.span[0] + localX(overview, event, 800) / 800 * (current.span[1] - current.span[0]);
  const half = (window[1] - window[0]) / 2;
  setWindow([center - half, center + half]);
});
document.querySelector('#wave-cursor-slider').addEventListener('input', event => {
  cursor = window[0] + Number(event.target.value) / 1000 * (window[1] - window[0]);
  renderWindow();
});
document.querySelector('#wave-copy').addEventListener('click', async () => {
  const prompt = current.prompt;
  try {
    await navigator.clipboard.writeText(prompt);
    text('#wave-copy-status', '已复制，可粘贴到本地 AI 助手');
  } catch {
    const range = document.createRange();
    range.selectNodeContents(document.querySelector('#wave-prompt'));
    getSelection()?.removeAllRanges();
    getSelection()?.addRange(range);
    text('#wave-copy-status', '请手动复制已选中的问题');
  }
});
selectCase(current.id);

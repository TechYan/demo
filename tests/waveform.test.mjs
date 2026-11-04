import test from 'node:test';
import assert from 'node:assert/strict';

const wave = await import('../src/lib/waveform.mjs').catch(() => ({}));
const events = [[0, '0'], [10, '1'], [20, 'x'], [30, '0']];

test('waveform helper is available to the real browser renderer', () => {
  assert.equal(typeof wave.clipIntervals, 'function');
});
test('a focused window retains the value established before its left boundary', () => {
  assert.deepEqual(wave.clipIntervals?.(events, [12, 28]), [[12, 20, '1'], [20, 28, 'x']]);
});
test('window end is exclusive and an exact event boundary uses the new value', () => {
  assert.deepEqual(wave.clipIntervals?.(events, [10, 20]), [[10, 20, '1']]);
  assert.equal(wave.valueAt?.(events, 20), 'x');
});
test('zoom and pan retain the requested span inside the capture bounds', () => {
  assert.deepEqual(wave.zoomWindow?.([20, 60], [0, 100], 0.5, 40), [30, 50]);
  assert.deepEqual(wave.panWindow?.([0, 20], [0, 100], -15), [0, 20]);
  assert.deepEqual(wave.panWindow?.([80, 100], [0, 100], 15), [80, 100]);
  assert.deepEqual(wave.fitWindow?.([-20, 150], [0, 100]), [0, 100]);
});
test('picosecond-scale captures can zoom without integer nanosecond rounding', () => {
  const result = wave.zoomWindow?.([0, 0.04], [0, 0.04], 0.25, 0.02);
  assert.deepEqual(result, [0.015, 0.025]);
  assert.equal(wave.formatTime?.(0.015, [0, 0.04]), '15 ps');
});
test('overview counts actual changes, preserving unknown values and excluding initial snapshots', () => {
  assert.deepEqual(wave.activityBins?.([{ events: [[0, '0'], [5, '0'], [10, '1'], [20, 'x']] }], [0, 40], 4), [0, 1, 1, 0]);
});

test('formatting does not round an end-exclusive cursor into the next event', () => {
  assert.equal(wave.formatTime?.(0.020999993, [0, 0.04]), '20.999993 ps');
});

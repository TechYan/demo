const mode = document.querySelector('#mode');
const width = document.querySelector('#width');
const query = new URLSearchParams(location.search);
if (['standard', 'full', 'compact'].includes(query.get('mode'))) mode.value = query.get('mode');
if (['120', '80', '60'].includes(query.get('width'))) width.value = query.get('width');
function show() {
  document.querySelectorAll('.panel').forEach(panel => {
    panel.hidden = panel.dataset.mode !== mode.value || panel.dataset.width !== width.value;
  });
  const capture = `captures/${mode.value}.${width.value}`;
  document.querySelector('#txt').href = capture + '.txt';
  document.querySelector('#ansi').href = capture + '.ansi';
  document.querySelector('#command').textContent = document.body.dataset.command + ` --report-mode ${mode.value} --trend all`;
  history.replaceState(null, '', `?mode=${mode.value}&width=${width.value}`);
}
mode.addEventListener('change', show);
width.addEventListener('change', show);
show();

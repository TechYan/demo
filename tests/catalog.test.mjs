import test from 'node:test';
import assert from 'node:assert/strict';

const catalog = await import('../src/lib/catalog.mjs').catch(() => ({}));
const projects = [
  { id: 'pvkit', name: 'PVKit', category: 'analysis', description: '总线性能分析', tags: ['AXI4', 'CXL', 'WSTRB'], keywords: ['tracker'] },
  { id: 'bus-protocol-lab', name: 'Bus Protocol Lab', category: 'protocol', description: '交互协议实验室', tags: ['AXI4', 'PCIe'], keywords: ['TLP'] },
  { id: 'pg_gen', name: 'PG Builder', category: 'registers', description: '寄存器编程指南', tags: ['JSON', 'SystemVerilog'], keywords: [] },
];

test('catalog provides the production filter', () => {
  assert.equal(typeof catalog.filterProjects, 'function');
});
test('query matches case-insensitive tags and Chinese descriptions', () => {
  assert.deepEqual(catalog.filterProjects?.(projects, 'axi4 cxl', 'all')?.map(p => p.id), ['pvkit']);
  assert.deepEqual(catalog.filterProjects?.(projects, '寄存器', 'all')?.map(p => p.id), ['pg_gen']);
});
test('category and query combine without changing the original catalog', () => {
  assert.deepEqual(catalog.filterProjects?.(projects, 'AXI4', 'protocol')?.map(p => p.id), ['bus-protocol-lab']);
  assert.deepEqual(catalog.filterProjects?.(projects, 'not-present', 'all'), []);
  assert.equal(projects.length, 3);
});
test('internal links work at a root domain and at the GitHub project subpath', () => {
  assert.equal(catalog.sitePath?.('pvkit/examples/axi4/concurrent/traffic.pv.html', '/demo/'), '/demo/pvkit/examples/axi4/concurrent/traffic.pv.html');
  assert.equal(catalog.sitePath?.('/projects/xDCT/', '/'), '/projects/xDCT/');
  assert.equal(catalog.sitePath?.('', '/demo/'), '/demo/');
});

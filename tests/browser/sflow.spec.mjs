import { test, expect } from '@playwright/test';

async function readDeclaration(page, id) {
  return JSON.parse(await page.locator(`#${id}`).textContent());
}

test('Sflow component, tile and config edits update the exported declarations', async ({ page }) => {
  await page.goto('sflow/');
  let assembly = await readDeclaration(page, 'cp-partitioned-code');
  expect(assembly.instances).toHaveLength(3);
  expect(assembly.connections).toHaveLength(2);

  await page.locator('[data-cp-preset="dual"]').click();
  assembly = await readDeclaration(page, 'cp-partitioned-code');
  expect(assembly.instances.filter(instance => instance.design === 'pcie')).toHaveLength(2);
  await expect(page.locator('.cp-unit').filter({ hasText: 'pcie_rc_x16' })).toHaveCount(1);

  await page.locator('[data-cp-config="soc_flat"]').click();
  await expect(page.locator('.cp-tile')).toHaveCount(1);
  await page.locator('[data-cp-tile="dnoc"]').selectOption('io');
  await expect(page.locator('[data-cp-config="soc_partitioned"]')).toHaveAttribute('aria-pressed', 'true');
  assembly = await readDeclaration(page, 'cp-partitioned-code');
  expect(assembly.instances.find(instance => instance.name === 'dnoc').tile).toBe('io');

  await page.locator('[data-cp-config="soc_debug"]').click();
  const project = await readDeclaration(page, 'cp-project-code');
  expect(project.default_config).toBe('soc_debug');
  expect(project.targets.compose.views.debug.filesets).toEqual(['rtl', 'debug']);
  expect(project.targets.compose.views.debug.defines).toContain('SFLOW_VIEW_DEBUG=1');
  expect(assembly.instances.every(instance => instance.view === 'tile')).toBe(true);
});

test('Sflow connection editing, mobile layout and print output retain usable declarations', async ({ page }) => {
  await page.goto('sflow/');
  await page.locator('[data-cp-preset="full"]').click();
  await page.locator('[data-cp-remove="0"]').click();
  let assembly = await readDeclaration(page, 'cp-partitioned-code');
  expect(assembly.connections).toHaveLength(6);
  expect(assembly.top_ports.bundles.map(port => port.bundle)).toContain('pcie.mem');

  await page.locator('#cp-source').selectOption('pcie.mem');
  await page.locator('#cp-sink').selectOption('dnoc.in0');
  await page.locator('#cp-add-link').click();
  assembly = await readDeclaration(page, 'cp-partitioned-code');
  expect(assembly.connections).toHaveLength(7);
  const endpoints = assembly.connections.flatMap(connection => [connection.from, connection.to]);
  const exports = assembly.top_ports.bundles.map(port => port.bundle);
  expect(new Set([...endpoints, ...exports]).size).toBe(endpoints.length + exports.length);

  const downloadEvent = page.waitForEvent('download');
  await page.locator('#cp-download').click();
  expect((await downloadEvent).suggestedFilename()).toBe('sflow-composition-files.json');
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('[data-cp-panel="project"]')).toBeVisible();
  await expect(page.locator('[data-cp-panel="flat"]')).toBeVisible();
});

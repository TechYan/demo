import { test, expect } from '@playwright/test';

test('xDCT filters, port search and all evidence tabs show the shipped data', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/xDCT/index.html');
  await expect(page.locator('.change-card:visible')).toHaveCount(10);
  await page.locator('[data-filter="breaking"]').click();
  await expect(page.locator('.change-card:visible')).toHaveCount(6);
  await page.locator('#search').fill('rx_data');
  await expect(page.locator('.change-card:visible')).toHaveCount(1);
  await expect(page.locator('.change-card:visible')).toContainText('WIDTH_CHANGED');
  await page.locator('#search').clear();
  await page.locator('[data-filter="order"]').click();
  await expect(page.locator('.change-card:visible')).toHaveCount(3);
  for (const name of ['source', 'manifests', 'diff', 'report']) {
    await page.locator(`[data-evidence="${name}"]`).click();
    await expect(page.locator(`#evidence-${name}`)).toBeVisible();
  }
  expect(errors).toEqual([]);
  await page.screenshot({ path: 'test-results/xdct.png', fullPage: false });
});

test('xpggen loads all five real captures and authentic export formats', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/xpggen/index.html');
  await expect(page.locator('#frame-buttons button')).toHaveCount(5);
  await expect(page.locator('#steps-body tr')).toHaveCount(6);
  for (let index = 0; index < 5; index++) {
    await page.locator('#frame-buttons button').nth(index).click();
    await expect(page.locator('#frame-position')).toHaveText(`${index + 1} / 5`);
    await expect.poll(() => page.locator('#capture').evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
  }
  for (const format of ['csv', 'sv', 'md', 'json']) {
    await page.locator(`[data-format="${format}"]`).click();
    const link = await page.locator('#download-export').getAttribute('href');
    const response = await page.request.get('/xpggen/' + link);
    expect(response.status()).toBe(200);
    expect((await page.locator('#export-code').textContent()).replaceAll('\r\n', '\n')).toBe((await response.text()).replaceAll('\r\n', '\n'));
  }
  expect(errors).toEqual([]);
  await page.screenshot({ path: 'test-results/xpggen.png', fullPage: false });
});

test('PG sample remains interactive and standalone tools initialize without exceptions', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/pg_gen/index.html');
  await page.locator('#loadSample').click();
  await expect(page.locator('body')).toContainText('DEMO_CONTROL');
  for (const path of ['bus-protocol-lab/axi-pcie-packet-studio.html', 'bus-protocol-lab/axi4-atomic-format-table.html', 'bus-protocol-lab/pcie-tlp-split-demo.html', 'uvm_wiki/uvm_wiki.html']) {
    expect((await page.goto('/' + path)).status()).toBe(200);
    await expect(page.locator('body')).not.toBeEmpty();
  }
  expect(errors).toEqual([]);
});

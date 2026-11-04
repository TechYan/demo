import { test, expect } from '@playwright/test';

test('catalog filters and search compose, empty state resets, keyboard shortcut focuses search', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('./');
  await expect(page.locator('[data-project]:visible')).toHaveCount(7);
  await page.getByRole('button', { name: '寄存器与配置' }).click();
  await expect(page.locator('[data-project]:visible')).toHaveCount(2);
  const search = page.getByRole('searchbox', { name: '搜索项目、协议或技术' });
  await search.fill('Textual');
  await expect(page.locator('[data-project]:visible')).toHaveCount(1);
  await expect(page.locator('[data-project="xpggen"]')).toBeVisible();
  await search.fill('missing-result');
  await expect(page.locator('#empty-state')).toBeVisible();
  await page.getByRole('button', { name: '清除搜索与筛选' }).click();
  await expect(page.locator('[data-project]:visible')).toHaveCount(7);
  await page.locator('h1').click();
  await page.keyboard.press('/');
  await expect(search).toBeFocused();
  await search.fill('AXI4 CXL');
  await expect(page.locator('[data-project]:visible')).toHaveCount(1);
  await expect(page.locator('[data-project="pvkit"]')).toBeVisible();
  expect(errors).toEqual([]);
});

test('theme is accessible and persists, and a category URL opens the right selection', async ({ page }) => {
  await page.goto('./?category=verification#projects');
  await expect(page.locator('[data-project]:visible')).toHaveCount(2);
  await page.getByRole('button', { name: '切换浅色主题' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.reload();
  await expect(page.getByRole('button', { name: '切换深色主题' })).toBeVisible();
  await page.getByRole('button', { name: '切换深色主题' }).click();
});

test('all seven project routes expose actual demo and artifact links', async ({ page }) => {
  const projects = [ ['pvkit', 'PVKit'], ['bus-protocol-lab', 'Bus Protocol Lab'], ['pg_gen', 'PG Builder'], ['uvm_wiki', 'UVM Wiki'], ['svip', 'SVIP'], ['xpggen', 'xpggen'], ['xDCT', 'xDCT'] ];
  for (const [id, name] of projects) {
    const response = await page.goto(`projects/${id}/`);
    expect(response.status()).toBe(200);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(name);
    const demo = page.getByRole('link', { name: '进入演示', exact: true });
    const href = await demo.getAttribute('href');
    expect(href).toContain(`/${id}/`);
    for (const link of await page.locator('.artifact-link').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')))) {
      expect((await page.request.get(link)).status(), link).toBe(200);
    }
  }
});

test('desktop and mobile catalog remain readable without horizontal overflow', async ({ page }) => {
  await page.goto('./');
  await page.screenshot({ path: 'test-results/catalog-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('./');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole('searchbox')).toBeVisible();
  await page.screenshot({ path: 'test-results/catalog-mobile.png', fullPage: true });
  await page.goto('projects/uvm_wiki/');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/project-mobile.png', fullPage: true });
});

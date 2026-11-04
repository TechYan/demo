import { test, expect } from '@playwright/test';

test('guided cases connect waveform windows with evidence and preserve picosecond timing', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('wavedbg/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('关键几拍');
  const cases = page.locator('[data-wave-case]');
  await expect(cases).toHaveCount(4);
  for (const button of await cases.all()) {
    await button.click();
    await expect(button).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('#wave-question')).not.toBeEmpty();
    const steps = page.locator('[data-wave-step]');
    expect(await steps.count()).toBeGreaterThanOrEqual(3);
    for (const step of await steps.all()) {
      await step.click();
      await expect(step).toHaveAttribute('aria-pressed', 'true');
      await expect(page.locator('#wave-evidence li').first()).toBeVisible();
    }
    await expect(page.locator('#wave-conclusion')).not.toBeEmpty();
    if (!await page.locator('.wave-result details').evaluate(node => node.open)) await page.getByText('本例资料与观察边界', { exact: true }).click();
    await expect(page.locator('#wave-references a').first()).toBeVisible();
  }
  await cases.first().click();
  await expect(page.locator('#wave-range')).toContainText('ps');
  const globalSpan = Number(await page.locator('#wave-svg').getAttribute('data-span'));
  await page.getByRole('button', { name: '关键几拍', exact: true }).click();
  const detailSpan = Number(await page.locator('#wave-svg').getAttribute('data-span'));
  expect(detailSpan).toBeGreaterThan(0);
  expect(detailSpan).toBeLessThan(globalSpan);
  await page.getByRole('button', { name: '放大波形' }).click();
  expect(Number(await page.locator('#wave-svg').getAttribute('data-span'))).toBeLessThan(detailSpan);
  const beforePan = Number(await page.locator('#wave-svg').getAttribute('data-start'));
  await page.getByRole('button', { name: '向右平移' }).click();
  expect(Number(await page.locator('#wave-svg').getAttribute('data-start'))).toBeGreaterThan(beforePan);
  await page.getByRole('button', { name: '全局', exact: true }).click();
  expect(Number(await page.locator('#wave-svg').getAttribute('data-span'))).toBe(globalSpan);
  expect(errors).toEqual([]);
});

test('drag selection zooms, cursor exposes signal values, and prompts are copyable', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('wavedbg/');
  const svg = page.locator('#wave-svg');
  await svg.scrollIntoViewIfNeeded();
  const bounds = await svg.boundingBox();
  const initialSpan = Number(await svg.getAttribute('data-span'));
  const x = fraction => bounds.x + bounds.width * fraction;
  await page.mouse.move(x(0.35), bounds.y + 95);
  await page.mouse.down();
  await page.mouse.move(x(0.65), bounds.y + 95, { steps: 8 });
  await page.mouse.up();
  expect(Number(await svg.getAttribute('data-span'))).toBeLessThan(initialSpan);
  await page.mouse.click(x(0.5), bounds.y + 95);
  await expect(page.locator('#wave-cursor')).toContainText('ps');
  await expect(page.locator('#wave-values')).toContainText('clk');
  await page.getByRole('button', { name: '复制当前问题' }).click();
  await expect(page.locator('#wave-copy-status')).toHaveText('已复制，可粘贴到本地 AI 助手');
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(await page.locator('#wave-prompt').textContent());
});

test('protocol skills and mobile waveform controls remain usable in both themes', async ({ page }) => {
  await page.goto('wavedbg/');
  await expect(page.locator('#skills [data-skill]')).toHaveCount(7);
  await page.screenshot({ path: 'test-results/wavedbg-desktop.png', fullPage: true });
  await page.locator('.wave-workbench').screenshot({ path: 'test-results/wavedbg-workbench.png' });
  await page.getByRole('button', { name: '切换浅色主题' }).click();
  await page.locator('#wave-demo').screenshot({ path: 'test-results/wavedbg-light.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: '关键几拍', exact: true }).click();
  await expect(page.locator('#wave-range')).toContainText('ps');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: 'test-results/wavedbg-mobile.png', fullPage: true });
});

test('the rightmost cursor stays before the excluded end and overview coordinates match their drawing', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto('wavedbg/');
  await page.getByRole('slider', { name: '移动波形游标' }).press('End');
  await expect(page.locator('#wave-cursor')).toHaveText('39.96 ps');
  await expect(page.locator('#wave-values')).toContainText('clk 1');
  for (const width of [1920, 1100]) {
    await page.setViewportSize({ width, height: 1080 });
    await page.getByRole('button', { name: '关键几拍', exact: true }).click();
    await page.locator('#wave-overview-svg').scrollIntoViewIfNeeded();
    const start = Number(await page.locator('#wave-svg').getAttribute('data-start'));
    const overview = await page.locator('#wave-overview-svg').boundingBox();
    const box = await page.locator('.wave-overview-window').boundingBox();
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    // Browser pointer coordinates may round to the nearest rendered pixel.
    expect(Math.abs(Number(await page.locator('#wave-svg').getAttribute('data-start')) - start)).toBeLessThan(0.04 / overview.width);
  }
});

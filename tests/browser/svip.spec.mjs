import { test, expect } from '@playwright/test';

test('SVIP is the second catalog entry and XDP search reaches the product page', async ({ page }) => {
  await page.goto('./');
  const cards = page.locator('[data-project]');
  await expect(cards.nth(0)).toHaveAttribute('data-project', 'wavedbg');
  await expect(cards.nth(1)).toHaveAttribute('data-project', 'svip');
  await page.getByRole('searchbox').fill('xdp');
  await expect(page.locator('[data-project]:visible')).toHaveCount(1);
  await cards.nth(1).getByRole('link', { name: '进入演示' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('SVIP');
  await page.locator('.hero-visual img').waitFor();
  await page.screenshot({ path: 'test-results/svip-desktop.png', animations: 'disabled' });
  await page.locator('#timing').screenshot({ path: 'test-results/svip-timing.png' });
  const diagram = await page.getByRole('link', { name: 'draw.io 源图' }).getAttribute('href');
  const response = await page.request.get(diagram);
  expect(response.ok()).toBe(true);
  expect(await response.text()).toContain('<mxGraphModel');
});

test('XDP timing, tracker cross-reference and integration example work on a phone', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('projects/svip/');
  await page.screenshot({ path: 'test-results/svip-mobile.png', animations: 'disabled' });
  await page.getByRole('link', { name: '进入演示', exact: true }).click();
  await expect(page).toHaveURL(/#timing$/);
  const cases = page.locator('.timing-case');
  for (const entry of await cases.all()) {
    if (!(await entry.evaluate(element => element.open))) await entry.locator('summary').click();
    const image = entry.getByRole('img');
    await expect.poll(() => image.evaluate(el => el.complete && el.naturalWidth > 0)).toBe(true);
    const source = await entry.getByRole('link', { name: 'WaveJSON' }).getAttribute('href');
    expect((await (await page.request.get(source)).json()).signal[0].name).toBe('CLK');
  }
  await expect(cases.first()).not.toHaveAttribute('open');
  await page.getByRole('link', { name: 'pin_trk=41' }).click();
  await expect(page.locator(':target')).toContainText('edge=24 chan=RDATA');
  await page.locator('.code-disclosure > summary').click();
  await expect(page.locator('.code-disclosure pre')).toContainText('checks.attach(port)');
  for (const width of [320, 390, 768]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});

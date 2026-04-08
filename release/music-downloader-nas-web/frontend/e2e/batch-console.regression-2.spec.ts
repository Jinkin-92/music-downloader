import { test, expect } from '@playwright/test';

// Regression: ISSUE-002 — batch page emitted deprecated Ant Design dropdownRender warning
// Found by /qa on 2026-03-26
// Report: .gstack/qa-reports/qa-report-localhost-2026-03-26.md

test.describe('batch page console regression', () => {
  test('batch page loads without dropdownRender deprecation warning', async ({ page }) => {
    const consoleMessages: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'warning' || msg.type() === 'error') {
        consoleMessages.push(msg.text());
      }
    });

    await page.goto('/batch');
    await page.waitForLoadState('networkidle');

    expect(consoleMessages).not.toContainEqual(expect.stringContaining('dropdownRender'));
  });
});

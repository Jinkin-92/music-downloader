import { test, expect } from '@playwright/test';

// Regression: ISSUE-003 — text input did not enable batch search
// Found by /qa on 2026-03-26
// Report: .gstack/qa-reports/qa-report-localhost-2026-03-26.md

test.describe('text input batch search regression', () => {
  test('typing valid lines enables batch search', async ({ page }) => {
    await page.goto('/batch');
    await page.waitForLoadState('networkidle');

    const textInput = page.locator('textarea').first();
    const batchSearchButton = page.getByRole('button', { name: /批量搜索/ });

    await expect(batchSearchButton).toBeDisabled();

    await textInput.fill('夜曲 - 周杰伦\n晴天 - 周杰伦');

    await expect(batchSearchButton).toBeEnabled();
    await expect(page.getByText('已识别')).toContainText('2');
  });
});

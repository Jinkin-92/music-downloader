import { test, expect } from '@playwright/test';

// Regression: ISSUE-QA-PLAYLIST-ROUTE — /playlist route rendered a blank content area
// Found by /qa on 2026-03-26
// Report: .gstack/qa-reports/qa-report-localhost-2026-03-26.md

test.describe('playlist route regression', () => {
  test('legacy /playlist route redirects to batch page content', async ({ page }) => {
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/batch$/);
    await expect(page.getByText('歌单导入')).toBeVisible();
    await expect(page.getByPlaceholder(/网易云或QQ音乐的歌单分享链接/)).toBeVisible();
  });
});

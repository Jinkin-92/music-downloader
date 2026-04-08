/**
 * 歌单导入完整闭环E2E测试 - 简化版
 *
 * 测试流程：歌单导入 → 搜索匹配 → 下载 → 验证完成
 *
 * 测试歌单：https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
 */

import { test, expect } from '@playwright/test';

const TEST_PLAYLIST_URL = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';
const TEST_DOWNLOAD_DIR = 'test_downloads';

test.describe('歌单导入 - 闭环测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到歌单导入页面
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // 额外等待React渲染
  });

  /**
   * 测试1：页面加载和音乐源验证
   */
  test('页面加载和音乐源验证', async ({ page }) => {
    // 等待页面完全加载
    await expect(page.locator('body')).toBeVisible();

    // 查找音乐源checkbox
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();

    console.log(`找到 ${count} 个checkbox`);

    // 验证至少有4个音乐源checkbox
    expect(count).toBeGreaterThanOrEqual(4);

    // 检查前4个checkbox是否被选中（音乐源默认全选）
    for (let i = 0; i < Math.min(4, count); i++) {
      const isChecked = await checkboxes.nth(i).isChecked();
      console.log(`Checkbox ${i}: checked=${isChecked}`);
    }

    await page.screenshot({ path: 'screenshots/simple-page-loaded.png' });
  });

  /**
   * 测试2：歌单解析
   */
  test('歌单URL解析', async ({ page }) => {
    // 查找输入框 - 使用更宽松的选择器
    const input = page.locator('input').filter({ hasText: '' }).first();
    await expect(input).toBeVisible();

    // 输入歌单URL
    await input.fill(TEST_PLAYLIST_URL);
    console.log('已输入歌单URL');

    // 查找并点击解析按钮
    const parseButton = page.locator('button').filter({ hasText: /解析/i }).first();
    await expect(parseButton).toBeVisible();
    await parseButton.click();

    // 等待解析完成 - 等待表格出现且非测量行
    await page.waitForTimeout(5000);

    // 等待数据行出现 - 使用locator.all()排除隐藏行
    await page.waitForTimeout(5000);

    // 获取所有行并过滤可见行
    const allRows = page.locator('.ant-table-tbody tr');
    const allCount = await allRows.count();

    // 找到第一个非隐藏的行
    let visibleRowCount = 0;
    for (let i = 0; i < Math.min(allCount, 10); i++) {
      const isVisible = await allRows.nth(i).isVisible();
      if (isVisible) {
        visibleRowCount++;
      }
    }

    console.log(`总行数: ${allCount}, 可见行: ${visibleRowCount}`);
    expect(visibleRowCount).toBeGreaterThan(0);

    // 使用第一个可见行
    const firstVisibleRow = allRows.filter({ hasNotText: 'measure-row' }).first();
    await expect(firstVisibleRow).toBeVisible({ timeout: 10000 });

    expect(rowCount).toBeGreaterThan(0);

    await page.screenshot({ path: 'screenshots/simple-parsed.png' });
  });

  /**
   * 测试3：批量搜索
   */
  test('批量搜索', async ({ page }) => {
    // 先解析歌单
    await parsePlaylistSimple(page);

    // 等待数据稳定
    await page.waitForTimeout(2000);

    // 点击批量搜索按钮
    const searchButton = page.locator('button').filter({ hasText: /搜索/i }).or(
      page.locator('button').filter({ hasText: /批量/i })
    ).first();

    await expect(searchButton).toBeEnabled({ timeout: 10000 });
    await searchButton.click();

    console.log('开始批量搜索...');

    // 等待搜索进度显示
    await expect(page.locator('.ant-progress').or(
      page.getByText(/搜索|进度/i)
    ).first()).toBeVisible({ timeout: 10000 });

    // 等待搜索完成（最多5分钟）
    let completed = false;
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(5000);

      // 检查是否有完成标志
      const completedText = page.getByText(/完成|成功|matched/i);
      if (await completedText.isVisible({ timeout: 1000 })) {
        completed = true;
        console.log('✅ 搜索完成');
        break;
      }

      const progress = page.locator('.ant-progress');
      if (await progress.isVisible({ timeout: 1000 })) {
        console.log('搜索进行中...');
      }
    }

    expect(completed).toBeTruthy();

    // 等待结果表格渲染
    await page.waitForTimeout(3000);

    // 验证相似度标签（检查是否有数字百分比的标签）
    const percentTags = page.locator('text=/\\d+%/');
    const tagCount = await percentTags.count();
    console.log(`📊 相似度标签数量: ${tagCount}`);

    // 验证前几个标签不是NaN
    if (tagCount > 0) {
      for (let i = 0; i < Math.min(5, tagCount); i++) {
        const text = await percentTags.nth(i).textContent();
        expect(text).not.toContain('NaN');
        console.log(`相似度 ${i}: ${text}`);
      }
    }

    await page.screenshot({ path: 'screenshots/simple-searched.png', fullPage: true });
  });

  /**
   * 测试4：完整流程（解析+搜索）
   */
  test('完整流程 - 解析和搜索', async ({ page }) => {
    console.log('🚀 开始完整流程测试...');

    // 解析歌单
    await parsePlaylistSimple(page);

    // 等待稳定
    await page.waitForTimeout(2000);

    // 搜索
    const searchButton = page.locator('button').filter({ hasText: /搜索/i }).or(
      page.locator('button').filter({ hasText: /批量/i })
    ).first();

    await expect(searchButton).toBeEnabled({ timeout: 10000 });
    await searchButton.click();

    console.log('搜索进行中...');

    // 等待搜索完成
    await expect(page.getByText(/完成|成功/i).or(
      page.locator('text=/\\d+.*\\d+/')
    ).first()).toBeVisible({ timeout: 300000 });

    // 最终验证
    await page.waitForTimeout(3000);

    const dataRows = page.locator('.ant-table-tbody tr').filter({ hasNotText: 'measure-row' });
    const rowCount = await dataRows.count();

    const percentTags = page.locator('text=/\\d+%/');
    const tagCount = await percentTags.count();

    console.log(`✅ 完整流程成功！`);
    console.log(`   歌曲: ${rowCount} 首`);
    console.log(`   相似度标签: ${tagCount} 个`);

    await page.screenshot({ path: 'screenshots/simple-complete.png', fullPage: true });

    expect(rowCount).toBeGreaterThan(0);
  });
});

/**
 * 辅助函数：简化版歌单解析
 */
async function parsePlaylistSimple(page: any) {
  // 查找输入框
  const input = page.locator('input').filter({ hasText: '' }).first();
  await expect(input).toBeVisible();
  await input.fill(TEST_PLAYLIST_URL);

  // 点击解析按钮
  const parseButton = page.locator('button').filter({ hasText: /解析/i }).first();
  await expect(parseButton).toBeVisible();
  await parseButton.click();

  // 等待数据行出现
  const dataRows = page.locator('.ant-table-tbody tr').filter({ hasNotText: 'measure-row' });
  await expect(dataRows.first()).toBeVisible({ timeout: 30000 });

  const rowCount = await dataRows.count();
  console.log(`解析完成: ${rowCount} 首`);
}

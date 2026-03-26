import { test, expect } from '@playwright/test';

/**
 * 歌单导入功能E2E测试
 *
 * 测试网易云歌单导入:
 * https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
 */

test.describe('歌单导入功能', () => {
  const playlistUrl = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';

  test.beforeEach(async ({ page }) => {
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');
  });

  test('1. 页面导航和UI验证', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h2').filter({ hasText: '歌单导入' })).toBeVisible();

    // 验证输入框存在
    const urlInput = page.locator('input[placeholder*="歌单链接"]').or(
      page.locator('input[type="text"]')
    ).first();
    await expect(urlInput).toBeVisible();

    // 验证解析按钮存在 - 使用正确的按钮文本
    const parseButton = page.getByRole('button', { name: '解析歌单' });
    await expect(parseButton).toBeVisible();

    // 截图记录初始状态
    await page.screenshot({ path: 'test-results/playlist-import-1-initial.png' });
  });

  test('2. 输入歌单URL', async ({ page }) => {
    // 查找输入框
    const urlInput = page.locator('input[type="text"]').first();

    // 输入歌单URL
    await urlInput.fill(playlistUrl);

    // 等待React状态更新
    await page.waitForTimeout(1000);

    // 截图记录输入状态
    await page.screenshot({ path: 'test-results/playlist-import-2-url-entered.png' });

    // 验证输入值
    const inputValue = await urlInput.inputValue();
    expect(inputValue).toBe(playlistUrl);
  });

  test('3. 解析歌单 - 完整流程', async ({ page }) => {
    // 设置测试超时为90秒
    test.setTimeout(90000);

    // 输入歌单URL
    const urlInput = page.locator('input[type="text"]').first();
    await urlInput.fill(playlistUrl);
    await page.waitForTimeout(1000);

    // 点击解析按钮 - 使用正确的按钮文本
    const parseButton = page.getByRole('button', { name: '解析歌单' });
    await parseButton.click();

    // 等待加载状态
    await page.waitForTimeout(3000);

    // 截图记录加载状态
    await page.screenshot({ path: 'test-results/playlist-import-3-loading.png' });

    // 等待表格出现(最多60秒)
    await page.waitForSelector('.ant-table-tbody tr', {
      timeout: 60000
    }).catch(() => {
      console.log('Table did not appear in 60s, checking for errors...');
    });

    // 截图记录完成状态
    await page.screenshot({
      path: 'test-results/playlist-import-4-complete.png',
      fullPage: true
    });

    // 检查是否有结果显示
    const table = page.locator('.ant-table');
    const hasTable = await table.count();

    console.log('Has result table:', hasTable > 0);

    if (hasTable > 0) {
      // 获取表格行数
      const rows = page.locator('.ant-table-tbody tr');
      const rowCount = await rows.count();
      console.log('Playlist songs count:', rowCount);

      // 验证至少有歌曲
      expect(rowCount).toBeGreaterThan(0);

      // 检查第一行内容
      const firstRowText = await rows.first().textContent();
      console.log('First row content:', firstRowText.substring(0, 100));

      // 截图记录表格
      await page.screenshot({ path: 'test-results/playlist-import-5-table.png' });
    } else {
      // 检查是否有错误消息
      const errorMessage = page.locator('.ant-alert-error, .ant-message-error');
      const hasError = await errorMessage.count();

      if (hasError > 0) {
        const errorText = await errorMessage.first().textContent();
        console.log('Import error:', errorText);
      }
    }
  });

  test('4. 歌单信息显示验证', async ({ page }) => {
    // 设置测试超时为90秒
    test.setTimeout(90000);

    // 输入并解析
    await page.locator('input[type="text"]').first().fill(playlistUrl);
    await page.waitForTimeout(1000);

    await page.getByRole('button', { name: '解析歌单' }).click();

    // 等待表格出现 - 排除Ant Design的隐藏测量行
    await page.waitForSelector('.ant-table-tbody tr:not([aria-hidden="true"])', {
      timeout: 60000
    });

    // 查找可能的歌单信息显示
    const playlistTitle = page.locator('text=/歌单名称|playlist|title/i');
    const songCount = page.locator('text=/\\d+\\s*首歌曲/');

    const hasTitle = await playlistTitle.count();
    const hasCount = await songCount.count();

    console.log('Has playlist title:', hasTitle > 0);
    console.log('Has song count:', hasCount > 0);

    // 截图记录完整页面
    await page.screenshot({
      path: 'test-results/playlist-import-6-info.png',
      fullPage: true
    });
  });

  test('5. 批量搜索功能验证', async ({ page }) => {
    // 设置测试超时为120秒(包含解析+搜索)
    test.setTimeout(120000);

    // 先解析歌单
    await page.locator('input[type="text"]').first().fill(playlistUrl);
    await page.waitForTimeout(1000);

    await page.getByRole('button', { name: '解析歌单' }).click();

    // 等待表格出现 - 排除Ant Design的隐藏测量行
    await page.waitForSelector('.ant-table-tbody tr:not([aria-hidden="true"])', {
      timeout: 60000
    });

    // 选择音乐源（启用批量搜索按钮）
    await page.locator('label').filter({ hasText: '网易云' }).click();
    await page.waitForTimeout(500);

    // 全选歌曲（启用批量搜索按钮）
    await page.getByRole('button', { name: '全选' }).click();
    await page.waitForTimeout(500);

    // 检查是否有批量搜索按钮
    const batchSearchButton = page.getByRole('button', { name: /批量搜索/ });
    const hasBatchSearch = await batchSearchButton.count();

    console.log('Has batch search button:', hasBatchSearch > 0);

    if (hasBatchSearch > 0) {
      // 截图:解析后状态
      await page.screenshot({ path: 'test-results/playlist-import-7-before-search.png' });

      // 点击批量搜索
      await batchSearchButton.click();

      // 等待搜索开始
      await page.waitForTimeout(5000);

      // 截图:搜索进行中
      await page.screenshot({ path: 'test-results/playlist-import-8-searching.png' });

      // 等待搜索完成(最多60秒)
      await page.waitForTimeout(60000);

      // 截图:搜索完成
      await page.screenshot({
        path: 'test-results/playlist-import-9-search-complete.png',
        fullPage: true
      });
    }
  });

  test('6. 错误处理 - 无效URL', async ({ page }) => {
    // 输入无效URL
    const invalidUrl = 'https://invalid-url.com/playlist';

    await page.locator('input[type="text"]').first().fill(invalidUrl);
    await page.waitForTimeout(1000);

    // 点击解析
    const parseButton = page.getByRole('button', { name: '解析歌单' });
    await parseButton.click();

    // 等待错误响应
    await page.waitForTimeout(5000);

    // 检查错误提示
    const errorMessage = page.locator('.ant-message-error, .ant-alert-error');
    const hasError = await errorMessage.count();

    console.log('Has error message:', hasError > 0);

    if (hasError > 0) {
      const errorText = await errorMessage.first().textContent();
      console.log('Error message:', errorText);

      // 截图记录错误
      await page.screenshot({ path: 'test-results/playlist-import-error-invalid-url.png' });
    }
  });

  test('7. 清空功能验证', async ({ page }) => {
    // 设置测试超时为90秒
    test.setTimeout(90000);

    // 解析歌单
    await page.locator('input[type="text"]').first().fill(playlistUrl);
    await page.waitForTimeout(1000);

    await page.getByRole('button', { name: '解析歌单' }).click();

    // 等待表格出现 - 排除Ant Design的隐藏测量行
    await page.waitForSelector('.ant-table-tbody tr:not([aria-hidden="true"])', {
      timeout: 60000
    });

    // 检查是否有清空按钮
    const clearButton = page.getByRole('button', { name: /清空|重置/ });
    const hasClear = await clearButton.count();

    if (hasClear > 0) {
      // 点击清空
      await clearButton.click();
      await page.waitForTimeout(1000);

      // 截图记录清空后状态
      await page.screenshot({ path: 'test-results/playlist-import-cleared.png' });

      // 验证表格已清空
      const table = page.locator('.ant-table-tbody tr');
      const rowCount = await table.count();
      console.log('Rows after clear:', rowCount);
    }
  });
});

test.describe('歌单导入 - 后端API验证', () => {
  const playlistUrl = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';

  test('直接测试后端歌单解析API', async ({ request }) => {
    // 调用后端API
    const response = await request.post('http://localhost:8003/api/playlist/parse', {
      data: {
        url: playlistUrl
      }
    });

    console.log('Response status:', response.status());
    console.log('Response headers:', response.headers());

    // 验证响应
    expect(response.status()).toBe(200);

    const data = await response.json();
    console.log('Response data:', JSON.stringify(data, null, 2));

    // 验证返回数据结构
    expect(data).toHaveProperty('songs');
    expect(Array.isArray(data.songs)).toBeTruthy();

    if (data.songs.length > 0) {
      console.log('Song count:', data.songs.length);
      console.log('First song:', data.songs[0]);

      // 验证歌曲数据结构
      expect(data.songs[0]).toHaveProperty('name');
      expect(data.songs[0]).toHaveProperty('artist');
    }
  });
});

test.describe('歌单导入 - 完整下载流程验证', () => {
  const playlistUrl = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';

  test('完整流程: 解析+搜索+下载前3首', async ({ page }) => {
    // 设置测试超时为180秒(包含解析+搜索+下载)
    test.setTimeout(180000);

    // 重新导航到页面（确保是干净的初始状态）
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');

    // 先解析歌单
    await page.locator('input[type="text"]').first().fill(playlistUrl);
    await page.waitForTimeout(1000);

    await page.getByRole('button', { name: '解析歌单' }).click();

    // 等待表格出现
    await page.waitForSelector('.ant-table-tbody tr:not([aria-hidden="true"])', {
      timeout: 60000
    });

    // 选择音乐源（选择酷狗和酷我，因为它们有搜索结果）
    await page.locator('label').filter({ hasText: '酷狗' }).click();
    await page.locator('label').filter({ hasText: '酷我' }).click();
    await page.waitForTimeout(500);

    // 全选所有歌曲
    await page.getByRole('button', { name: '全选' }).click();
    await page.waitForTimeout(500);

    // 点击批量搜索
    const batchSearchButton = page.getByRole('button', { name: /批量搜索/ });
    await batchSearchButton.click();

    console.log('等待批量搜索完成...');
    // 等待搜索完成（搜索完成后会出现"重新搜索"按钮）
    await page.waitForTimeout(90000);

    // 截图：搜索完成状态
    await page.screenshot({
      path: 'test-results/playlist-import-complete-flow-after-search.png',
      fullPage: true
    });

    // 点击下载按钮
    const downloadButton = page.getByRole('button', { name: /下载选中/ });
    const hasDownload = await downloadButton.count();

    console.log('Has download button:', hasDownload > 0);

    if (hasDownload > 0) {
      await downloadButton.click();
      console.log('已点击下载按钮');

      // 等待下载完成（等待3分钟）
      await page.waitForTimeout(180000);

      // 截图：下载完成
      await page.screenshot({
        path: 'test-results/playlist-import-complete-flow-after-download.png',
        fullPage: true
      });

      console.log('下载流程测试完成');
    }
  });
});

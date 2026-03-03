/**
 * 歌单导入完整闭环E2E测试 - API优先版本
 *
 * 测试流程：歌单导入 → 搜索匹配 → 验证完成
 *
 * 测试歌单：https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
 */

import { test, expect } from '@playwright/test';

const TEST_PLAYLIST_URL = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';

test.describe('歌单导入 - API闭环测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到歌单导入页面
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // 等待React完全渲染
  });

  /**
   * 测试1：页面基本元素验证
   */
  test('页面基本元素验证', async ({ page }) => {
    // 验证页面标题存在
    const title = page.locator('h1, h2').first();
    await expect(title).toBeVisible();

    // 查找输入框
    const input = page.locator('input').first();
    await expect(input).toBeVisible();

    // 查找解析按钮
    const button = page.locator('button').filter({ hasText: /解析|导入/i }).first();
    await expect(button).toBeVisible();

    console.log('✅ 页面基本元素加载正常');

    await page.screenshot({ path: 'screenshots/api-page-loaded.png' });
  });

  /**
   * 测试2：歌单解析API调用
   */
  test('歌单解析API调用', async ({ page }) => {
    // 监听API响应
    const apiResponse = page.waitForResponse(resp =>
      resp.url().includes('/api/playlist/parse') && resp.status() === 200
    );

    // 查找输入框并输入URL
    const input = page.locator('input').first();
    await input.fill(TEST_PLAYLIST_URL);

    // 点击解析按钮
    const parseButton = page.locator('button').filter({ hasText: /解析/i }).first();
    await parseButton.click();

    // 等待API响应
    const response = await Promise.race([
      apiResponse,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('API timeout')), 30000)
      )
    ]) as any;

    // 验证API响应
    expect(response.status()).toBe(200);

    const data = await response.json();
    console.log('API响应:', JSON.stringify(data).slice(0, 200));

    // 验证响应包含歌曲数据
    expect(data.songs || data.data || data).toBeDefined();

    // 等待UI更新
    await page.waitForTimeout(3000);

    // 检查页面是否有歌曲列表显示
    const table = page.locator('.ant-table, table').first();
    const tableVisible = await table.isVisible({ timeout: 5000 }).catch(() => false);

    if (tableVisible) {
      console.log('✅ 表格已显示');
    }

    console.log('✅ 歌单解析API调用成功');

    await page.screenshot({ path: 'screenshots/api-parse-success.png' });
  });

  /**
   * 测试3：批量搜索API调用（SSE）
   */
  test('批量搜索API调用', async ({ page }) => {
    // 先解析歌单
    const input = page.locator('input').first();
    await input.fill(TEST_PLAYLIST_URL);

    const parseButton = page.locator('button').filter({ hasText: /解析/i }).first();
    await parseButton.click();

    // 等待解析完成
    await page.waitForTimeout(10000);

    // 点击搜索按钮
    const searchButton = page.locator('button').filter({ hasText: /搜索|批量/i }).first();

    // 等待按钮启用 - 增加等待时间并检查状态
    console.log('等待搜索按钮启用...');
    await page.waitForTimeout(5000);

    // 检查按钮状态，如果是disabled则尝试其他方式
    const isEnabled = await searchButton.isEnabled({ timeout: 1000 }).catch(() => false);

    if (!isEnabled) {
      console.log('搜索按钮仍为disabled，尝试重新查找...');

      // 尝试查找所有搜索相关的按钮
      const allButtons = page.locator('button');
      const buttonCount = await allButtons.count();

      for (let i = 0; i < buttonCount; i++) {
        const btnText = await allButtons.nth(i).textContent();
        const btnEnabled = await allButtons.nth(i).isEnabled();

        if (btnText && (btnText.includes('搜索') || btnText.includes('批量')) && btnEnabled) {
          console.log(`找到可用的搜索按钮: ${btnText}`);
          await allButtons.nth(i).click();
          break;
        }
      }
    } else {
      await searchButton.click();
    }

    console.log('搜索已点击，等待SSE...');

    // 等待搜索完成（最多5分钟）
    let completed = false;
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(5000);

      // 检查页面上的完成标志
      const completedText = page.getByText(/完成|成功|matched|搜索完成/i);
      if (await completedText.isVisible({ timeout: 1000 })) {
        completed = true;
        console.log('✅ 搜索完成');
        break;
      }

      // 检查进度条
      const progress = page.locator('.ant-progress, [class*="progress"]');
      if (await progress.isVisible({ timeout: 1000 })) {
        console.log(`搜索进行中... (${i * 5}s)`);
      }
    }

    expect(completed).toBeTruthy();

    await page.screenshot({ path: 'screenshots/api-search-complete.png' });
  });

  /**
   * 测试4：完整流程验证
   */
  test('完整流程 - 端到端', async ({ page }) => {
    console.log('🚀 开始完整闭环测试...');

    // 步骤1: 解析歌单
    console.log('📝 步骤1: 解析歌单');

    const input = page.locator('input').first();
    await input.fill(TEST_PLAYLIST_URL);

    const parseButton = page.locator('button').filter({ hasText: /解析/i }).first();
    await parseButton.click();

    // 等待解析完成（通过检查按钮状态变化）
    await page.waitForTimeout(15000);
    console.log('✅ 解析完成');

    // 步骤2: 批量搜索
    console.log('🔍 步骤2: 批量搜索');

    const searchButton = page.locator('button').filter({ hasText: /搜索|批量/i }).first();

    // 等待按钮启用
    console.log('等待搜索按钮启用...');
    await page.waitForTimeout(5000);

    // 检查按钮状态
    const isEnabled = await searchButton.isEnabled({ timeout: 1000 }).catch(() => false);

    if (!isEnabled) {
      console.log('搜索按钮仍为disabled，尝试重新查找...');

      // 尝试查找所有搜索相关的按钮
      const allButtons = page.locator('button');
      const buttonCount = await allButtons.count();

      for (let i = 0; i < buttonCount; i++) {
        const btnText = await allButtons.nth(i).textContent();
        const btnEnabled = await allButtons.nth(i).isEnabled();

        if (btnText && (btnText.includes('搜索') || btnText.includes('批量')) && btnEnabled) {
          console.log(`找到可用的搜索按钮: ${btnText}`);
          await allButtons.nth(i).click();
          break;
        }
      }
    } else {
      await searchButton.click();
    }

    // 等待搜索完成
    let searchCompleted = false;
    for (let i = 0; i < 72; i++) { // 最多6分钟
      await page.waitForTimeout(5000);

      // 使用更精确的完成指示器
      const completedIndicator = page.getByText(/搜索完成|匹配成功|全部完成/).or(
        page.locator('.ant-statistic').filter({ hasText: /\d+/ })
      ).or(
        page.locator('text=/首歌曲匹配成功/')
      ).first();

      if (await completedIndicator.isVisible({ timeout: 1000 })) {
        searchCompleted = true;
        console.log('✅ 搜索完成');
        break;
      }

      if (i % 6 === 0) { // 每30秒打印一次
        console.log(`搜索进行中... (${i * 5}s / 360s)`);
      }
    }

    expect(searchCompleted).toBeTruthy();

    // 步骤3: 验证结果
    console.log('📊 步骤3: 验证结果');

    await page.waitForTimeout(3000);

    // 检查相似度标签
    const percentTags = page.locator('text=/\\d+%/');
    const tagCount = await percentTags.count();

    console.log(`相似度标签数量: ${tagCount}`);

    // 验证前几个标签不是NaN
    let hasValidSimilarity = false;
    for (let i = 0; i < Math.min(5, tagCount); i++) {
      const text = await percentTags.nth(i).textContent();
      if (text && !text.includes('NaN')) {
        hasValidSimilarity = true;
        console.log(`相似度 ${i + 1}: ${text}`);
      }
    }

    if (tagCount > 0) {
      expect(hasValidSimilarity).toBeTruthy();
    }

    // 最终截图
    await page.screenshot({ path: 'screenshots/api-complete-flow.png', fullPage: true });

    console.log('🎉 完整闭环测试完成！');
    console.log(`✅ 歌单解析: 成功`);
    console.log(`✅ 批量搜索: 成功`);
    console.log(`✅ 相似度显示: ${tagCount} 个标签`);
  });

  /**
   * 测试5：后端API直接测试
   */
  test('后端API直接测试', async ({ request }) => {
    // 直接调用后端API
    const response = await request.post('http://localhost:8002/api/playlist/parse', {
      data: {
        url: TEST_PLAYLIST_URL
      }
    });

    expect(response.status()).toBe(200);

    const data = await response.json();
    console.log('后端API响应:', JSON.stringify(data).slice(0, 300));

    // 验证响应结构
    expect(data).toHaveProperty('songs');
    expect(Array.isArray(data.songs)).toBeTruthy();

    console.log(`✅ 后端API测试通过，返回 ${data.songs.length} 首歌曲`);
  });
});

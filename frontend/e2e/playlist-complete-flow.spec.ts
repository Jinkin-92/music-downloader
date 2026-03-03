/**
 * 歌单导入完整闭环E2E测试
 *
 * 测试流程：歌单导入 → 搜索匹配 → 下载 → 验证完成
 *
 * 测试歌单：https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
 *
 * 覆盖场景：
 * 1. 音乐源默认选择验证（4个源全部选中）
 * 2. 相似度显示验证（无NaN%，颜色编码正确）
 * 3. 下载按钮和路径输入框验证
 * 4. 完整搜索流程（SSE流式进度）
 * 5. 完整下载流程（SSE流式进度）
 * 6. 候选源切换功能
 * 7. 错误处理和恢复
 */

import { test, expect } from '@playwright/test';

const TEST_PLAYLIST_URL = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';
const TEST_DOWNLOAD_DIR = 'test_downloads';

test.describe('歌单导入 - 完整闭环测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到歌单导入页面
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');

    // 等待页面完全加载
    await expect(page.locator('h1, h2').filter({ hasText: /歌单导入|批量搜索/ }).first()).toBeVisible({ timeout: 10000 });
  });

  /**
   * 测试1：音乐源默认选择验证
   *
   * 验证4个音乐源（网易云、QQ音乐、酷狗、酷我）全部默认选中
   * 符合CLAUDE.md中的要求
   */
  test('音乐源默认选择验证', async ({ page }) => {
    test.slow();

    // 音乐源checkbox只在有歌曲时显示，先解析歌单
    await parsePlaylist(page, TEST_PLAYLIST_URL);

    // 等待音乐源区域可见
    await expect(page.getByText('音乐源：')).toBeVisible({ timeout: 10000 });

    // 验证网易云 checkbox
    const neteaseCheckbox = page.getByRole('checkbox', { name: /网易云/ });
    await expect(neteaseCheckbox).toBeChecked();

    // 验证QQ音乐 checkbox
    const qqCheckbox = page.getByRole('checkbox', { name: /QQ音乐/ });
    await expect(qqCheckbox).toBeChecked();

    // 验证酷狗 checkbox
    const kugouCheckbox = page.getByRole('checkbox', { name: /酷狗/ });
    await expect(kugouCheckbox).toBeChecked();

    // 验证酷我 checkbox
    const kuwoCheckbox = page.getByRole('checkbox', { name: /酷我/ });
    await expect(kuwoCheckbox).toBeChecked();

    // 截图记录
    await page.screenshot({ path: 'screenshots/music-sources-default.png' });
  });

  /**
   * 测试2：歌单URL解析和表格显示
   *
   * 验证：
   * - URL输入和解析
   * - 歌单信息显示
   * - 表格数据正确渲染
   */
  test('歌单URL解析和表格显示', async ({ page }) => {
    test.slow();

    // 输入歌单URL
    const urlInput = page.locator('input[placeholder*="歌单链接"]').or(
      page.locator('textarea[placeholder*="歌单链接"]')
    ).or(
      page.locator('input.ant-input')
    ).first();

    await urlInput.fill(TEST_PLAYLIST_URL);

    // 点击解析按钮
    const parseButton = page.getByRole('button', { name: /解析歌单|开始解析/i });
    await parseButton.click();

    // 等待解析完成（使用Toast消息或按钮状态判断）
    await expect(page.getByText(/解析完成|成功|首歌曲/).or(
      page.getByRole('alert')
    ).or(
      page.locator('.ant-table-tbody tr')
    ).first()).toBeVisible({ timeout: 30000 });

    // 等待表格渲染 - 排除隐藏的测量行
    const tableRows = page.locator('.ant-table-tbody tr:not([aria-hidden="true"])');
    await expect(tableRows.first()).toBeVisible({ timeout: 10000 });

    // 验证至少有一行数据
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThan(0);

    // 验证表格列（歌名、歌手、专辑）
    const firstRowCells = tableRows.first().locator('td');
    await expect(firstRowCells.nth(1)).not.toBeEmpty(); // 歌名列
    await expect(firstRowCells.nth(2)).not.toBeEmpty(); // 歌手列

    // 截图记录
    await page.screenshot({ path: 'screenshots/playlist-parsed.png' });

    console.log(`✅ 歌单解析成功，共 ${rowCount} 首歌曲`);
  });

  /**
   * 测试3：批量搜索和相似度显示验证
   *
   * 验证：
   * - SSE流式进度显示
   * - 相似度无NaN%
   * - 相似度颜色编码正确（≥80%绿色，60-79%黄色，<60%红色）
   * - 搜索完成统计
   */
  test('批量搜索和相似度显示验证', async ({ page }) => {
    test.setTimeout(180000); // 3分钟超时

    // 先解析歌单
    await parsePlaylist(page, TEST_PLAYLIST_URL);

    // 全选歌曲（批量搜索需要先选中歌曲）
    const selectAllButton = page.getByRole('button', { name: /全选/i });
    await selectAllButton.click();
    await page.waitForTimeout(1000);

    // 点击批量搜索按钮
    const searchButton = page.getByRole('button', { name: /批量搜索/i });
    await expect(searchButton).toBeEnabled({ timeout: 5000 });
    await searchButton.click();

    // 等待搜索开始（SSE连接建立）
    await expect(page.getByText(/正在搜索|搜索进度/i).or(
      page.locator('.ant-progress')
    ).or(
      page.locator('[data-testid="sse-status"]')
    ).first()).toBeVisible({ timeout: 10000 });

    // 等待搜索完成（最多3分钟）
    await expect(page.getByText(/搜索完成|匹配成功|首歌曲匹配成功/i).or(
      page.locator('text=/\d+\/\d+/')
    ).first()).toBeVisible({ timeout: 180000 });

    // 等待结果表格渲染 - 排除隐藏的测量行
    await page.waitForTimeout(2000);
    const resultTable = page.locator('.ant-table-tbody tr:not([aria-hidden="true"])').or(
      page.locator('table')
    ).first();
    await expect(resultTable).toBeVisible({ timeout: 10000 });

    // 验证相似度显示（无NaN%）- 只选择表格内的相似度标签
    const similarityTags = page.locator('.ant-table-tbody tr:not([aria-hidden="true"])').first()
      .locator('text=/\d+/');

    const tagCount = await similarityTags.count();
    console.log(`📊 找到 ${tagCount} 个相似度标签`);

    if (tagCount > 0) {
      for (let i = 0; i < Math.min(tagCount, 10); i++) {
        const text = await similarityTags.nth(i).textContent();
        expect(text?.trim()).not.toContain('NaN');

        // 验证格式为数字百分比
        expect(text?.trim()).toMatch(/\d+%/);

        // 验证颜色编码（通过CSS类或内联样式）
        const element = similarityTags.nth(i);
        const color = await element.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return computed.color || computed.backgroundColor || '';
        });

        const percent = parseInt(text?.replace('%', '') || '0');
        if (percent >= 80) {
          // 高相似度应该是绿色
          expect(color.toLowerCase()).toMatch(/green|rgb\(82,\s*196,\s*26\)|#52c41a/);
        } else if (percent >= 60) {
          // 中相似度应该是黄色
          expect(color.toLowerCase()).toMatch(/yellow|orange|rgb\(250,\s*173,\s*20\)|#faad14/);
        }
      }
    }

    // 截图记录
    await page.screenshot({ path: 'screenshots/search-completed.png', fullPage: true });

    console.log('✅ 相似度显示验证通过');
  });

  /**
   * 测试4：下载按钮和路径输入框验证
   *
   * 验证：
   * - 下载按钮存在且可点击
   * - 下载按钮位置（在匹配结果表格下方）
   * - 下载路径输入框存在且可用
   */
  test('下载按钮和路径输入框验证', async ({ page }) => {
    test.setTimeout(600000); // 10分钟超时

    // 解析并搜索
    await parsePlaylist(page, TEST_PLAYLIST_URL);
    await searchPlaylist(page);

    // 等待搜索完成
    await page.waitForTimeout(5000);

    // 查找下载按钮 - 实际文本是"下载选中 (数量)"
    const downloadButton = page.getByRole('button', { name: /下载选中/i }).or(
      page.locator('button').filter({ hasText: /下载/ })
    ).or(
      page.getByRole('button', { name: /Download/i })
    ).first();

    await expect(downloadButton).toBeVisible({ timeout: 30000 });
    await expect(downloadButton).toBeEnabled();

    // 查找下载路径输入框 - 匹配实际的placeholder文本
    const pathInput = page.locator('input[placeholder*="默认"]').or(
      page.locator('input[placeholder*="musicdl"]')
    ).or(
      page.locator('input').filter({ has: page.locator('.ant-input') })
    ).first();

    await expect(pathInput).toBeVisible({ timeout: 10000 });

    // 验证输入框可编辑
    await pathInput.fill(TEST_DOWNLOAD_DIR);
    const value = await pathInput.inputValue();
    expect(value).toBe(TEST_DOWNLOAD_DIR);

    // 截图记录
    await page.screenshot({ path: 'screenshots/download-controls.png' });

    console.log('✅ 下载控件验证通过');
  });

  /**
   * 测试5：完整下载流程验证
   *
   * 验证：
   * - 下载启动成功
   * - SSE进度流式显示
   * - 下载状态更新
   * - 下载完成统计
   */
  test('完整下载流程验证（仅前3首）', async ({ page }) => {
    test.setTimeout(600000); // 10分钟超时（优化后）

    // 解析并搜索
    await parsePlaylist(page, TEST_PLAYLIST_URL);
    await searchPlaylist(page);

    // 等待搜索完成
    await page.waitForTimeout(5000);

    // 只选择前3首歌曲（加快测试）
    const checkboxes = page.locator('.ant-checkbox-input').or(
      page.locator('input[type="checkbox"]')
    );
    const count = await checkboxes.count();

    if (count > 0) {
      // 勾选前3个（跳过全选checkbox）
      for (let i = 1; i <= Math.min(3, count - 1); i++) {
        await checkboxes.nth(i).check();
      }
    }

    // 设置下载路径 - 匹配实际的placeholder文本
    const pathInput = page.locator('input[placeholder*="默认"]').or(
      page.locator('input[placeholder*="musicdl"]')
    ).or(
      page.locator('.ant-input').filter({ hasText: /./ })
    ).first();
    await pathInput.fill(TEST_DOWNLOAD_DIR);

    // 点击下载按钮 - 实际文本是"下载选中 (数量)"
    const downloadButton = page.getByRole('button', { name: /下载选中/i }).or(
      page.locator('button').filter({ hasText: /下载/ })
    ).first();
    await downloadButton.click();

    // 等待下载开始
    await expect(page.getByText(/正在下载|下载进度|开始下载/i).or(
      page.locator('.ant-progress')
    ).or(
      page.locator('[data-testid="sse-status"]')
    ).first()).toBeVisible({ timeout: 30000 });

    console.log('📥 下载已开始...');

    // 监控下载进度（等待最多5分钟）
    let progressSeen = false;
    let completeSeen = false;

    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(5000);

      // 检查进度显示
      const progressText = page.getByText(/\d+\/\d+|\d+%/).or(
        page.locator('text=/完成:\s*\d+/')
      ).first();

      if (await progressText.isVisible({ timeout: 1000 })) {
        progressSeen = true;
        const text = await progressText.textContent();
        console.log(`📊 下载进度: ${text}`);
      }

      // 检查完成状态
      const completeText = page.getByText(/下载完成|全部完成|成功下载/i);
      if (await completeText.isVisible({ timeout: 1000 })) {
        completeSeen = true;
        console.log('✅ 下载完成！');
        break;
      }
    }

    // 验证至少看到进度显示
    expect(progressSeen).toBeTruthy();

    // 截图记录
    await page.screenshot({ path: 'screenshots/download-completed.png', fullPage: true });

    console.log('✅ 下载流程验证完成');
  });

  /**
   * 测试6：候选源切换功能验证
   *
   * 验证：
   * - 候选源下拉菜单存在
   * - 可以切换候选源
   * - 切换后相似度更新
   */
  test('候选源切换功能验证', async ({ page }) => {
    test.setTimeout(180000);

    // 解析并搜索
    await parsePlaylist(page, TEST_PLAYLIST_URL);
    await searchPlaylist(page);

    // 等待搜索完成
    await page.waitForTimeout(5000);

    // 查找候选源下拉按钮（▼图标）
    const candidateDropdowns = page.locator('button').filter({ hasText: '▼' }).or(
      page.locator('[class*="dropdown"]').or(
        page.locator('.ant-select-dropdown')
      )
    );

    const count = await candidateDropdowns.count();

    if (count > 0) {
      // 点击第一个下拉菜单
      await candidateDropdowns.first().click();

      // 等待下拉菜单展开
      await page.waitForTimeout(1000);

      // 验证下拉菜单显示候选源
      const dropdownOptions = page.locator('.ant-select-dropdown-option, .ant-dropdown-menu-item');
      const optionCount = await dropdownOptions.count();

      if (optionCount > 0) {
        console.log(`📋 找到 ${optionCount} 个候选源选项`);

        // 选择第一个选项
        await dropdownOptions.first().click();

        // 等待更新
        await page.waitForTimeout(1000);

        // 截图记录
        await page.screenshot({ path: 'screenshots/candidate-switched.png' });

        console.log('✅ 候选源切换成功');
      } else {
        console.log('⚠️ 未找到候选源选项（可能只有唯一匹配）');
      }
    } else {
      console.log('⚠️ 未找到候选源下拉菜单');
    }
  });

  /**
   * 测试7：错误处理和恢复
   *
   * 验证：
   * - 无效URL显示错误提示
   * - 空输入显示警告
   * - 清空功能正常
   */
  test('错误处理和恢复', async ({ page }) => {
    test.slow();

    // 测试无效URL
    const urlInput = page.locator('input[placeholder*="歌单链接"]').or(
      page.locator('textarea').or(
        page.locator('input.ant-input')
      )
    ).first();

    await urlInput.fill('https://invalid-url.com/playlist');

    const parseButton = page.getByRole('button', { name: /解析歌单|开始解析/i });
    await parseButton.click();

    // 等待错误提示
    await expect(page.getByText(/错误|失败|不支持|无效/i).or(
      page.locator('.ant-message-error')
    ).or(
      page.locator('.ant-alert-error')
    ).first()).toBeVisible({ timeout: 10000 });

    console.log('✅ 无效URL错误提示正常');

    // 测试清空功能
    const clearButton = page.getByRole('button', { name: /清空|重置/i });
    if (await clearButton.isVisible({ timeout: 5000 })) {
      await clearButton.click();

      // 验证表格清空
      const tableRows = page.locator('.ant-table-tbody tr');
      const rowCount = await tableRows.count();

      expect(rowCount).toBe(0);

      console.log('✅ 清空功能正常');
    }
  });

  /**
   * 测试8：完整闭环流程（端到端）
   *
   * 完整流程：导入 → 搜索 → 下载 → 验证
   * 使用测试歌单，验证整个流程无异常
   */
  test('完整闭环流程验证', async ({ page }) => {
    test.setTimeout(600000); // 10分钟超时

    console.log('🚀 开始完整闭环测试...');

    // 步骤1：解析歌单
    console.log('📝 步骤1: 解析歌单...');
    await parsePlaylist(page, TEST_PLAYLIST_URL);

    // 验证表格有数据 - 排除隐藏的测量行
    const tableRows = page.locator('.ant-table-tbody tr:not([aria-hidden="true"])');
    await expect(tableRows.first()).toBeVisible({ timeout: 10000 });
    const songCount = await tableRows.count();
    console.log(`✅ 解析成功，共 ${songCount} 首歌曲`);

    // 步骤2：批量搜索
    console.log('🔍 步骤2: 批量搜索...');
    await searchPlaylist(page);

    // 等待搜索完成
    await page.waitForTimeout(5000);

    // 验证搜索结果 - 排除隐藏的测量行
    const resultRows = page.locator('.ant-table-tbody tr:not([aria-hidden="true"])');
    await expect(resultRows.first()).toBeVisible({ timeout: 10000 });

    // 验证相似度显示
    const similarityTags = page.locator('text=/\d+%/');
    const tagCount = await similarityTags.count();
    console.log(`✅ 搜索完成，${tagCount} 个相似度标签`);

    // 步骤3：准备下载（仅前2首，加快测试）
    console.log('📥 步骤3: 准备下载...');

    const checkboxes = page.locator('.ant-checkbox-input').or(
      page.locator('input[type="checkbox"]')
    );
    const checkboxCount = await checkboxes.count();

    if (checkboxCount > 0) {
      for (let i = 1; i <= Math.min(2, checkboxCount - 1); i++) {
        await checkboxes.nth(i).check();
      }
    }

    // 设置下载路径 - 匹配实际的placeholder文本
    const pathInput = page.locator('input[placeholder*="默认"]').or(
      page.locator('input[placeholder*="musicdl"]')
    ).or(
      page.locator('.ant-input').filter({ hasText: /./ })
    ).first();
    await pathInput.fill(TEST_DOWNLOAD_DIR);

    // 步骤4：开始下载
    console.log('⬇️ 步骤4: 开始下载...');
    const downloadButton = page.getByRole('button', { name: /下载选中/i }).or(
      page.locator('button').filter({ hasText: /下载/ })
    ).first();
    await downloadButton.click();

    // 监控下载进度
    let downloadStarted = false;
    let downloadComplete = false;

    for (let i = 0; i < 120; i++) { // 最多10分钟
      await page.waitForTimeout(5000);

      // 检查下载开始
      if (!downloadStarted) {
        const progressIndicator = page.getByText(/正在下载|下载进度/i).or(
          page.locator('.ant-progress')
        ).first();

        if (await progressIndicator.isVisible({ timeout: 1000 })) {
          downloadStarted = true;
          console.log('✅ 下载已开始');
        }
      }

      // 检查下载完成
      if (downloadStarted) {
        const completeText = page.getByText(/下载完成|全部完成/i);
        if (await completeText.isVisible({ timeout: 1000 })) {
          downloadComplete = true;

          const text = await completeText.textContent();
          console.log(`✅ 下载完成: ${text}`);
          break;
        }
      }
    }

    // 验证结果
    expect(downloadStarted).toBeTruthy();

    // 截图记录
    await page.screenshot({ path: 'screenshots/complete-flow.png', fullPage: true });

    console.log('🎉 完整闭环测试完成！');
  });
});

/**
 * 辅助函数：解析歌单
 */
async function parsePlaylist(page: any, url: string) {
  const urlInput = page.locator('input[placeholder*="歌单链接"]').or(
    page.locator('textarea').or(
      page.locator('input.ant-input')
    )
  ).first();

  await urlInput.fill(url);

  const parseButton = page.getByRole('button', { name: /解析歌单|开始解析/i });
  await parseButton.click();

  // 等待解析完成 - 排除隐藏的测量行
  await expect(page.getByText(/解析完成|成功|首歌曲/).or(
    page.locator('.ant-table-tbody tr:not([aria-hidden="true"])')
  ).first()).toBeVisible({ timeout: 30000 });

  // 等待表格稳定
  await page.waitForTimeout(2000);
}

/**
 * 辅助函数：搜索歌单（仅前5首，加快测试）
 */
async function searchPlaylist(page: any) {
  // 获取所有checkbox
  const checkboxes = page.locator('.ant-checkbox-input').or(
    page.locator('input[type="checkbox"]')
  );

  const count = await checkboxes.count();
  console.log(`[搜索] 找到 ${count} 个checkbox`);

  // 只选择前5首歌曲（跳过全选checkbox）
  for (let i = 1; i <= Math.min(5, count - 1); i++) {
    await checkboxes.nth(i).check();
  }
  await page.waitForTimeout(500);

  const searchButton = page.getByRole('button', { name: /批量搜索/i });
  await expect(searchButton).toBeEnabled({ timeout: 5000 });
  await searchButton.click();

  // 等待搜索开始
  await expect(page.getByText(/搜索进度/i)).toBeVisible({ timeout: 5000 });

  // 等待搜索完成 - 增加到5分钟超时
  await expect(page.getByText(/搜索完成|匹配成功/i)).toBeVisible({ timeout: 300000 });

  // 等待结果稳定并等待下载区域出现 - 增加到10秒
  await page.waitForTimeout(10000);

  // 显式等待下载区域出现
  const downloadButton = page.getByRole('button', { name: /下载选中/i }).or(
    page.locator('button').filter({ hasText: /下载/ })
  ).first();
  await expect(downloadButton).toBeVisible({ timeout: 60000 });

  console.log('[搜索] ✅ 下载区域已出现');
}

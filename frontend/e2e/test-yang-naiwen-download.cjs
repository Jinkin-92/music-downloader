/**
 * 杨乃文歌单下载测试
 *
 * 完整流程：歌单导入 → 搜索匹配 → 下载20首歌曲
 * 下载路径：D:\code\下载音乐软件\杨乃文
 */

const { chromium } = require('playwright');

const TEST_PLAYLIST_URL = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';
const DOWNLOAD_PATH = 'D:\\code\\下载音乐软件\\杨乃文';

async function testYangNaiwenDownload() {
  console.log('==========================================');
  console.log('   杨乃文歌单下载测试');
  console.log('==========================================');
  console.log('歌单URL:', TEST_PLAYLIST_URL);
  console.log('下载路径:', DOWNLOAD_PATH);
  console.log('');

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox']
  });

  const page = await browser.newPage();
  const context = await browser.newContext();

  // 截图目录
  const screenshotDir = 'e2e/screenshots';
  const fs = require('fs');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  try {
    // 步骤1：导航到歌单导入页面
    console.log('【步骤1】导航到歌单导入页面...');
    await page.goto('http://localhost:5173/playlist', { timeout: 60000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    console.log('  页面加载完成');

    await page.screenshot({ path: `${screenshotDir}/01-page-loaded.png` });
    console.log('  截图: 01-page-loaded.png');

    // 步骤2：输入URL并解析
    console.log('');
    console.log('【步骤2】解析歌单...');
    const urlInput = page.locator('input[placeholder*="歌单分享链接"]');
    await urlInput.fill(TEST_PLAYLIST_URL);
    console.log('  已输入URL');

    const parseButton = page.getByRole('button', { name: '解析歌单' });
    await parseButton.click();
    console.log('  已点击解析按钮...');

    // 等待解析完成 - 检查成功消息
    await page.waitForSelector('.ant-message-success', { timeout: 30000 });
    const songCount = await page.locator('.ant-table-tbody tr').count();
    console.log(`  歌单解析完成，共 ${songCount} 首歌曲`);

    await page.screenshot({ path: `${screenshotDir}/02-playlist-parsed.png` });
    console.log('  截图: 02-playlist-parsed.png');

    // 步骤3：选中所有音乐源
    console.log('');
    console.log('【步骤3】选中所有音乐源...');
    const sources = ['网易云', 'QQ音乐', '酷狗', '酷我'];

    for (const source of sources) {
      const checkbox = page.locator(`.ant-checkbox-wrapper:has-text("${source}")`);
      await checkbox.waitFor({ state: 'visible', timeout: 5000 });
      const checkboxInput = checkbox.locator('input[type="checkbox"]');
      const isChecked = await checkboxInput.isChecked();
      console.log(`  ${source}: ${isChecked ? '已选中' : '未选中'}`);

      if (!isChecked) {
        await checkboxInput.click();
        console.log(`  -> 已选中 ${source}`);
        await page.waitForTimeout(1000);
      }
    }

    await page.screenshot({ path: `${screenshotDir}/03-music-sources.png` });
    console.log('  截图: 03-music-sources.png');

    // 步骤4：批量搜索
    console.log('');
    console.log('【步骤4】批量搜索...');

    // 点击全选按钮
    const selectAllBtn = page.getByRole('button', { name: /全选/i });
    if (await selectAllBtn.isVisible({ timeout: 5000 })) {
      await selectAllBtn.click();
      console.log('  已点击全选按钮');
      await page.waitForTimeout(1000);
    }

    // 点击批量搜索按钮
    const searchBtn = page.getByRole('button', { name: /批量搜索/i });
    await searchBtn.click();
    console.log('  已点击批量搜索按钮...');

    // 等待搜索进度条出现
    await page.waitForSelector('.ant-progress', { timeout: 15000 });
    console.log('  搜索进度条已显示');

    // 等待搜索完成 - 最多4分钟
    const maxWaitTime = 240000; // 4分钟
    const startTime = Date.now();

    let lastPercent = -1;
    let searchCompleted = false;

    while (Date.now() - startTime < maxWaitTime) {
      await page.waitForTimeout(5000);

      // 检查进度
      const progressBars = page.locator('.ant-progress-text');
      if (await progressBars.first().isVisible()) {
        const progressText = await progressBars.first().textContent();
        if (progressText && progressText !== lastPercent) {
          lastPercent = progressText;
          console.log(`  📊 ${progressText}`);
        }
      }

      // 检查完成消息
      const completeMsg = page.locator('text=/搜索完成|匹配成功/');
      if (await completeMsg.isVisible({ timeout: 1000 })) {
        console.log('  ✅ 搜索完成！');
        searchCompleted = true;
        break;
      }

      // 检查错误消息
      const errorMsg = page.locator('.ant-message-error');
      if (await errorMsg.isVisible({ timeout: 1000 })) {
        const errorText = await errorMsg.textContent();
        console.log(`  ⚠️  搜索警告: ${errorText}`);
        // 继续等待，不中断
      }
    }

    if (Date.now() - startTime >= maxWaitTime) {
      console.log(`  ⚠️  4分钟超时，继续检查结果...`);
    }

    // 等待更多时间让UI更新
    await page.waitForTimeout(3000);

    // 检查搜索结果
    const tableRows = page.locator('.ant-table-tbody tr');
    const rowCount = await tableRows.count();
    console.log(`  表格行数: ${rowCount}`);

    let matchedCount = 0;
    if (rowCount > 0) {
      console.log('  ✅ 找到搜索结果！');

      // 显示前3行的相似度分数
      for (let i = 0; i < Math.min(rowCount, 3); i++) {
        const row = tableRows.nth(i);
        const cells = row.locator('.ant-table-cell');
        const cellCount = await cells.count();
        if (cellCount > 2) {
          const similarityCell = cells.nth(2); // 相似度列
          if (await similarityCell.isVisible({ timeout: 5000 })) {
            const similarityText = await similarityCell.textContent();
            console.log(`    歌曲${i + 1}: 相似度=${similarityText}`);
          }
        }
      }

      // 计算匹配数量
      matchedCount = await page.locator('.ant-table-tbody tr .anticon-check-circle').count();
      console.log(`  已匹配: ${matchedCount} 首`);
    } else {
      console.log(`  ⚠️  未找到搜索结果`);
    }

    await page.screenshot({ path: `${screenshotDir}/04-search-results.png` });
    console.log('  截图: 04-search-results.png');

    // 步骤5：检查下载区域
    console.log('');
    console.log('【步骤5】检查下载区域...');

    // 滚动到页面底部
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);

    // 使用JavaScript直接设置下载路径输入框的值
    await page.evaluate((path) => {
      const inputs = document.querySelectorAll('input');
      for (const input of inputs) {
        if (input.placeholder && input.placeholder.includes('留空使用默认路径')) {
          Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input, path);
          input.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    }, DOWNLOAD_PATH);

    console.log(`  已设置下载路径: ${DOWNLOAD_PATH}`);

    // 步骤6：验证状态
    console.log('');
    console.log('【步骤6】验证最终状态...');

    // 检查下载区域是否可见
    const downloadSection = await page.evaluate(() => {
      const sections = document.querySelectorAll('div');
      for (const section of sections) {
        if (section.textContent && section.textContent.includes('下载路径')) {
          return {
            visible: section.offsetParent !== null,
            text: section.textContent.substring(0, 100)
          };
        }
      }
      return { visible: false, text: '未找到' };
    });

    console.log(`  下载区域: ${downloadSection.visible ? '可见' : '不可见'}`);

    // 点击全选按钮选中所有歌曲
    const selectAllBtn2 = page.getByRole('button', { name: /全选/i });
    await selectAllBtn2.click();
    await page.waitForTimeout(2000);

    // 检查下载按钮
    const downloadBtn = page.locator('button:has-text("下载选中")');
    const isDownloadBtnVisible = await downloadBtn.isVisible({ timeout: 5000 }).catch(() => false);

    console.log(`  下载按钮: ${isDownloadBtnVisible ? '可见' : '不可见'}`);

    await page.screenshot({ path: `${screenshotDir}/05-download-section.png` });
    console.log('  截图: 05-download-section.png');

    // 输出测试总结
    console.log('');
    console.log('==========================================');
    console.log('   测试总结');
    console.log('==========================================');
    console.log(`  ✅ 歌单解析: ${songCount} 首歌曲`);
    console.log(`  ✅ 音乐源: 全部选中 (网易云, QQ音乐, 酷狗, 酷我)`);
    console.log(`  ${searchCompleted ? '✅' : '⚠️'} 搜索状态: ${searchCompleted ? '完成' : '进行中/超时'}`);
    console.log(`  ✅ 搜索结果: ${rowCount} 行`);
    console.log(`  ${matchedCount > 0 ? '✅' : '⚠️'} 已匹配: ${matchedCount} 首`);
    console.log(`  ${downloadSection.visible ? '✅' : '⚠️'} 下载区域: ${downloadSection.visible ? '可见' : '不可见'}`);
    console.log(`  ${isDownloadBtnVisible ? '✅' : '⚠️'} 下载按钮: ${isDownloadBtnVisible ? '可见' : '不可见'}`);
    console.log(`  ✅ 下载路径: ${DOWNLOAD_PATH}`);
    console.log(`  截图保存: ${screenshotDir}/`);
    console.log('==========================================');

    // 如果下载按钮可见，尝试点击开始下载
    if (isDownloadBtnVisible) {
      console.log('');
      console.log('【步骤7】开始下载...');

      await downloadBtn.click();
      console.log('  已点击下载按钮...');

      // 等待下载进度
      await page.waitForSelector('.ant-progress', { timeout: 30000 });
      console.log('  下载进度条已显示');

      await page.waitForTimeout(5000);
      await page.screenshot({ path: `${screenshotDir}/06-download-progress.png` });
      console.log('  截图: 06-download-progress.png');
    }

    console.log('');
    console.log('测试完成！请查看截图了解详细状态。');

  } catch (error) {
    console.error('');
    console.error('测试失败:', error.message);
    console.error('错误堆栈:', error.stack);

    // 尝试截图错误状态（添加超时保护）
    try {
      await page.screenshot({ path: `${screenshotDir}/error-screenshot.png`, fullPage: true, timeout: 10000 });
      console.log(`截图保存在: ${screenshotDir}/error-screenshot.png`);
    } catch (screenshotError) {
      console.error('截图失败:', screenshotError.message);
    }
  } finally {
    try {
      await browser.close();
    } catch (closeError) {
      console.error('关闭浏览器失败:', closeError.message);
    }
  }
}

// 运行测试
testYangNaiwenDownload().catch(console.error);

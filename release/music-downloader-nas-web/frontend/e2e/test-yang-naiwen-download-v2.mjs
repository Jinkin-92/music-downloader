/**
 * 杨乃文歌单下载测试 - 增强版
 *
 * 完整流程：歌单导入 → 搜索匹配 → 下载20首歌曲
 * 下载路径：D:\code\下载音乐软件\杨乃文
 */

import { chromium } from 'playwright';
import fs from 'fs';

const TEST_PLAYLIST_URL = 'https://music.163.com/m/playlist?id=6922195323&creatorId=610906171';
const DOWNLOAD_PATH = 'D:\\code\\下载音乐软件\\杨乃文';

async function testYangNaiwenDownload() {
  console.log('==========================================');
  console.log('   杨乃文歌单下载测试 - 增强版');
  console.log('==========================================');
  console.log('歌单URL:', TEST_PLAYLIST_URL);
  console.log('下载路径:', DOWNLOAD_PATH);
  console.log('');

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox'],
    slowMo: 1000 // 4秒超时便于调试
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // 截图目录
  const screenshotDir = 'e2e/screenshots';
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  // 全局错误处理
  let hasError = false;
  const screenshotList = [];

  async function takeScreenshot(name) {
    const path = `${screenshotDir}/${name}.png`;
    await page.screenshot({ path, fullPage: true });
    screenshotList.push(name);
    console.log(`  📸 截图: ${name}`);
  }

  try {
    // 步骤1：导航到歌单导入页面
    console.log('【步骤1】导航到歌单导入页面...');
    await page.goto('http://localhost:5173/playlist', { timeout: 60000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    await takeScreenshot('01-page-loaded');
    console.log('  页面加载完成');

    // 步骤2：解析歌单
    console.log('');
    console.log('【步骤2】解析歌单...');

    // 查找URL输入框 - 多种方式尝试
    const urlInputSelectors = [
      'input[placeholder*="歌单链接"]',
      'input[placeholder*="粘贴"]',
      'textarea[placeholder*="歌单"]',
      'input.ant-input[size="large"]',
      '.ant-input'
    ];

    let urlInput = null;
    for (const selector of urlInputSelectors) {
      try {
        urlInput = page.locator(selector).first();
        if (await urlInput.count() > 0) {
          console.log(`  找到输入框: ${selector}`);
          break;
        }
      } catch {}
    }

    if (!urlInput) {
      console.log('  未找到URL输入框');
      console.log('  可用选择器：');
      const selectText = await page.locator('body').textContent();
      console.log('  页面文本:', selectText.substring(0, 200));
      await takeScreenshot('error-no-url-input');
      throw new Error('未找到URL输入框');
    }

    await urlInput.fill(TEST_PLAYLIST_URL);
    console.log('  已输入URL');
    await takeScreenshot('02-url-filled');

    // 点击解析按钮
    const parseButtonSelectors = [
      'button:has-text("解析歌单")',
      '.ant-btn-primary',
      'button:has-text("开始解析")',
      'button[type="button"]'
    ];

    let parseButton = null;
    for (const selector of parseButtonSelectors) {
      try {
        parseButton = page.locator(selector).first();
        if (await parseButton.count() > 0) {
          console.log(`  找到解析按钮: ${selector}`);
          break;
        }
      } catch {}
    }

    if (!parseButton) {
      console.log('  未找到解析按钮');
      await takeScreenshot('error-no-parse-button');
      throw new Error('未找到解析按钮');
    }

    await parseButton.click();
    console.log('  已点击解析按钮...');

    // 等待解析完成 - 多种检查方式
    let parseSuccess = false;
    const maxWaitTime = 30000; // 30秒

    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(1000);

      // 检查方式1：表格行
      const tableRows = page.locator('.ant-table-tbody tr');
      const rowCount = await tableRows.count();
      if (rowCount > 0) {
        parseSuccess = true;
        console.log(`  ✅ 表格出现 (${rowCount} 行)`);
        break;
      }

      // 检查方式2：成功消息
      if (!parseSuccess) {
        const successMsg = page.locator('.ant-message-success, .ant-message-info, .ant-message-warning').first();
        if (await successMsg.isVisible({ timeout: 5000 })) {
          const text = await successMsg.textContent();
          if (text.includes('解析完成') || text.includes('首歌曲')) {
            parseSuccess = true;
            console.log(`  ✅ 成功消息: ${text}`);
            break;
          }
        }
      }

      // 检查方式3：进度条（如果有）
      const progressBar = page.locator('.ant-progress');
      if (await progressBar.isVisible({ timeout: 5000 })) {
        parseSuccess = true;
        console.log(`  ✅ 进度条可见`);
        break;
      }
    }

      if (i >= 30) {
        console.log(`  ⚠️ 等待${i}秒后仍未完成...`);
      }
    }

    if (!parseSuccess) {
      console.log('  解析失败或超时');
      await takeScreenshot('error-parse-timeout');
      throw new Error(`解析超时（${maxWaitTime/1000}秒）`);
    }

    console.log('  解析完成');
    await takeScreenshot('03-playlist-parsed');
    console.log(`  歌曲数: ${await tableRows.count()}`);

    // 检查是否有歌曲数据
    const hasSongData = await tableRows.count() > 0;
    if (!hasSongData) {
      console.log('  未解析到歌曲数据');
      await takeScreenshot('error-no-song-data');
      throw new Error('未解析到歌曲数据');
    }

    // 步骤3：选中音乐源
    console.log('');
    console.log('【步骤3】选中音乐源...');

    // 滚动到顶部
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(1000);

    const sources = ['网易云', 'QQ音乐', '酷狗', '酷我'];
    let selectedCount = 0;

    for (const source of sources) {
      // 尝试查找checkbox的多种方式
      const checkbox = page.locator(`label:has-text("${source}")`).or(
        page.locator(`.ant-checkbox-wrapper:has-text("${source}")`)
      ).or(
        page.locator(`input[type="checkbox"][value*="${source}"]`)
      ).first();

      if (await checkbox.count() > 0) {
        const isChecked = await checkbox.isChecked();
        console.log(`  ${source}: ${isChecked ? '已选中' : '未选中'}`);

        if (!isChecked) {
          await checkbox.check();
          selectedCount++;
          console.log(`  → 已选中 ${source}`);
        }

        await page.waitForTimeout(500);
      }
    }

    console.log(`  共选中 ${selectedCount} 个音乐源`);
    await takeScreenshot('04-music-sources');
    console.log('  截图: 04-music-sources.png');

    // 步骤4：批量搜索
    console.log('');
    console.log('【步骤4】批量搜索...');

    // 查找全选按钮
    const selectAllBtn = page.getByRole('button', { name: /全选/i }).first();
    if (await selectAllBtn.isVisible({ timeout: 5000 })) {
      await selectAllBtn.click();
      console.log('  已点击全选按钮');
      await page.waitForTimeout(1000);
    } else {
      console.log('  全选按钮不可见，尝试手动选择');
    }

    // 查找批量搜索按钮
    const searchButton = page.getByRole('button', { name: /批量搜索/i }).first();
    if (await searchButton.isVisible({ timeout: 5000 })) {
      console.log('  找到批量搜索按钮');
    } else {
      console.log('  未找到批量搜索按钮');
      await takeScreenshot('error-no-search-button');
      throw new Error('未找到批量搜索按钮');
    }

    await searchButton.click();
    console.log('  已点击批量搜索按钮...');

    // 等待搜索进度条出现
    await page.waitForSelector('.ant-progress', { timeout: 15000 });
    console.log('  搜索进度条已显示');

    // 等待搜索完成 - 最长5分钟
    console.log('  等待搜索完成（最多5分钟）...');

    const searchStartTime = Date.now();
    let searchCompleted = false;
    let lastProgress = '';

    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(5000);

      // 检查进度
      const progressBar = page.locator('.ant-progress-text, .ant-progress-success').first();
      if (await progressBar.isVisible({ timeout: 1000 })) {
        const progressText = await progressBar.textContent().catch(() => '');
        if (progressText && progressText !== lastProgress) {
          lastProgress = progressText;
          console.log(`  📊 ${progressText}`);
        }
      }

      // 检查完成消息
      const completeMsg = page.locator('text=/搜索完成|匹配成功|首歌曲匹配成功/i');
      if (await completeMsg.isVisible({ timeout: 1000 })) {
        searchCompleted = true;
        console.log('  ✅ 搜索完成！');
        break;
      }

      // 检查错误消息
      const errorMsg = page.locator('.ant-message-error, .ant-alert-error').first();
      if (await errorMsg.isVisible({ timeout: 1000 })) {
        const errorText = await errorMsg.textContent();
        console.log(`  ⚠️ 错误: ${errorText}`);
      }

      // 如果超时
      if (i === 59) {
        console.log('  ⚠️ 等待5分钟超时，强制继续...');
        // 强制点击搜索按钮再试一次
        await searchButton.click();
      }
    }

    const searchDuration = Date.now() - searchStartTime;
    console.log(`  搜索耗时: ${Math.round(searchDuration / 1000)}秒`);

    if (!searchCompleted) {
      console.log('  搜索未完成');
      await takeScreenshot('error-search-timeout');
      throw new Error(`搜索超时（300秒）未完成`);
    }

    console.log('  搜索完成');
    await takeScreenshot('05-search-completed');
    console.log(`  耗时: ${Math.round(searchDuration / 1000)}秒`);

    // 步骤5：设置下载路径
    console.log('');
    console.log('【步骤5】设置下载路径...');

    // 滚动到页面底部
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);

    // 查找下载路径输入框
    const pathInputSelectors = [
      'input[placeholder*="下载路径"]',
      'input[placeholder*="路径"]',
      'input[placeholder*="留空"]',
      '.ant-input'
    ];

    let pathInput = null;
    for (const selector of pathInputSelectors) {
      try {
        pathInput = page.locator(selector).first();
        if (await pathInput.count() > 0) {
          console.log(`  找到路径输入框: ${selector}`);
          break;
        }
      } catch {}
    }

    if (!pathInput) {
      console.log('  未找到路径输入框');
      await takeScreenshot('error-no-path-input');
      throw new Error('未找到下载路径输入框');
    }

    await pathInput.fill(DOWNLOAD_PATH);
    console.log(`  已设置下载路径: ${DOWNLOAD_PATH}`);
    await page.waitForTimeout(1000);
    await takeScreenshot('06-download-path');
    console.log('  截图: 06-download-path.png');

    // 步骤6：开始下载
    console.log('');
    console.log('【步骤6】开始下载...');

    // 查找下载按钮
    const downloadButtonSelectors = [
      'button:has-text("下载选中")',
      'button:has-text("开始下载")',
      '.ant-btn-primary',
      'button[type="button"]'
    ];

    let downloadButton = null;
    for (const selector of downloadButtonSelectors) {
      try {
        downloadButton = page.locator(selector).first();
        if (await downloadButton.count() > 0) {
          console.log(`  找到下载按钮: ${selector}`);
          break;
        }
      } catch {}
    }

    if (!downloadButton) {
      console.log('  未找到下载按钮');
      await takeScreenshot('error-no-download-button');
      throw new Error('未找到下载按钮');
    }

    await downloadButton.click();
    console.log('  已点击下载按钮...');

    // 等待下载进度条出现
    await page.waitForSelector('.ant-progress', { timeout: 15000 });
    console.log(' 下载进度条已显示');

    // 监控下载进度
    console.log('');
    console.log('【监控下载进度】...');

    let downloadCompleted = false;
    let downloadProgress = '';
    const maxWaitTime = 600000; // 10分钟

    for (let i = 0; i < maxWaitTime / 5000; i++) {
      await page.waitForTimeout(5000);

      // 检查进度
      const progressBars = page.locator('.ant-progress-text');
      if (await progressBars.first().isVisible({ timeout: 1000 })) {
        const progressText = await progressBars.first().textContent().catch(() => '');
        if (progressText && progressText !== downloadProgress) {
          downloadProgress = progressText;
          console.log(`  📊 ${progressText}`);
        }
      }

      // 检查完成
      const completeMsg = page.locator('text=/下载完成|成功:.*首|completed.*success/i');
      if (await completeMsg.isVisible({ timeout: 1000 })) {
        const completeText = await completeMsg.textContent();
        if (completeText.includes('下载完成')) {
          downloadCompleted = true;
          console.log('  ✅ ${completeText}`);
          break;
        }
      }

      // 检查错误
      const errorMsg = page.locator('.ant-message-error').first();
      if (await errorMsg.isVisible({ timeout: 1000 })) {
        const errorText = await errorMsg.textContent();
        console.log(`  ⚠️ 错误: ${errorText}`);
        hasError = true;
      }

      // 检查是否超时
      if (i >= maxWaitTime / 5000) {
        console.log('  ⚠️ 10分钟超时，强制继续...');
      }
    }

      if (downloadCompleted) {
        console.log('  下载完成！');
        break;
      }
    }

    await takeScreenshot('07-download-complete');
    console.log('  截图: 07-download-complete.png');

    // 步骤7：验证结果
    console.log('');
    console.log('【步骤7】验证结果...');

    // 等待一下确保下载完成
    await page.waitForTimeout(5000);

    // 检查是否有成功消息
    const finalMessages = page.locator('.ant-message-success, .ant-message-info').allTextContents();
    const hasCompleteMsg = finalMessages.some(msg => msg.includes('下载完成') || msg.includes('成功'));

    console.log(`  成功消息: ${finalMessages.length > 0 ? '有' : '无'}`);

    // 检查下载文件夹
    console.log('  检查下载文件夹是否存在歌曲文件...');
    const downloadDirExists = fs.existsSync(DOWNLOAD_PATH.replace(/\\/g, '\\'));

    // 统计可能下载的文件数
    let downloadedCount = 0;
    if (downloadDirExists) {
      try {
        const files = fs.readdirSync(DOWNLOAD_PATH);
        downloadedCount = files.filter(f => f.endsWith('.mp3') || f.endsWith('.flac') || f.endsWith('.ogg') || f.endsWith('.m4a')).length;
        console.log(`  找到 ${downloadedCount} 个音频文件`);
      } catch {}
    }

    console.log(`  下载结果: ${downloadCompleted ? '成功' : '部分成功'} (${downloadedCount} 首歌曲)`);
    await takeScreenshot('08-final-status');
    console.log('  截图: 08-final-status.png');

    console.log('');
    console.log('==========================================');
    console.log('   测试总结');
    console.log('==========================================');

    if (hasError) {
      console.log('❌ 测试过程中遇到错误');
    } else {
      console.log('✅ 测试完成');
    }

    console.log('  结果详情:');
    console.log(`  - 歌曲解析: ${await tableRows.count()} 首`);
    console.log(`  - 音乐源选中: ${selectedCount}/4`);
    console.log(`  - 搜索完成: ${searchCompleted ? '是' : '否'}`);
    console.log(`  - 下载完成: ${downloadCompleted ? '是' : '否'}`);
    console.log(`  - 验证文件数: ${downloadedCount} 首`);
    console.log(`  - 截图保存: ${screenshotList.length} 张`);
    console.log('==========================================');

  } catch (error) {
    console.error('');
    console.error('❌ 测试失败:', error.message);
    await takeScreenshot('09-error-screenshot');

    // 打印页面内容用于调试
    try {
      const bodyText = await page.locator('body').textContent();
      console.log('页面内容:', bodyText.substring(0, 500));
    } catch {}
  } finally {
    await browser.close();
  }
}

// 运行测试
testYangNaiwenDownload().catch(console.error);

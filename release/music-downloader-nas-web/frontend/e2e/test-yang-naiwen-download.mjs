/**
 * 杨乃文歌单下载测试 - 简化版
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
  console.log('   杨乃文歌单下载测试');
  console.log('==========================================');
  console.log('歌单URL:', TEST_PLAYLIST_URL);
  console.log('下载路径:', DOWNLOAD_PATH);
  console.log('');

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox']
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 截图目录
  const screenshotDir = 'e2e/screenshots';
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

    // 截图
    await page.screenshot({ path: `${screenshotDir}/01-page-loaded.png` });
    console.log('  截图: 01-page-loaded.png');

    // 步骤2：输入URL并解析
    console.log('');
    console.log('【步骤2】解析歌单...');

    // 找到URL输入框
    const urlInput = page.getByPlaceholder('粘贴网易云或QQ音乐的歌单分享链接');
    await urlInput.fill(TEST_PLAYLIST_URL);
    console.log('  已输入URL');

    // 点击解析按钮
    await page.getByRole('button', { name: '解析歌单' }).click();
    console.log('  已点击解析按钮...');

    // 等待解析完成
    await page.waitForFunction(() => {
      const text = document.body.innerText;
      return text.includes('首歌曲') && (text.includes('成功') || text.includes('解析'));
    }, { timeout: 60000 });

    // 统计歌曲数量
    const songCount = await page.locator('.ant-table-tbody tr').count();
    console.log(`  歌单解析完成，共 ${songCount} 首歌曲`);

    await page.screenshot({ path: `${screenshotDir}/02-playlist-parsed.png` });
    console.log('  截图: 02-playlist-parsed.png');

    // 步骤3：选中所有音乐源
    console.log('');
    console.log('【步骤3】选中所有音乐源...');

    // 滚动到顶部
    await page.evaluate(() => window.scrollTo(0, 0));

    // 选中4个音乐源
    const sources = ['网易云', 'QQ音乐', '酷狗', '酷我'];
    for (const source of sources) {
      const checkbox = page.getByRole('checkbox', { name: source });
      if (await checkbox.count() > 0) {
        const isChecked = await checkbox.isChecked();
        if (!isChecked) {
          await checkbox.click();
          console.log(`  已选中 ${source}`);
        } else {
          console.log(`  ${source} 已选中`);
        }
      }
    }

    // 步骤4：全选歌曲并搜索
    console.log('');
    console.log('【步骤4】批量搜索...');

    // 点击全选
    const selectAllBtn = page.getByRole('button', { name: /全选/ });
    if (await selectAllBtn.count() > 0 && await selectAllBtn.isVisible()) {
      await selectAllBtn.click();
      console.log('  已点击全选按钮');
    }

    // 点击批量搜索
    const searchBtn = page.getByRole('button', { name: /批量搜索/ });
    await searchBtn.click();
    console.log('  已点击批量搜索按钮...');

    // 等待搜索进度
    await page.waitForSelector('.ant-progress', { timeout: 15000 });
    console.log('  搜索进度条已显示');

    // 等待搜索完成（最多4分钟）
    console.log('  等待搜索完成（最多4分钟）...');
    await page.waitForFunction(() => {
      const text = document.body.innerText;
      return text.includes('搜索完成') || text.includes('匹配成功');
    }, { timeout: 240000 });

    // 获取匹配结果
    const matchText = await page.locator('text=/\d+\/\d+.*匹配成功/').textContent();
    console.log(`  ${matchText}`);

    await page.screenshot({ path: `${screenshotDir}/03-search-completed.png` });
    console.log('  截图: 03-search-completed.png');

    // 步骤5：设置下载路径
    console.log('');
    console.log('【步骤5】设置下载路径...');

    // 滚动到页面底部
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);

    // 找到下载路径输入框
    const pathInput = page.getByPlaceholder('留空使用默认路径');
    await pathInput.fill(DOWNLOAD_PATH);
    console.log(`  已设置下载路径: ${DOWNLOAD_PATH}`);

    await page.screenshot({ path: `${screenshotDir}/04-download-path.png` });
    console.log('  截图: 04-download-path.png');

    // 步骤6：开始下载
    console.log('');
    console.log('【步骤6】开始下载...');

    const downloadBtn = page.getByRole('button', { name: /下载选中/ });
    await downloadBtn.click();
    console.log('  已点击下载按钮...');

    // 等待下载进度
    await page.waitForSelector('.ant-progress', { timeout: 30000 });
    console.log('  下载进度条已显示');

    // 监控下载进度（最多10分钟）
    console.log('');
    console.log('【监控下载进度】');

    for (let i = 0; i < 120; i++) {
      await page.waitForTimeout(5000);

      // 获取进度文字
      const progressText = await page.locator('.ant-progress-text').first().textContent().catch(() => '');
      if (progressText) {
        console.log(`  ${progressText}`);
      }

      // 检查完成消息
      const messages = await page.locator('.ant-message').textContent().catch(() => '');
      if (messages && messages.includes('下载完成')) {
        console.log('');
        console.log('  下载完成！');
        break;
      }
    }

    await page.screenshot({ path: `${screenshotDir}/05-download-complete.png` });
    console.log('  截图: 05-download-complete.png');

    // 步骤7：验证结果
    console.log('');
    console.log('【步骤7】验证结果...');

    // 检查最终消息
    const finalMsg = await page.locator('.ant-message-success').last().textContent().catch(() => '无');
    console.log(`  最终状态: ${finalMsg}`);

    await page.screenshot({ path: `${screenshotDir}/06-final-status.png`, fullPage: true });
    console.log('  截图: 06-final-status.png');

    console.log('');
    console.log('==========================================');
    console.log('   测试完成!');
    console.log(`  截图保存在: ${screenshotDir}/`);
    console.log('==========================================');

  } catch (error) {
    console.error('');
    console.error('测试失败:', error.message);

    // 截图错误状态
    try {
      await page.screenshot({ path: `${screenshotDir}/error-screenshot.png`, fullPage: true });
    } catch {}
    console.log(`截图保存在: ${screenshotDir}/error-screenshot.png`);

    // 打印页面内容用于调试
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
    console.log('页面内容:', bodyText);
  } finally {
    await browser.close();
  }
}

// 运行测试
testYangNaiwenDownload().catch(console.error);

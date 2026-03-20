/**
 * 简单测试 - 验证搜索功能
 */
const { chromium } = require('playwright');

(async () => {
  console.log('启动测试...');

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });

  // 监听控制台日志
  page.on('console', msg => {
    if (msg.text().includes('[后台任务]') || msg.text().includes('错误')) {
      console.log('浏览器控制台:', msg.text());
    }
  });

  // 监听请求
  page.on('response', response => {
    if (response.url().includes('batch-search')) {
      console.log('API响应:', response.url(), response.status());
    }
  });

  try {
    await page.goto('http://localhost:5173/batch', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 输入歌曲
    await page.locator('textarea').first().fill('夜曲 - 周杰伦');
    console.log('已输入歌曲');

    // 点击搜索
    await page.locator('button.ant-btn-primary').filter({ hasText: '批量搜索' }).click();
    console.log('已点击搜索按钮');

    // 等待搜索进度卡片出现
    console.log('等待搜索进度...');
    await page.waitForSelector('.ant-card:has-text("搜索进度")', { timeout: 60000 }).catch(() => {
      console.log('未找到搜索进度卡片');
    });

    // 等待搜索完成 - 等待结果卡片
    console.log('等待搜索结果...');
    const startTime = Date.now();
    const maxWait = 120000; // 2分钟

    while (Date.now() - startTime < maxWait) {
      const hasResults = await page.evaluate(() => {
        const cards = document.querySelectorAll('.ant-card-head-title');
        for (const card of cards) {
          if (card.textContent?.includes('搜索结果')) {
            return true;
          }
        }
        return false;
      });

      if (hasResults) {
        console.log('搜索结果已显示');
        break;
      }

      await page.waitForTimeout(2000);
      console.log(`等待中... ${Math.round((Date.now() - startTime) / 1000)}秒`);
    }

    // 检查结果
    const resultCount = await page.locator('.ant-table-tbody tr').count();
    console.log(`结果行数: ${resultCount}`);

    // 截图
    await page.screenshot({ path: 'test_result.png', fullPage: true });
    console.log('已保存截图: test_result.png');

  } catch (e) {
    console.error('测试错误:', e);
  }

  // 不关闭浏览器，让用户检查
  console.log('\n测试完成，浏览器将保持打开，按Ctrl+C退出');
  // await browser.close();
})();
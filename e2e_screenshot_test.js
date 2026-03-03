/**
 * 截图调试批量下载页面
 */

const { chromium } = require('playwright');

(async () => {
  console.log('启动浏览器进行截图调试...');

  const browser = await chromium.launch({
    headless: false
  });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });

  // 导航到批量下载页面
  await page.goto('http://localhost:5173/batch', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  // 等待页面加载
  await page.waitForTimeout(3000);

  // 截图
  await page.screenshot({ path: 'batch_page_screenshot.png', fullPage: true });
  console.log('截图已保存到 batch_page_screenshot.png');

  // 输入歌曲并搜索
  console.log('输入歌曲并搜索...');
  const textarea = await page.locator('textarea').first();
  await textarea.fill('夜曲 - 周杰伦');

  const searchButton = page.locator('button').filter({ hasText: '开始批量搜索' });
  await searchButton.click();

  // 等待更长时间（60秒）
  console.log('等待搜索结果（最多60秒）...');
  try {
    await page.waitForFunction(() => {
      return document.querySelector('table') !== null;
    }, { timeout: 60000 });
    console.log('搜索结果已显示！');
  } catch (e) {
    console.log('搜索超时或失败');
  }

  // 再次截图
  await page.screenshot({ path: 'batch_page_after_search.png', fullPage: true });
  console.log('搜索后截图已保存到 batch_page_after_search.png');

  // 检查页面元素
  const elements = await page.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('input')).map(i => ({
      placeholder: i.placeholder,
      value: i.value,
      type: i.type
    }));

    const buttons = Array.from(document.querySelectorAll('button, .ant-btn')).map(b => ({
      text: b.textContent?.trim(),
      visible: b.offsetParent !== null
    }));

    const selects = Array.from(document.querySelectorAll('.ant-select')).map(s => ({
      exists: true,
      visible: s.offsetParent !== null
    }));

    return { inputs, buttons, selects };
  });

  console.log('页面元素:', JSON.stringify(elements, null, 2));

  // 保持浏览器打开
  console.log('浏览器保持打开，按Ctrl+C退出...');
  await new Promise(() => {});
})();

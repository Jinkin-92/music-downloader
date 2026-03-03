/**
 * 调试E2E测试 - 截图查看页面状态
 */

const { chromium } = require('playwright');

(async () => {
  console.log('启动浏览器进行调试...');

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
  await page.screenshot({ path: 'e2e_debug_screenshot.png' });
  console.log('截图已保存到 e2e_debug_screenshot.png');

  // 检查页面内容
  const pageContent = await page.evaluate(() => {
    return {
      title: document.title,
      url: window.location.href,
      hasTextarea: document.querySelectorAll('textarea').length,
      hasInput: document.querySelectorAll('input').length,
      hasButton: document.querySelectorAll('button').length,
      hasCheckbox: document.querySelectorAll('input[type="checkbox"]').length,
      bodyText: document.body?.textContent?.substring(0, 500)
    };
  });

  console.log('页面信息:', JSON.stringify(pageContent, null, 2));

  // 保持浏览器打开以便手动检查
  console.log('浏览器保持打开，按Ctrl+C退出...');
  await new Promise(() => {});
})();

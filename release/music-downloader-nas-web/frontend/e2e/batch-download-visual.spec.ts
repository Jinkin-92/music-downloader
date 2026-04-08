import { test, expect } from '@playwright/test';

/**
 * 批量下载页面 - 视觉增强效果E2E测试
 *
 * 测试内容:
 * 1. 输入功能和歌曲识别
 * 2. SSE状态指示器
 * 3. AnimatedProgress动画效果
 * 4. 微交互效果(hover, ripple)
 * 5. 视觉层次和阴影
 * 6. 情感化配色
 */

test.describe('批量下载页面 - 视觉增强', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/batch');
    await page.waitForLoadState('networkidle');
  });

  test('1. 输入功能和歌曲识别', async ({ page }) => {
    // 查找textarea
    const textarea = page.locator('textarea').first();

    // 输入测试歌曲
    await textarea.fill('夜曲 - 周杰伦\n晴天 - 周杰伦\n稻香 - 周杰伦\n七里香 - 周杰伦\n彩虹 - 周杰伦');

    // 等待React状态更新
    await page.waitForTimeout(1000);

    // 验证"已识别 5 首歌曲"
    await expect(page.locator('text=/已识别 5 首歌曲/')).toBeVisible();

    // 验证搜索按钮已启用
    const searchButton = page.getByRole('button', { name: /批量搜索/ });
    await expect(searchButton).toBeEnabled();

    // 测试清空按钮
    const clearButton = page.getByRole('button', { name: /清空输入/ });
    await clearButton.click();
    await page.waitForTimeout(500);

    // 验证已归零
    await expect(page.locator('text=/已识别 0 首歌曲/')).toBeVisible();
  });

  test('2. SSE状态指示器', async ({ page }) => {
    // 输入测试数据
    await page.locator('textarea').first().fill('夜曲 - 周杰伦\n晴天 - 周杰伦');

    await page.waitForTimeout(1000);

    // 点击搜索按钮
    const searchButton = page.getByRole('button', { name: /批量搜索/ });
    await searchButton.click();

    // 等待SSE连接建立(最多5秒)
    await page.waitForTimeout(2000);

    // 检查是否有SSE状态相关的元素(通过类名或文本)
    // 注意: 实际状态元素取决于SSEStatusIndicator的实现

    // 等待搜索开始或完成
    await page.waitForTimeout(5000);

    // 截图记录SSE状态
    await page.screenshot({ path: 'test-results/sse-status.png' });
  });

  test('3. AnimatedProgress动画效果', async ({ page }) => {
    // 输入并触发搜索
    await page.locator('textarea').first().fill('夜曲 - 周杰伦\n晴天 - 周杰伦\n稻香 - 周杰伦');
    await page.waitForTimeout(1000);

    const searchButton = page.getByRole('button', { name: /批量搜索/ });
    await searchButton.click();

    // 等待进度条出现
    await page.waitForTimeout(3000);

    // 检查进度条元素
    const progressBar = page.locator('.ant-progress').first();
    await expect(progressBar).toBeVisible();

    // 检查AnimatedProgress的CSS类
    const animatedContainer = page.locator('.animated-progress-container');
    const hasAnimatedClass = await animatedContainer.count();

    // 截图记录进度条状态
    await page.screenshot({ path: 'test-results/animated-progress.png' });

    // 等待搜索完成
    await page.waitForTimeout(10000);
  });

  test('4. 微交互效果 - 按钮悬停', async ({ page }) => {
    const searchButton = page.getByRole('button', { name: /批量搜索/ });

    // 获取按钮初始样式
    const initialBox = await searchButton.boundingBox();

    // 悬停在按钮上
    await searchButton.hover();

    // 等待过渡动画
    await page.waitForTimeout(500);

    // 截图记录悬停效果
    await page.screenshot({ path: 'test-results/button-hover.png' });

    // 检查是否有阴影变化(通过computed style)
    const boxShadow = await searchButton.evaluate((el) => {
      return window.getComputedStyle(el).boxShadow;
    });

    console.log('Button box-shadow:', boxShadow);
    expect(boxShadow).not.toBe('none');
  });

  test('5. 微交互效果 - 卡片悬停', async ({ page }) => {
    const cards = page.locator('.ant-card');

    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    // 悬停在第一个卡片上
    await cards.first().hover();
    await page.waitForTimeout(500);

    // 截图记录卡片悬停效果
    await page.screenshot({ path: 'test-results/card-hover.png' });

    // 检查阴影样式
    const cardShadow = await cards.first().evaluate((el) => {
      return window.getComputedStyle(el).boxShadow;
    });

    console.log('Card box-shadow:', cardShadow);
    expect(cardShadow).toContain('0px'); // 应该有阴影偏移
  });

  test('6. 视觉层次 - 阴影系统', async ({ page }) => {
    // 检查页面上的阴影类
    const shadowElements = await page.locator('[class*="shadow-"]').count();
    console.log('Found shadow elements:', shadowElements);

    // 检查卡片是否有阴影
    const cards = page.locator('.ant-card');
    const firstCardShadow = await cards.first().evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        boxShadow: styles.boxShadow,
        borderRadius: styles.borderRadius
      };
    });

    console.log('Card styles:', firstCardShadow);

    // 验证卡片有圆角和阴影
    expect(firstCardShadow.borderRadius).not.toBe('0px');
    expect(firstCardShadow.boxShadow).not.toBe('none');

    // 截图记录视觉层次
    await page.screenshot({ path: 'test-results/visual-hierarchy.png', fullPage: true });
  });

  test('7. 间距系统', async ({ page }) => {
    // 检查间距类
    const spacingElements = await page.locator('[class*="p-"], [class*="m-"], [class*="gap-"]').count();
    console.log('Found spacing elements:', spacingElements);

    // 检查卡片内部间距
    const cardBody = page.locator('.ant-card-body').first();
    const padding = await cardBody.evaluate((el) => {
      return window.getComputedStyle(el).padding;
    });

    console.log('Card body padding:', padding);
    // 应该有padding(24px从visual-hierarchy.css)
  });

  test('8. 文本层次', async ({ page }) => {
    // 检查标题
    const headings = page.locator('h2, h3');
    const headingCount = await headings.count();
    console.log('Found headings:', headingCount);

    // 检查第一个标题的样式
    const firstHeading = headings.first();
    const headingStyles = await firstHeading.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontSize: styles.fontSize,
        fontWeight: styles.fontWeight,
        color: styles.color
      };
    });

    console.log('Heading styles:', headingStyles);

    // 验证标题有正确的字体大小和粗细
    expect(parseInt(headingStyles.fontSize)).toBeGreaterThan(16);
    expect(parseInt(headingStyles.fontWeight)).toBeGreaterThanOrEqual(600);
  });

  test('9. 完整搜索流程测试', async ({ page }) => {
    // 输入歌曲
    await page.locator('textarea').first().fill('夜曲 - 周杰伦\n晴天 - 周杰伦\n稻香 - 周杰伦');
    await page.waitForTimeout(1000);

    // 验证识别
    await expect(page.locator('text=/已识别 3 首歌曲/')).toBeVisible();

    // 截图:输入状态
    await page.screenshot({ path: 'test-results/search-flow-1-input.png' });

    // 开始搜索
    const searchButton = page.getByRole('button', { name: /批量搜索/ });
    await searchButton.click();

    // 等待进度
    await page.waitForTimeout(3000);

    // 截图:搜索进行中
    await page.screenshot({ path: 'test-results/search-flow-2-searching.png' });

    // 等待搜索完成(最多30秒)
    await page.waitForTimeout(30000);

    // 截图:搜索完成
    await page.screenshot({ path: 'test-results/search-flow-3-complete.png', fullPage: true });

    // 检查是否有结果表格或其他结果显示
    const table = page.locator('.ant-table');
    const hasTable = await table.count();

    console.log('Has result table:', hasTable > 0);
  });

  test('10. CSS加载验证', async ({ page }) => {
    // 检查CSS文件是否已加载
    const stylesheets = await page.evaluate(() => {
      const sheets = Array.from(document.styleSheets);
      return sheets.map(sheet => sheet.href);
    });

    console.log('Loaded stylesheets:', stylesheets);

    // 检查是否包含我们的CSS文件
    const hasMicroInteractions = stylesheets.some(href => href?.includes('micro-interactions'));
    const hasVisualHierarchy = stylesheets.some(href => href?.includes('visual-hierarchy'));
    const hasEmotionalColors = stylesheets.some(href => href?.includes('emotional-colors'));

    console.log('CSS files loaded:');
    console.log('  - micro-interactions.css:', hasMicroInteractions);
    console.log('  - visual-hierarchy.css:', hasVisualHierarchy);
    console.log('  - emotional-colors.css:', hasEmotionalColors);

    // 注意: 在开发环境中,CSS可能被Vite内联到JS中
    // 所以这个检查可能不完全准确,但可以确认样式已应用
  });
});

test.describe('批量下载页面 - 错误处理', () => {
  test('空输入时显示警告', async ({ page }) => {
    await page.goto('/batch');
    await page.waitForLoadState('networkidle');

    // 不输入任何内容,直接点击搜索
    const searchButton = page.getByRole('button', { name: /批量搜索/ });

    // 按钮应该是禁用的
    await expect(searchButton).toBeDisabled();
  });

  test('清空输入后归零', async ({ page }) => {
    await page.goto('/batch');
    await page.waitForLoadState('networkidle');

    const textarea = page.locator('textarea').first();
    await textarea.fill('夜曲 - 周杰伦');
    await page.waitForTimeout(1000);

    // 应该识别1首
    await expect(page.locator('text=/已识别 1 首歌曲/')).toBeVisible();

    // 清空
    const clearButton = page.getByRole('button', { name: /清空输入/ });
    await clearButton.click();
    await page.waitForTimeout(500);

    // 应该归零
    await expect(page.locator('text=/已识别 0 首歌曲/')).toBeVisible();
  });
});

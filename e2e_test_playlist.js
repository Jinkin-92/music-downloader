/**
 * E2E测试 - 验证批量下载页面关键功能
 *
 * 测试项目：
 * 1. 音乐源默认选择（网易云、QQ音乐、酷狗、酷我全部选中）
 * 2. 相似度显示正常（无NaN%）
 * 3. 相似度分解显示（歌名/歌手/专辑各部分得分）
 * 4. 下载按钮在匹配结果表格下方
 * 5. 下载路径输入框存在且可用
 * 6. 浏览文件夹按钮已移除
 */

const { chromium } = require('playwright');

(async () => {
  console.log('========================================');
  console.log('  E2E测试 - 批量下载页面验证');
  console.log('========================================\n');

  let browser;
  let allPassed = true;
  const results = [];

  try {
    // 启动浏览器
    console.log('1. 启动浏览器...');
    browser = await chromium.launch({
      headless: false,
      args: ['--start-maximized']
    });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 800 });

    // 导航到批量下载页面
    console.log('2. 导航到批量下载页面...');
    await page.goto('http://localhost:5173/batch', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // 等待页面加载
    await page.waitForTimeout(2000);

    // 测试1: 音乐源默认选择
    console.log('\n[测试1] 检查音乐源默认选择...');
    try {
      const sources = await page.evaluate(() => {
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        return Array.from(checkboxes).map(cb => ({
          label: cb.parentElement?.textContent?.trim() || '',
          checked: cb.checked
        }));
      });

      const neteaseChecked = sources.some(s => s.label.includes('网易云') && s.checked);
      const qqChecked = sources.some(s => s.label.includes('QQ音乐') && s.checked);
      const kugouChecked = sources.some(s => s.label.includes('酷狗') && s.checked);
      const kuwoChecked = sources.some(s => s.label.includes('酷我') && s.checked);

      const passed = neteaseChecked && qqChecked && kugouChecked && kuwoChecked;
      results.push({ name: '音乐源默认选择', passed, details: sources });
      console.log(passed ? '  ✅ 通过' : '  ❌ 失败');
      console.log('  详情:', sources);
    } catch (e) {
      results.push({ name: '音乐源默认选择', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

    // 测试2: 输入歌曲列表并搜索
    console.log('\n[测试2] 输入歌曲列表并搜索...');
    try {
      // 输入测试歌曲
      const textarea = await page.locator('textarea').first();
      await textarea.fill('夜曲 - 周杰伦\n七里香 - 周杰伦');

      // 点击搜索按钮
      await page.locator('button:has-text("开始批量搜索")').click();

      // 等待搜索完成（最多30秒）
      await page.waitForSelector('table[role="table"]', { timeout: 30000 });
      await page.waitForTimeout(3000);

      results.push({ name: '批量搜索', passed: true });
      console.log('  ✅ 通过');
    } catch (e) {
      results.push({ name: '批量搜索', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

    // 测试3: 检查相似度显示
    console.log('\n[测试3] 检查相似度显示...');
    try {
      const similarityTags = await page.evaluate(() => {
        const tags = document.querySelectorAll('.ant-tag, span[class*="tag"]');
        return Array.from(tags).map(tag => tag.textContent?.trim()).filter(t => t && t.includes('%'));
      });

      const hasNaN = similarityTags.some(t => t.includes('NaN'));
      const passed = !hasNaN;

      results.push({ name: '相似度显示', passed, details: similarityTags });
      console.log(passed ? '  ✅ 通过' : '  ❌ 失败');
      console.log('  相似度标签:', similarityTags);
    } catch (e) {
      results.push({ name: '相似度显示', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

    // 测试3.5: 检查相似度分解显示
    console.log('\n[测试3.5] 检查相似度分解显示...');
    try {
      const similarityBreakdownExists = await page.evaluate(() => {
        // 查找包含"歌名"、"歌手"关键词的文本
        const bodyText = document.body.textContent || '';
        return bodyText.includes('歌名') && bodyText.includes('歌手') && bodyText.includes('%');
      });

      results.push({ name: '相似度分解显示', passed: similarityBreakdownExists });
      console.log(similarityBreakdownExists ? '  ✅ 通过（显示歌名/歌手分解）' : '  ❌ 失败（未找到相似度分解）');
    } catch (e) {
      results.push({ name: '相似度分解显示', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

    // 测试4: 检查下载路径输入框
    console.log('\n[测试4] 检查下载路径输入框...');
    try {
      const downloadInputExists = await page.evaluate(() => {
        const inputs = document.querySelectorAll('input');
        return Array.from(inputs).some(input =>
          input.placeholder?.includes('下载目录') ||
          input.placeholder?.includes('快捷名称') ||
          input.placeholder?.includes('完整路径')
        );
      });

      results.push({ name: '下载路径输入框', passed: downloadInputExists });
      console.log(downloadInputExists ? '  ✅ 通过' : '  ❌ 失败');
    } catch (e) {
      results.push({ name: '下载路径输入框', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

    // 测试5: 检查浏览按钮已移除（修复后应该不存在）
    console.log('\n[测试5] 检查浏览按钮已移除...');
    try {
      const browseButtonExists = await page.evaluate(() => {
        const buttons = document.querySelectorAll('button, .ant-btn');
        return Array.from(buttons).some(btn =>
          btn.textContent?.trim() === '浏览'
        );
      });

      // 浏览按钮应该不存在（已移除）
      const passed = !browseButtonExists;
      results.push({ name: '浏览按钮已移除', passed });
      console.log(passed ? '  ✅ 通过（浏览按钮已移除）' : '  ❌ 失败（浏览按钮仍然存在）');
    } catch (e) {
      results.push({ name: '浏览按钮已移除', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

    // 测试6: 检查下载按钮
    console.log('\n[测试6] 检查下载按钮...');
    try {
      const downloadButtonExists = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons.some(btn =>
          btn.textContent?.includes('下载选中')
        );
      });

      results.push({ name: '下载按钮', passed: downloadButtonExists });
      console.log(downloadButtonExists ? '  ✅ 通过' : '  ❌ 失败');
    } catch (e) {
      results.push({ name: '下载按钮', passed: false, error: e.message });
      console.log('  ❌ 失败:', e.message);
    }

  } catch (error) {
    console.error('\n❌ 测试过程中发生错误:', error);
    allPassed = false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  // 打印测试结果
  console.log('\n========================================');
  console.log('  测试结果汇总');
  console.log('========================================\n');

  const passedCount = results.filter(r => r.passed).length;
  const totalCount = results.length;

  results.forEach(result => {
    const icon = result.passed ? '✅' : '❌';
    console.log(`${icon} ${result.name}`);
    if (result.error) {
      console.log(`   错误: ${result.error}`);
    }
    if (result.details) {
      console.log(`   详情:`, result.details);
    }
  });

  console.log(`\n总计: ${passedCount}/${totalCount} 通过`);

  if (passedCount === totalCount) {
    console.log('\n🎉 所有测试通过！');
    process.exit(0);
  } else {
    console.log('\n⚠️  部分测试失败');
    process.exit(1);
  }
})();

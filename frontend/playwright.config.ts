import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E测试配置
 * 用于测试批量下载页面的视觉增强效果
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // 批量搜索需要串行执行
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // 单worker避免端口冲突
  timeout: 120000, // 全局超时120秒(2分钟)
  reporter: [
    ['html'],
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 60000, // 操作超时60秒
    navigationTimeout: 60000, // 导航超时60秒
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 启动开发服务器
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true, // 使用已存在的服务器
    timeout: 120000,
  },
});

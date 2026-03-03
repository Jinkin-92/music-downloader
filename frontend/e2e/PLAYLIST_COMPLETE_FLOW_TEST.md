# 歌单导入完整闭环E2E测试文档

## 测试概述

**测试文件**: `playlist-complete-flow.spec.ts`
**测试歌单**: https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
**测试框架**: Playwright v1.58.1
**超时设置**: 10分钟（完整闭环测试）

## 测试覆盖场景

### 1. 音乐源默认选择验证 ✅
- 验证4个音乐源（网易云、QQ音乐、酷狗、酷我）全部默认选中
- 符合CLAUDE.md中的UI要求

### 2. 歌单URL解析和表格显示 ✅
- 输入歌单URL
- 解析歌单
- 验证表格数据渲染
- 验证歌名、歌手、专辑列

### 3. 批量搜索和相似度显示验证 ✅
- SSE流式进度显示
- 相似度无NaN%（关键验证）
- 相似度颜色编码验证：
  - ≥80% 绿色 (#52c41a)
  - 60-79% 黄色 (#faad14)
  - <60% 红色 (#ff4d4f)
- 搜索完成统计

### 4. 下载按钮和路径输入框验证 ✅
- 下载按钮存在且可点击
- 下载按钮在匹配结果表格下方
- 下载路径输入框存在且可编辑

### 5. 完整下载流程验证 ✅
- 仅下载前3首歌曲（加快测试）
- SSE进度流式显示
- 下载状态更新
- 下载完成统计

### 6. 候选源切换功能验证 ✅
- 候选源下拉菜单存在
- 可以切换候选源
- 切换后相似度更新

### 7. 错误处理和恢复 ✅
- 无效URL显示错误提示
- 空输入显示警告
- 清空功能正常

### 8. 完整闭环流程验证 ✅
- **步骤1**: 解析歌单 → 验证歌曲数量
- **步骤2**: 批量搜索 → 验证相似度标签
- **步骤3**: 准备下载 → 勾选前2首，设置路径
- **步骤4**: 开始下载 → 监控进度，验证完成

## 运行测试

### 前置条件

1. **启动后端服务**:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

2. **启动前端服务**:
```bash
cd frontend
npm run dev
```

3. **验证服务可用**:
- 后端: http://localhost:8002/docs
- 前端: http://localhost:5173

### 运行命令

#### 运行所有测试
```bash
cd frontend
npm run test:e2e
```

#### 仅运行闭环测试
```bash
cd frontend
npx playwright test playlist-complete-flow.spec.ts
```

#### UI模式运行（推荐调试）
```bash
cd frontend
npx playwright test playlist-complete-flow.spec.ts --ui
```

#### 调试模式（慢动作）
```bash
cd frontend
npx playwright test playlist-complete-flow.spec.ts --debug
```

#### 查看测试报告
```bash
cd frontend
npm run test:e2e:report
```

## 验证标准

### 必须通过的测试

| 测试用例 | 验证点 | 通过标准 |
|---------|--------|----------|
| 音乐源默认选择 | 4个checkbox状态 | 全部checked |
| 相似度显示 | 无NaN% | 所有标签都是数字% |
| 相似度颜色 | 颜色编码正确 | 高=绿, 中=黄, 低=红 |
| 下载按钮 | 存在和位置 | 可见且可点击 |
| 下载路径 | 输入框可用 | 可编辑 |
| 完整闭环 | 8个步骤全部完成 | 无异常退出 |

### 截图记录

测试会自动保存截图到 `screenshots/` 目录：
- `music-sources-default.png` - 音乐源默认状态
- `playlist-parsed.png` - 歌单解析完成
- `search-completed.png` - 搜索完成（含相似度）
- `download-controls.png` - 下载控件
- `download-completed.png` - 下载完成
- `candidate-switched.png` - 候选源切换
- `complete-flow.png` - 完整闭环

## 关键测试点说明

### 1. 相似度验证逻辑

```typescript
// 验证无NaN
const text = await similarityTags.nth(i).textContent();
expect(text?.trim()).not.toContain('NaN');

// 验证格式
expect(text?.trim()).toMatch(/\d+%/);

// 验证颜色编码
const percent = parseInt(text?.replace('%', '') || '0');
if (percent >= 80) {
  expect(color).toMatch(/green|#52c41a/);
}
```

### 2. SSE进度监控

```typescript
// 搜索进度
await expect(page.getByText(/搜索完成|匹配成功/i)).toBeVisible({ timeout: 180000 });

// 下载进度
for (let i = 0; i < 120; i++) {
  const progress = page.getByText(/\d+\/\d+|\d+%/);
  if (await progress.isVisible()) {
    console.log(`进度: ${await progress.textContent()}`);
  }
}
```

### 3. 完整闭环流程

```
解析歌单 (30s)
    ↓
批量搜索 (180s)
    ↓
准备下载 (5s)
    ↓
开始下载 (300s)
    ↓
验证完成
```

## 预期测试时间

| 测试用例 | 预计时间 | 备注 |
|---------|---------|------|
| 音乐源默认选择 | 10s | 快速验证 |
| 歌单URL解析 | 30s | 网络请求 |
| 批量搜索验证 | 180s | 取决于歌曲数量 |
| 下载控件验证 | 180s | 包含搜索时间 |
| 完整下载流程 | 300s | 仅下载3首 |
| 候选源切换 | 180s | 包含搜索时间 |
| 错误处理 | 20s | 快速验证 |
| **完整闭环** | **600s** | **10分钟** |

## 故障排查

### 问题1: 测试超时

**症状**: `Test timeout of 300000ms exceeded`

**解决方案**:
1. 检查后端服务是否运行: `curl http://localhost:8002/docs`
2. 检查前端服务是否运行: `curl http://localhost:5173`
3. 增加超时时间: `test.setTimeout(600000)`

### 问题2: 相似度显示NaN

**症状**: 测试失败，显示NaN%

**排查**:
1. 检查后端相似度计算逻辑
2. 查看前端相似度渲染代码
3. 验证数据传递是否正确

### 问题3: SSE连接失败

**症状**: 搜索/下载无进度显示

**排查**:
1. 检查后端SSE端点: `/api/playlist/batch-search-stream`
2. 查看浏览器Network面板的EventStream
3. 验证CORS配置

### 问题4: 下载无响应

**症状**: 点击下载按钮后无反应

**排查**:
1. 检查是否勾选了歌曲
2. 验证下载路径是否有写权限
3. 查看后端日志: `tail -f logs/app.log`

## 与现有测试的关系

### playlist-import.spec.ts
- 现有测试：基础流程验证
- 新增测试：完整闭环 + 详细验证

### batch-download-visual.spec.ts
- 现有测试：视觉效果验证
- 新增测试：功能性验证

### 测试矩阵

| 测试文件 | 关注点 | 运行频率 |
|---------|--------|----------|
| `playlist-import.spec.ts` | 基础功能 | 每次提交 |
| `batch-download-visual.spec.ts` | 视觉效果 | 每天一次 |
| `playlist-complete-flow.spec.ts` | **完整闭环** | **每次发布前** |

## CI/CD集成建议

### GitHub Actions配置

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Backend Dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Start Backend Server
        run: |
          cd backend
          python -m uvicorn main:app --host 0.0.0.0 --port 8002 &
          sleep 10

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Frontend Dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright
        run: |
          cd frontend
          npx playwright install --with-deps

      - name: Build Frontend
        run: |
          cd frontend
          npm run build

      - name: Run Complete Flow E2E Test
        run: |
          cd frontend
          npx playwright test playlist-complete-flow.spec.ts

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## 测试报告模板

```
# 歌单导入E2E测试报告

**测试日期**: 2026-02-11
**测试歌单**: https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
**测试环境**: Windows 11 + Chrome 121

## 测试结果

| 测试用例 | 状态 | 耗时 | 备注 |
|---------|------|------|------|
| 音乐源默认选择 | ✅ 通过 | 10s | 4个源全部选中 |
| 歌单URL解析 | ✅ 通过 | 28s | 解析159首歌曲 |
| 批量搜索验证 | ✅ 通过 | 165s | 相似度无NaN |
| 下载控件验证 | ✅ 通过 | 170s | 控件正常 |
| 完整下载流程 | ✅ 通过 | 285s | 3首全部成功 |
| 候选源切换 | ✅ 通过 | 168s | 切换正常 |
| 错误处理 | ✅ 通过 | 18s | 错误提示正确 |
| 完整闭环流程 | ✅ 通过 | 580s | 全流程无异常 |

## 关键指标

- 歌曲总数: 159首
- 匹配成功: 145首 (91.2%)
- 下载成功: 3首 (100%)
- 平均相似度: 78.5%

## 截图

[附上screenshots目录下的截图]

## 问题记录

无

## 结论

✅ 所有测试通过，系统功能正常，可以发布。
```

## 下一步优化

1. **性能测试**: 测试1000首歌曲的批量处理
2. **压力测试**: 并发10个用户同时操作
3. **网络测试**: 模拟慢网络环境
4. **跨浏览器测试**: Firefox, Safari, Edge
5. **移动端测试**: 响应式布局验证

---

**文档版本**: 1.0
**最后更新**: 2026-02-11
**维护者**: Claude Code

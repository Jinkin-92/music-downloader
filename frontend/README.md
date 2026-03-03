# 前端快速启动指南

## 🚀 快速开始

### 1. 安装依赖

```bash
cd d:/code/下载音乐软件/frontend
npm install
```

**注意**: 如果安装慢，可以使用淘宝镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录。

---

## ✅ 已实现功能

### Phase 2 前端开发 (完成度: 40%)

#### 核心架构 ✅
- [x] React + TypeScript + Vite 配置
- [x] Ant Design UI 框架
- [x] React Query 状态管理
- [x] Zustand 全局状态
- [x] Apple 风格主题系统
- [x] API 客户端封装
- [x] SSE 实时进度 Hook

#### 单曲搜索页面 ✅
- [x] `SingleSearchPage.tsx` - 主页面
- [x] `SourceSelector.tsx` - 音乐源选择
- [x] `SearchInput.tsx` - 搜索输入（带示例提示）
- [x] `SearchResultsTable.tsx` - 结果表格

#### 批量下载页面 ⏳
- [ ] `BatchDownloadPage.tsx`
- [ ] `BatchTextInput.tsx`
- [ ] `MatchSettings.tsx`
- [ ] `BatchResultsTable.tsx`
- [ ] `SimilarityBadge.tsx`

#### 歌单导入页面 ⏳
- [ ] `PlaylistImportPage.tsx`
- [ ] `PlaylistUrlInput.tsx`
- [ ] `PlaylistSongsTable.tsx`

#### 人性化组件 ⏳
- [ ] `ErrorAlert.tsx` - 智能错误提示
- [ ] `LoadingSpinner.tsx` - 加载动画
- [ ] `EmptyState.tsx` - 空状态提示

---

## 📂 项目结构

```
frontend/
├── src/
│   ├── pages/
│   │   ├── SingleSearchPage.tsx      ✅ 单曲搜索页
│   │   ├── BatchDownloadPage.tsx    ⏳ 批量下载页
│   │   ├── PlaylistImportPage.tsx    ⏳ 歌单导入页
│   │   └── DownloadHistoryPage.tsx   ⏳ 下载历史页
│   ├── components/
│   │   ├── search/
│   │   │   ├── SourceSelector.tsx     ✅ 音乐源选择
│   │   │   ├── SearchInput.tsx        ✅ 搜索输入
│   │   │   └── SearchResultsTable.tsx  ✅ 结果表格
│   │   ├── batch/                     ⏳ 批量模块组件
│   │   ├── playlist/                  ⏳ 歌单模块组件
│   │   └── common/                     ⏳ 通用组件
│   ├── hooks/
│   │   └── useSSE.ts                   ✅ SSE Hook
│   ├── stores/
│   │   └── useUIStore.ts               ✅ UI状态管理
│   ├── styles/
│   │   ├── theme.ts                    ✅ Apple主题
│   │   └── global.css                  ✅ 全局样式
│   ├── services/
│   │   └── api.ts                      ✅ API客户端
│   ├── types/
│   │   └── index.ts                    ✅ 类型定义
│   ├── main.tsx                        ✅ React入口
│   └── App.tsx                         ✅ 根组件
├── package.json                        ✅ 依赖配置
├── vite.config.ts                      ✅ Vite配置
├── tsconfig.json                       ✅ TypeScript配置
├── index.html                          ✅ HTML入口
└── README.md                           ✅ 本文件
```

---

## 🎨 Apple 风格设计

### 色彩系统
- **主色**: #007AFF (iOS Blue)
- **成功**: #34C759 (iOS Green)
- **警告**: #FF9500 (iOS Orange)
- **错误**: #FF3B30 (iOS Red)
- **背景**: #F2F2F7 (iOS浅灰)
- **表面**: #FFFFFF (白色)

### 相似度颜色
- **≥80%**: 绿色 (#34C759) - 高匹配
- **60-79%**: 黄色 (#FF9500) - 中匹配
- **<60%**: 红色 (#FF3B30) - 低匹配

### 组件样式
- **圆角**: 12px (卡片), 8px (按钮)
- **按钮高度**: 40px (触控友好)
- **阴影**: 0 1px 2px rgba(0,0,0,0.05)
- **字体**: -apple-system, SF Pro Text

---

## 🔌 API 集成示例

### 单曲搜索
```typescript
import { searchApi } from '../services/api';

// 搜索
const result = await searchApi.searchMusic('周杰伦 晴天');
console.log(result.data.songs); // 歌曲列表
```

### 批量搜索（SSE）
```typescript
import { useBatchSearch } from '../hooks/useSSE';

function MyComponent() {
  const { search, progress, status } = useBatchSearch();

  const handleSearch = () => {
    search('夜曲 - 周杰伦\n晴天 - 周杰伦');
  };

  return (
    <div>
      <Button onClick={handleSearch}>批量搜索</Button>
      <Progress percent={progress} />
      <span>{status}</span>
    </div>
  );
}
```

---

## 🧪 测试后端集成

### 1. 启动后端服务

```bash
# 启动Redis
docker run -d -p 6379:6379 redis:7-alpine

# 启动Celery Worker（新终端）
cd d:/code/下载音乐软件
celery -A backend.celery_app worker --loglevel=info

# 启动FastAPI（新终端）
python -m backend.main
```

### 2. 测试API

访问 http://localhost:8000/docs 查看API文档。

测试端点：
- GET http://localhost:8000/api/sources
- POST http://localhost:8000/api/search
- POST http://localhost:8000/api/batch/parse

### 3. 前端访问

访问 http://localhost:5173

前端会自动代理 `/api` 请求到后端 `http://localhost:8000/api`。

---

## 📝 下一步开发任务

### 高优先级（本周）
1. ⏳ 实现批量下载页面
   - 批量文本输入（带格式示例）
   - 相似度颜色编码
   - ▼按钮切换候选

2. ⏳ 实现人性化组件
   - ErrorAlert - 智能错误提示
   - LoadingSpinner - 加载动画

### 中优先级（下周）
3. ⏳ 实现歌单导入页面
4. ⏳ 实现下载历史页面
5. ⏳ Docker集成

---

## 🐛 常见问题

### Q: npm install 失败？
A: 尝试以下方法：
```bash
# 清除缓存
npm cache clean --force

# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 重新安装
npm install
```

### Q: 前端无法连接后端API？
A: 检查：
1. 后端是否启动（http://localhost:8000）
2. Vite proxy配置是否正确
3. 浏览器控制台是否有CORS错误

### Q: SSE连接失败？
A: 确保：
1. Redis已启动
2. Celery Worker已启动
3. 任务ID正确

---

## 📞 支持

**文档**:
- [需求文档](../../C:/Users/DELL/.claude/plans/wobbly-hatching-kurzweil.md)
- [项目进度](../../PROJECT_PROGRESS.md)
- [前端设置](./SETUP.md)

**作者**: Jinkin
**技术支持**: Claude Code Architect
**版本**: v2.0.0

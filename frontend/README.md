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

## ✅ 当前前端状态

当前以 Web 主界面为准，已落地的主要页面是：

#### 核心架构 ✅
- [x] React + TypeScript + Vite 配置
- [x] Ant Design UI 框架
- [x] React Query 状态管理
- [x] Zustand 全局状态
- [x] Apple 风格主题系统
- [x] API 客户端封装
- [x] SSE 实时进度 Hook

- [x] `BatchDownloadPage.tsx` - Web 主页面，包含批量文本输入与歌单导入
- [x] `DownloadHistoryPage.tsx` - 下载历史页面
- [x] `PlaylistImportSection.tsx` - 集成在批量下载页中的歌单导入板块
- [x] `BatchResultsTable.tsx` - 匹配结果表格
- [x] `MatchSettingsPanel.tsx` - 匹配设置与搜索入口
- [x] `SourceSelector.tsx` - 音乐源选择
- [x] `api.ts` - API 客户端封装
- [x] `useUIStore.ts` - 全局 UI 状态

说明：

- 仓库里仍保留后端单曲搜索 API，但当前 React 主界面不再把单曲搜索作为导航主入口
- 前端文档中早期关于 `SingleSearchPage.tsx`、`PlaylistImportPage.tsx` 的规划已过时，应以 `src/pages/` 和 `src/components/batch/` 现状为准

---

## 📂 项目结构

```
frontend/
├── src/
│   ├── pages/
│   │   ├── BatchDownloadPage.tsx      ✅ Web 主页面
│   │   └── DownloadHistoryPage.tsx    ✅ 下载历史页
│   ├── components/
│   │   ├── batch/                     ✅ 批量下载与歌单导入组件
│   │   └── common/                    ✅ 通用组件
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

访问 http://localhost:8003/docs 查看API文档。

测试端点：
- GET http://localhost:8003/api/sources
- POST http://localhost:8003/api/search
- POST http://localhost:8003/api/batch/parse

### 3. 前端访问

访问 http://localhost:5173

前端会自动代理 `/api` 请求到后端 `http://localhost:8003/api`。

---

## 📝 下一步开发任务

### 建议后续方向
1. 对齐 `frontend/README.md` 与真实页面结构，避免再引用已删除的规划页
2. 继续完善 Web 端 E2E 覆盖，围绕批量下载、歌单导入、下载历史三条主流程
3. 将 PyQt 相关说明继续迁出前端文档，减少界面基线混淆

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
1. 后端是否启动（http://localhost:8003）
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

# React前端项目设置指南

## 项目初始化

```bash
# 进入frontend目录
cd d:/code/下载音乐软件/frontend

# 安装Vite和React
npm install vite@latest @vitejs/plugin-react@latest --save-dev

# 安装React和TypeScript
npm install react@^18 react-dom@^18

# 安装TypeScript和类型定义
npm install --save-dev typescript @types/react @types/react-dom @types/node

# 安装UI组件库
npm install antd@^5 @ant-design/icons@^5

# 安装状态管理
npm install @tanstack/react-query@^5 zustand@^4

# 安装HTTP客户端和路由
npm install axios@^1 react-router-dom@^6

# 安装SSE支持
npm install @microsoft/fetch-event-source@^1

# 安装工具库
npm install dayjs lodash
```

## 项目结构

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env
├── public/
│   └── favicon.ico
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── pages/
    │   ├── BatchDownloadPage.tsx
    │   └── DownloadHistoryPage.tsx
    ├── components/
    │   ├── batch/
    │   │   ├── BatchTextInput.tsx
    │   │   ├── MatchSettingsPanel.tsx
    │   │   ├── BatchResultsTable.tsx
    │   │   └── PlaylistImportSection.tsx
    │   └── common/
    │       ├── ErrorAlert.tsx
    │       ├── LoadingSpinner.tsx
    │       └── EmptyState.tsx
    ├── hooks/
    │   ├── useBatchSearch.ts
    │   ├── useDownload.ts
    │   └── useSSE.ts
    ├── stores/
    │   └── useUIStore.ts
    ├── styles/
    │   ├── theme.ts
    │   └── global.css
    ├── services/
    │   └── api.ts
    └── types/
        └── index.ts
```

## 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 核心功能实现

### 1. Apple风格主题系统

文件：`src/styles/theme.ts`
- 定义iOS色彩系统（蓝#007AFF、绿#34C759、橙#FF9500、红#FF3B30）
- 相似度颜色编码（绿≥80%、黄60-79%、红<60%）
- 圆角、阴影、间距设计令牌

### 2. 批量下载页面

文件：`src/pages/BatchDownloadPage.tsx`
- 批量文本输入
- 歌单导入板块
- 匹配设置面板
- 批量搜索按钮
- 批量结果表格
- 下载进度显示

### 3. 下载历史页面

文件：`src/pages/DownloadHistoryPage.tsx`
- 历史记录列表
- 状态筛选
- 清理失效记录
- 打开文件夹

### 4. 人性化功能

**输入示例提示**：
```tsx
<Input.TextArea
  placeholder={`每行一首歌曲，格式：歌名 - 歌手\n\n示例：\n夜曲 - 周杰伦\n晴天 - 周杰伦\n七里香 - 周杰伦`}
  autoSize={{ minRows: 6, maxRows: 12 }}
/>
```

**智能错误提示**：
```tsx
<ErrorAlert
  error="403 Forbidden"
  onRetry={() => retryDownload()}
/>
// 显示：
// 标题：版权保护
// 消息：该歌曲受版权保护，正在尝试切换其他音乐源...
// 按钮：自动重试中
```

**实时进度显示**：
```tsx
const { progress, status } = useSSE(`/api/stream/download/${taskId}`);

<Progress
  percent={progress}
  status={status === 'completed' ? 'success' : 'active'}
/>
```

## API集成

### 基础配置

文件：`src/services/api.ts`
```typescript
import axios from 'axios';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000,
    },
  },
});
```

### 使用示例

```typescript
// 批量搜索（SSE进度）
const { data, progress } = useBatchSearch();
await search(batchText);
// 自动连接SSE获取实时进度
```

## Docker集成

前端构建产物将集成到Docker镜像中：

```dockerfile
# Dockerfile.web中的前端构建阶段
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 复制到最终镜像
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html
```

## 性能优化

- **代码分割**: React.lazy()动态导入页面组件
- **缓存策略**: React Query自动缓存API响应
- **Tree Shaking**: Vite自动移除未使用代码
- **Gzip压缩**: Nginx启用gzip压缩

## 下一步

1. 安装依赖：`npm install`
2. 复制下方代码文件到对应路径
3. 启动开发服务器：`npm run dev`
4. 访问 http://localhost:5173

---

**注意**: 由于这是一个7周的大型项目，这里提供了完整的实施指南。您可以：
- 按照《需求文档.md》中的计划逐步实施
- 使用`application-performance:frontend-developer`技能获取开发支持
- 参考`backend/api/`中的API端点进行集成

# TODOS

## 已完成 ✅

### 2026-03-20
- [x] **CSS动画系统实现** - 添加micro-interactions、visual-hierarchy、emotional-colors三个CSS文件
- [x] **删除键盘快捷键功能** - 为避免浏览器快捷键冲突(Ctrl+H历史, Ctrl+D收藏)，删除了所有键盘快捷键
- [x] **重构BatchDownloadPage** - 消除useEffect依赖循环，移除ref模式
- [x] **添加CSS版本注释** - 在CSS文件中添加Ant Design 5.x版本兼容性说明

## 待处理 📋

### UI/UX 改进
- [ ] **EmptyState组件增强** - 为历史页面添加专门的空状态插图和文案
- [ ] **PyQt加载动画** - 为VerifyWorker添加spinner动画，提升用户等待体验

### 性能优化
- [ ] **CSS动画性能监控** - 当表格行数超过1000时，考虑优化hover动画性能
- [ ] **Ant Design升级准备** - 升级到6.x时检查CSS覆盖是否失效

### 功能扩展
- [ ] **快捷键系统重新设计** - 如果需要键盘快捷键，考虑使用Shift+Ctrl组合或允许用户自定义
- [ ] **无障碍访问增强** - 进一步完善prefers-reduced-motion和键盘导航支持

## 技术债务

### 代码质量
- [ ] **BatchDownloadPage拆分** - 组件过大(700+行)，考虑拆分为更小的子组件
- [ ] **SSE错误处理增强** - 添加指数退避重试机制替代当前的简单轮询

### 测试覆盖
- [ ] **CSS动画测试** - 添加视觉回归测试验证动画效果
- [ ] **E2E测试扩展** - 覆盖EmptyState history类型和所有交互动画

## 备注

### CSS兼容性
- **当前Ant Design版本**: 5.x
- **覆盖的类名**: `.ant-btn-primary`, `.ant-btn-default`, `.ant-card`, `.ant-input`, `.ant-table-tbody`
- **升级检查清单**:
  1. 验证选择器是否仍然有效
  2. 检查暗色模式适配
  3. 测试动画性能

### 已删除功能
- **键盘快捷键**: Ctrl+H(历史), Ctrl+Enter(搜索), Ctrl+D(下载)
- **删除原因**: 与浏览器默认快捷键冲突
- **恢复方案**: 如需恢复，使用Shift+Ctrl组合或添加自定义配置面板

---

**最后更新**: 2026-03-20
**维护者**: Claude Code

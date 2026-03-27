# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [2.0.0.0] - 2026-03-23

### Added
- CSS动画系统 - micro-interactions、visual-hierarchy、emotional-colors
- 下载历史管理功能
- 咪咕音乐源支持
- 歌单导入功能 (网易云、QQ音乐)

### Fixed
- 修复下载历史 API 500 错误 (datetime 解析问题)
- 修复 Ant Design Select dropdownRender 警告
- 修复 favicon.ico 404 错误
- 修复 React Router Future Flag 警告
- 修复键盘快捷键 useEffect 依赖循环问题
- 修复 BatchDownloadPage 中 totalSongCount 变量初始化顺序错误

### Changed
- 将 batch 模块迁移到 core 目录
- 优化歌曲匹配逻辑
- 优化并发下载稳定性
- 优化搜索过滤和统一UI

### Removed
- 删除键盘快捷键功能 (避免浏览器快捷键冲突)
- 删除 pyqt_ui/batch/ 目录下的 matcher.py, models.py, parser.py


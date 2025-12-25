# PyQt5 Music Downloader

一个基于 Python 和 musicdl 的桌面音乐下载工具，提供简洁的图形界面进行音乐搜索和下载。

## 功能特性

- **多平台搜索**：支持 QQ 音乐、网易云、酷狗、酷我等主流音乐平台
- **批量下载**：支持单曲下载和批量下载选中歌曲
- **实时进度**：显示下载进度条和详细状态
- **图形界面**：简洁美观的 PyQt5 图形界面
- **Windows 兼容**：完美支持 Windows 系统，无编码问题

## 环境要求

- Python 3.7+
- pip 包管理器

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 或手动安装
pip install musicdl PyQt5
```

## 使用方法

### 启动应用

```bash
python -m pyqt_ui.main
```

### 搜索音乐

1. 选择音乐来源（默认全选）
   - QQ Music
   - Netease (网易云)
   - Kugou (酷狗)
   - Kuwo (酷我)

2. 在搜索框输入歌曲名、歌手或关键词

3. 点击"Search"按钮

4. 浏览搜索结果表格

### 下载歌曲

1. **单曲下载**：
   - 右键点击任意歌曲
   - 选择"Download Selected"

2. **批量下载**：
   - 右键点击任意歌曲
   - 选择"Download All Results"

3. **复制信息**：
   - 右键点击歌曲
   - 选择"Copy Song Info"

## 下载文件位置

默认下载目录：`musicdl_outputs/`

文件按平台组织：
```
musicdl_outputs/
├── QQMusicClient/
│   └── 2025-12-25-HH-MM-SS 歌曲名/
│       └── 歌曲名 - 文件ID.ogg
├── NeteaseMusicClient/
└── ...
```

## 故障排除

### PyQt5 安装问题

如果遇到 PyQt5 安装问题：
```bash
pip install --upgrade pip
pip install PyQt5
```

### 网络错误

- 检查网络连接
- 某些平台可能需要 VPN
- 尝试不同的音乐来源

### 下载失败

- 检查磁盘空间
- 验证下载目录写入权限
- 查看 `logs/app.log` 获取详细错误信息

### 中文乱码

应用使用 UTF-8 日志编码，所有输出记录在 `logs/app.log`，避免 Windows 控制台编码问题。

## 技术架构

- **GUI 框架**：PyQt5 (Qt Widgets)
- **后端**：musicdl 库
- **多线程**：QThread 防止 GUI 冻结
- **日志**：Python logging 模块文件输出
- **模式**：MusicDL 客户端使用单例模式

## 项目结构

```
pyqt_ui/
├── __init__.py              # 包初始化
├── main.py                  # 主窗口和 UI 逻辑
├── config.py                # 配置设置
├── music_downloader.py      # MusicDL 包装（单例）
└── workers.py               # 后台工作线程
```

## 开发

### 运行测试

```bash
# 启动应用
python -m pyqt_ui.main

# 搜索"七里香"
# 右键第一首 → Download Selected
# 验证文件在 musicdl_outputs/ 目录
```

### 添加新音乐源

编辑 `pyqt_ui/config.py`：
```python
DEFAULT_SOURCES = [
    'QQMusicClient',
    'NeteaseMusicClient',
    'KugouMusicClient',
    'KuwoMusicClient',
    # 'NewMusicClient'  # 在此添加
]
```

## 已知问题

- 某些平台可能有访问频率限制
- 下载速度因平台而异
- 并非所有歌曲在所有平台都可用

## 免责声明

本工具仅供个人学习使用，请支持正版音乐。下载的文件请勿用于商业用途。

## 许可证

MIT License

## 版本历史

### v1.0.0 (2025-12-25)

- 初始 PyQt5 版本
- 多平台音乐搜索
- 单曲和批量下载
- 进度跟踪
- 错误处理
- Windows 编码修复

---

**最后更新**: 2025-12-25
**版本**: 1.0.0

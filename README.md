# 音乐下载器

一个基于 Python 和 musicdl 的本地音乐下载工具，提供简洁的 Web 界面进行音乐搜索和下载。

## 项目状态

**新项目 - 从零开始构建**

## 功能目标

- **多平台搜索**：支持 QQ音乐、网易云、酷狗、酷我等主流音乐平台
- **在线预览**：搜索结果显示歌曲名、歌手、专辑、时长等详细信息
- **批量下载**：支持单曲下载和批量下载选中歌曲
- **实时进度**：显示下载进度条和详细状态
- **Web 界面**：简洁美观的响应式 Web 界面

## 技术栈

- **后端**: Python 3.7+ + Flask + musicdl
- **前端**: HTML5 + CSS3 + 原生 JavaScript (ES6+)
- **图标**: Font Awesome 6
- **模板引擎**: Jinja2

## 环境要求

- Python 3.7+
- pip

## 安装依赖

```bash
pip install musicdl flask
```

## 项目结构（规划中）

```
下载音乐软件/
├── app/                        # 源码目录
│   ├── __init__.py
│   ├── main.py                 # 程序入口
│   ├── core/                   # 核心下载逻辑
│   │   ├── __init__.py
│   │   └── downloader.py       # musicdl 封装
│   └── web/                    # Web 应用
│       ├── app.py              # Flask 应用
│       ├── templates/          # HTML 模板
│       │   ├── base.html
│       │   └── index.html
│       └── static/             # 静态资源
│           ├── css/
│           │   └── style.css
│           └── js/
│               └── main.js
├── config/                     # 配置文件
│   └── settings.json           # 下载路径、默认平台
├── downloads/                  # 下载的音乐文件
├── logs/                       # 日志文件
├── venv/                       # 虚拟环境
├── CLAUDE.md                   # Claude 开发指南
└── README.md                   # 项目说明
```

## 开发说明

详细的开发指南请参考 [CLAUDE.md](CLAUDE.md)

## 免责声明

- 本工具仅供个人学习使用
- 请支持正版音乐
- 下载的文件请勿用于商业用途

## 许可证

MIT License

# CLAUDE.md - 音乐下载器开发指南

## 项目概述

基于 **Flask + musicdl** 的本地音乐下载工具，提供 Web 界面进行音乐搜索和下载。

**当前状态**: 全新项目 - 从零开始

## 技术栈

- **后端**: Python 3.7+ / Flask / musicdl
- **前端**: HTML5 / CSS3 / 原生 JavaScript (ES6+)
- **架构**: 单页应用 + RESTful API

## 核心功能（按优先级）

1. **音乐搜索** - 搜索多平台音乐（QQ音乐、网易云、酷狗、酷我）
2. **下载功能** - 单曲下载和批量下载
3. **Web UI** - 简洁的搜索和下载界面
4. **进度显示** - 实时显示下载状态

## 项目结构

```
app/
├── __init__.py
├── main.py                 # 程序入口（支持 --web 参数）
├── core/
│   ├── __init__.py
│   └── downloader.py       # musicdl 封装类
└── web/
    ├── app.py              # Flask 应用和路由
    ├── templates/
    │   ├── base.html       # 基础模板
    │   └── index.html      # 主界面
    └── static/
        ├── css/
        │   └── style.css   # 样式文件
        └── js/
            └── main.js     # 前端逻辑
config/
└── settings.json           # 配置文件
downloads/                  # 下载目录
logs/                       # 日志目录
```

## API 端点设计

- `GET /` - 主页面
- `POST /api/search` - 搜索歌曲
  - 输入: `{keyword: string}`
  - 输出: `{results: [{song_name, singers, album, platform, ...}]}`
- `POST /api/download` - 下载歌曲
  - 输入: `{songs: array}`
  - 输出: `{success: boolean, message: string}`

## 关键技术点

### musicdl 库特性

1. **初始化**:
```python
from musicdl.musicdl import MusicClient
client = MusicClient(
    music_sources=['QQMusicClient', 'NeteaseMusicClient'],
    init_music_clients_cfg={
        'QQMusicClient': {'work_dir': 'downloads'}
    }
)
```

2. **搜索返回**: `{platform: [SongInfo, ...]}`
   - `SongInfo` 是**对象**，不是字典
   - 使用 `getattr(song, 'song_name', '')` 访问属性
   - **不要**使用 `song.get('song_name')`（这是字典方法）

3. **下载**: `client.download([song])`
   - 返回 `None`，无法通过返回值判断成功
   - 需要检查文件系统确认下载结果

### Windows 兼容性

1. **路径编码**: 避免中文路径
   - ❌ `os.path.join(os.getcwd(), "下载")`
   - ✅ 使用绝对路径：`r"D:\project\downloads"`

2. **控制台编码**: 避免中文 print
   - ❌ `print("创建中...")`
   - ✅ `print("Creating...")` 或使用日志文件

3. **路径分隔符**: 始终使用 `os.path.join()`

### Flask 最佳实践

1. **全局客户端**: 缓存 `MusicClient` 实例（单例模式）
```python
_music_client = None
_lock = threading.Lock()

def get_client():
    global _music_client
    if _music_client is None:
        with _lock:
            if _music_client is None:
                _music_client = MusicClient(...)
    return _music_client
```

2. **错误处理**: 不要暴露堆栈信息
```python
except Exception as e:
    # ❌ traceback.print_exc()
    # ✅ 记录日志并返回友好消息
    logger.error(f"Error: {e}")
    return {"error": str(e)}, 500
```

## 开发流程

### 第一步：核心封装

创建 `core/downloader.py`:
```python
class MusicDownloader:
    def __init__(self, download_dir):
        self.client = MusicClient(...)
        self.download_dir = download_dir

    def search(self, keyword):
        """搜索并返回统一格式"""
        results = self.client.search(keyword)
        # 转换 SongInfo 为字典
        return self._format_results(results)

    def download(self, songs):
        """下载歌曲"""
        self.client.download(songs)
```

### 第二步：Flask 应用

创建 `web/app.py`:
```python
app = Flask(__name__)
downloader = MusicDownloader('downloads')

@app.route('/api/search', methods=['POST'])
def search():
    keyword = request.json.get('keyword')
    results = downloader.search(keyword)
    return jsonify(results)
```

### 第三步：前端界面

创建 `templates/index.html`:
- 简洁的搜索表单
- 结果列表展示
- 下载按钮

### 第四步：集成测试

1. 使用 curl 测试 API
2. 使用浏览器测试 UI
3. 验证下载文件

## 测试策略

### 单元测试（可选）
```python
# test_downloader.py
def test_search():
    downloader = MusicDownloader('test_downloads')
    results = downloader.search('周杰伦')
    assert len(results) > 0
```

### 手动测试
```bash
# 测试 musicdl 直接调用
python -c "from musicdl.musicdl import MusicClient; c = MusicClient(); print(c.search('test'))"

# 测试 Flask API
curl -X POST http://127.0.0.1:5000/api/search -H "Content-Type: application/json" -d '{"keyword":"test"}'
```

## 常见问题

### Q: 搜索结果显示为 UUID？
**A**: SongInfo 对象被当作字典访问了。使用 `getattr()` 而不是 `.get()`

### Q: Windows 路径错误？
**A**: 避免中文路径和 `os.getcwd()`，使用绝对路径

### Q: 中文显示乱码？
**A**: 确保 HTML 使用 UTF-8 编码：`<meta charset="UTF-8">`

### Q: 下载后找不到文件？
**A**: 检查 `work_dir` 配置，使用绝对路径

## 配置文件

`config/settings.json`:
```json
{
  "download_path": "D:\\code\\downloads",
  "default_platforms": ["QQMusicClient", "NeteaseMusicClient"],
  "max_results": 50,
  "log_file": "logs/musicdl.log"
}
```

## 开发原则

1. **简单优先**: 先实现核心功能，避免过度设计
2. **小步迭代**: 每个功能都要测试验证
3. **错误友好**: 捕获异常，返回清晰错误信息
4. **日志记录**: 使用日志代替 print
5. **Windows 兼容**: 注意路径和编码问题

## 命令速查

```bash
# 安装依赖
pip install musicdl flask

# 运行应用
python -m app.main --web

# 测试 API
curl -X POST http://127.0.0.1:5000/api/search -d '{"keyword":"周杰伦"}'

# 查看日志
tail -f logs/musicdl.log
```

## 版本管理

更新 VERSION 文件：
- 0.1.0: 基础搜索功能
- 0.2.0: 添加下载功能
- 0.3.0: Web UI 完善

---

**最后更新**: 2025-12-25
**版本**: 1.0.0 (全新开始)

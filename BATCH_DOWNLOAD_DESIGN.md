# 批量下载功能 - 系统设计文档

## 1. 概述

本文档定义了音乐下载器批量下载功能的系统架构设计。

### 1.1 功能需求

1. **模式切换**：支持单曲下载模式和批量下载模式切换
2. **批量输入**：支持输入最多200首歌曲，格式为"歌名-歌手"，每行一首
3. **智能搜索**：按平台优先级顺序搜索，每首歌只返回第一个匹配结果
4. **结果展示**：批量模式以表格形式展示，每首歌一行，支持勾选
5. **批量下载**：支持批量下载勾选的歌曲，自动检查并跳过重复文件

### 1.2 技术栈

- **GUI框架**: PyQt6
- **核心库**: MusicDL (现有)
- **语言**: Python 3.8+
- **架构模式**: MVC + Worker Thread

---

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     MainWindow (UI Layer)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Mode Tab  │  │ Search Area │  │Result Table │         │
│  │  (新增)     │  │  (改造)     │  │  (改造)     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Controller Layer                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ModeController│  │SearchController│  │BatchController│     │
│  │   (新增)     │  │   (改造)     │  │   (新增)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Threads                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │SearchWorker  │  │BatchSearchWorker│ │DownloadWorker│     │
│  │  (现有)      │  │    (新增)     │  │  (改造)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Layer                                │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │MusicDownloader│  │ BatchParser │  │DuplicateChecker│     │
│  │  (现有)      │  │   (新增)     │  │   (新增)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

#### 2.2.1 单曲模式流程（保持不变）

```
用户输入关键词 → 点击搜索
    ↓
SearchWorker.search() → 所有选中平台并行搜索
    ↓
返回所有平台的多个匹配结果
    ↓
显示结果表格（每个结果一行）
    ↓
用户勾选 → 点击下载
    ↓
DownloadWorker.download() → 下载
```

#### 2.2.2 批量模式流程（新增）

```
用户切换到批量模式
    ↓
用户输入多行歌曲（每行"歌名-歌手"）
    ↓
点击搜索 → BatchParser解析输入
    ↓
BatchSearchWorker依次处理每首歌:
  For 每首歌:
    For 每个平台（按优先级）:
      搜索 → 匹配度检查
      If 找到匹配:
        使用该结果 → Break
    Next 平台
  Next 歌曲
    ↓
返回批量结果（每首歌一个匹配）
    ↓
显示批量结果表格（可勾选）
    ↓
用户调整勾选 → 点击批量下载
    ↓
DuplicateChecker检查重复
    ↓
DownloadWorker批量下载（跳过重复）
```

---

## 3. UI设计

### 3.1 模式切换区域

**位置**: 顶部，音乐源选择之前

```python
# Mode Tab Widget
┌─────────────────────────────────────────┐
│ [单曲下载]  [批量下载]                   │
└─────────────────────────────────────────┘
```

**组件**:
- `QTabWidget` 或 两个 `QRadioButton` + `QStackedWidget`
- 推荐: `QRadioButton` + `QStackedWidget` (更灵活)

### 3.2 单曲模式UI（现有）

```
┌─────────────────────────────────────────┐
│ Music Sources: [☑全选] [☑QQ] [☑网易云] │
├─────────────────────────────────────────┤
│ [输入框: 歌名 歌手        ] [搜索按钮]  │
├─────────────────────────────────────────┤
│ [进度条]                                 │
│ 状态信息                                 │
├─────────────────────────────────────────┤
│ 搜索结果表格（所有结果）                 │
│ ☐ | # | 歌名 | 歌手 | 专辑 | ...        │
└─────────────────────────────────────────┘
```

### 3.3 批量模式UI（新增）

```
┌─────────────────────────────────────────┐
│ Music Sources: [☑全选] [☑QQ] [☑网易云] │
│ (注：顺序代表搜索优先级)                 │
├─────────────────────────────────────────┤
│ 批量输入区域:                            │
│ ┌───────────────────────────────────┐   │
│ │ 没关系 - 容祖儿                     │   │
│ │ 告白气球 - 周杰伦                   │   │
│ │ ...                                │   │
│ │ (最多200首，每行一首，格式：歌名-歌手) │   │
│ └───────────────────────────────────┘   │
│           [搜索] [清空] [导入示例]       │
├─────────────────────────────────────────┤
│ [进度条] 显示：正在搜索 3/10 首歌曲...    │
├─────────────────────────────────────────┤
│ 批量搜索结果:                            │
│ ┌─────────────────────────────────────┐ │
│ │ [批量下载已选] [全选] [取消全选]    │ │
│ ├─────────────────────────────────────┤ │
│ │☐│歌名│歌手│匹配平台│匹配结果│状态│ │ │
│ │☐│没关│容祖│网易云 │没关系(live)│待下载│ │ │
│ │☐│告白│周杰伦│QQ│告白气球│待下载│ │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**组件定义**:
```python
# 批量输入区域
batch_input_text = QTextEdit()
batch_input_text.setPlaceholderText(
    "请输入歌曲列表，每行一首，格式：歌名-歌手\n"
    "最多支持200首\n\n"
    "示例：\n"
    "没关系 - 容祖儿\n"
    "告白气球 - 周杰伦"
)
batch_input_text.setMaximumHeight(200)

# 按钮组
clear_btn = QPushButton("清空")
import_example_btn = QPushButton("导入示例")
search_btn = QPushButton("批量搜索")

# 批量结果表格
batch_results_table = QTableWidget()
batch_results_table.setColumnCount(7)
batch_results_table.setHorizontalHeaderLabels([
    '☐', '#', '歌名', '歌手', '匹配平台', '匹配结果', '状态'
])

# 批量操作按钮
batch_download_btn = QPushButton("批量下载已选")
select_all_btn = QPushButton("全选")
unselect_all_btn = QPushButton("取消全选")
```

---

## 4. 模块划分

### 4.1 新增模块

```
pyqt_ui/
├── main.py                 (改造 - 添加批量模式UI)
├── workers.py              (改造 - 添加BatchSearchWorker)
├── music_downloader.py     (保持)
├── batch/                  (新增目录)
│   ├── __init__.py
│   ├── parser.py           (批量输入解析)
│   ├── matcher.py          (智能匹配算法)
│   └── duplicate.py        (重复检查)
├── ui/                     (新增目录 - UI组件)
│   ├── __init__.py
│   ├── batch_tab.py        (批量模式标签页)
│   └── single_tab.py       (单曲模式标签页 - 重构)
└── config.py               (扩展 - 添加批量模式配置)
```

### 4.2 核心模块设计

#### 4.2.1 batch/parser.py

**功能**: 解析批量输入文本

```python
class BatchParser:
    """批量输入解析器"""

    MAX_SONGS = 200

    @staticmethod
    def parse(text: str) -> List[Dict[str, str]]:
        """
        解析批量输入文本

        Args:
            text: 多行文本，格式："歌名-歌手"

        Returns:
            [{"name": "歌名", "singer": "歌手"}, ...]

        Raises:
            ValueError: 超过最大数量或格式错误
        """
        lines = [line.strip() for line in text.strip().split('\n')]
        lines = [line for line in lines if line]  # 移除空行

        if len(lines) > BatchParser.MAX_SONGS:
            raise ValueError(
                f"超过最大数量限制 ({BatchParser.MAX_SONGS}首)"
            )

        songs = []
        for i, line in enumerate(lines, 1):
            try:
                # 支持 "歌名-歌手" 或 "歌名 歌手"
                if ' - ' in line:
                    name, singer = line.split(' - ', 1)
                elif ' -' in line:
                    name, singer = line.split(' -', 1)
                elif '- ' in line:
                    name, singer = line.split('- ', 1)
                elif '-' in line:
                    name, singer = line.split('-', 1)
                else:
                    # 尝试按空格分割
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        name, singer = parts
                    else:
                        raise ValueError(f"无法解析: {line}")

                songs.append({
                    'name': name.strip(),
                    'singer': singer.strip(),
                    'original_line': line
                })
            except Exception as e:
                raise ValueError(f"第{i}行格式错误: {line}")

        return songs
```

#### 4.2.2 batch/matcher.py

**功能**: 智能匹配算法

```python
class SongMatcher:
    """歌曲智能匹配器"""

    # 匹配度阈值
    SIMILARITY_THRESHOLD = 0.6

    @staticmethod
    def calculate_similarity(query: str, result: str) -> float:
        """
        计算查询和结果的相似度

        Args:
            query: 查询文本
            result: 搜索结果文本

        Returns:
            0.0 ~ 1.0 的相似度分数
        """
        from difflib import SequenceMatcher

        # 归一化处理
        query_norm = SongMatcher._normalize_text(query)
        result_norm = SongMatcher._normalize_text(result)

        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, query_norm, result_norm).ratio()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """归一化文本"""
        # 移除特殊字符、空格、统一大小写
        import re
        text = text.lower()
        text = re.sub(r'[^\w]', '', text)
        return text

    @staticmethod
    def is_match(name_query: str, singer_query: str,
                 name_result: str, singer_result: str) -> bool:
        """
        判断是否为匹配结果

        Args:
            name_query: 查询的歌名
            singer_query: 查询的歌手
            name_result: 搜索结果的歌名
            singer_result: 搜索结果的歌手

        Returns:
            True if 匹配
        """
        # 检查歌名相似度
        name_sim = SongMatcher.calculate_similarity(
            name_query, name_result
        )

        # 检查歌手相似度
        singer_sim = SongMatcher.calculate_similarity(
            singer_query, singer_result
        )

        # 综合判断（歌名权重更高）
        return (
            name_sim >= SongMatcher.SIMILARITY_THRESHOLD and
            singer_sim >= SongMatcher.SIMILARITY_THRESHOLD * 0.5
        )
```

#### 4.2.3 batch/duplicate.py

**功能**: 重复文件检查

```python
import os
from pathlib import Path
from typing import Set, List

class DuplicateChecker:
    """重复文件检查器"""

    @staticmethod
    def check_duplicates(songs: List[Dict],
                        download_dir: Path) -> Set[int]:
        """
        检查哪些歌曲已存在

        Args:
            songs: 歌曲列表
            download_dir: 下载目录

        Returns:
            Set of indices (重复歌曲的索引集合)
        """
        # 获取已存在的文件名
        existing_files = set()
        if download_dir.exists():
            for f in download_dir.iterdir():
                if f.is_file():
                    existing_files.add(DuplicateChecker._normalize_filename(f.name))

        # 检查每首歌
        duplicates = set()
        for i, song in enumerate(songs):
            expected_name = DuplicateChecker._generate_filename(song)
            expected_norm = DuplicateChecker._normalize_filename(expected_name)

            # 精确匹配
            if expected_norm in existing_files:
                duplicates.add(i)

        return duplicates

    @staticmethod
    def _generate_filename(song: Dict) -> str:
        """生成期望的文件名"""
        name = song.get('name', 'Unknown')
        singer = song.get('singer', 'Unknown')
        return f"{name} - {singer}"

    @staticmethod
    def _normalize_filename(filename: str) -> str:
        """归一化文件名（用于比较）"""
        import re
        # 移除扩展名
        name = os.path.splitext(filename)[0]
        # 移除特殊字符和空格
        name = name.lower()
        name = re.sub(r'[^\w]', '', name)
        return name
```

---

## 5. 核心函数接口

### 5.1 BatchSearchWorker (workers.py)

```python
class BatchSearchWorker(QThread):
    """批量搜索Worker线程"""

    # Signals
    batch_search_started = pyqtSignal(int)  # 总数
    batch_search_progress = pyqtSignal(int, str)  # 当前索引, 歌曲信息
    batch_search_finished = pyqtSignal(list)  # 批量结果
    batch_search_error = pyqtSignal(str)

    def __init__(self, songs: List[Dict], sources: List[str]):
        """
        Args:
            songs: [{"name": "", "singer": ""}, ...]
            sources: 按优先级排序的平台列表
        """
        super().__init__()
        self.songs = songs
        self.sources = sources
        self.downloader = MusicDownloader()
        self.matcher = SongMatcher()

    def run(self):
        """执行批量搜索"""
        try:
            self.batch_search_started.emit(len(self.songs))

            results = []

            for i, song in enumerate(self.songs):
                self.batch_search_progress.emit(
                    i,
                    f"搜索: {song['name']} - {song['singer']}"
                )

                # 按平台顺序搜索
                matched = None
                for source in self.sources:
                    # 搜索单个平台
                    search_results = self.downloader.search(
                        f"{song['name']} {song['singer']}",
                        [source]
                    )

                    # 检查匹配
                    if search_results and source in search_results:
                        songs_from_source = search_results[source]
                        for result in songs_from_source:
                            if self.matcher.is_match(
                                song['name'], song['singer'],
                                result['song_name'], result['singers']
                            ):
                                matched = result
                                break

                    if matched:
                        break

                # 添加到结果（无论是否找到）
                results.append({
                    'query': song,
                    'result': matched,  # None if 未找到
                    'status': 'found' if matched else 'not_found'
                })

            self.batch_search_finished.emit(results)

        except Exception as e:
            self.batch_search_error.emit(str(e))
```

### 5.2 ModeController (main.py)

```python
class ModeController:
    """模式切换控制器"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.current_mode = 'single'  # 'single' or 'batch'

    def switch_mode(self, mode: str):
        """切换模式"""
        self.current_mode = mode

        if mode == 'single':
            self.main_window.show_single_mode()
        else:
            self.main_window.show_batch_mode()
```

---

## 6. 数据结构

### 6.1 批量搜索结果数据结构

```python
# 单个批量搜索结果
{
    "query": {
        "name": "没关系",
        "singer": "容祖儿",
        "original_line": "没关系 - 容祖儿"
    },
    "result": {
        "song_name": "没关系 (live版)",
        "singers": "容祖儿",
        "album": "...",
        "file_size": "...",
        "duration": "...",
        "source": "NeteaseMusicClient",
        "ext": "mp3",
        "song_info_obj": <SongInfo object>
    },
    "status": "found"  # or "not_found"
}
```

### 6.2 批量下载任务数据结构

```python
{
    "results": [...],  # 批量搜索结果列表
    "selected_indices": [0, 2, 5, ...],  # 用户勾选的索引
    "duplicate_indices": [1, 3],  # 重复的索引
    "target_dir": Path("musicdl_outputs/")
}
```

---

## 7. 配置扩展 (config.py)

```python
# 批量模式配置
BATCH_MAX_SONGS = 200
BATCH_MATCH_SIMILARITY_THRESHOLD = 0.6

# UI Labels
MODE_LABELS = {
    'single': '单曲下载',
    'batch': '批量下载'
}

# Batch status labels
BATCH_STATUS_LABELS = {
    'found': '已找到',
    'not_found': '未找到',
    'duplicate': '重复',
    'downloading': '下载中',
    'completed': '已完成',
    'failed': '失败'
}
```

---

## 8. 错误处理

### 8.1 输入验证

```python
# BatchParser.parse() 错误处理
try:
    songs = BatchParser.parse(batch_input_text)
except ValueError as e:
    QMessageBox.warning(
        self,
        "输入错误",
        str(e)
    )
```

### 8.2 搜索失败处理

```python
# BatchSearchWorker 部分失败处理
for i, result in enumerate(results):
    if result['status'] == 'not_found':
        # 在表格中标记为"未找到"
        # 用户可以选择跳过或重试
```

### 8.3 下载失败处理

```python
# DownloadWorker 改进
for i, song in enumerate(songs):
    try:
        # 下载单个文件
        self.downloader.download([song])
        success.append(song)
    except Exception as e:
        failed.append((song, str(e)))

# 最后报告成功和失败
```

---

## 9. 实现步骤

### Phase 1: 基础架构 (Day 1-2)
1. ✅ 创建batch模块目录结构
2. ✅ 实现BatchParser
3. ✅ 实现SongMatcher
4. ✅ 实现DuplicateChecker
5. ✅ 扩展config.py配置

### Phase 2: UI组件 (Day 3-4)
6. ✅ 实现ModeController
7. ✅ 创建批量模式标签页UI
8. ✅ 重构单曲模式为独立标签页
9. ✅ 实现UI切换逻辑

### Phase 3: Worker线程 (Day 5)
10. ✅ 实现BatchSearchWorker
11. ✅ 改进DownloadWorker支持批量

### Phase 4: 业务逻辑 (Day 6-7)
12. ✅ 实现批量搜索流程
13. ✅ 实现批量结果展示
14. ✅ 实现勾选/全选逻辑
15. ✅ 实现重复检查
16. ✅ 实现批量下载

### Phase 5: 测试和优化 (Day 8)
17. ✅ 单元测试
18. ✅ 集成测试
19. ✅ UI测试
20. ✅ 性能优化

---

## 10. 风险和注意事项

### 10.1 性能风险
- **风险**: 批量搜索可能触发API限流
- **缓解**:
  - 添加搜索延迟（每首歌间隔1-2秒）
  - 提供并发控制配置
  - 显示搜索进度，允许用户取消

### 10.2 用户体验风险
- **风险**: 批量下载时间较长，用户焦虑
- **缓解**:
  - 实时显示详细进度
  - 允许后台运行
  - 支持暂停/恢复

### 10.3 数据一致性风险
- **风险**: 重复检查误判
- **缓解**:
  - 提供用户配置选项（严格/宽松模式）
  - 支持手动覆盖

---

## 11. 后续优化方向

1. **导入/导出功能**:
   - 支持从文件导入歌曲列表
   - 支持导出搜索结果

2. **历史记录**:
   - 保存批量搜索历史
   - 快速重新下载

3. **高级匹配**:
   - 支持自定义匹配规则
   - 支持模糊搜索阈值调整

4. **批量编辑**:
   - 支持批量修改歌曲信息
   - 支持批量删除结果

---

## 12. 附录

### 12.1 相关文件
- 主设计文档: `BATCH_DOWNLOAD_DESIGN.md`
- API文档: `API_REFERENCE.md` (待创建)
- 测试计划: `TEST_PLAN.md` (待创建)

### 12.2 参考资料
- PyQt6官方文档
- MusicDL文档
- Python最佳实践

---

**文档版本**: 1.0
**创建日期**: 2025-12-26
**最后更新**: 2025-12-26
**作者**: Claude (AI Design Assistant)

#!/usr/bin/env python3
"""测试 musicdl 基本功能"""
from musicdl.musicdl import MusicClient
import os

# 配置下载目录（可自定义）
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 创建客户端
print("初始化 MusicClient...")
client = MusicClient(
    music_sources=['QQMusicClient'],  # 先用一个平台测试
    init_music_clients_cfg={
        'QQMusicClient': {
            'work_dir': DOWNLOAD_DIR
        }
    }
)

# 测试搜索
keyword = "晴天"
print(f"\n搜索: {keyword}")
results = client.search(keyword)

print(f"\n找到 {len(results)} 个平台的结果")

# 显示前 3 个结果
for platform, songs in results.items():
    if songs and len(songs) > 0:
        print(f"\n{platform} 平台:")
        for i, song in enumerate(songs[:3]):
            print(f"  {i+1}. {song.get('song_name')} - {song.get('singers')}")

# 下载第一首歌
if results:
    first_platform = list(results.keys())[0]
    first_song = results[first_platform][0]

    print(f"\n开始下载: {first_song.get('song_name')}")
    client.download([first_song])

    # 等待下载完成
    print("等待下载完成...")
    import time
    time.sleep(15)

    # 检查下载的文件
    import glob
    pattern = os.path.join(DOWNLOAD_DIR, first_platform, '*', '*.*')
    files = glob.glob(pattern)
    # 过滤掉 .pkl 文件
    music_files = [f for f in files if not f.endswith('.pkl')]

    if music_files:
        for f in music_files:
            size = os.path.getsize(f)
            print(f"下载完成: {os.path.basename(f)} (大小: {size} 字节)")
        print(f"下载目录: {DOWNLOAD_DIR}")
    else:
        print(f"错误: 未找到下载的文件!")
        print(f"搜索路径: {pattern}")
        # 列出 downloads 目录下的所有内容
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            level = root.replace(DOWNLOAD_DIR, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                fpath = os.path.join(root, file)
                size = os.path.getsize(fpath)
                print(f'{subindent}{file} ({size} bytes)')

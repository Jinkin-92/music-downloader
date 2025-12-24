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
        'work_dir': DOWNLOAD_DIR
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
    print(f"下载完成！请检查 {DOWNLOAD_DIR} 目录")

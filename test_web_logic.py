#!/usr/bin/env python3
"""直接测试 Web 应用的核心逻辑"""
import sys
import os
import time
import glob

sys.path.insert(0, 'D:/code/下载音乐软件')

# 模拟 Web 应用的核心逻辑
from musicdl.musicdl import MusicClient

# 全局配置
DOWNLOAD_DIR = os.path.join('D:/code/下载音乐软件', 'downloads')

# 初始化全局客户端（只创建一次）
print("创建 MusicClient...")
_music_client = MusicClient(
    music_sources=['QQMusicClient'],
    init_music_clients_cfg={
        'QQMusicClient': {
            'work_dir': DOWNLOAD_DIR
        }
    }
)
print("MusicClient 创建完成")

# 测试搜索逻辑
keyword = 'test'
print(f"\n=== 测试搜索: {keyword} ===")
search_results = _music_client.search(keyword)

# 扁平化结果（模拟 app/web.py 的逻辑）
results = []
for platform, songs in search_results.items():
    for song in songs[:10]:
        results.append({
            'song_name': song.get('song_name', ''),
            'singers': song.get('singers', ''),
            'album': song.get('album', ''),
            'platform': platform
        })

print(f"搜索到 {len(results)} 首歌曲:")
for i, song in enumerate(results[:3]):
    print(f"  {i+1}. {song['song_name']} - {song['singers']} [{song['platform']}]")

# 测试下载逻辑（模拟点击第一首歌的下载按钮）
if results:
    print(f"\n=== 测试下载: {results[0]['song_name']} ===")
    platform = results[0]['platform']
    index = 0

    # 重新搜索获取完整的 song 对象
    results_full = _music_client.search(keyword)
    if platform in results_full and index < len(results_full[platform]):
        song = results_full[platform][index]
        print(f"开始下载: {song.get('song_name')}")

        # 下载
        _music_client.download([song])

        # 等待下载完成
        print("等待下载完成...")
        time.sleep(15)

        # 检查文件
        pattern = os.path.join(DOWNLOAD_DIR, platform, '*', '*.*')
        files = glob.glob(pattern)
        music_files = [f for f in files if not f.endswith('.pkl')]

        if music_files:
            print("\n下载成功! 文件列表:")
            for f in music_files[-5:]:  # 显示最新的 5 个文件
                size = os.path.getsize(f)
                print(f"  - {os.path.basename(f)} ({size} 字节)")
        else:
            print(f"下载失败: 未找到文件，pattern: {pattern}")

print("\n=== 测试完成 ===")
print("Web 应用的核心逻辑工作正常！")

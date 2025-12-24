#!/usr/bin/env python3
"""测试 Flask + musicdl 基本兼容性"""
from flask import Flask
from musicdl.musicdl import MusicClient
import os

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.getcwd(), "test_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 预先创建全局客户端（只创建一次）
print("初始化 MusicClient...")
client = MusicClient(
    music_sources=['QQMusicClient'],
    init_music_clients_cfg={
        'QQMusicClient': {
            'work_dir': DOWNLOAD_DIR
        }
    }
)
print("初始化完成")

@app.route('/test')
def test():
    """简单测试页面"""
    return '<h1>Flask 正常运行</h1><a href="/search/test">搜索 test</a>'

@app.route('/search/<keyword>')
def search(keyword):
    """搜索 API"""
    try:
        print(f"搜索: {keyword}")
        results = client.search(keyword)

        # 简单返回前3首
        songs = []
        for platform, song_list in results.items():
            for song in song_list[:3]:
                songs.append({
                    'name': song.get('song_name', ''),
                    'singer': song.get('singers', ''),
                    'url': f"/download/{platform}/{song_list.index(song)}"
                })

        return {'songs': songs}
    except Exception as e:
        return {'error': str(e)}

@app.route('/download/<platform>/<int:index>')
def download(platform, index):
    """下载 API（同步，简单测试）"""
    try:
        results = client.search("test")
        if platform in results and index < len(results[platform]):
            song = results[platform][index]
            print(f"下载: {song.get('song_name')}")

            # 下载
            client.download([song])

            # 等待更长时间确保下载完成
            import time
            time.sleep(15)

            # 检查文件
            import glob
            pattern = os.path.join(DOWNLOAD_DIR, platform, '*', '*.*')
            files = glob.glob(pattern)
            music_files = [f for f in files if not f.endswith('.pkl')]

            if music_files:
                return f"下载成功: {os.path.basename(music_files[0])}"
            else:
                return f"下载失败: 未找到文件，pattern: {pattern}"

        return "下载失败: 歌曲不存在"
    except Exception as e:
        return f"下载失败: {str(e)}"

if __name__ == '__main__':
    print("启动测试服务器...")
    print("访问 http://127.0.0.1:5555/test")
    app.run(host='127.0.0.1', port=5555, debug=False)

from flask import Flask, render_template, request
from musicdl.musicdl import MusicClient
import os
import time
import threading

app = Flask(__name__)

# 全局下载目录配置
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 全局 MusicClient 单例（只初始化一次）
_music_client = None
_client_lock = threading.Lock()

def get_music_client():
    """获取全局 MusicClient 单例"""
    global _music_client
    if _music_client is None:
        with _client_lock:
            if _music_client is None:
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
    return _music_client

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None

    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()

        if not keyword:
            error = '请输入搜索关键词'
        else:
            try:
                client = get_music_client()  # 使用全局客户端
                search_results = client.search(keyword)

                # 扁平化结果
                results = []
                for platform, songs in search_results.items():
                    for song in songs[:10]:  # 每平台最多10首
                        results.append({
                            'song_name': song.get('song_name', ''),
                            'singers': song.get('singers', ''),
                            'album': song.get('album', ''),
                            'platform': platform
                        })

            except Exception as e:
                error = f'搜索失败: {str(e)}'

    return render_template('index.html', results=results, error=error)

@app.route('/download/<platform>/<int:index>')
def download(platform, index):
    try:
        # 从查询参数获取关键词重新搜索
        keyword = request.args.get('keyword', '')
        if not keyword:
            return "缺少关键词", 400

        client = get_music_client()
        results = client.search(keyword)

        # 找到要下载的歌曲
        if platform in results and index < len(results[platform]):
            song = results[platform][index]
            print(f"下载: {song.get('song_name')}")
            client.download([song])

            # 等待下载完成
            time.sleep(15)

            # 检查文件
            import glob
            pattern = os.path.join(DOWNLOAD_DIR, platform, '*', '*.*')
            files = glob.glob(pattern)
            music_files = [f for f in files if not f.endswith('.pkl')]

            if music_files:
                filename = os.path.basename(music_files[0])
                return f"下载成功: {filename}<br><a href='/'>返回</a>"
            else:
                return f"下载失败: 未找到文件，pattern: {pattern}<br><a href='/'>返回</a>"

        return "下载失败", 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"下载失败: {str(e)}<br><a href='/'>返回</a>", 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

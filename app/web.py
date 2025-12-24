from flask import Flask, render_template, request
from musicdl.musicdl import MusicClient
import os
import time

app = Flask(__name__)

# 全局 MusicClient（只初始化一次）
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
                # 每次请求创建新客户端（简单但慢）
                client = MusicClient(
                    music_sources=['QQMusicClient'],
                    init_music_clients_cfg={'work_dir': DOWNLOAD_DIR}
                )
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

        client = MusicClient(
            music_sources=['QQMusicClient'],
            init_music_clients_cfg={'work_dir': DOWNLOAD_DIR}
        )
        results = client.search(keyword)

        # 找到要下载的歌曲
        if platform in results and index < len(results[platform]):
            song = results[platform][index]
            print(f"下载: {song.get('song_name')}")
            client.download([song])
            time.sleep(2)  # 等待下载完成
            return f"下载完成: {song.get('song_name')} - 请检查 {DOWNLOAD_DIR} 目录"

        return "下载失败", 404

    except Exception as e:
        return f"下载失败: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

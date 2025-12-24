from flask import Flask, render_template, request
from musicdl.musicdl import MusicClient
import os

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

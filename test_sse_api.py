#!/usr/bin/env python
"""测试SSE API"""
import asyncio
import httpx
import json
from urllib.parse import quote, urlencode

async def test():
    print("Starting SSE test...")
    songs = [{'name': '夜曲', 'artist': '周杰伦'}]
    # Use UTF-8 JSON and properly URL encode it
    songs_json_utf8 = json.dumps(songs, ensure_ascii=False)
    print(f"UTF-8 JSON: {songs_json_utf8}")

    # URL encode the JSON string
    songs_json_encoded = quote(songs_json_utf8, safe='')
    print(f"URL encoded: {songs_json_encoded}")

    # Build URL with properly encoded parameter
    base_url = 'http://localhost:8002/api/playlist/batch-search-stream'
    url = f"{base_url}?songs_json={songs_json_encoded}&sources=KuwoMusicClient&concurrency=2"

    print(f"Full URL: {url}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream('GET', url) as response:
            print(f"Response status: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith('data:'):
                    try:
                        data = json.loads(line[5:])
                        print(f"Data: {json.dumps(data, ensure_ascii=False)}")
                    except:
                        print(f"Raw data: {line[5:]}")
                elif line.startswith('event:'):
                    print(f"Event: {line[6:]}")

if __name__ == '__main__':
    asyncio.run(test())

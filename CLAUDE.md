# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **NEW** music download software project based on Python Flask and the `musicdl` library. The project will provide a Web interface for searching and downloading music from multiple platforms.

**Current Status**: Starting from scratch - no code implementation yet.

## Project Goals

### Core Features (Priority Order)
1. **Music Search** - Search across multiple platforms (QQ Music, Netease, Kugou, Kuwo)
2. **Download Function** - Download individual songs or batch downloads
3. **Web UI** - Clean and responsive interface for search and download
4. **Progress Display** - Show download progress and status in real-time

## Technical Stack

### Backend
- **Language**: Python 3.7+
- **Framework**: Flask (lightweight web framework)
- **Music Library**: musicdl (multi-platform music downloader)
- **Architecture**: RESTful API + single page application

### Frontend
- **Language**: HTML5, CSS3, JavaScript (ES6+)
- **Style**: Custom CSS (no framework)
- **Icons**: Font Awesome 6
- **Communication**: Fetch API for async requests

## Planned Architecture

### File Structure
```
app/
├── __init__.py
├── main.py                 # Entry point with --web flag
├── core/
│   ├── __init__.py
│   └── downloader.py       # MusicDownloader wrapper class
└── web/
    ├── app.py              # Flask application & routes
    ├── templates/
    │   ├── base.html       # Base template with common layout
    │   └── index.html      # Main search/download interface
    └── static/
        ├── css/
        │   └── style.css   # Main stylesheet
        └── js/
            └── main.js     # Frontend logic
```

### API Endpoints (Planned)
- `GET /` - Serve main page
- `POST /api/search` - Search for songs
  - Input: `{keywords: string, platforms: array}`
  - Output: `{results: array}`
- `POST /api/download` - Download songs
  - Input: `{songs: array}`
  - Output: `{success: boolean, message: string}`
- `GET /api/status/<task_id>` - Get download status (optional for progress tracking)

## Design Principles

### 1. Simplicity First
- Start with minimum viable product
- Focus on core functionality (search + download)
- Avoid over-engineering
- Use vanilla JavaScript instead of frameworks

### 2. Modular Architecture
- Separate concerns (core logic vs web interface)
- Reusable downloader class
- Clean API boundaries

### 3. Error Handling
- Graceful degradation when platforms fail
- User-friendly error messages
- Comprehensive logging for debugging

### 4. Performance Considerations
- Cache MusicClient instance (avoid re-initialization)
- Async operations for I/O
- Efficient database/file handling

## Known Challenges (From Previous Experience)

### Windows Compatibility Issues
1. **Encoding Problem**: Windows console uses GBK encoding
   - Solution: Avoid Chinese characters in print statements
   - Use ASCII-only console output or redirect to file

2. **File Path Issues**: Windows uses backslashes
   - Solution: Always use `os.path.join()` for paths
   - Handle path separators carefully

3. **Flask + musicdl Compatibility**: May have conflicts
   - Solution: Use subprocess isolation if needed
   - Test search and download separately before integration

### musicdl Library Specifics
1. **Search Returns Nested Dict**: `{platform: [SongInfo, ...]}`
2. **Download Returns None**: Cannot rely on return value for success check
3. **SongInfo Object**: Use `getattr()` to safely access attributes

## Development Workflow

1. **Setup Phase**
   - Create project structure
   - Install dependencies (musicdl, flask)
   - Test musicdl independently

2. **Core Logic First**
   - Implement `MusicDownloader` class
   - Test search functionality (CLI)
   - Test download functionality (CLI)

3. **Web Layer**
   - Create basic Flask app
   - Implement search API
   - Implement download API
   - Test with curl/Postman

4. **Frontend**
   - Build HTML structure
   - Add CSS styling
   - Implement JavaScript interaction
   - Test full workflow

5. **Integration Testing**
   - End-to-end testing
   - Error handling
   - Edge cases

## Testing Strategy

### Unit Testing
- Test `MusicDownloader` methods independently
- Mock musicdl responses if needed

### Integration Testing
- Test Flask routes with test client
- Verify API contracts

### Manual Testing
- Test search with various keywords
- Test download of different platforms
- Verify file outputs

## Configuration

### settings.json (Planned)
```json
{
  "log_path": "logs/musicdl.log",
  "download_path": "downloads",
  "default_platforms": ["qq", "netease", "kugou", "kuwo"],
  "max_results": 50
}
```

## Common Commands

```bash
# Install dependencies
pip install musicdl flask

# Run application (when implemented)
python -m app.main --web

# Test musicdl directly
python -c "from musicdl.musicdl import MusicClient; client = MusicClient(); print(client.search('周杰伦'))"
```

## Important Notes

1. **Start Simple**: Don't build all features at once
2. **Test Incrementally**: Verify each component before moving to next
3. **Document Decisions**: Note why certain approaches are chosen
4. **Handle Errors**: Always use try-except blocks
5. **Windows Caution**: Be aware of platform-specific issues

## Version Management

When implementing features:
1. Update VERSION file
2. Document changes in README.md
3. Tag releases in git (when ready)

---

**Last Updated**: 2025-12-24 (Project Reset - Starting from Scratch)

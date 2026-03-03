# PyQt6 音乐下载器 - Docker 镜像
# 多平台支持：使用 VNC Server 提供 GUI 访问

FROM python:3.12-slim

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=xcb

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # Qt6 依赖
    libqt6svg6 \
    libqt6widgets6 \
    libqt6gui6 \
    libqt6core6 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    # X11 和 VNC 依赖
    x11vnc \
    xvfb \
    xvfb \
    fluxbox \
    # 其他工具
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY pyqt_ui/ ./pyqt_ui/
COPY README.md .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/musicdl_outputs /app/logs

# 暴露 VNC 端口（5901 = Display :1）
EXPOSE 5901

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 启动 Xvfb（虚拟帧缓冲）\n\
Xvfb :1 -screen 0 1024x768x24 &\n\
\n\
# 启动 Fluxbox 窗口管理器\n\
DISPLAY=:1 fluxbox &\n\
\n\
# 启动 x11vnc（无密码）\n\
x11vnc -display :1 -forever -nopw &\n\
\n\
# 等待 X server 启动\n\
sleep 2\n\
\n\
echo "==========================================="\n\
echo "PyQt6 音乐下载器容器已启动"\n\
echo "VNC 端口: 5901"\n\
echo "连接方式: vnc://localhost:5901"\n\
echo "==========================================="\n\
\n\
# 启动 PyQt6 应用\n\
DISPLAY=:1 python -m pyqt_ui.main\n\
' > /app/start.sh && chmod +x /app/start.sh

# 设置入口点
CMD ["/app/start.sh"]

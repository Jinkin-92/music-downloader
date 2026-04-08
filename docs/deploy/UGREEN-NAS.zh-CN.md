# 绿联 NAS 部署 Web 版

这份说明对应当前主产品界面，也就是 React + FastAPI 的 Web 版。

## 为什么你之前会觉得 “NAS 不能跑 Web 版”

不是 NAS 不能跑，而是仓库里之前默认的 `docker-compose.yml` 实际上启动的是旧的 PyQt 桌面容器：

- 容器里跑的是 `python -m pyqt_ui.main`
- 通过 `xvfb + x11vnc` 暴露 VNC 桌面
- 对应的不是当前 Web 界面

现在默认的 `docker-compose.yml` 已经改成 Web 版：

- `backend`：FastAPI，端口 `8003`
- `frontend`：Nginx 托管 React 构建产物，端口 `8080`
- 前端通过 `/api` 反向代理到后端

另外我还补了两份更适合 NAS 常驻运行的 Compose：

- `docker-compose.nas.yml`
- `docker-compose.nas-auth.yml`
- `docker-compose.nas.simple.yml`

## 目录准备

把整个仓库上传到 NAS，例如：

```text
/volume1/docker/music-downloader
```

建议确保以下目录存在，Compose 首次启动也会自动创建：

```text
musicdl_outputs/
logs/
data/
```

## 在绿联 Docker Compose 中部署

如果你的 NAS 面板支持 Docker Compose，我更推荐直接用：

- 普通版：`docker-compose.nas.yml`
- 带鉴权版：`docker-compose.nas-auth.yml`

### 推荐方案一：NAS 普通版

1. 新建一个项目，项目目录指向仓库根目录
2. 使用 `docker-compose.nas.yml`
3. 按需设置环境变量：

```text
WEB_PORT=8080
TZ=Asia/Shanghai
DOWNLOADS_PATH=./musicdl_outputs
LOGS_PATH=./logs
DATA_PATH=./data
```

4. 启动项目

这个版本的特点是：

- 只对外暴露 `WEB_PORT`
- 后端 `8003` 不直接暴露到 NAS 外部
- 下载目录、日志目录、数据库目录都可以改

### 最省事方案：无 `.env` 版

如果你的绿联面板不方便改环境变量，直接使用：

- `docker-compose.nas.simple.yml`

这个文件已经写死了默认值：

- Web 端口：`8080`
- 时区：`Asia/Shanghai`
- 下载目录：`./musicdl_outputs`
- 日志目录：`./logs`
- 数据目录：`./data`

也就是说，你不需要额外准备 `.env`，直接导入这个 Compose 就能启动。

### 推荐方案二：NAS 鉴权版

如果你希望 NAS 上打开网页时先输账号密码，用 `docker-compose.nas-auth.yml`。

额外准备步骤：

1. 复制文件：

```text
docker/.htpasswd.example -> docker/.htpasswd
```

2. 把 `docker/.htpasswd` 换成你自己的 htpasswd 内容

说明：

- 当前仓库只提供了一个示例文件，避免把真实密码提交到 GitHub
- `docker/.htpasswd` 已加入 `.dockerignore`，不会被打进镜像上下文
- `docker-compose.nas-auth.yml` 会在运行时把本地的 `docker/.htpasswd` 挂载到前端容器

如果你暂时不需要鉴权，直接用普通版就够了

### 兼容方案：默认 Compose

如果你只是想快速跑起来，也可以直接继续用根目录默认的 `docker-compose.yml`

它仍然能跑 Web 版，只是会额外把后端 `8003` 也暴露出来

### 旧说明

如果你仍然想用默认 Compose：

1. 新建一个项目，项目目录指向仓库根目录
2. 使用根目录的 `docker-compose.yml`
3. 如需改端口，可以设置环境变量：

```text
WEB_PORT=8080
BACKEND_PORT=8003
```

4. 启动项目

默认访问地址：

- Web 界面：`http://NAS_IP:8080`
- API 文档：`http://NAS_IP:8003/docs`
- 也可通过前端代理访问：`http://NAS_IP:8080/docs`

## 命令行部署

如果你是通过 SSH 登录 NAS：

```bash
cd /volume1/docker/music-downloader
docker compose -f docker-compose.nas.yml up -d --build
```

查看日志：

```bash
docker compose -f docker-compose.nas.yml logs -f
```

停止：

```bash
docker compose -f docker-compose.nas.yml down
```

## 持久化说明

当前 Compose 会保留这些数据：

- `./musicdl_outputs:/app/musicdl_outputs`：下载的歌曲
- `./logs:/app/logs`：后端日志
- `./data:/app/data`：下载历史数据库

所以容器重建后，下载记录和文件仍然会保留。

## 旧桌面版容器

如果你确实还要用旧的 PyQt + VNC 容器，改用：

```bash
docker compose -f docker-compose.legacy-desktop.yml up -d --build
```

这个模式只是兼容保留，不是当前推荐入口。

## 建议

对外使用时，优先暴露 `8080` 这个 Web 端口。

如果你后面想让我继续，我可以再补两件事：

- 针对绿联面板的 `.env` 示例
- 带鉴权和自定义下载目录的 NAS 生产版 Compose

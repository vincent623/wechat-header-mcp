# UVX部署指南

## 🚀 UVX零部署方案

UVX是Python应用程序运行器，可以实现零依赖安装和版本隔离。

### 快速开始

```bash
# 方法1: 直接从GitHub运行
uvx run git+https://github.com/your-org/wechat-header-mcp.git

# 方法2: 本地目录运行
uvx run .
```

### 环境变量配置

在使用UVX运行时，可以通过以下方式设置环境变量：

#### 方法1: Shell环境变量
```bash
export VOLC_ACCESSKEY=your_access_key_here
export VOLC_SECRETKEY=your_secret_key_here
uvx run git+https://github.com/your-org/wechat-header-mcp.git
```

#### 方法2: .env文件
```bash
# 在项目根目录创建.env文件
echo "VOLC_ACCESSKEY=your_access_key_here" > .env
echo "VOLC_SECRETKEY=your_secret_key_here" >> .env

# UVX会自动加载.env文件
uvx run .
```

#### 方法3: 命令行传递
```bash
VOLC_ACCESSKEY=your_access_key_here \
VOLC_SECRETKEY=your_secret_key_here \
uvx run git+https://github.com/your-org/wechat-header-mcp.git
```

## IDE配置

### Claude Desktop配置

编辑配置文件 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wechat-header": {
      "command": "uvx",
      "args": ["git+https://github.com/your-org/wechat-header-mcp.git"],
      "env": {
        "VOLC_ACCESSKEY": "your_access_key_here",
        "VOLC_SECRETKEY": "your_secret_key_here"
      }
    }
  }
}
```

### VS Code配置

创建 `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "wechat-header": {
      "command": "uvx",
      "args": ["git+https://github.com/your-org/wechat-header-mcp.git"],
      "env": {
        "VOLC_ACCESSKEY": "your_access_key_here",
        "VOLC_SECRETKEY": "your_secret_key_here"
      }
    }
  }
}
```

### Cursor配置

在Cursor设置中添加MCP服务器配置：

```json
{
  "mcp": {
    "servers": {
      "wechat-header": {
        "command": "uvx",
        "args": ["git+https://github.com/your-org/wechat-header-mcp.git"],
        "env": {
          "VOLC_ACCESSKEY": "your_access_key_here",
          "VOLC_SECRETKEY": "your_secret_key_here"
        }
      }
    }
  }
}
```

## 本地开发部署

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/your-org/wechat-header-mcp.git
cd wechat-header-mcp

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env
```

### 运行服务器

```bash
# 使用UV运行
uv run wechat-header-mcp

# 或直接运行Python模块
uv run python -m wechat_header_mcp.server

# 或激活环境后运行
source .venv/bin/activate
python -m wechat_header_mcp.server
```

## Docker部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制项目文件
COPY pyproject.toml .
COPY src/ ./src/

# 安装依赖
RUN uv pip install --system -e .

# 设置环境变量
ENV VOLC_ACCESSKEY=""
ENV VOLC_SECRETKEY=""

# 运行服务器
CMD ["python", "-m", "wechat_header_mcp.server"]
```

构建和运行：

```bash
# 构建镜像
docker build -t wechat-header-mcp .

# 运行容器
docker run -e VOLC_ACCESSKEY=your_key -e VOLC_SECRETKEY=your_secret wechat-header-mcp
```

## 故障排除

### 常见问题

1. **UVX命令未找到**
   ```bash
   # 安装UV
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **权限错误**
   ```bash
   # 确保脚本有执行权限
   chmod +x src/wechat_header_mcp/server.py
   ```

3. **网络连接问题**
   ```bash
   # 使用代理运行
   https_proxy=your_proxy uvx run git+https://github.com/your-org/wechat-header-mcp.git
   ```

4. **环境变量未生效**
   ```bash
   # 检查环境变量
   uvx run --env VOLC_ACCESSKEY=your_key git+https://github.com/your-org/wechat-header-mcp.git
   ```

### 调试模式

启用详细日志：

```bash
export LOG_LEVEL=DEBUG
uvx run git+https://github.com/your-org/wechat-header-mcp.git
```

### 版本管理

指定特定版本：

```bash
# 运行特定版本
uvx run git+https://github.com/your-org/wechat-header-mcp.git@v1.0.0

# 运行特定分支
uvx run git+https://github.com/your-org/wechat-header-mcp.git@main
```

## 生产部署

### 系统服务

创建systemd服务文件 `/etc/systemd/system/wechat-header-mcp.service`:

```ini
[Unit]
Description=WeChat Header MCP Server
After=network.target

[Service]
Type=simple
User=wechat-header
WorkingDirectory=/opt/wechat-header-mcp
Environment=VOLC_ACCESSKEY=your_access_key_here
Environment=VOLC_SECRETKEY=your_secret_key_here
ExecStart=/usr/local/bin/uvx run /opt/wechat-header-mcp
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable wechat-header-mcp
sudo systemctl start wechat-header-mcp
sudo systemctl status wechat-header-mcp
```

### 负载均衡

使用Nginx进行负载均衡：

```nginx
upstream wechat_header_mcp {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name mcp.example.com;

    location / {
        proxy_pass http://wechat_header_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 安全建议

1. **API密钥管理**
   - 使用环境变量存储密钥
   - 定期轮换API密钥
   - 使用密钥管理服务

2. **网络安全**
   - 使用HTTPS连接
   - 配置防火墙规则
   - 启用访问日志

3. **容器安全**
   - 使用非root用户运行
   - 最小权限原则
   - 定期更新基础镜像

---

如有其他部署问题，请查看 [故障排除](#故障排除) 或提交 [Issue](https://github.com/your-org/wechat-header-mcp/issues)。
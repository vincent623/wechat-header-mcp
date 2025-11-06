# WeChat Header MCP Server

🎨 **即梦AI图像生成MCP服务器 - 微信公众号头图专用**

基于FastMCP框架，集成SENSE框架智能提示词优化，支持火山引擎即梦AI 4.0真实API，专门用于生成高质量的微信公众号头图和各种创意图片。

## ✨ 核心特性

- 🎯 **真实API集成**: 基于火山引擎即梦AI 4.0官方接口
- 🧠 **SENSE智能优化**: 5维度提示词智能优化框架
- ⚡ **异步任务处理**: 完整的任务提交→查询→结果流程
- 🖼️ **多尺寸支持**: 1:1、2.35:1、16:9、4:3、3:2等比例
- 🔧 **多IDE兼容**: Claude Desktop、VS Code、Cursor、Cline
- 🚀 **零部署方案**: UVX一键部署，开箱即用
- 💰 **成本优化**: 智能参数控制，强制单图输出

## 🚀 快速开始

### 1. UVX零部署 (推荐) 🚀

即梦AI MCP服务器支持UVX零部署，无需预安装任何依赖：

```bash
# 直接运行最终版服务器
uvx run src/final_mcp_server.py
```

**UVX优势**：
- ✅ **零依赖安装**: 自动下载所需包
- ✅ **版本隔离**: 避免依赖冲突
- ✅ **跨平台**: Windows/macOS/Linux通用
- ✅ **一键启动**: 单命令即可运行

### 2. 配置API密钥

复制环境变量模板并配置：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的火山引擎API密钥
```

```env
VOLC_ACCESSKEY=your_access_key_here
VOLC_SECRETKEY=your_secret_key_here
```

### 3. 自动配置Claude Desktop

```bash
python setup_mcp.py
```

### 4. 重启Claude Desktop

### 5. 开始使用

在Claude Desktop中直接对话：
- "生成一个科技感的微信头图"
- "生成一张可爱的小狗图片"
- "优化这个提示词：蓝色背景的科技公司"

### 📋 本地开发环境 (可选)

如果需要本地开发，可以安装依赖：

```bash
pip install -r requirements.txt
python src/final_mcp_server.py
```

## 🛠️ MCP工具列表

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| `generate_wechat_header` | 生成微信公众号头图(2.35:1) | prompt, style, quality |
| `generate_image` | 生成任意图片 | prompt, aspect_ratio, style |
| `optimize_prompt_with_sense` | SENSE框架优化提示词 | prompt, use_case |
| `get_available_styles` | 获取可用艺术风格 | category |

## 📁 项目结构

```
wechat-header-mcp/
├── src/
│   └── final_mcp_server.py        # 主MCP服务器
├── config/                        # IDE配置文件
│   ├── claude.json               # Claude Desktop配置
│   ├── vscode.json               # VS Code配置
│   ├── cursor.json               # Cursor配置
│   └── cline.json                # Cline配置
├── docs/                          # 详细文档
├── archive/                       # 开发过程文件
├── README.md                      # 本文件
├── requirements.txt               # 依赖包列表
├── setup_mcp.py                   # 自动配置脚本
└── .env.example                   # 环境变量模板
```

## 🔧 技术架构

### API集成
- **服务提供商**: 火山引擎 VolcEngine
- **AI模型**: 即梦AI 4.0 (jimeng_t2i_v40)
- **签名算法**: V4签名（官方标准实现）
- **接口协议**: HTTP/JSON + 异步任务模式

### SENSE优化框架
```
SENSE = Subject + Environment + Norm + Style + Element
```
- **Subject**: 主题内容识别和优化
- **Environment**: 专业摄影环境构建
- **Norm**: 输出标准和规格定义
- **Style**: AI驱动艺术风格推荐
- **Element**: 细节增强和质量提升

### 开发和测试

```bash
# 运行开发服务器
fastmcp dev src/final_mcp_server.py

# 测试服务器功能
python -c "import sys; sys.path.append('src'); from final_mcp_server import *; print('✅ 服务器加载成功')"

# 查看测试文件
ls archive/development/tests/
```

## 📊 官方规格限制

基于即梦AI官方文档：

### 输入限制
- **图片格式**: JPEG、PNG
- **文件大小**: 最大15MB
- **分辨率**: 最大4096×4096
- **宽高比**: [1/3, 3]
- **图片数量**: 最多10张

### 输出限制
- **分辨率**: 最大4096×4096
- **宽高比**: [1/3, 3]
- **图片数量**: 15 - 输入图数量
- **计费**: 按输出图片数量计费

### 优化建议
- 使用 `force_single=true` 强制单图输出
- 英文提示词效果更佳
- 合理控制输出尺寸和数量

## 🎯 使用示例

### Claude Desktop中使用
```
用户: 帮我生成一个科技感的微信头图
Claude: [自动调用generate_wechat_header工具]
✅ 返回SENSE优化后的2.35:1比例高清图片
```

### 编程调用示例
```python
# 在支持MCP的环境中直接调用
result = generate_wechat_header(
    prompt="科技感十足的蓝色背景",
    style="现代科技风",
    quality="high"
)
```

## 🔍 故障排除

### 常见问题
1. **API密钥错误**: 检查火山引擎控制台权限
2. **签名失败**: ✅ 已修复 - 使用正确的火山引擎V4签名算法
3. **图片生成慢**: 即梦AI通常需要30-60秒
4. **提示词无效**: 尝试使用英文提示词
5. **IDE连接失败**: ✅ 已修复 - 支持Cursor/VS Code等IDE
6. **API频率限制**: 429错误为正常现象，稍后重试即可

### 调试文件
开发过程中的调试文件保存在 `archive/development/` 目录中。

## 📄 文档链接

- [项目概览](PROJECT_OVERVIEW.md)
- [技术报告](FINAL_REPORT.md)
- [成功总结](SUCCESS_SUMMARY.md)
- [项目结构说明](PROJECT_STRUCTURE.md)

## 🎉 项目状态

✅ **开发完成** - 所有功能已验证，可投入生产使用

## 📜 许可证

MIT License

---

**🎨 让创意与技术完美融合，用即梦AI创造无限可能！**
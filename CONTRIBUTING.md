# 贡献指南

感谢您对公众号头图MCP服务器项目的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题

- 使用 [GitHub Issues](https://github.com/your-org/wechat-header-mcp/issues) 报告bug
- 提供详细的重现步骤和环境信息
- 包含相关的错误日志和截图

### 提出新功能

- 在Issues中讨论新功能想法
- 提供详细的功能描述和使用场景
- 考虑向后兼容性

### 提交代码

1. **Fork项目**
   ```bash
   git clone https://github.com/your-username/wechat-header-mcp.git
   cd wechat-header-mcp
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **进行开发**
   - 遵循代码风格规范
   - 添加必要的测试
   - 更新相关文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **推送并创建PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 代码规范

### Python代码风格

- 使用 `black` 进行代码格式化
- 使用 `ruff` 进行代码检查
- 遵循 PEP 8 规范

```bash
# 格式化代码
uv run black src/

# 检查代码
uv run ruff check src/
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型说明：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(server): add support for 4K resolution

- Add 4K resolution option for WeChat headers
- Update size validation logic
- Add tests for new resolution settings

Closes #123
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_server.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=wechat_header_mcp
```

### 编写测试

- 为新功能编写单元测试
- 确保测试覆盖率不低于80%
- 使用有意义的测试名称和描述

```python
import pytest
from wechat_header_mcp.server import create_wechat_header

@pytest.mark.asyncio
async def test_create_wechat_header_basic():
    """测试基础微信头图生成功能"""
    result = await create_wechat_header(
        prompt="测试图片",
        style_category="business",
        resolution="2k"
    )

    assert result is not None
    assert "status" in result
```

## 📚 文档

### 更新文档

- README.md: 项目概述和快速开始
- DEPLOYMENT.md: 部署指南
- API文档: 工具接口说明
- 代码注释: 复杂逻辑的详细说明

### 文档风格

- 使用清晰简洁的语言
- 提供代码示例
- 包含必要的截图和图表
- 保持文档与代码同步

## 🔍 代码审查

### 审查要点

- 代码逻辑正确性
- 性能影响
- 安全性考虑
- 测试覆盖率
- 文档完整性

### PR检查清单

- [ ] 代码通过所有测试
- [ ] 代码符合项目规范
- [ ] 更新了相关文档
- [ ] 添加了必要的测试
- [ ] 提交信息符合规范

## 🚀 发布流程

### 版本管理

- 使用语义化版本 (Semantic Versioning)
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 发布步骤

1. 更新版本号
2. 更新CHANGELOG.md
3. 创建Git标签
4. 发布GitHub Release

## 💬 交流

- GitHub Issues: 报告问题和功能请求
- GitHub Discussions: 一般讨论和问答
- 邮件列表: 重要公告和讨论

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下授权。

## 🙏 致谢

感谢所有为项目做出贡献的开发者！

---

有任何问题，请随时通过GitHub Issues联系我们。
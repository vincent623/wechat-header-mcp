"""
公众号头图MCP服务器

一个专业的微信公众号头图生成服务，基于FastMCP框架和即梦AI。
支持精确尺寸控制和多比例输出。
"""

__version__ = "1.0.0"
__author__ = "MCP Developer"
__email__ = "developer@example.com"

from .server import main

__all__ = ["main"]
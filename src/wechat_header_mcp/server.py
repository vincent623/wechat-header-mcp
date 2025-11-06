#!/usr/bin/env python3
"""
公众号头图MCP服务器

一个专业的微信公众号头图生成服务，基于FastMCP框架和即梦AI。
支持精确尺寸控制和多比例输出。
"""

import asyncio
import json
import logging
import os
import sys
import time
import hashlib
import hmac
import datetime
import base64
import io
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from PIL import Image
import httpx

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP not found. Please install: uv add fastmcp", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wechat-header-mcp")

# 创建FastMCP实例
mcp = FastMCP("wechat-header")

# 从环境变量获取API配置
ACCESS_KEY = os.getenv("VOLC_ACCESSKEY")
SECRET_KEY = os.getenv("VOLC_SECRETKEY")

if not ACCESS_KEY or not SECRET_KEY:
    logger.warning("API keys not found in environment variables. Please set VOLC_ACCESSKEY and VOLC_SECRETKEY")

# 内置风格建议
STYLE_SUGGESTIONS = {
    "business": ["professional photography", "clean minimalist", "corporate style", "modern business"],
    "social": ["vibrant colors", "engaging", "social media style", "eye-catching"],
    "artistic": ["digital art", "watercolor painting", "oil painting", "concept art"],
    "nature": ["natural lighting", "organic", "landscape photography", "environmental"],
    "tech": ["futuristic", "sci-fi", "cyberpunk", "tech aesthetic", "digital"],
    "casual": ["friendly", "warm tones", "approachable", "everyday style"]
}

# 官方推荐的标准尺寸配置 (根据即梦AI 4.0文档)
STANDARD_DIMENSIONS = {
    "square_1k": {"width": 1024, "height": 1024, "ratio": "1:1", "description": "1K正方形"},
    "square_2k": {"width": 2048, "height": 2048, "ratio": "1:1", "description": "2K正方形"},
    "square_4k": {"width": 4096, "height": 4096, "ratio": "1:1", "description": "4K正方形"},

    "four_three_2k": {"width": 2304, "height": 1728, "ratio": "4:3", "description": "2K 4:3比例"},
    "four_three_4k": {"width": 4694, "height": 3520, "ratio": "4:3", "description": "4K 4:3比例"},

    "three_two_2k": {"width": 2496, "height": 1664, "ratio": "3:2", "description": "2K 3:2比例"},
    "three_two_4k": {"width": 4992, "height": 3328, "ratio": "3:2", "description": "4K 3:2比例"},

    "sixteen_nine_2k": {"width": 2560, "height": 1440, "ratio": "16:9", "description": "2K 16:9比例"},
    "sixteen_nine_4k": {"width": 5404, "height": 3040, "ratio": "16:9", "description": "4K 16:9比例"},

    "twenty_one_nine_2k": {"width": 3024, "height": 1296, "ratio": "21:9", "description": "2K 21:9比例"},
    "twenty_one_nine_4k": {"width": 6198, "height": 2656, "ratio": "21:9", "description": "4K 21:9比例"},

    # 微信头图特殊比例 (接近2.35:1)
    "wechat_header": {"width": 2848, "height": 1212, "ratio": "2.35:1", "description": "微信头图标准"}
}

def get_standard_dimensions(use_case: str = "square") -> tuple:
    """
    根据使用场景获取标准尺寸

    Args:
        use_case: 使用场景 ("square", "wechat", "social", "widescreen")

    Returns:
        (width, height) 元组
    """
    if use_case == "wechat":
        # 微信头图需要2.35:1比例，使用最接近的标准尺寸
        return STANDARD_DIMENSIONS["wechat_header"]["width"], STANDARD_DIMENSIONS["wechat_header"]["height"]
    elif use_case == "social":
        # 社交媒体使用16:9比例
        return STANDARD_DIMENSIONS["sixteen_nine_2k"]["width"], STANDARD_DIMENSIONS["sixteen_nine_2k"]["height"]
    elif use_case == "widescreen":
        # 宽屏使用21:9比例
        return STANDARD_DIMENSIONS["twenty_one_nine_2k"]["width"], STANDARD_DIMENSIONS["twenty_one_nine_2k"]["height"]
    else:
        # 默认使用正方形
        return STANDARD_DIMENSIONS["square_2k"]["width"], STANDARD_DIMENSIONS["square_2k"]["height"]

class PromptOptimizer:
    """自动提示词优化器 - 让简单描述变成专业图片生成指令"""

    @staticmethod
    def optimize_prompt(prompt: str, use_case: str = "general") -> str:
        """
        自动优化用户提示词

        Args:
            prompt: 用户原始描述
            use_case: 使用场景 (general, wechat_header)

        Returns:
            优化后的专业提示词
        """
        # 基础优化
        optimized = prompt.strip()

        # 英文效果通常更好
        if not any(ord(char) > 127 for char in optimized):
            # 英文提示词，直接添加质量词汇
            quality_terms = {
                "wechat_header": "professional photography, high resolution, commercial grade, clean background",
                "general": "high quality, detailed, professional photography"
            }
            optimized += f", {quality_terms.get(use_case, quality_terms['general'])}"
        else:
            # 中文提示词，添加中文优化词汇
            if use_case == "wechat_header":
                optimized += ", 专业摄影, 高清, 商业级, 纯净背景"
            else:
                optimized += ", 高质量, 细节丰富, 专业摄影"

        # 智能添加风格建议
        if "科技" in optimized or "tech" in optimized.lower():
            optimized += ", futuristic technology style"
        elif "自然" in optimized or "nature" in optimized.lower():
            optimized += ", natural environment"
        elif "商务" in optimized or "business" in optimized.lower():
            optimized += "professional business style"

        return optimized

class ImageCropper:
    """智能图片裁剪器 - 将1:1图片裁剪成2.35:1微信头图"""

    @staticmethod
    def get_crop_params(original_width: int, original_height: int, target_ratio: float = 2.35) -> Dict[str, Any]:
        """
        计算裁剪参数

        Args:
            original_width: 原始宽度
            original_height: 原始高度
            target_ratio: 目标宽高比

        Returns:
            裁剪参数
        """
        if original_width / original_height >= target_ratio:
            # 图片太宽，裁剪宽度
            new_width = int(original_height * target_ratio)
            x_offset = (original_width - new_width) // 2
            return {
                "x": x_offset,
                "y": 0,
                "width": new_width,
                "height": original_height,
                "crop_needed": True
            }
        else:
            # 图片太高，裁剪高度
            new_height = int(original_width / target_ratio)
            y_offset = (original_height - new_height) // 2
            return {
                "x": 0,
                "y": y_offset,
                "width": original_width,
                "height": new_height,
                "crop_needed": True
            }

    @staticmethod
    async def get_actual_image_size(image_url: str) -> Optional[tuple]:
        """
        获取实际图片的尺寸

        Args:
            image_url: 图片URL

        Returns:
            (width, height) 元组或None
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(image_url)
                if response.status_code == 200:
                    image_data = io.BytesIO(response.content)
                    img = Image.open(image_data)
                    return img.size
        except Exception as e:
            logger.error(f"Failed to get image size: {e}")
        return None

    @staticmethod
    async def smart_crop_to_ratio(image_url: str, target_ratio: float = 2.35,
                                 output_format: str = "params") -> Optional[Dict[str, Any]]:
        """
        智能裁剪图片到目标比例

        首先获取实际图片尺寸，然后计算正确的裁剪参数并执行裁剪

        Args:
            image_url: 原始图片URL
            target_ratio: 目标宽高比
            output_format: 输出格式 ("params", "base64", "compressed")

        Returns:
            包含裁剪信息的字典或None
        """
        try:
            # 1. 获取实际图片尺寸
            actual_size = await ImageCropper.get_actual_image_size(image_url)
            if not actual_size:
                return None

            actual_width, actual_height = actual_size
            logger.info(f"Actual image size: {actual_width}x{actual_height}")

            # 2. 计算裁剪参数
            crop_params = ImageCropper.get_crop_params(actual_width, actual_height, target_ratio)

            result = {
                "original_url": image_url,
                "actual_size": f"{actual_width}x{actual_height}",
                "crop_params": crop_params,
                "cropped_size": f"{crop_params['width']}x{crop_params['height']}",
                "target_ratio": target_ratio,
                "output_format": output_format
            }

            # 3. 根据输出格式处理
            if output_format == "params":
                # 只返回裁剪参数，避免Base64字符超限
                result["crop_url"] = f"{image_url}#crop={crop_params['x']},{crop_params['y']},{crop_params['width']},{crop_params['height']}"
                result["usage"] = "使用图片编辑软件按参数裁剪，或使用支持URL参数的图片服务"

            elif output_format == "base64":
                # 生成Base64（可能很长）
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(image_url)
                    if response.status_code == 200:
                        image_data = io.BytesIO(response.content)
                        img = Image.open(image_data)

                        cropped_img = img.crop((
                            crop_params['x'],
                            crop_params['y'],
                            crop_params['x'] + crop_params['width'],
                            crop_params['y'] + crop_params['height']
                        ))

                        # 压缩图片以减少Base64长度
                        buffered = io.BytesIO()

                        # 如果图片太大，先压缩尺寸
                        max_size = 800
                        if cropped_img.width > max_size or cropped_img.height > max_size:
                            cropped_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                        cropped_img.save(buffered, format="JPEG", quality=85, optimize=True)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()

                        result["cropped_base64"] = f"data:image/jpeg;base64,{img_base64}"
                        result["base64_length"] = len(img_base64)
                        result["usage"] = "Base64编码图片，可直接使用（已压缩优化）"

            elif output_format == "compressed":
                # 生成压缩的Base64
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(image_url)
                    if response.status_code == 200:
                        image_data = io.BytesIO(response.content)
                        img = Image.open(image_data)

                        cropped_img = img.crop((
                            crop_params['x'],
                            crop_params['y'],
                            crop_params['x'] + crop_params['width'],
                            crop_params['y'] + crop_params['height']
                        ))

                        # 强制压缩到较小尺寸
                        max_size = 600
                        if cropped_img.width > max_size or cropped_img.height > max_size:
                            cropped_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                        buffered = io.BytesIO()
                        cropped_img.save(buffered, format="JPEG", quality=75, optimize=True)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()

                        result["cropped_base64"] = f"data:image/jpeg;base64,{img_base64}"
                        result["base64_length"] = len(img_base64)
                        result["compressed_size"] = f"{cropped_img.width}x{cropped_img.height}"
                        result["usage"] = "压缩版本Base64图片，适合快速预览和使用"

            logger.info(f"Smart crop completed: {crop_params['width']}x{crop_params['height']} (ratio: {target_ratio})")
            return result

        except Exception as e:
            logger.error(f"Smart crop failed: {e}")
            return None

class JiemengAPIClient:
    """即梦AI API客户端 - 使用已验证的签名算法"""

    def __init__(self):
        self.access_key = ACCESS_KEY
        self.secret_key = SECRET_KEY
        self.base_url = "https://visual.volcengineapi.com"

        if not self.access_key or not self.secret_key:
            logger.error("API keys not configured. Please set VOLC_ACCESSKEY and VOLC_SECRETKEY environment variables.")
        else:
            logger.info("JiemengAPIClient initialized successfully")

    def _sign_request(self, query_params: Dict[str, str], body: str) -> tuple:
        """火山引擎V4签名算法 - 完全复制自工作版本"""
        if self.access_key is None or self.secret_key is None:
            print('No access key is available.')
            return None, None

        t = datetime.datetime.utcnow()
        current_date = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')

        canonical_uri = '/'
        canonical_querystring = '&'.join([f"{k}={v}" for k, v in sorted(query_params.items())])
        signed_headers = 'content-type;host;x-content-sha256;x-date'
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        content_type = 'application/json'

        canonical_headers = ('content-type:' + content_type + '\n' +
                            'host:visual.volcengineapi.com\n' +
                            'x-content-sha256:' + payload_hash + '\n' +
                            'x-date:' + current_date + '\n')

        canonical_request = ('POST\n' +
                            canonical_uri + '\n' +
                            canonical_querystring + '\n' +
                            canonical_headers + '\n' +
                            signed_headers + '\n' +
                            payload_hash)

        algorithm = 'HMAC-SHA256'
        credential_scope = datestamp + '/' + 'cn-north-1' + '/' + 'cv' + '/' + 'request'
        string_to_sign = (algorithm + '\n' +
                         current_date + '\n' +
                         credential_scope + '\n' +
                         hashlib.sha256(canonical_request.encode('utf-8')).hexdigest())

        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

        def getSignatureKey(key, dateStamp, regionName, serviceName):
            """获取签名密钥 - 完全复制自工作版本"""
            kDate = sign(key.encode('utf-8'), dateStamp)
            kRegion = sign(kDate, regionName)
            kService = sign(kRegion, serviceName)
            kSigning = sign(kService, 'request')
            return kSigning

        signing_key = getSignatureKey(self.secret_key, datestamp, "cn-north-1", "cv")
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

        authorization_header = (algorithm + ' ' + 'Credential=' + self.access_key + '/' +
                               credential_scope + ', ' + 'SignedHeaders=' +
                               signed_headers + ', ' + 'Signature=' + signature)

        headers = {
            'X-Date': current_date,
            'Authorization': authorization_header,
            'X-Content-Sha256': payload_hash,
            'Content-Type': content_type
        }

        request_url = "https://visual.volcengineapi.com?" + canonical_querystring

        return headers, request_url

    async def submit_task(self, prompt: str, width: Optional[int] = None, height: Optional[int] = None) -> Optional[str]:
        """
        提交图片生成任务 - 使用官方4.0 API格式

        Args:
            prompt: 生成提示词
            width: 目标宽度，根据官方文档选择标准尺寸
            height: 目标高度，根据官方文档选择标准尺寸
        """
        try:
            if not self.access_key or not self.secret_key:
                logger.error("Cannot submit task: API keys not configured")
                return None

            # 添加必需的Action参数
            query_params = {
                'Action': 'CVSync2AsyncSubmitTask',
                'Version': '2022-08-31'
            }

            # 根据官方文档构建请求体
            body = {
                "req_key": "jimeng_t2i_v40",
                "prompt": prompt,
                "force_single": True  # 强制生成单图，提高稳定性
            }

            # 如果指定了宽高，添加到请求中
            if width is not None and height is not None:
                # 验证宽高是否符合官方要求
                area = width * height
                if area < 1024 * 1024:  # 最小面积
                    area = 1024 * 1024
                elif area > 4096 * 4096:  # 最大面积
                    area = 4096 * 4096

                # 计算宽高比
                ratio = width / height
                if ratio < 1/3:  # 最小比例
                    height = int(width * 3)
                elif ratio > 3:  # 最大比例
                    width = int(height * 3)

                body["width"] = width
                body["height"] = height
                logger.info(f"Using specified dimensions: {width}x{height}")
            else:
                # 使用默认尺寸 - 根据官方文档推荐2048x2048
                body["width"] = 2048
                body["height"] = 2048
                logger.info("Using default dimensions: 2048x2048")

            body_json = json.dumps(body)
            headers, request_url = self._sign_request(query_params, body_json)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(request_url, headers=headers, data=body_json)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 10000:
                        task_id = result.get("data", {}).get("task_id")
                        logger.info(f"Task submitted successfully: {task_id}")
                        return task_id
                    else:
                        logger.error(f"API error: {result.get('message', 'Unknown error')}")
                else:
                    logger.error(f"HTTP error: {response.status_code}")

        except Exception as e:
            logger.error(f"Submit task failed: {e}")

        return None

    async def get_result(self, task_id: str) -> Optional[str]:
        """获取任务结果"""
        try:
            if not self.access_key or not self.secret_key:
                logger.error("Cannot get result: API keys not configured")
                return None

            query_params = {
                'Action': 'CVSync2AsyncGetResult',
                'Version': '2022-08-31'
            }

            req_json = {"return_url": True, "logo_info": {"add_logo": False}}
            body = {
                "req_key": "jimeng_t2i_v40",
                "task_id": task_id,
                "req_json": json.dumps(req_json)
            }

            body_json = json.dumps(body)
            headers, request_url = self._sign_request(query_params, body_json)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(request_url, headers=headers, data=body_json)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 10000:
                        data = result.get("data", {})
                        if data.get("status") == "done":
                            image_urls = data.get("image_urls", [])
                            if image_urls:
                                return image_urls[0]

        except Exception as e:
            logger.error(f"Get result failed: {e}")

        return None

    async def generate_image(self, prompt: str, width: int = 512, height: int = 512, max_wait: int = 60) -> Dict[str, Any]:
        """生成图片的完整流程"""
        # 1. 提交任务
        task_id = await self.submit_task(prompt, width, height)
        if not task_id:
            return {
                "status": "error",
                "message": "图片生成任务提交失败，请稍后重试",
                "suggestion": "检查API配置或联系技术支持"
            }

        # 2. 轮询结果
        start_time = time.time()
        while time.time() - start_time < max_wait:
            image_url = await self.get_result(task_id)
            if image_url:
                return {
                    "status": "success",
                    "image_url": image_url,
                    "task_id": task_id,
                    "generation_time": round(time.time() - start_time, 1),
                    "prompt": prompt,
                    "dimensions": f"{width}x{height}"
                }

            await asyncio.sleep(5)

        return {
            "status": "timeout",
            "message": f"图片生成超时（{max_wait}秒），请稍后查看结果",
            "task_id": task_id,
            "suggestion": "可以稍后使用任务ID查询生成结果"
        }

# 全局客户端实例
_client = None

def get_client():
    global _client
    if _client is None:
        _client = JiemengAPIClient()
    return _client

# ===== MCP TOOLS =====

@mcp.tool()
async def create_image(
    prompt: str,
    style_category: Optional[str] = None,
    resolution: str = "2k"
) -> str:
    """
    生成通用图片 (1:1比例)

    为用户生成高质量的方形图片，适合头像、图标、社交媒体帖子等使用场景。

    Args:
        prompt: 图片描述，用简单的语言描述你想要的图片
        style_category: 风格类别 (business, social, artistic, nature, tech, casual)
        resolution: 分辨率选择 ("1k", "2k", "4k")

    Returns:
        JSON格式的生成结果，包含图片链接和使用建议
    """
    try:
        # 1. 自动优化提示词
        optimizer = PromptOptimizer()
        optimized_prompt = optimizer.optimize_prompt(prompt, "general")

        # 2. 获取标准尺寸
        if resolution == "1k":
            width, height = 1024, 1024
        elif resolution == "4k":
            width, height = 4096, 4096
        else:  # 默认2k
            width, height = 2048, 2048

        # 3. 生成图片
        client = get_client()
        result = await client.generate_image(optimized_prompt, width, height)

        # 4. 添加使用建议
        if result["status"] == "success":
            result.update({
                "use_case": "通用图片",
                "aspect_ratio": "1:1 (正方形)",
                "resolution": f"{resolution.upper()} ({width}x{height})",
                "suitable_for": ["头像", "社交媒体帖子", "图标", "缩略图"],
                "next_steps": "直接下载使用，或根据需要进行后期编辑"
            })

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Create image failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"图片生成失败: {str(e)}",
            "suggestion": "请尝试简化描述或更换风格，稍后重试"
        }, ensure_ascii=False)

@mcp.tool()
async def create_wechat_header(
    prompt: str,
    style_category: Optional[str] = "business",
    resolution: str = "2k"
) -> str:
    """
    生成微信公众号头图 (2.35:1比例)

    专门为微信公众号设计的头图，使用官方推荐的2.35:1比例，确保最佳显示效果。

    Args:
        prompt: 头图描述，描述你想要的公众号头图内容
        style_category: 风格类别 (business, social, artistic, nature, tech, casual)
        resolution: 分辨率选择 ("1k", "2k", "4k")

    Returns:
        JSON格式的生成结果，包含微信头图图片和使用建议
    """
    try:
        # 1. 自动优化提示词（针对微信头图）
        optimizer = PromptOptimizer()
        optimized_prompt = optimizer.optimize_prompt(prompt, "wechat_header")

        # 2. 获取微信头图标准尺寸 (2.35:1比例)
        if resolution == "1k":
            # 计算1K级别的2.35:1比例
            width, height = 1424, 606
        elif resolution == "4k":
            # 使用4K级别的微信头图尺寸
            width, height = 5696, 2424
        else:  # 默认2K
            width, height = STANDARD_DIMENSIONS["wechat_header"]["width"], STANDARD_DIMENSIONS["wechat_header"]["height"]

        # 3. 生成2.35:1比例的微信头图
        client = get_client()
        result = await client.generate_image(optimized_prompt, width, height)

        # 3. 添加微信头图专用信息
        if result["status"] == "success":
            result.update({
                "use_case": "微信公众号头图",
                "aspect_ratio": "2.35:1 (微信标准)",
                "resolution": f"{resolution.upper()} ({width}x{height})",
                "original_image_url": result["image_url"],
                "suitable_for": ["微信公众号头图", "文章封面", "品牌展示", "社交媒体横幅"],
                "next_steps": "图片已按微信头图比例生成，可直接下载使用",
                "usage_tips": [
                    f"✅ 微信头图比例 ({width}x{height})",
                    "✅ 无需裁剪，直接可用",
                    "✅ 高清分辨率，适合各种显示设备",
                    "✅ 已优化提示词，提升生成效果"
                ]
            })

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Create WeChat header failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"微信头图生成失败: {str(e)}",
            "suggestion": "请尝试简化描述或更换风格，稍后重试"
        }, ensure_ascii=False)

@mcp.tool()
async def crop_image_to_url(
    original_image_url: str,
    target_ratio: float = 2.35,
    output_format: str = "params"
) -> str:
    """
    将图片裁剪到指定比例并提供多种输出格式

    支持将任意图片裁剪为微信头图、社交媒体帖子等标准比例。
    提供参数、Base64、压缩等多种输出格式以避免字符超限。

    Args:
        original_image_url: 原始图片URL
        target_ratio: 目标宽高比 (2.35为微信头图, 1.0为正方形, 1.91为社交媒体横幅)
        output_format: 输出格式 ("params"=裁剪参数, "compressed"=压缩Base64, "base64"=完整Base64)

    Returns:
        JSON格式的裁剪结果，包含详细的尺寸信息和输出数据
    """
    try:
        cropper = ImageCropper()

        # 执行智能裁剪
        crop_result = await cropper.smart_crop_to_ratio(original_image_url, target_ratio, output_format)

        if not crop_result:
            return json.dumps({
                "status": "error",
                "message": "图片裁剪失败，请检查图片URL是否有效",
                "suggestion": "确保图片URL可访问，或尝试其他图片"
            }, ensure_ascii=False)

        # 格式化比例描述
        ratio_descriptions = {
            2.35: "微信头图标准",
            1.0: "正方形",
            1.91: "社交媒体横幅",
            16/9: "宽屏视频",
            4/3: "传统照片"
        }

        ratio_desc = ratio_descriptions.get(target_ratio, f"自定义比例 {target_ratio}")

        result = {
            "status": "success",
            "operation": "图片智能裁剪",
            "original_url": original_image_url,
            "actual_size": crop_result["actual_size"],
            "target_ratio": f"{target_ratio:.2f} ({ratio_desc})",
            "cropped_size": crop_result["cropped_size"],
            "crop_params": crop_result["crop_params"],
            "output_format": output_format,
            "usage": crop_result.get("usage", ""),
            "next_steps": "根据选择的输出格式使用相应结果"
        }

        # 添加格式特定的结果
        if output_format == "params":
            result["crop_url"] = crop_result.get("crop_url", "")
            result["manual_instructions"] = {
                "photoshop": f"使用裁剪工具，设置 x={crop_result['crop_params']['x']}, y={crop_result['crop_params']['y']}, 宽度={crop_result['crop_params']['width']}, 高度={crop_result['crop_params']['height']}",
                "online_tools": "使用支持URL参数的在线图片编辑器",
                "apps": "使用手机图片编辑应用，手动输入裁剪参数"
            }

        elif output_format in ["base64", "compressed"]:
            result["cropped_base64"] = crop_result.get("cropped_base64", "")
            result["base64_length"] = crop_result.get("base64_length", 0)
            if output_format == "compressed":
                result["compressed_size"] = crop_result.get("compressed_size", "")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Crop image failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"图片裁剪失败: {str(e)}",
            "suggestion": "请检查图片URL和参数设置，稍后重试"
        }, ensure_ascii=False)

@mcp.tool()
async def get_style_suggestions(
    content_type: str,
    mood: Optional[str] = None
) -> str:
    """
    获取风格建议

    根据内容类型和情感需求，推荐最适合的艺术风格，帮助用户获得更好的图片效果。

    Args:
        content_type: 内容类型 (business, social, artistic, nature, tech, casual)
        mood: 情感倾向 (professional, friendly, creative, calm, energetic)

    Returns:
        JSON格式的风格建议和使用示例
    """
    try:
        suggestions = STYLE_SUGGESTIONS.get(content_type, STYLE_SUGGESTIONS["casual"])

        # 根据情感倾向调整建议
        if mood == "professional":
            suggestions = [s for s in suggestions if "professional" in s or "clean" in s or "modern" in s]
        elif mood == "friendly":
            suggestions = [s for s in suggestions if "warm" in s or "friendly" in s or "casual" in s]
        elif mood == "creative":
            suggestions = [s for s in suggestions if "art" in s or "creative" in s or "concept" in s]

        # 生成使用示例
        examples = []
        base_prompts = ["产品展示", "团队合影", "办公环境", "品牌logo"]

        for style in suggestions[:3]:  # 取前3个建议
            for prompt in base_prompts[:2]:  # 取前2个示例
                examples.append({
                    "style": style,
                    "prompt": f"{prompt}，{style}",
                    "use_case": content_type
                })

        result = {
            "content_type": content_type,
            "mood": mood,
            "recommended_styles": suggestions,
            "usage_examples": examples,
            "tips": [
                "选择与内容匹配的风格能获得更好的效果",
                "可以组合多个风格关键词",
                "英文提示词通常效果更好",
                "简洁描述往往比复杂描述更有效"
            ]
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Get style suggestions failed: {e}")
        return json.dumps({
            "error": str(e),
            "message": "获取风格建议失败",
            "suggestion": "请检查输入参数，稍后重试"
        }, ensure_ascii=False)

def main():
    """主入口点，支持通过UVX运行"""
    mcp.run()

if __name__ == "__main__":
    main()
"""模块功能：加载 FastOCR 模型并执行单次文字识别。

上层调用：
- common.vision.adapters.text_recognition：取用通用 OCR 组合能力。

下层依赖：
- MaaFramework：提供 OCR 模型和识别任务。
- OpenCV：提供图片通道转换。
- NumPy：提供数组类型。
- common.vision.config：提供模型路径、文件清单和阈值配置。

边界：只返回标准化识别事实，不负责 OCR 文本修正、候选业务规则或页面流程。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2

from autowsgr.common.vision import config


if TYPE_CHECKING:
    import numpy


@dataclass(frozen=True, slots=True)
class TextDetection:
    """FastOCR 标准化后的单个识别结果。"""

    recognized_text: str
    confidence_score: float
    text_region: tuple[int, int, int, int] | None = None


class OCRExecutor:
    """只负责加载 FastOCR 模型并执行一次识别。"""

    _BUNDLED_MODEL_DIR = Path(__file__).resolve().parent / 'model'

    def __init__(self) -> None:
        """加载模型并准备 OCR 运行时资源。

        Raises:
            RuntimeError: 模型文件、MaaFramework、CPU 执行器或阈值配置不可用。
        """
        # MaaFramework 只在真正创建 OCR 执行器时加载，避免基础视觉导入强制初始化模型。
        from maa.library import Library
        from maa.pipeline import JOCR, JRecognitionType
        from maa.resource import Resource
        from maa.tasker import Tasker
        from maa.toolkit import Toolkit

        # 1. 解析模型位置并确认运行所需的模型文件齐全。
        configured_model_dir = os.getenv(config.OCR_MODEL_DIR_ENV, '').strip()
        model_dir = (
            Path(configured_model_dir).expanduser().resolve()
            if configured_model_dir
            else self._BUNDLED_MODEL_DIR
        )
        missing = [name for name in config.OCR_MODEL_FILES if not (model_dir / name).is_file()]
        if missing:
            raise RuntimeError(f'FastOCR 模型目录缺少文件: {", ".join(missing)}')

        # 2. 初始化 MaaFramework 用户目录，避免把运行数据写回模型资源目录。
        configured_user_dir = os.getenv(config.OCR_USER_DIR_ENV, '').strip()
        user_dir = (
            Path(configured_user_dir).expanduser().resolve()
            if configured_user_dir
            else Path.home() / '.autowsgr' / 'fastocr'
        )
        user_dir.mkdir(parents=True, exist_ok=True)
        if not Toolkit.init_option(user_dir, {'logging': False}):
            raise RuntimeError('FastOCR 初始化 MaaFramework Toolkit 失败')

        # 3. 加载模型并固定使用 CPU 执行器。
        resource = Resource()
        if not resource.use_cpu():
            raise RuntimeError('FastOCR 无法启用 CPU 执行器')
        model_job = resource.post_ocr_model(model_dir).wait()
        if not model_job.succeeded:
            raise RuntimeError(f'FastOCR 无法加载模型: {model_dir}')

        # 4. 将 OCR 资源绑定到任务执行器，形成可复用的运行时对象。
        tasker = Tasker()
        tasker._resource_holder = resource
        bound = Library.framework().MaaTaskerBindResource(
            tasker._handle,
            resource._handle,
        )
        if not bound or not tasker.inited:
            raise RuntimeError('FastOCR 无法绑定 OCR Resource')

        # 5. 读取并校验模型阈值，后续识别统一使用该配置。
        try:
            threshold = float(
                os.getenv(config.OCR_THRESHOLD_ENV, str(config.OCR_DEFAULT_THRESHOLD))
            )
        except ValueError as exc:
            raise RuntimeError(f'{config.OCR_THRESHOLD_ENV} 必须是数字') from exc

        self._threshold = threshold
        self._tasker = tasker
        self._resource = resource
        self._recognition_type = JRecognitionType.OCR
        self._ocr_options_type = JOCR

    def recognize(
        self,
        image: numpy.ndarray,
        allowlist: str = '',
    ) -> list[TextDetection]:
        """执行完整文字检测并返回按阅读顺序排列的结果。

        Args:
            image: RGB 顺序的待识别图片数组。
            allowlist: 可选的允许字符集合，空字符串表示不做字符过滤。

        Returns:
            标准化的文字、置信度和区域结果列表。
        """
        return self._recognize(image, allowlist, only_rec=False)

    def recognize_line(
        self,
        image: numpy.ndarray,
        allowlist: str = '',
    ) -> list[TextDetection]:
        """识别已裁剪的单行文字并返回按阅读顺序排列的结果。

        Args:
            image: 已裁剪为单行文字的 RGB 图片数组。
            allowlist: 可选的允许字符集合，空字符串表示不做字符过滤。

        Returns:
            标准化的文字、置信度和区域结果列表。
        """
        return self._recognize(image, allowlist, only_rec=True)

    def _recognize(
        self,
        image: numpy.ndarray,
        allowlist: str,
        *,
        only_rec: bool,
    ) -> list[TextDetection]:
        """调用 FastOCR 并转换模型结果。

        Args:
            image: RGB 顺序的待识别图片数组。
            allowlist: 可选的允许字符集合。
            only_rec: 是否跳过检测阶段，按单行图片执行识别。

        Returns:
            按图片阅读顺序排列的标准化识别结果。

        Raises:
            RuntimeError: FastOCR 任务失败或没有返回识别详情。
        """
        # 1. FastOCR 使用 BGR 输入，先转换图片通道顺序。
        bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # 2. 提交一次识别任务并等待模型返回结果。
        job = self._tasker.post_recognition(
            self._recognition_type,
            self._ocr_options_type(
                only_rec=only_rec,
                threshold=self._threshold,
            ),
            bgr_image,
        ).wait()
        if not job.succeeded:
            raise RuntimeError('FastOCR 识别任务失败')
        detail = job.get()
        if detail is None:
            raise RuntimeError('FastOCR 未返回识别详情')

        # 3. 过滤空文本、应用字符约束，并统一识别区域坐标。
        detections: list[TextDetection] = []
        for node in detail.nodes:
            recognition = node.recognition
            if recognition is None:
                continue
            for detection in recognition.filtered_results:
                text = str(getattr(detection, 'text', ''))
                if allowlist:
                    text = ''.join(character for character in text if character in allowlist)
                if not text:
                    continue
                box_x, box_y, box_width, box_height = map(float, detection.box)
                detections.append(
                    TextDetection(
                        recognized_text=text,
                        confidence_score=float(detection.score),
                        text_region=(
                            round(box_x),
                            round(box_y),
                            round(box_x + box_width),
                            round(box_y + box_height),
                        ),
                    )
                )
        return sorted(
            detections,
            key=lambda detection: (
                detection.text_region[1] if detection.text_region is not None else 0,
                detection.text_region[0] if detection.text_region is not None else 0,
            ),
        )


__all__ = ['OCRExecutor', 'TextDetection']

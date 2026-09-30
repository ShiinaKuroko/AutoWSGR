"""模块功能：定义注入到 dispatch ContextScope 的运行时服务引用。

上层调用：
- dispatch.context.manager：绑定并向 ContextHandle 暴露服务引用。

下层依赖：
- 标准库 dataclasses：保存不可变的服务引用集合。

本模块只定义引用契约，不创建、连接、调用或释放服务。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeBindings:
    """保存 runtime composition root 注入的只读服务引用。"""

    ctrl: Any
    config: Any
    ocr: Any
    ship_ocr: Any


__all__ = ['RuntimeBindings']

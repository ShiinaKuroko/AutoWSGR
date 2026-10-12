"""模块功能：加载页码检查器共用的模板与静态数据。

上层调用：
- application.ui.navigation.checker 下各模块检查器：读取模板与本期活动数据。

下层依赖：
- common.system.files：读取活动静态数据。
- common.system.logger：记录加载事实。
- common.vision：加载模板并返回模板模型。

本模块只做加载与缓存，不解释识别规则、不持有页面状态，也不执行视觉识别。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from autowsgr.common.system.files import load_yaml
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import Template
from autowsgr.common.vision.adapters.template_matching import load_template


_log = get_logger('ui')


# 模板根目录，位于 common.vision 的模板根下，按模块命名空间分目录。
_TEMPLATE_ROOT = 'application/ui/navigation/checker'
# 活动静态数据根目录，按期存放各活动的数据文件。
_DATA_ROOT = Path(__file__).resolve().parents[5] / 'resources' / 'data' / 'map' / 'event'


def require_activity(event_type: str, activity: str) -> None:
    """校验调用方选择的活动玩法与当前 checker 一致。

    Args:
        event_type: 调用方给出的活动玩法标识。
        activity: 当前 checker 归属的活动标识。

    Raises:
        ValueError: 活动玩法标识与当前 checker 不一致。
    """
    if event_type != activity:
        raise ValueError(f'当前 checker 不支持的活动玩法: {event_type!r}')


def load_module_template(namespace: str, filename: str, *, name: str) -> Template:
    """加载某个模块命名空间下的模板。

    Args:
        namespace: 模板根下的相对目录，例如 `event/normal` 或 `home`。
        filename: 命名空间内的模板文件名。
        name: 模板业务名称，用于识别日志和匹配结果。

    Returns:
        已加载的模板。
    """
    return load_template(f'{_TEMPLATE_ROOT}/{namespace}/{filename}', name=name)


@lru_cache(maxsize=None)
def load_activity_data(activity: str, period: str) -> dict[str, Any]:
    """读取并缓存某个活动某一期的静态数据。

    Args:
        activity: 活动标识，对应数据文件名。
        period: 活动期号，对应数据目录名。

    Returns:
        活动数据映射。

    Raises:
        FileNotFoundError: 该期没有该活动的数据文件。
    """
    data = load_yaml(_DATA_ROOT / period / f'{activity}.yaml', allowed_root=_DATA_ROOT)
    _log.debug('[UI] 活动数据 → 加载：activity={!r}，period={!r}', activity, period)
    return data

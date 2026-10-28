"""模块功能：聚合基础执行器与 service 的重新修饰方法。

上层调用：
- common.vision.service：取用单帧识别和组合方法。

下层依赖：
- common.vision.numpy、opencv 和 ocr：提供基础识别能力。

只把基础执行器重新修饰成 service 可直接使用的形态，不持有设备截图、页面状态或
业务领域识别规则。
"""

from autowsgr.common.vision.adapters.pixel_matching import match_pixels
from autowsgr.common.vision.adapters.template_matching import (
    match_template,
    match_templates,
)
from autowsgr.common.vision.adapters.text_recognition import (
    parse_counter,
    prepare_text,
    recognize_prepared_text,
    recognize_text,
)


__all__ = [
    'match_pixels',
    'match_template',
    'match_templates',
    'parse_counter',
    'prepare_text',
    'recognize_prepared_text',
    'recognize_text',
]

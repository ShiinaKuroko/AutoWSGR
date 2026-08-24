"""基础功能 · 常量 — 游戏界面静态事实, 按分类 YAML 单源管理。

模块组成 (文件名 = 页面名, 键支持点号嵌套路径):
    coordinates/  点击坐标与探测点 YAML (1280x720 绝对整数, point() 归一化)
    colors/       颜色与容差 YAML ({rgb: [R,G,B], tolerance: N}), color()/tolerance()
    ocr/          OCR 裁切区域与识别参数 YAML, param() 原样返回
    signatures/   页面/状态像素签名 YAML, signature() 构造 PixelSignature
    shipnames.py  舰名数据 (待迁移)

原则:
    - 值一经采集即视为静态事实, 游戏 UI 更新时直接改 YAML, 不改代码;
    - 坐标 YAML 不得携带 color/tolerance 等元数据 (见 coordinates/__init__.py 硬约束);
    - 时序参数 (超时/等待/延迟) 由各执行器自行管理, 不入库。
"""

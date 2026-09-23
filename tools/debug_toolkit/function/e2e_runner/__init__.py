"""E2E 快速实机验证工具包 (tools.debug_toolkit)。

用法::

    python tools/debug_toolkit/main.py e2e --list
    python tools/debug_toolkit/main.py e2e screenshot --no-launch
    python tools/debug_toolkit/main.py e2e normal_fight --with-ocr --plan 1-1 --times 1

新增加速验证: 在 cases/ 目录复制 template 改写 run() 即可, 无需改框架。
"""

"""兼容 shim — 实现已迁移至 :mod:`autowsgr.application.ui.pages.main_page`。

老代码仍可 ``from autowsgr.application.ui.legacy.main_page import MainPage``，
新代码请直接使用新路径。
"""

from autowsgr.application.ui.pages.main_page import MainPage


__all__ = ['MainPage']

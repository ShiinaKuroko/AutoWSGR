"""模块功能：common 层技术能力命名空间。

上层调用：
- application、business、dispatch 和 server：按子包路径导入 system、device 和 vision 能力。
- common 内部各子包：互相引用基础能力。

下层依赖：
- 本包的 system、device 和 vision 子模块。

只做技术能力命名空间，不持有项目层依赖或业务语义。
"""

__all__: list[str] = []

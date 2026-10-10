# common/system 架构说明

版本：AutoWSGR-3.0 第一轮

## 1. 模块定位

common/system 是程序级基础能力层。它只提供不带业务含义的枚举基类、错误基类、
通用文件边界和日志基础设施，不保存页面状态、设备对象、战斗规则或任务状态。

本层的判断标准是：能力是否可以脱离具体业务继续成立。能被多个模块以相同方式使用的
机制可以进入 system；只解释某种业务数据的代码必须留在业务所有者处。

## 2. 模块架构

~~~text
autowsgr/common/system/
├── __init__.py       # 稳定能力命名空间
├── config.py         # 统一配置模型，字段按能力前缀命名
├── enums.py          # 通用枚举基类
├── errors.py         # 程序级错误基类
├── files.py          # 通用文件读取和安全写入
└── logger.py         # 日志对象和输出初始化
~~~

依赖方向：

~~~text
enums.py   ──→ Python 标准库
errors.py  ──→ Python 内置异常
config.py  ──→ Pydantic
files.py   ──→ Python 标准库 / YAML 解析库
logger.py  ──→ config.py / Python 标准库 / Loguru
~~~

system 不反向依赖 common/device、common/vision、common/ui、application、
business 或具体业务配置模块。

__init__.py 只暴露能力模块，不把函数、配置对象或具体领域错误再次转出：

~~~python
from autowsgr.common import system

system.enums
system.errors
system.files
system.logger
~~~

配置模型通过明确路径导入，不作为根包的隐式出口：

~~~python
from autowsgr.common.system.config import LogConfig
~~~

## 3. 能力总览

| 模块 | 对外能力 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- |
| enums.py | BaseEnum、StrEnum、IntEnum | 通用枚举行为和非法值提示 | 具体业务枚举成员 |
| errors.py | SystemError 及四个层级基类 | 稳定的错误捕获边界 | 具体领域错误和恢复策略 |
| files.py | load_yaml、save_yaml | 路径校验、解析、编码和原子写入 | 业务字段解释和业务加载器 |
| logger.py | get_logger、setup_logger | 日志对象、级别筛选和输出 sink | 业务日志内容和业务结果判断 |
| config.py | LogConfig | 配置字段、默认值和输入校验 | 执行配置、读取用户文件和运行时状态 |

## 4. 枚举能力：system.enums

### 4.1 能力说明

system.enums 只定义通用枚举基类。具体枚举的成员、中文含义和业务判断由使用它的
模块定义，system 不知道这些成员代表页面、战斗状态还是设备类型。

BaseEnum 重写 _missing_，当输入值不存在时抛出包含合法值列表的 ValueError。
StrEnum 和 IntEnum 分别提供字符串枚举和整数枚举的基础类型组合。

### 4.2 调用示例

~~~python
from autowsgr.common import system


class RepairMode(system.enums.IntEnum):
    MODERATE = 1
    SEVERE = 2


mode = RepairMode(1)
~~~

非法值会直接失败：

~~~python
RepairMode(9)  # ValueError：包含支持的枚举值
~~~

### 4.3 维护规则

- 新增业务枚举时，在业务模块定义具体 class，不修改 system 基类。
- 只有所有枚举都需要的基础行为才能进入 enums.py。
- 枚举成员变化不属于 system 变更，不在这里增加配置。

## 5. 错误能力：system.errors

### 5.1 错误树

~~~text
SystemError
├── CommonError       # 设备、视觉、配置等公共基础能力
├── ApplicationError  # 应用导航、页面和上下文控制
├── BusinessError     # 战斗、后勤及其他业务控制
└── DispatchError     # 处理器和任务调度
~~~

这些基类是捕获标签，不在基类中增加业务字段、恢复动作或统一错误文本。具体错误
由实际拥有该语义的模块定义：

~~~python
from autowsgr.common import system


class FleetRuleError(system.errors.BusinessError):
    """舰队规则无法满足业务约束。"""
~~~

### 5.2 维护规则

- system 只维护 SystemError 和四个程序层级基类。
- 设备、视觉、页面、导航、战斗和后勤具体错误由所属模块定义。
- 具体错误需要的构造参数、错误文本和恢复方式不放进 system。
- TaskPaused、TaskStopped 等任务控制信号不属于错误树。
- 新增错误基类前，必须证明现有四个层级无法表达该捕获边界。

## 6. 文件能力：system.files

### 6.1 能力说明

system.files 是统一的通用文件边界。当前提供 YAML 映射的读取和保存；以后新增
通用文件格式时，仍在此模块增加明确的 load_<format> 或 save_<format> 方法。

它只处理“如何安全地读写”，不处理“文件内容代表什么”：

~~~text
system.files.load_yaml(path, allowed_root=...)  # 读取通用 YAML
业务模块解析返回值                         # 解释业务字段
~~~

禁止在这里增加 load_ship_names、load_fight_plan、load_user_config 等业务加载器，
也不增加没有输入输出契约的 load_file 总入口。

### 6.2 load_yaml

~~~python
from pathlib import Path

from autowsgr.common import system

path = Path('data/state.yaml')
data = system.files.load_yaml(path, allowed_root=path.parent)
~~~

契约：

~~~text
load_yaml(path: str | Path, *, allowed_root: str | Path) -> dict[str, Any]
~~~

- path 和 allowed_root 先规范化为绝对路径。
- 目标路径不在允许根目录内时抛出 ValueError。
- 文件不存在时抛出 FileNotFoundError。
- 空文件返回空映射。
- YAML 解析和权限错误向调用方抛出，不静默吞掉。

### 6.3 save_yaml

~~~python
from pathlib import Path

from autowsgr.common import system

system.files.save_yaml(
    {'enabled': True},
    Path('data/state.yaml'),
    allowed_root=Path('data'),
)
~~~

契约：

~~~text
save_yaml(
    data: dict[str, Any],
    path: str | Path,
    *,
    allowed_root: str | Path,
) -> None
~~~

- 目标路径必须位于 allowed_root 内。
- 父目录不存在时，只创建目标路径所需目录。
- 使用 UTF-8 和 Unicode 输出。
- 先写同目录临时文件，再使用原子替换，替换失败时保留原文件。
- 写入失败必须向调用方报告。

### 6.4 新增文件格式

新增格式前先确认它属于通用文件机制，而不是业务解析。实现时必须：

1. 使用 load_<format> / save_<format> 表达格式。
2. 复用路径规范化和允许目录校验。
3. 明确输入类型、返回类型和解析错误。
4. 对用户数据写入复用原子替换规则。
5. 在 testing/common/system 增加成功和失败路径测试。
6. 在本文档补充方法契约和示例。

## 7. 日志能力：system.logger

### 7.1 get_logger

~~~python
from autowsgr.common import system

log = system.logger.get_logger('combat')
log.info('[COMBAT] 状态机 → 进入战斗：结果=成功')
~~~

get_logger 返回带有稳定通道名的日志对象。调用方仍然使用普通的
.debug()、.info()、.warning() 和 .error() 方法；通道只用于 DEBUG 筛选，
不能代替日志文本中的可读模块名和职责位置。

契约：

~~~text
get_logger(channel: str) -> Logger
~~~

### 7.2 setup_logger

~~~python
from autowsgr.common import system
from autowsgr.common.system.config import LogConfig

system.logger.setup_logger(
    LogConfig(
        LOG_LEVEL='INFO',
        LOG_USER_DIR='logs/manual',
        LOG_COMBAT_OPEN=True,
    ),
)
~~~

setup_logger 只在启动或明确的测试入口调用。它会清理旧 sink，注册统一的记录
补充逻辑，并配置控制台和文件输出。

契约：

~~~text
setup_logger(config: LogConfig | None = None) -> None
~~~

输出规则：

- 项目只认 DEBUG、INFO、WARNING、ERROR 四级。
- LOG_LEVEL 控制普通日志的最低级别。
- LOG_<MODULE>_OPEN=True 只放行对应模块及子通道的 DEBUG。
- LOG_COMBAT_OPEN=True 匹配 combat 和 combat.*，不匹配 business.combat.*。
- DEBUG 开关默认为关闭；其他模块的 INFO、WARNING、ERROR 不因 DEBUG 开关关闭。
- 日志记录时间、文件日期和默认目录名统一使用北京时间。
- 文件按 LOG_ROTATION 切分，并由 LOG_RETENTION 控制保留周期。
- Loguru 的 TRACE、SUCCESS、CRITICAL 不属于项目日志契约。

日志文件路径为 LOG_USER_DIR；未指定时使用 LOG_SYSTEM_DIR 加北京时间目录名。
控制台和文件使用相同的级别筛选，避免文件继续产生未选择模块的 DEBUG 日志。

### 7.3 日志维护规则

- 模块 logger 通过 get_logger 创建，不直接操作 Loguru sink。
- 业务日志文本遵守 Python 代码规范中的四级日志和 INFO 格式。
- 新增 DEBUG 模块开关时，配置字段使用 LOG_<MODULE>_OPEN，默认值为 False。
- 通道名使用小写稳定业务词根，子通道使用点号连接，例如 combat.recognition。
- 不在 system logger 中增加页面、设备或业务动作方法。
- 不为旧的 logger 级别或旧配置字段增加兼容别名。

## 8. 统一配置：config.py

### 8.1 配置定位

config.py 是统一配置模型文件，不是某个能力的私有配置文件。配置字段通过模块
前缀区分所有权，当前日志字段使用 LOG_ 前缀；以后只有确实需要可调整行为的
能力才能增加对应前缀。

当前模型为 LogConfig，因为现阶段只有日志配置。它不读取 usersettings.yaml，
只负责保存已传入的字段、默认值和校验结果。

### 8.2 当前字段

| 字段 | 默认值 | 作用 | 是否可覆写 |
| --- | --- | --- | --- |
| LOG_LEVEL | DEBUG | 普通日志最低级别 | 是 |
| LOG_SYSTEM_DIR | logs | 默认日志根目录 | 是 |
| LOG_USER_DIR | 自动生成 | 用户指定的实际日志目录 | 是 |
| LOG_ROTATION | 10 MB | 单个日志文件切分条件 | 是 |
| LOG_RETENTION | 7 days | 日志文件保留周期 | 是 |
| LOG_COMBAT_OPEN | False | 是否放行 combat DEBUG | 是 |

旧的 show_*、channels 和 effective_channels 不属于当前配置契约。它们被删除，
避免用两套规则控制同一类 DEBUG 输出。

### 8.3 配置覆盖

用户或 GUI 只覆盖公开字段，流程如下：

~~~text
用户/GUI 输入
    ↓
顶层配置入口读取并校验
    ↓
common.system.config.LogConfig
    ↓
system.logger.setup_logger
~~~

覆盖必须发生在模型创建或校验阶段。模型创建后保持不可变，system 不在运行中通过
全局变量修改配置，也不直接读写用户配置文件。

### 8.4 什么时候增加配置

满足以下条件才增加配置字段：

1. 它确实改变模块的运行行为。
2. 不同用户、环境或调试场景需要不同取值。
3. 需要从用户配置或 GUI 覆写，而不是一次调用参数即可解决。
4. 它有明确的模块所有者、默认值和校验规则。
5. 它能通过单元测试证明覆盖前后的行为差异。

以下内容不增加配置字段：

- 固定时区、固定算法规则和固定业务事实。
- 坐标、模板和 ROI 等模块静态数据，应放在对应模块的 constants.py。
- 只使用一次的参数，应作为调用参数或消费文件顶部常量。
- 枚举成员、错误分类和没有运行时行为的标记类。
- 仅为未来可能扩展而预留的空字段。

新增字段格式：

~~~text
ENUMS_<NAME>
ERROR_<NAME>
FILES_<NAME>
LOG_<NAME>
~~~

字段只属于一个模块。配置模型负责数据和校验，实际行为仍由对应模块实现。

## 9. 公开出口和调用边界

### 9.1 稳定出口

~~~text
system.enums.BaseEnum
system.enums.StrEnum
system.enums.IntEnum

system.errors.SystemError
system.errors.CommonError
system.errors.ApplicationError
system.errors.BusinessError
system.errors.DispatchError

system.files.load_yaml
system.files.save_yaml

system.logger.get_logger
system.logger.setup_logger
~~~

system.config.LogConfig 是配置模型的明确导入路径，不通过 system 根包聚合。

### 9.2 不属于公开出口的内容

- _src_patcher、_open_debug_channels、_make_filter 等 logger 内部函数。
- _resolve_path 等文件路径安全实现。
- 具体枚举成员和具体领域异常。
- 截图保存、调用栈采集和通用字典合并。
- 页面、设备、视觉、战斗和任务状态。

调用方不得通过私有函数拼接 system 内部流程。需要新的稳定能力时，应在所属模块
定义公开入口，而不是从 __init__.py 转出内部实现。

## 10. 模块维护方法

### 10.1 添加 system 能力

1. 先判断能力是否无业务语义且能被多个模块以同一方式理解。
2. 将实现放入现有能力文件；一个文件无法保持单一职责时再拆目录。
3. 定义一个可独立理解的公开入口，写清输入、输出和失败边界。
4. 只在需要暴露能力命名空间时修改 __init__.py。
5. 在 testing/common/system 增加最小契约测试。
6. 在对应章节补充调用示例、边界和维护规则。

### 10.2 添加文件支持

新增文件格式只修改 files.py 和对应测试。不得把业务字段解析、搜索顺序或配置
迁移逻辑塞进 system。读写方法必须复用允许根目录校验；保存方法必须复用原子写入。

### 10.3 修改配置

1. 确认字段是否真的改变运行行为。
2. 按所有者增加大写前缀字段，例如 LOG_、FILES_ 或 ENUMS_。
3. 给出默认值、类型校验和可覆写边界。
4. 在实际消费者中读取该字段，不把行为逻辑放进配置模型。
5. 增加默认值、合法覆写和非法输入测试。
6. 同步本说明中的字段表和调用示例。

### 10.4 修改日志

日志级别、通道筛选和输出路径属于 logger 能力；日志文本的业务语义属于产生日志
的业务模块。修改 sink 机制时必须验证控制台、文件、级别、DEBUG 开关和北京时间；
不为旧接口增加兼容层。

## 11. 验收门禁

每次修改 system 至少执行：

~~~text
1. 公开出口 import smoke
2. system 源码 compileall
3. testing/common/system 专项 pytest
4. 配置默认值、合法覆写和非法字段测试
5. files 读取、路径拒绝和原子写入测试
6. logger 四级、DEBUG 通道和时间戳 smoke
7. scoped pre-commit
8. git diff --check
~~~

system 不以旧上层调用方暂时可运行为本轮验收条件。旧调用方应在后续适配批次中
按照本文档的稳定出口迁移。

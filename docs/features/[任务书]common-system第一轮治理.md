# [任务书] common/device 第一轮治理

Task Status: done

Next Step: device 第一轮治理已完成；后续由上层适配 device.XXX 契约。

## 1. 任务目标

将 autowsgr/common/device 从混合型设备实现重组为边界清晰的设备基础能力模块。

device 的业务语义是：

> 提供一切和模拟器操作相关的方法，为整个程序运行提供支撑。

本轮目标：

- 定义 device 对外提供的能力，并统一使用 device.XXX 形式调用。
- 打散 device 内部每一个 class、def、配置和资源依赖。
- 识别每个定义的真实业务语义和唯一所有者。
- 将 device 能力按入口垂直聚合到独立子模块。
- 建立 device 私有配置，并定义用户配置对它的覆写边界。
- 将 ADB 运行资源迁入 autowsgr，由 tools 只引用 device 能力或资源。
- 在不适配旧上层调用方的前提下，形成新的 device 模块契约。
- 建立 device 架构说明、专项单测和交付门禁。

## 2. 用户原始要求

以下内容保留用户原文，执行每个阶段前必须重新阅读：

> @C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/docs/features/[任务书]common-system第一轮治理.md 重置这个任务书，接下来把@C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/autowsgr/common/device 这个模块的治理任务，覆写到旧的任务书里，要求是一样的。
>
> 1、你要定义device对外提供的能力，我们这个模块按照 device.XXX来提供方法，这个device模块在业务上的语义是，提供一切和模拟器操作相关的方法，为整个程序运行提供支撑。这个模块需要内置一个adb，这个adb你可以从 tools里找到，我额外要求把这个adb迁移到autowsgr里，tools只做引用。如果需要用到同层 system的方法，则去看@C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/docs/AutoWSGR-3.0 架构说明，并且严格按照规范进行调用
>
> 2、要打散内部的每一个def，然后重新按照提供的方法来聚合子模块每一个device提供的入口，垂直下面就是一个子模块，这个子模块你可以单独用一个文件夹来包，没关系如果明确不是你device模块使用的def，你就往外丢，放到common/TEMP里，我会喊别的模块来收
>
> 3、你要遍历同层的其他模块，确保其他模块没有device模块需要的def和配置，然后结合：@C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/autowsgr/config.py @C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/autowsgr/config_compat.py @C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/autowsgr/config_method.py @C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/autowsgr/config_method_compat.py 这里的内容，看看有没有device需要的东西
>
> 4、作为common方法，一定要有独立的 config，这个config是device私有，主要作用是为了配置device的各种方法，同时这个device的部分方法要决定是否给用户使用，如果是要考虑怎么被覆写，用户通常会通过@C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/usersettings.yaml 最外层的这个文件来配置用户配置，用户配置可能会影响到device的config
>
> 5、我们本次的任务是重写模块，不用考虑与上层交互的契约，我们的目的是形成自己的边界，为同层、或者上层提供调用方法。并且有明确的契约
>
> 6、要求产出：一份task任务书，你要自己规划这一轮的治理，和门禁，以及台账。产出一份docs，和@C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/docs/AutoWSGR3.0/common/[架构]system.md 类似与架构说明，作用是描述 device模块提供了什么方法，怎么调用，这些方法的业务作用是什么。文档位置暂时放在 docs/AutoWSGR-3.0 目录下
>
> 7、任务书的需要包含我的原文，每一次阶段结束重新阅读任务书并且理解我的需求，修正后续的任务并且执行，直到任务结束
>
> 8、模块最终出版交付标准，参考同层的system模块。

## 3. 执行约束

### 3.1 范围内

- autowsgr/common/device 及其内部资源。
- device 私有配置、类型、错误、发现、控制器和生命周期能力。
- tools 对 device ADB 资源和公开能力的引用。
- docs/AutoWSGR-3.0 下的 device 架构说明。
- testing/common/device 下的 device 专项单测。

### 3.2 范围外

- 不适配旧 application、business、server、testing/ops 或 GUI 调用方。
- 不恢复 system 已删除的旧出口或兼容别名。
- 不把页面、OCR、战斗、任务和用户业务逻辑放入 device。
- 不顺手治理与 device 无关的 common、tools 或资源迁移。
- 不以旧上层全仓可运行为本轮验收条件。

common 层文档不强调上层调用清单，重点描述能力、输入输出、依赖方向、边界和维护方式。

## 4. 目标公开契约

device 根包提供能力命名空间，调用形式统一为：

~~~python
from autowsgr.common import device

device.adb.find_adb()
device.adb.list_devices()
device.controller.ScrcpyController(...)
device.lifecycle.create_emulator_manager(...)
device.platform.detect_host_os()
device.timing.operation_delay()
~~~

目标命名空间：

| 命名空间 | 业务能力 |
| --- | --- |
| device.config | device 私有配置模型，不作为根包聚合出口 |
| device.adb | 内置 ADB 路径、命令执行、连接和原始截图 |
| device.types | 设备和宿主平台的值类型 |
| device.errors | device 错误类型 |
| device.discovery | ADB 路径、在线设备和 serial 发现 |
| device.controller | Android I/O 协议及 Scrcpy 实现 |
| device.lifecycle | 宿主模拟器进程启动、停止和在线等待 |
| device.platform | 宿主系统检测和模拟器安装路径事实 |
| device.timing | 设备操作后的延迟策略 |
| device._resources | 内置设备资源路径；私有实现，不作为稳定出口 |

根包只暴露稳定命名空间和明确的模块出口，不通过 __init__.py 平铺复制类和函数。

## 5. ADB 资源契约

ADB 及其 Windows 运行库由 device 持有：

~~~text
autowsgr/common/device/_resources/bin/
├── adb.exe
├── AdbWinApi.dll
├── AdbWinUsbApi.dll
└── scrcpy-server.jar
~~~

规则：

- device 是 ADB 资源的唯一所有者。
- tools/debug_toolkit 不再携带 ADB 二进制副本。
- tools 通过 device.discovery 的公开入口解析 ADB，或通过 device 的资源入口取得路径。
- 包内资源只读，不回写安装目录。
- device 资源路径必须同时支持源码运行和打包运行。
- 资源缺失必须抛出明确的 DeviceNotFoundError 或 DeviceConnectionError。
- ADB 迁移必须验证文件存在、可执行文件可调用和 tools 不再保留重复副本。

## 6. 第一轮阶段计划

### 阶段一：重置任务书和建立基线

动作：

- 用本任务书覆盖旧的 common-system 任务书。
- 保存用户原文、范围、目标出口、阶段和门禁。
- 确认 Git 根目录、绑定 worktree、当前分支和现有用户改动。
- 记录 device 当前目录、资源、配置和测试基线。

阶段门禁：

- 任务书包含完整用户原文。
- 没有覆盖或回退其他 Agent 改动。
- 任务状态为 in_progress。
- 旧任务书内容不再作为当前执行依据。

阶段结束动作：

- 重新阅读本任务书第 1、2、3、4 节。
- 根据基线结果修正下一阶段，不改变用户原始要求。

### 阶段二：打散

动作：

- 对 autowsgr/common/device 下每个 Python 文件做 AST 和人工定义清单。
- 逐项登记每个 class、def、property、配置字段、常量和资源路径。
- 记录直接依赖和被调用关系。
- 区分公开出口、模块内部实现和迁移残留。

当前定义清单：

| 文件 | 定义 | 初步语义归属 |
| --- | --- | --- |
| __init__.py | __all__ | device 能力命名空间出口 |
| config.py | DeviceConfig | 设备配置模型 |
| adb.py | _registry_adb_candidates_windows、_run_adb | ADB 路径和命令的私有实现 |
| adb.py | find_adb、list_devices、connect、capture_screen、restart_server | 内置 ADB 和原始设备 I/O |
| errors.py | DeviceError、DeviceConnectionError、DeviceNotFoundError、GameError、NetworkError、ResourceError | device 错误 |
| types.py | OSType、EmulatorType | device 值类型 |
| timing.py | set_operation_delay、operation_delay | device 操作时序 |
| platform.py | detect_host_os、is_wsl、default_emulator_serial、find_emulator_path | 平台事实 |
| platform.py | _find_windows_emulator_path、_find_macos_emulator_path | 平台内部实现 |
| discovery.py | EmulatorCandidate、__post_init__ | 设备候选值对象 |
| discovery.py | _SERIAL_RULES、_KNOWN_TCP_SERIALS | serial 识别和 TCP 连接规则 |
| discovery.py | identify_emulator_type、detect_emulators | 模拟器候选识别 |
| discovery.py | connect_and_list_devices、prompt_user_select、resolve_serial | 设备选择和 serial 解析 |
| controller/protocol.py | DeviceInfo | 设备连接结果值对象 |
| controller/protocol.py | AndroidController 及抽象方法 | Android I/O 契约 |
| controller/scrcpy.py | ScrcpyController.__init__、connect、disconnect、resolution | Scrcpy 生命周期 |
| controller/scrcpy.py | screenshot、click、swipe、long_tap、key_event、text | 画面和输入操作 |
| controller/scrcpy.py | start_app、stop_app、is_app_running、shell | Android 应用和 shell 操作 |
| controller/scrcpy.py | 其余下划线方法 | Scrcpy 内部连接、编码、解码和恢复 |
| lifecycle/base.py | EmulatorProcessManager 及其方法 | 宿主模拟器生命周期契约 |
| lifecycle/windows.py | WindowsEmulatorManager 及其方法 | Windows 进程适配 |
| lifecycle/linux.py | LinuxEmulatorManager 及其方法 | Linux/WSL 进程适配 |
| lifecycle/macos.py | MacEmulatorManager 及其方法 | macOS 进程适配 |
| lifecycle/__init__.py | create_emulator_manager | 生命周期实现选择 |

阶段门禁：

- 每个定义有唯一语义和目标文件。
- 公开名称不因测试方便而保留。
- 私有实现不被 tools 或上层当作契约。
- 所有资源和配置来源都已登记。

打散结论：ADB 原始命令属于独立的 device.adb 能力；discovery 只负责 serial 和模拟器
候选判断，不再持有 ADB 可执行文件查找和截图实现。

阶段结束动作：

- 重新阅读本任务书第 2、4、5 节。
- 如果发现定义不属于 device，移交 common/TEMP 或明确删除，不继续堆叠兼容层。

阶段状态：已完成。

### 阶段三：识别

动作：

- 遍历 common 同层模块，检查设备连接、ADB、平台、时序、生命周期和设备错误是否重复。
- 检查 common/system 架构说明，严格使用 system.enums、system.errors、system.logger 和 system.files 的现行出口。
- 检查 autowsgr/config.py、config_compat.py、config_method.py、config_method_compat.py 中的设备字段、默认值、迁移和操作延迟。
- 检查 usersettings.yaml 的模拟器配置输入。
- 检查 tools/debug_toolkit 对 ADB、截图和设备控制的调用。
- 记录所有需要上层后续适配的旧路径，但不修改旧调用方。

识别重点：

- EmulatorConfig 的字段所有权和用户覆写边界。
- operation_delay 的可变状态所有权。
- ADB 路径的显式配置、内置资源、系统 PATH 和宿主安装路径优先级。
- Scrcpy server 与 ADB 的资源关系。
- Scrcpy 控制器的连接、截图、输入、应用和 shell 能力边界。
- lifecycle 与 controller 的调用方向。
- device 错误与 system.CommonError 的继承关系。

阶段门禁：

- 没有 device 反向依赖 application、business、server 或页面模块。
- 没有重复的设备配置、时序状态或 ADB 解析器。
- 每个外部配置字段都有 device 或其他模块的唯一所有者。
- system 依赖只使用架构文档允许的出口。

阶段结束动作：

- 重新阅读本任务书第 3、4、5 节。
- 根据依赖审计结果决定哪些旧定义迁入 device、删除或留给其他模块。

识别结论：

- common/system 只提供 system.enums、system.errors、system.logger 和 system.files；device
  不读取 system 私有配置，也不依赖 system 已删除的旧平铺出口。
- autowsgr/config.py 中的 emulator 和 operation_delay 字段属于旧顶层适配输入，本轮不反向
  修改；device 以 DeviceConfig 作为新的私有配置契约。
- config_method.py 和 config_method_compat.py 没有额外的 device 行为配置。
- tools/debug_toolkit 的 ADB 连接、原始截图和 ADB 路径解析应改为调用 device.adb。
- device 内置资源统一放在 common/device/_resources/bin，旧 common/data/bin 的 scrcpy 路径
  不再作为 device 资源来源。

阶段状态：已完成。

### 阶段四：补充

动作：

- 建立 device 私有 DeviceConfig 模型，只有真实 device 行为配置进入其中。
- 区分用户可覆写配置和 device 内部固定参数。
- 建立内置 ADB 资源路径和缺失错误契约。
- 为 controller、discovery、lifecycle 和 timing 补齐输入输出及失败边界。
- 为资源路径、设备连接、平台选择和操作时序补充最小契约测试。
- 不为未来扩展增加空 manager、factory、registry 或兼容字段。

候选 device 配置：

| 配置 | 归属 | 用户是否可覆写 | 说明 |
| --- | --- | --- | --- |
| DEVICE_EMULATOR_TYPE | device | 是 | 模拟器类型 |
| DEVICE_EMULATOR_PATH | device | 是 | 模拟器宿主程序路径 |
| DEVICE_SERIAL | device | 是 | 目标 ADB serial |
| DEVICE_PROCESS_NAME | device | 是 | 宿主进程名 |
| DEVICE_ADB_PATH | device | 是 | 外部 ADB 路径，默认优先内置资源 |
| DEVICE_OPERATION_DELAY_MIN | device | 是 | 操作后延迟下界，单位秒 |
| DEVICE_OPERATION_DELAY_MAX | device | 是 | 操作后延迟上界，单位秒 |
| DEVICE_SCREENSHOT_TIMEOUT | device | 是 | 截图等待上限，单位秒 |
| DEVICE_SCRCPY_MAX_SIZE | device | 是 | 视频最大边长 |
| DEVICE_SCRCPY_BITRATE | device | 是 | 视频码率 |
| DEVICE_SCRCPY_MAX_FPS | device | 是 | 视频帧率 |

以上字段进入本轮 DeviceConfig；字段名使用 DEVICE_ 前缀，用户适配层可在后续映射
usersettings.yaml 的输入。固定协议常量、资源路径和安全校验不作为用户配置。

阶段门禁：

- 配置模型只保存值和校验，不执行连接、启动、截图或输入。
- 用户配置不可以覆盖固定资源路径、协议常量和安全边界。
- 内置 ADB 和 scrcpy server 路径不回写包资源目录。
- 所有新增配置都有默认值、类型、范围和失败测试。

阶段结束动作：

- 重新阅读本任务书第 1、4、5、8 节。
- 删除没有真实行为消费者的配置候选，不因为“以后可能有用”保留。

阶段状态：已完成。

### 阶段五：重组

动作：

- 按 device.XXX 入口重组文件和目录。
- 收缩根包出口，避免平铺旧对象。
- 将 ADB、Windows DLL 和 scrcpy server 统一放入 device 私有资源目录。
- 让 tools/debug_toolkit 只调用 device 公开入口或资源能力。
- 将不属于 device 的定义删除或交给明确的其他所有者。
- 保留旧实现只作为只读参考，不建立旧新双轨运行时路径。

阶段门禁：

- 每个公开入口只有一个定义源。
- device 根包、各子模块和私有实现的依赖方向清晰。
- tools 不含重复 ADB 二进制。
- source、editable install 和打包运行的资源路径均可验证。
- 中间状态不依赖已删除的 TEMP 聚合出口。

阶段结束动作：

- 重新阅读本任务书第 2、4、5、6 节。
- 按实际重组结果修正架构文档，不反向修改用户要求。

阶段状态：已完成。

### 阶段六：文档、单测和验收

动作：

- 产出 docs/AutoWSGR3.0/common/[架构]device.md。
- 文档描述模块架构、功能、调用示例、配置覆写、资源规则、维护方法和边界。
- 单测统一放在 testing/common/device。
- 验证各公开出口、配置模型、ADB 资源、平台分支、发现逻辑、时序和控制器协议。
- 执行 scoped pre-commit、compileall、pytest、import smoke、资源 smoke 和 git diff --check。
- 记录未验证的实机路径，不伪称端到端可用。

阶段状态：已完成。

最终门禁：

~~~text
1. 任务书包含用户原文且状态为 done
2. device AST 定义清单无遗漏
3. device 根包和子模块公开出口 import smoke
4. device 私有配置默认值、用户覆写和非法输入测试
5. 内置 ADB、DLL、scrcpy server 资源存在性和路径测试
6. discovery、platform、timing 单元测试
7. controller/lifecycle 协议和模拟测试
8. testing/common/device 专项 pytest
9. scoped pre-commit
10. git diff --check
11. 记录上层旧调用方未适配范围
~~~

## 7. 台账

| 阶段 | 时间 | 结果 | 门禁 | 状态 |
| --- | --- | --- | --- | --- |
| 任务重置 | 2026-09-16 | 以 device 治理要求覆写旧 common-system 任务书 | 用户原文、范围和目标出口已写入 | 已完成 |
| 打散 | 2026-09-16 | 登记 device 全量定义、资源和旧实现去向 | AST 清单、定义唯一归属 | 已完成 |
| 识别 | 2026-09-16 | 审计 common 同层、四个配置文件和 debug toolkit | 依赖/配置/资源来源检查 | 已完成 |
| 补充 | 2026-09-16 至 2026-09-17 | 建立 DeviceConfig、ADB 资源和失败边界 | 配置、资源、发现和时序测试 | 已完成 |
| 重组 | 2026-09-16 至 2026-09-17 | 按 device.XXX 重排模块并收缩根包出口 | 出口、依赖、资源和打包检查 | 已完成 |
| 文档与单测 | 2026-09-17 | 产出架构说明和 testing/common/device 测试 | 14 个专项测试、compileall、import smoke | 已完成 |
| 最终验收 | 2026-09-17 | 形成可交付 device 模块 | 构建、资源归档、scoped pre-commit、diff check | 已完成 |

## 8. 错误与风险记录

| 问题 | 处理 |
| --- | --- |
| 旧 common-system 任务书与当前 device 任务冲突 | 已按用户要求覆写，本任务书原文作为当前事实来源 |
| device 现有根包平铺大量对象 | 先盘点，再收缩为 device.XXX 命名空间 |
| tools/debug_toolkit 当前携带 ADB 副本 | 迁移到 device 资源目录，tools 后续只引用 |
| 上层仍引用旧 system/device 出口 | 本轮不适配，记录为后续联调风险 |
| device 配置字段可能与顶层配置重复 | 先审计所有权，再保留唯一配置源 |
| 实机连接和 Scrcpy 视频流无法在离线环境验证 | 保留模拟器/协议 smoke，并明确未验证实机路径 |

## 9. 当前状态

### 最终验收记录

- `testing/common/device`：13 passed。
- `autowsgr/common/device`、`testing/common/device` 和 `tools/debug_toolkit`：compileall 通过。
- device 根包、子模块、配置和生命周期工厂：import smoke 通过。
- DeviceConfig 合法/非法配置、ADB 命令解析、设备发现、平台、生命周期和时序：专项测试通过。
- wheel 和源码包均包含 ADB、两份 Windows DLL 与 Scrcpy server。
- scoped `pre-commit` 通过，包含 Ruff、AST、尾空格、密钥和 codespell 检查。
- `git diff --check` 通过。
- 真实模拟器、Scrcpy 视频流和宿主进程启停未在本环境执行，属于后续实机门禁。
- 旧 application、business、server、testing/ops、GUI 及工具旧调用方未适配，符合本轮范围外约束。

本任务书状态为 done。后续工作是由上层按本文和
`docs/AutoWSGR3.0/common/[架构]device.md` 适配新的 device.XXX 契约。

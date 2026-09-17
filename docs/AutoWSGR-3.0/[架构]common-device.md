# common/device 架构说明

版本：AutoWSGR-3.0

## 1. 模块定位

`common/device` 是程序级设备基础能力层，负责为程序提供模拟器连接、Android 输入、
设备截图、应用控制和宿主模拟器生命周期能力。

本模块只处理设备事实和设备 I/O，不识别游戏页面，不编排业务任务，不理解战斗、后勤、
导航或用户业务字段。对外使用 `service.DeviceService` 作为统一入口；其下的执行器和
流程模块只服务于 device 内部的垂直调用链。

## 2. 模块架构

~~~text
autowsgr/common/device/
├── __init__.py                         # device 命名空间，只暴露 service
├── config.py                           # ADB、Scrcpy 和设备操作配置
├── errors.py                           # device 错误类型
├── service.py                          # DeviceService 统一入口
├── adb_engine/
│   ├── __init__.py                     # ADB 执行器包
│   ├── executor.py                     # ADB 可执行文件和 adb.exe 调用
│   ├── adb.exe                         # Windows 随包 ADB
│   ├── AdbWinApi.dll
│   └── AdbWinUsbApi.dll
├── scrcpy_engine/
│   ├── __init__.py                     # Scrcpy 执行器包
│   ├── executor.py                     # Scrcpy server、socket 和输入协议
│   └── scrcpy-server.jar
└── device_engine/
    ├── __init__.py                     # 设备引擎包
    ├── session.py                      # 设备会话唯一状态持有者
    ├── foundation/
    │   ├── __init__.py                 # 基础能力包
    │   ├── platform.py                 # 宿主系统和模拟器路径事实
    │   └── delay.py                    # 操作前延迟计算
    └── orchestration/
        ├── __init__.py                 # 流程包
        ├── connection.py               # 设备连接和断开流程
        ├── discovery.py                # 设备发现和 serial 选择
        ├── operation.py                # 输入、应用和 Shell 操作聚合
        ├── screenshot.py               # 截图读取和保存流程
        └── lifecycle/
            ├── __init__.py             # 生命周期稳定出口
            ├── service.py              # 生命周期工厂和会话流程
            ├── base.py                 # 宿主生命周期抽象契约
            ├── linux.py                # Linux/WSL 实现
            ├── macos.py                # macOS 实现
            └── windows.py              # Windows 实现
~~~

依赖方向：

~~~text
DeviceService
    └── device_engine.orchestration
        ├── connection ──→ discovery ──→ adb_engine.executor
        │       └──────────────→ scrcpy_engine.executor
        ├── operation ─────────→ session ──→ scrcpy_engine / ADB 设备对象
        ├── screenshot ────────→ session / system.files
        └── lifecycle ─────────→ platform / ADB 设备列表 / 宿主进程实现

adb_engine.executor ──→ system.logger / device.errors
scrcpy_engine.executor ──→ device.config / device_engine.foundation.delay
device.config ──→ device_engine.foundation.platform
~~~

`device_engine` 可以聚合 `adb_engine` 和 `scrcpy_engine`，但 ADB 执行器不依赖
Scrcpy，Scrcpy 执行器不直接负责设备发现，平台生命周期不负责 Android 输入。

## 3. 统一入口：service.py

### 3.1 DeviceService

`DeviceService` 持有一个 `DeviceSession`，把设备能力按四个业务区域提供给调用方：

| 区域 | 入口 | 作用 |
| --- | --- | --- |
| 连接模拟器 | `connect()` | 选择设备，建立 ADB、Scrcpy、视频和控制通道 |
| 操作模拟器 | `click()`、`swipe()`、`long_tap()`、`key_event()`、`text()` | 执行屏幕输入 |
| Android 控制 | `start_app()`、`stop_app()`、`is_app_running()`、`shell()` | 控制应用和执行设备内 Shell |
| 截图 | `resolution`、`screenshot()`、`save_screenshot()` | 获取分辨率、读取 RGB 截图和受限保存 |
| 连接维护 | `is_connected()`、`disconnect()`、`reconnect()` | 维护 Scrcpy 设备连接 |
| 模拟器维护 | 在线检查、启动、停止、重启和等待上线 | 管理宿主模拟器进程 |

统一入口的方法保留简洁设备语义；入口内部调用使用带对象名的私有函数，例如
`connection._connect_device()`、`operation._click_screen()` 和
`screenshot._capture_device_screenshot()`。

### 3.2 调用示例

~~~python
from autowsgr.common import device

device_service = device.service.DeviceService()
info = device_service.connect()

try:
    device_service.click(0.5, 0.5)
    screen = device_service.screenshot()
finally:
    device_service.disconnect()
~~~

坐标使用 0.0 到 1.0 的屏幕相对坐标。`screenshot()` 返回 RGB 数组；底层 ADB 截图
函数返回 OpenCV BGR 数组，两个契约不能混用。`save_screenshot()` 必须显式传入
`allowed_root`，目标路径只能写入允许目录。

## 4. ADB 执行器：adb_engine.executor

### 4.1 能力

ADB 执行器是 `adb.exe` 的唯一调用边界，负责：

- 定位显式、系统 PATH、随包和宿主注册表中的 ADB；
- 读取 ADB 设备列表及状态；
- 连接指定 serial 并确认设备状态；
- 通过 `exec-out screencap` 获取 BGR 截图；
- 重启 ADB server。

它不选择目标模拟器，不解释 serial 对应的业务类型，不管理宿主进程，也不启动 Scrcpy。

### 4.2 入口契约

~~~python
from autowsgr.common.device.adb_engine import executor

adb_path = executor.find_adb_executable()
devices = executor.read_adb_devices(adb_path)
executor.connect_adb_device('127.0.0.1:16384', adb_path)
screen = executor.capture_device_screenshot('127.0.0.1:16384', adb_path)
~~~

| 方法 | 返回值 | 业务作用 |
| --- | --- | --- |
| `find_adb_executable(adb_path=None)` | `Path` | 定位可执行 ADB |
| `read_adb_devices(adb_path=None)` | `list[tuple[str, str]]` | 读取 serial 和状态 |
| `connect_adb_device(serial, adb_path=None)` | `None` | 建立并确认 ADB 连接 |
| `capture_device_screenshot(serial, adb_path=None)` | `numpy.ndarray` | 读取 BGR 设备截图 |
| `restart_adb_server(adb_path=None)` | `None` | 重启 ADB server |

显式路径不存在时直接抛出 `DeviceNotFoundError`。未指定路径时，定位顺序为系统 PATH、
Windows 随包 ADB、Windows 模拟器注册表路径；所有路径都不存在时失败。

## 5. Scrcpy 执行器：scrcpy_engine.executor

### 5.1 ScrcpyEngine

`ScrcpyEngine` 负责一个已连接 ADB 设备的 Scrcpy 生命周期和 Android 输入协议：

~~~text
已连接 ADB 设备
    ↓
推送并启动 scrcpy-server
    ↓
建立视频通道和控制通道
    ↓
启动 H264 解码线程并等待首帧
    ↓
提供 RGB 截图和输入事件
~~~

主要方法：

| 方法 | 作用 |
| --- | --- |
| `connect_scrcpy(device, serial)` | 建立服务、双通道、解码线程并等待首帧 |
| `disconnect_scrcpy()` | 关闭服务、socket 和解码线程 |
| `is_scrcpy_connected()` | 读取当前 Scrcpy 通道状态 |
| `capture_screenshot()` | 获取当前 RGB 视频帧 |
| `click_screen(x, y, delay=False)` | 发送一次点击 |
| `swipe_screen(x1, y1, x2, y2, duration, delay=False)` | 发送一次滑动 |
| `long_press_screen(x, y, duration)` | 发送一次长按 |
| `send_key_event(key_code, delay=False)` | 发送 Android 按键事件 |
| `input_text(content, delay=False)` | 输入 ASCII 或通过剪贴板输入文本 |

通道建立、服务部署、控制消息和恢复函数属于执行器内部实现，不作为跨层流程拼装入口。
视频或控制流断开时，执行器可以尝试重建 Scrcpy 流；恢复耗尽则抛出
`DeviceConnectionError`。

### 5.2 操作前延迟

`DeviceConfig.DEVICE_OPERATION_DELAY_MIN/MAX` 初始化当前进程的延迟范围。点击、滑动、
按键和文本输入只有在入口参数 `delay=True` 时才会在操作前取随机延迟；配置默认上下界
均为 `0.0`，因此默认不产生实际等待。长按保持现有语义，不额外应用该延迟。

## 6. device_engine 流程

### 6.1 会话状态

`DeviceSession` 是一次设备服务实例的状态持有者，保存：

- `DeviceConfig`；
- ADB serial 和 `adbutils` 设备对象；
- `ScrcpyEngine`；
- 宿主模拟器生命周期管理器。

连接、操作、截图和生命周期流程都通过同一会话读取状态，不各自创建第二份连接状态。

### 6.2 连接流程

`orchestration.connection` 的内部流程为：

~~~text
_connect_device(session)
    ↓
resolve_device_serial(config)
    ↓
connect_adb_device(serial)
    ↓
connect_scrcpy(adb_device, serial)
    ↓
写回 session.serial / session.adb_device
~~~

连接失败时清理会话中的 ADB 引用；完整连接成功后返回 `DeviceInfo(serial, resolution)`。
`_disconnect_device()` 清理 Scrcpy 通道、ADB 对象和 serial，`_reconnect_device()` 先断开
再完整建立连接；这些函数只由 `DeviceService` 调用。

### 6.3 设备发现

`orchestration.discovery` 按以下职责提供入口：

| 方法 | 作用 |
| --- | --- |
| `recognize_emulator_type(serial)` | 根据 serial 规则识别模拟器类型 |
| `discover_emulator_candidates(adb_path=None)` | 读取并筛选在线设备候选 |
| `discover_known_adb_devices()` | 连接已知 TCP 地址后读取设备列表 |
| `select_emulator_candidate(candidates)` | 通过命令行选择一个候选 |
| `resolve_device_serial(config=None, adb_path=None)` | 按配置、唯一候选、类型匹配和交互选择 serial |

`ADB_CONNECTION` 存在时优先使用显式地址；否则只接受状态为 `device` 的候选。多设备且
无法按模拟器类型唯一确定时，在非交互环境直接失败，不静默选择。

### 6.4 操作和截图

`orchestration.operation` 只聚合下层能力，不保存新的设备状态；其函数均为 service 的私有
转发实现：

- `_click_screen`、`_swipe_screen`、`_long_press_screen` 调用 Scrcpy 输入；
- `_send_key_event`、`_input_text` 调用 Scrcpy 按键和文本输入；
- `_start_application`、`_stop_application`、`_check_application_running` 和
  `_execute_shell_command` 调用 ADB 设备对象。

`orchestration.screenshot` 使用 `_capture_device_screenshot(session)` 读取 RGB 视频帧，
使用 `_save_device_screenshot(session, path, allowed_root=...)` 委托 `system.files` 保存，
不自行实现文件写入。

### 6.5 模拟器生命周期

`orchestration.lifecycle.service` 根据宿主 `OSType` 创建 `EmulatorProcessManager`。工厂是该
子模块唯一的创建入口，管理器类只承载宿主生命周期实现契约，service 会话包装均为私有实现：

| 方法 | 作用 |
| --- | --- |
| `create_emulator_process_manager(...)` | 选择 Windows、Linux/WSL 或 macOS 实现 |
| `_check_emulator_running(session)` | 检查模拟器是否运行 |
| `_start_emulator(session)` | 启动模拟器并等待上线 |
| `_stop_emulator(session)` | 停止模拟器 |
| `_restart_emulator(session)` | 停止后重新启动模拟器 |
| `_wait_for_emulator_online(session, timeout=120)` | 等待模拟器上线 |

管理器类内部使用同一组明确方法：`check_emulator_running()`、`start_emulator()`、
`stop_emulator()`、`restart_emulator()` 和 `wait_for_emulator_online()`。Windows、
Linux/WSL 和 macOS 文件只承载宿主命令差异。

## 7. 配置契约：config.py

`DeviceConfig` 只保存 device 真实消费的配置，不读取 `usersettings.yaml`，也不保存运行时
设备对象。模型不可变且拒绝未知字段：

| 字段 | 默认值 | 作用 |
| --- | --- | --- |
| `ADB_CONNECTION` | `None` | 多设备时显式指定 ADB 连接地址 |
| `SCRCPY_MAX_SIZE` | `0` | Scrcpy 最大边长，0 表示不限制 |
| `SCRCPY_BITRATE` | `8000000` | Scrcpy 视频码率，单位 bit/s |
| `SCRCPY_MAX_FPS` | `0` | Scrcpy 最大帧率，0 表示不限制 |
| `SCRCPY_SCREENSHOT_TIMEOUT` | `10.0` | 首帧和视频恢复等待上限，单位秒 |
| `DEVICE_EMULATOR_TYPE` | `雷电` | 模拟器类型 |
| `DEVICE_EMULATOR_PATH` | `None` | 宿主模拟器程序路径 |
| `DEVICE_OPERATION_DELAY_MIN` | `0.0` | 操作前延迟下界，单位秒 |
| `DEVICE_OPERATION_DELAY_MAX` | `0.0` | 操作前延迟上界，单位秒 |

增加字段前必须同时满足：它确实改变 device 行为、不同环境需要不同取值、有明确默认值
和校验边界，并且决定是否需要用户或 GUI 覆写。固定协议常量、随包资源路径、自动探测的
serial 和进程名不增加配置字段。

## 8. 错误契约：errors.py

device 错误继承 `system.errors.CommonError`：

~~~text
CommonError
└── DeviceError
    ├── DeviceConnectionError
    ├── DeviceNotFoundError
    └── GameError
        ├── NetworkError
        └── ResourceError
~~~

错误类只表达捕获边界，不在错误类中执行重连、重启或业务恢复。设备连接、路径、协议和
进程失败由执行器或流程抛出；调用方决定重试、回退或终止。

## 9. 日志契约

device 使用 `system.logger.get_logger()` 创建日志对象，只使用 DEBUG、INFO、WARNING 和
ERROR 四级。

INFO 遵守统一格式，固定业务词汇使用中文：

~~~text
[DEVICE] 设备连接 → 建立：序列号='127.0.0.1:16384'，分辨率=(960, 540)，结果=成功
[DEVICE] 设备发现 → 选择：来源=唯一在线设备，序列号='emulator-5554'，结果=成功
[DEVICE] 模拟器进程 → 启动：结果=成功
~~~

DEBUG 记录 ADB source、Scrcpy channel、重试次数和协议事实等诊断变量；WARNING 只用于
降级、重试或可继续恢复的异常；ERROR 只在目标无法完成、恢复耗尽或继续执行不安全时
收口。原子点击、普通帧轮询和纯参数转发不单独产生业务日志。

日志位置由拥有动作或判断的流程负责：设备连接流程记录完整连接结果，Scrcpy 执行器记录
窄范围通道诊断，生命周期管理器记录宿主进程动作和失败，不在 service 重复打印底层细节。

## 10. 模块维护方法

### 10.1 添加设备能力

1. 确认能力属于设备连接、Android I/O、截图或宿主模拟器生命周期。
2. 直接调用 `adb.exe` 的内容放入 `adb_engine/executor.py`；Scrcpy 协议放入
   `scrcpy_engine/executor.py`。
3. 跨执行器的完整流程放入 `device_engine/orchestration` 对应文件。
4. 给函数使用“动作 + 业务对象”命名，例如 `read_adb_devices`、`_connect_device`、
   `capture_device_screenshot`；纯判断使用 `check_`，纯转换使用 `convert_`，等待方法必须
   写明目标。
5. 更新本说明的目录、能力表、调用示例、日志和测试契约。

不要在 device 中增加 `utils`、`helpers`、`manage`、`process` 等无法说明所有权的容器，
也不要为旧调用方添加旧名称别名。

### 10.2 添加 ADB 或 Scrcpy 资源

1. 将随包资源放入对应的 `adb_engine` 或 `scrcpy_engine` 目录。
2. 由对应 executor 私有解析资源路径。
3. 流程模块只调用 executor 的语义化方法，不复制二进制调用逻辑。
4. 增加资源存在性和路径解析测试，并检查发行包是否包含资源。

### 10.3 移出 device

页面识别、ROI、OCR 和模板匹配归 vision 或 UI；业务规则和任务流程归 application 或
business；任务控制信号归 dispatch/runtime；调试产物归 tools。仅被其他模块使用、但不
属于设备 I/O 的定义不得为了方便继续留在 device。

## 11. 测试与交付门禁

新架构测试只放在：

~~~text
testing/common/device/
~~~

至少覆盖：

1. `autowsgr.common.device` 和 `device.service` 导入出口；
2. DeviceConfig 默认值、合法值和未知字段拒绝；
3. ADB 路径定位、设备列表解析、连接状态检查和截图解码；
4. serial 识别、候选筛选和选择失败边界；
5. 平台事实、生命周期工厂和模拟器管理器方法契约；
6. 操作前延迟上下界和 Scrcpy 基础状态；
7. `compileall`、定向 pytest、scoped pre-commit 和 `git diff --check`。

真实模拟器连接、Scrcpy 视频流、宿主进程启动停止属于实机门禁；离线单测通过不等于实机
链路已经验收。旧测试路径不再作为 device 契约维护。

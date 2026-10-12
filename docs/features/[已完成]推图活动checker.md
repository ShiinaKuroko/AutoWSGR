# [任务书] 推图活动 checker（v10 · 执行中）

> 状态：**本批完成**（2026-10-10 v15：§9 七项全部完成；导航器侧的点击编排属下一批，见 §1 范围）
> Task ID：`20260913-shiinaskuya-upgrade-7b3e`｜分支：`codex/20260913-shiinaskuya-upgrade-7b3e`
> 关联：`[台账]导航器重写.md`｜`[计划]活动域与活动导航器设计.md`｜`[规范]dispatch-context临时规范.md`｜
> `docs/AutoWSGR-3.0/[架构]common-vision.md`

## 0. 已对齐结论（用户六轮答复）

| # | 结论 |
| --- | --- |
| 1 | **识别全部做进导航器**；UI 控制器**只管操作（点击）** |
| 2 | 第 3 段目标 = **出征准备页（编队页）的前置页面** = 地图上的节点浮窗 |
| 3 | 流程为**前识别 / 后识别**；OCR 同样，在既有 def 上扩流程 |
| 4 | 地图名容错：有括号按括号判，认不出按"名称 + 困难"；**"困难"二字为困难模式独有** |
| 5 | 关卡标题形如 **Ex + 数字 + 名称**；去除非字母数字后匹配；大小写不敏感；EX/名称任一命中即可 |
| 6 | 所有任务**由 YAML 驱动**：GUI/CLI 发指令 → 处理器找 YAML → 解析加载 |
| 7 | **task_type = `event_fight`**、**`event = normal`**；章节 **`EX1…EX12`**；**期号 = `20260930`** |
| 8 | dispatch 是统一管上下文的地方，先临时桥接；**临时规范可以改** |
| 9 | 点击编排 = `checker → 控制器点击 → checker`，属导航器流程；**先做 checker，再做导航器** |
| 10 | 首页入口点击归 **main_page 控制器**，参数语义改成"活动入口" |
| 11 | 目录用**小写 `event`**；模板 + ROI 归导航器；点击坐标归 UI 控制器 |
| 12 | **静态验证数据外挂**（`debug/nav/event/`，不入库）；**`tools/` 随时可改** |
| 13 | OCR 扩展用参数；每期 list = 关卡名称；外挂到 `resources/data/map/event/20260930/stages.yaml` |
| 14 | "无按钮 + 普通名 = 普通未通关"是兜底逻辑，不需样本截图 |
| 15 | **checker 是一个文件** `checker/event.py`；**入口传入 `event_type`** 激活不同链路 |
| 16 | 用户对前/后识别的理解：**vision 已包一层循环**——前识别反复识别多次，确认**没有**识别到才报错；后识别反复识别多次，确认**还存在**才报错；目的是保证 UI 控制器在**正确页面**点击并得到**正确结果** |
| 17 | **是否符合架构说明决定做法**（用户授权"符合就做"） |
| 18 | 不为旧实现做兼容；先重写，跑通后由用户统一清死代码 |
| 19 | **报错归属定案（路径 A）**：`common.vision` 只返回识别结果；`satisfied=False` 当事实；"确认没出现/仍存在就报错"由**导航器**上报 |

## 1. 目标与范围

**本批交付**：`checker/event.py`（三个方法，推图 normal 链路）+ focused 单测 + E2E 静态帧入口 +
dispatch 两字段（含回写临时规范）。
**本批不做**：点击动作、导航器编排、编队页之后的流程、其它活动玩法实现。

## 2. 输入资产（外挂，不入库）

- 模板：`debug/nav/event/推图活动_模板/`（4 张 720P + `推图活动ROI_720P.yaml`）
- 截图：`debug/nav/event/推图活动截图/`；标注图：`debug/nav/event/推图活动roi裁切模板/`

### 2.1 ROI（**以 YAML 的 `roi_px` 为准**）

| 项 | 像素框 | 用途 |
| --- | --- | --- |
| 首页活动入口 | 1094,232,1265,492 | 模板匹配 |
| 模式按钮 | 13,648,143,671 | 模板匹配 |
| 地图名 | 515,21,762,52 | OCR |
| 出击准备按钮 | 1009,588,1184,635 | 模板匹配 |
| 关卡标题 | 35,45,266,78 | OCR |

> ⚠️ `[可参考]推图活动ROI与点击坐标.md` 的"归一化 ROI"列被截断且不自洽（模式按钮算成 128×20 < 模板 129×22），
> 会让 `match_template` 早退返回 0 分。该文档只取 OCR 框与点击坐标。

### 2.2 点击坐标（UI 控制器持有，本批不用）

模式切换 (77, 658.5)；出击准备 (1095.5, 610.5)；EX7/8/9 = (112,179)/(760,163)/(1007.5,155.5)；
EX10/11/12 = (263.5,376.5)/(608.5,452.5)/(1012,538)；EX1–EX6 与 EX7–EX12 共用同格（编号差 6）。

## 3. 实测证据（1280×720 真图，阈值 0.85）

| 截图 | 状态 | mode_normal | mode_hard | home_entry | sortie_prepare |
| --- | --- | --- | --- | --- | --- |
| 活动首页 | 首页 | 0.038 | 0.011 | **1.000 ✓** | −0.014 |
| 普通地图 | 干净页 | 0.644 | **1.000 ✓** | 0.119 | −0.101 |
| 困难地图 | 干净页 | **1.000 ✓** | 0.644 | 0.188 | −0.075 |
| E1–E12 | 节点浮窗 | 0.12–0.28 | 0.09–0.25 | ≈0 | **1.000 ✓** |

OCR：地图名 `最强之舟`(0.98)、`最强之舟（困难）`(0.913 全角)、E7/E12 `最强之舟 (困难)`(0.898 半角)；
标题 `Ex-1 天降火雨`、`Ex-7 天降火雨(困难)`、`Ex-12 海空鏖战(困难`（右括号丢失）；干净页标题 ROI 为空。

**三条硬结论：** ① 难度只能在**干净地图页**判；② 只能按**"困难"二字**判难度；③ `sortie_prepare` 命中 +
标题 ROI 有文本 ⇒ 浮窗态。

## 4. checker 契约（单文件 `event.py`）

```python
# autowsgr/application/ui/navigation/checker/event.py

class EventMode(StrEnum):
    NORMAL = 'normal'
    HARD = 'hard'

@dataclass(frozen=True, slots=True)
class EventMapState:
    on_clean_map: bool              # False = 浮窗态，难度结论不可信
    button_mode: EventMode | None   # 按钮显示的模式（= 切换目标）；None = 没有按钮
    title_mode: EventMode | None    # 地图名对应模式；None = 没读到
    current_mode: EventMode | None  # 结论；None = 不下结论

def check_event_entry(ctx: ContextHandle, *, event_type: str) -> bool: ...
def read_event_map_state(ctx: ContextHandle, *, event_type: str) -> EventMapState: ...
def check_event_sortie_prepare(ctx: ContextHandle, *, event_type: str, stage: str) -> bool: ...
```

- `event_type` 由调用方传入（用户第 15 条）；本批只实现 `normal`；未支持取值抛 `ValueError`（入参校验）。
- 两个 `check_*` 返回 `bool`（读不到时为 False），因为导航器需要拿到事实才能按路径 A 报错；checker 自身不抛业务错误。
- 三个方法**不包装、不上报识别错误**（用户第 16 条）：识别结果按 §5 的语义处理。

### 4.1 取值表（只给事实）

| 场景 | on_clean_map | button_mode | title_mode | current_mode |
| --- | --- | --- | --- | --- |
| 干净页·普通难度 | True | HARD | NORMAL | NORMAL |
| 干净页·困难难度 | True | NORMAL | HARD | HARD |
| 干净页·普通未通关（兜底） | True | None | NORMAL | NORMAL |
| 节点浮窗态 | False | None | 视情况 | None |
| 按钮与地图名矛盾 | True | NORMAL / HARD | 同名 | None |
| 无按钮 + 困难名（不可能态） | True | None | HARD | None |
| 按钮与地图名都没读到 | True | None | None | None |

### 4.2 判定规则

- **模式按钮**：`mode_normal` 命中 ⇒ 当前困难；`mode_hard` 命中 ⇒ 当前普通；都不中 ⇒ None。
- **地图名**：含 `困难` ⇒ HARD；否则含本期普通地图名 ⇒ NORMAL。
- **干净页判据**：`sortie_prepare` 未命中 **且** 标题 ROI 无文本 ⇒ `on_clean_map=True`。
- **方法 3**：`sortie_prepare` 命中 **且** 标题满足任一：EX+数字（去非字母数字、转小写后匹配 `ex(\d+)`，
  与目标章节号一致）或 章节名称（与本期 list 比对）。

## 5. 识别语义与错误的架构归属（读架构文档后的结论）

### 5.1 架构文档原文（`[架构]common-vision.md` §12）

- 本模块**没有自定义错误基类**；只用 `ValueError` / `FileNotFoundError` / `RuntimeError`；
- **调用方可以把 `TemplateMatchResult.matched=False`、空 OCR 列表或 `parse_counter` 的 `None`
  作为正常识别事实处理**；
- 通用视觉层不捕获后重试、不静默降级、不替调用方决定页面恢复；异常继续向**拥有恢复策略的上层**抛。

### 5.2 对照结论

| 用户诉求 | 架构现状 | 结论 |
| --- | --- | --- |
| 前/后识别已包一层循环（反复识别，确认没出现/仍存在） | 是，`service._retry` 就是唯一循环 | 一致 |
| "确认没识别到 / 仍存在"→ 报错 | 循环耗尽后返回 `satisfied=False`（正常事实），**不抛错** | **冲突**：架构把"读不到"定义为事实 |
| 报错由 common.vision 上报 | 架构把恢复与报错留给**上层** | 需二选一 |

### 5.3 定案：路径 A（用户 2026-10-09 确认）

> 用户原话："vision 只返回结果，报错由调用方处理……让导航器报错吧。"

**路径 A（推荐，零契约破坏）**：保持架构现状。

- `before_*` / `after_*` 继续"循环到期望满足，耗尽返回 `satisfied=False`"，不新增错误类型；
- checker 只把 `satisfied` 组装成事实返回（不报错，符合用户第 15/16 条"checker 不上报错误"）；
- **"确认没出现/仍存在就报错"由导航器编排层实现**（它拥有恢复策略，下一批做）；
- 探测场景（模式按钮是否存在）直接用 `before_template(..., attempts=1)` 的 `satisfied`，
  **不需要新增任何 def**（比我上一轮提的方案更省）。

**路径 B（按字面改 common.vision）**：`before_*` / `after_*` 在重试耗尽后抛识别错误。

- 需要新增错误类型（架构说本模块没有自定义错误基类）→ 要改架构文档 §12 + §2.4 + §16 门禁；
- 需要改全部调用方：`checker/home.py`、`checker/sortie.py`（两者是另一会话的未提交半成品）、
  `controller/home/main_page/page.py`、`workflow.py`；
- 页面身份判定会变成异常驱动（"不是这个页面"要看 try/except）。

## 6. 每期外挂数据

| 内容 | 落点 |
| --- | --- |
| 模板（4 张） | `resources/image/application/ui/navigation/checker/event/` |
| 关卡名称 list + 地图名 | `resources/data/map/event/20260930/stages.yaml` |
| ROI（5 个） | `checker/event.py` 常量 |
| 点击坐标 | `controller/home/event_page/constants.py`（本批不用） |

`stages.yaml` 拟稿（模板文件名固定不带期号，换期换内容）：

```yaml
map_name:
  normal: 最强之舟
  hard: 最强之舟（困难）
stages:
  EX1: 天降火雨
  EX2: 鹰群出击
  EX3: 追逐跳跃
  EX4: 火力全开
  EX5: 四面合围
  EX6: 海空鏖战
  EX7: 天降火雨（困难）
  EX8: 鹰群出击（困难）
  EX9: 追逐跳跃（困难）
  EX10: 火力全开（困难）
  EX11: 四面合围（困难）
  EX12: 海空鏖战（困难）
```

## 7. 任务 / 章节桥接（已批准）

`[规范]dispatch-context临时规范.md`：§8 禁止通用 `get/set`；§5 要求具名字段与所有权；§6 禁止把页面坐标、
模板路径、私有常量放进 Context。拟加两个具名任务字段：

| 字段 | 来源 | 生命周期 | 写入者 | 读取者 |
| --- | --- | --- | --- | --- |
| `event_type`（YAML `event`=normal） | 任务 YAML 参数 | 任务级 | 处理器（bind 时注入） | 导航器 / checker |
| `event_stage`（如 `EX7`） | 任务 YAML 参数 | 任务级 | 处理器 | 导航器 / checker |

导航器从 Context 读出后作为参数传给 checker（用户第 15 条）。实施时同步更新 `ContextTemplate`、
`ContextHandle` 语义入口、临时规范 §6 字段表。

## 8. 职责边界

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| 导航器 / checker | 模板、ROI、识别规则、前/后识别、页面事实、页面切换编排、**按事实决定报错** | 点击 |
| UI 控制器 | 点击动作 + 点击坐标 | 模板、ROI、页面识别 |
| main_page 控制器 | 首页活动入口点击（语义改"活动入口"） | 活动页识别 |
| 处理器 / YAML | 找 YAML、解析、task_type 分派、event 参数注入 | 识别与点击 |

## 9. 实施顺序

1. [x] 资产入库：4 张模板 + `resources/data/map/event/20260930/stages.yaml`。
2. [x] `before_ocr` / `after_ocr` 支持候选序列（在既有 def 上扩，不新开 def）。
3. [x] `checker/event.py` 三个方法 + `EventMapState`（后按 §12 拆成 `event/` 包）。
4. [x] focused 单测（合成数据 + 替身，不依赖外挂图）：12 项通过。
5. [x] E2E 静态帧入口（`--static` + 截图替身 `use_frame`）+ `event_check` case：真图静态验证 **8 步全过**
   （首页入口命中、普通地图=普通、困难地图=困难、EX7 前置页成立；模板匹配 score=1.000，OCR 真跑）。
6. [x] dispatch 加 `event_type` / `event_stage` 具名字段：`ContextTemplate.for_task` 可选参数 +
   `ContextHandle.read_event_type()` / `read_event_stage()`；已回写临时规范 §6 字段表与 §8 接口列表；
   `testing/dispatch/context/test_manager.py` 加 2 项契约测试。
7. [x] 按 §14 补日志：活动识别（读按钮/地图名/关卡标题/判浮窗/查入口）、活动地图状态结论、
   出征准备前置页校验、活动数据加载，各一条 DEBUG 事实日志，使用 loguru 风格占位符。

## 10. 验证方案

- **静态验证（外挂）**：E2E 加"帧来源"（真机 / 单张图 / 目录），设备替身返回固定 PNG；`shot()` 走
  `ctx.runtime.ctrl.screenshot()`；case 用绝对路径，不入库。
- **focused 单测**：取值表 7 种场景 + 方法 3 两条分支 + 章节越界 + 未支持 `event_type` 入参错误。
- 本期不跑全量 pytest / pre-commit（worktree 规则）。

## 11. 待确认（无；已全部对齐）

接口形态按 §4 执行：`check_event_entry` / `check_event_sortie_prepare` 为断言式（成功即返回，读不到时由导航器按事实报错），
`read_event_map_state` 返回 §4.1 的事实结构。

**§5.3 路径 A 还是路径 B？**

- **A（推荐）**：common.vision 不动；`satisfied=False` 当事实；"读不到就报错"由导航器编排层做；探测用
  `before_template(attempts=1)`，不加任何新 def。
- **B**：按字面把 `before_*`/`after_*` 改成耗尽即抛错；要改架构文档 §12/§2.4/§16，并改 4 个现有调用方
  （其中 2 个是另一会话的未提交文件）。

## 12. 结构调整（已执行，2026-10-10）

**背景**：用户指出单文件 `event.py` 不够框架化——① 将来要支持其它活动玩法；② 私有方法太多，checker 应当只留入口。

**已确认的方向（用户 2026-10-10）**：

1. 舰R 活动分三类：**普通推图 / 立体强袭 / 舰队问答**，识别方法不一致，因此**各自独立成一个 checker**，不共用实现。
2. **允许代码重复**：各玩法各持自己的入口与事实模型，重复没关系，后续再收，不求一次到位。
3. 父包 `event/` **引入 `__init__.py`** 做统一出口，按 `event_type` 分派。
4. 公共方法只保留**加载模板**和**获取静态数据**这类与玩法无关的机制。
5. 分层：`recognition.py` 放 vision 相关识别规则（阈值、OCR 规则、标题解析）；`constants.py` **只放坐标与模板路径**；`checker.py` 只留入口与结论组装。

**命名定案**：活动类型 `normal` / `assault` / `quiz`；公共模块用 `calibration`。

**落地结构**：

```text
checker/event/
├── __init__.py            # 导出各活动 checker，供导航器调用
├── calibration.py         # 公共加载：模板（common.vision）+ 活动数据（common.system）
└── normal_checker/        # 普通推图
    ├── __init__.py        # 模块入口：导出三个入口 + EventMode + EventMapState
    ├── checker.py         # 顶部 EventMapState；三个入口（零私有方法）
    ├── recognition.py     # 顶部 EventMode；识别与文本解析（只调 constants 与 common.vision）
    └── constants.py       # 坐标 + 模板路径
```

调用链（用户 2026-10-10 定稿）：

```text
导航器 → event.normal_checker（模块入口）
          └→ checker
               ├→ recognition → constants → common.vision
               └→ calibration → common.system / common.vision
```

- 活动数据由 **checker 取出后作为参数传给 recognition**；recognition 不读文件、不管缓存。
- `models.py` 取消：模型就近放——`EventMapState` 在 `checker.py` 顶部，`EventMode` 在 `recognition.py` 顶部。

调用形态：`event.normal_checker.check_event_entry(ctx, event_type='normal')`；入口保留 `event_type` 做玩法校验。

**同时发生的变化**：

| 变化 | 说明 |
| --- | --- |
| `event.py` 删除 | 拆入上面的包；`from ...checker import event` 导入路径不变 |
| 数据文件改名 | `20260930/stages.yaml` → `20260930/normal.yaml`（按期目录内按活动命名，为多活动留位） |
| 阈值 / 正则 / 归一化 | 从常量区移入 `recognition.py`；`constants.py` 只剩坐标与模板路径 |
| 单测迁移 | 直连 `normal_checker`；12 项全绿（合计 19 passed） |
| checker 收敛 | `checker.py` 只剩三个入口：玩法校验走 `calibration.require_activity`，章节校验在入口第一行 fail-fast |
| recognition 收窄 | 只做识别与文本解析；文件读取与缓存迁出，数据由 checker 传入 |
| 加载统一 | 模板与活动数据都走 `calibration`（公共层不解释业务语义） |
| 模板分目录 | 模板移到 `resources/image/.../checker/event/normal/`：加载按活动取目录，多活动不会重名 |
| E2E 静态帧 | `--static` 用外挂截图替身离线跑 checker；截图路径由 case 指定，不入库 |

**重构结果**：

| 已有产物 | 状态 |
| --- | --- |
| `checker/event.py`（373 行，三个入口，单测已通过） | **完成，待拆包** |
| `testing/ui/checker/test_event_page.py`（12 项） | **完成，随包结构微调导入** |
| `resources/.../checker/event/` 模板、`resources/data/map/event/20260930/stages.yaml` | **完成，不受影响** |
| `common/vision` 候选集合扩展 + 架构文档同步 | **完成，不受影响** |

## 13. 变更记录

| 日期 | 变更 |
| --- | --- |
| 2026-10-09 | v1→v2→v3→v4→v5→v6 见历史 |
| 2026-10-10 | **v15（本批完成）**：§9 第 6 项 dispatch 两字段（模板携带 + 具名读取入口 + 规范回写 + 2 项契约测试）、第 7 项按 §14 补 DEBUG 日志；静态帧 8 步全过，32 passed |
| 2026-10-10 | **v14**：任务书 §9 第 5 项完成——E2E 加 `--static` 静态帧模式与新 case `event_check`，真图 8 步全过；模板改为按活动分目录；26 passed（tools 7 + checker 12 + vision 7） |
| 2026-10-10 | **v13**：按用户「不想包很多层」的意见重排——recognition 收窄为纯识别、数据由 checker 传入、模板与数据加载统一走 calibration、取消 models.py（模型就近放）；19 passed |
| 2026-10-10 | **v12**：`checker.py` 去掉全部私有方法（三个入口零私有）；数据加载与难度结论移入 `recognition.py`，玩法校验移入 `calibration.require_activity`，章节校验提前到入口；19 passed |
| 2026-10-10 | **v11**：按 §12 落地包结构（`event/calibration.py` + `event/normal_checker/`），删除单文件 `event.py`，数据文件改名 `normal.yaml`，测试迁移后 19 passed |
| 2026-10-10 | **v10**：登记结构调整方向（三类活动 checker、父包分派、recognition/constants 分工、允许重复）；标记已完成但待重构的产物 |
| 2026-10-09 | **v9**：实现 `checker/event.py` 与 12 项 focused 单测；两个 `check_*` 返回值由 `None` 改为 `bool`（导航器需要事实才能报错）；实施顺序 1–4 完成 |
| 2026-10-09 | **v8 定稿**：报错归属定案路径 A（vision 只给结果，导航器报错）；接口形态确认；需求全部对齐，开始执行 |
| 2026-10-09 | v7：核实 `[架构]common-vision.md` §12——"读不到"在原架构中是**正常事实**，模块无自定义错误基类、恢复策略归上层；据此把"报错归属"收敛为路径 A/B 二选一（推荐 A）；并确认**探测不需要新增 def**（`before_template(attempts=1)` 即可）；用户第 16 条的前/后识别理解已原文记录 |

# Sakuya 战役迁移报告

日期：2026-09-01
分支：`codex/20260830-sakuya-exercise-consolidated-7a6c`

## 交付内容

- 战役入口已注册到 `Processor -> CampaignExecutor`，执行器每次只负责一场战役，
  重复次数由 `Request.count` 管理。
- 战役 YAML 在请求准入阶段读取和校验，`CampaignSpec` 冻结模式、章节、战斗计划和
  唯一舰队来源。GUI 队伍名称到个人/系统 YAML 的最终路径契约仍是集成 TODO。
- 战役页面使用共享 `business.navigation` 入口；地图面板在进入章节前上报
  `panel_ready`，战斗结束上报 `battle_done`，Processor 据此处理插队和连续任务。
- `CampaignFleetChangeMixin` 只做固定物理槽位的点对点替换/清空，不拖动、不左移；
  明确编队的每次执行先清空六个槽位，一号位不能为空。
- 普通战役允许一个槽位；困难战役固定检查舰种和数量。困难驱逐覆盖舰种 OCR，仍严格
  校验舰名/等级。
- 编队断点保存 `stage`、槽位和成员；暂停从首页恢复时，已清空的队伍不会再次清空。
- 战役支援实现位于 `application/combat/support.py`，不再由战役业务模块持有。
- 准备页舰队和 OCR 日志统一使用英文模块前缀，如 `[Campaign]`、`[Fleet]`、`[OCR]`。
- 新增 `tools/e2e/cases/campaign.py` 和简单驱逐 fixture，复用统一 E2E 初始化、异常
  恢复、日志和首页清理基座。

## 静态验证

```text
.venv\Scripts\python.exe -m pytest -q testing/business/combat/exercise testing/business/combat/campaign
42 passed

.venv\Scripts\python.exe -m pytest -q testing/ui/test_choose_ship_page.py -k signature
1 passed

uvx ruff check <本批 Python 文件>
Passed

uvx ruff format --check <本批 Python 文件>
Passed

.venv\Scripts\pre-commit.exe run --files <本批文件>
Passed

python -m compileall -q <本批模块>
Passed

git diff --check
Passed
```

未运行全量 pytest，符合任务书要求。Ruff 直接扫描其他旧舰队对齐文件时仍能看到既有
参数复杂度债务，本批没有扩大范围处理。

## 实机验证

设备：`127.0.0.1:16384`，`1280x720`，FastOCR CPU。每个 case 均由初始化开始并在
清理阶段回到首页。

| 日志目录 | 场景 | 结果 |
|---|---|---|
| `logs/e2e_tools/campaign/20260901_022134` | 选船页旧签名 | 失败；实际已进入选船页，识别签名过期，未进入战斗 |
| `logs/e2e_tools/campaign/20260901_024139` | 简单驱逐，无断点 | 通过；清空/填入 `U-177`、夜战、结算、首页 |
| `logs/e2e_tools/campaign/20260901_024621` | `panel_ready` + 远征检查 | 通过；收取 4 支远征后恢复战役 |
| `logs/e2e_tools/campaign/20260901_025213` | `formation_entered` + 奖励检查 | 通过 |
| `logs/e2e_tools/campaign/20260901_025505` | `fleet_checkpoint` + 远征检查 | 通过；恢复后未重复清空 |
| `logs/e2e_tools/campaign/20260901_025827` | `before_start` + 奖励检查 | 通过 |
| `logs/e2e_tools/campaign/20260901_030034` | `battle_done` + 远征检查 | 通过；战果已保存后再插队 |
| `logs/e2e_tools/campaign/20260901_030737` | `count=2` 连续战役 | 两场通过；运行时仍使用旧复用标记生命周期，日志显示两场间回首页 |

首场失败后只修正了共享选船页签名；截图验证当前签名在实机页面命中 5/5。战斗中出现
的一次状态识别超时由既有软重试恢复，最终结果均成功。

## 未完成与风险

- 最终连续战役复用标记已修正并有专项单测，但当日战役次数已在最后一轮 `count=2`
  用尽，修正后的“第二场不回首页”尚未重新实机验证。
- 困难驱逐六槽严格舰队、困难其他章节的固定舰种和非空约束已静态覆盖，未在本轮设备
  上执行，避免在没有对应测试资产时消耗错误战役次数。
- 任务书所述业务层 YAML 校验与架构纪要的 Processor/TaskDefinitionLoader 准入存在
  文字差异。本批保持单一准入所有权，不新增第二套 YAML 读取器。
- 没有修改 GUI 源码、页面样式、交互逻辑或跨仓契约；用户删除的历史文档和演习执行器
  未暂存修改均保持原状。

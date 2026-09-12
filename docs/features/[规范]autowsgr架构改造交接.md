# Agent Worktree Handoff

本文用于在 Agent 之间交接已经存在代码改动的 Git worktree。交接只转移
绑定记录的使用权，不删除、重置、暂存或提交代码。

## 当前任务

```powershell
$taskId = '20260830-sakuya-exercise-consolidated-7a6c'
$meta = 'C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\meta'
$autoWsgr = 'C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\AutoWSGR'
```

两个目录必须分别是独立 Git worktree，并且都使用同一个分支：
`codex/20260830-sakuya-exercise-consolidated-7a6c`。

## 旧 Agent：收到交接指令后快速解除绑定

旧 Agent 必须在仍拥有绑定的会话中执行以下步骤：

```powershell
$meta = 'C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\meta'
$autoWsgr = 'C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\AutoWSGR'

# 1. 停止继续写入，确认代码和计划文件都在目标 worktree 中。
git -C $autoWsgr status --short --branch
git -C $meta status --short --branch

# 2. 确认当前 Agent 的绑定目标没有偏移。
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" show
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" verify --cwd $autoWsgr
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" verify --cwd $meta

# 3. 释放当前 Agent 的绑定。此命令只删除绑定登记，不修改代码。
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" release --confirm RELEASE

# 4. 确认释放结果。
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" show
```

`release` 必须由旧 Agent 自己执行，并且确认参数必须逐字为
`--confirm RELEASE`。新 Agent 不能替旧 Agent 删除绑定记录；旧 Agent
没有释放时，新 Agent 的 `bind` 会因 worktree 已被其他 Agent 占用而失败。

释放绑定不会删除未提交改动。若状态中存在未提交内容，交接记录应先写明
文件范围、当前任务和验证结果，之后才能释放；不得使用
`git reset --hard`、`git checkout --` 或删除 worktree 来“清理”现场。

## 新 Agent：快速注册代码

新 Agent 进入任务后，先从实际路径确认仓库，不要在共享根目录切换分支：

```powershell
$taskId = '20260830-sakuya-exercise-consolidated-7a6c'
$meta = 'C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\meta'
$autoWsgr = 'C:\ShiinaKuroko\01.Project\.worktrees\20260830-exercise-team-contract-4c71\AutoWSGR'

# 1. 确认目录存在、Git 根和分支正确。
if (!(Test-Path -LiteralPath $meta)) { throw "meta worktree not found: $meta" }
if (!(Test-Path -LiteralPath $autoWsgr)) { throw "AutoWSGR worktree not found: $autoWsgr" }
git -C $meta rev-parse --show-toplevel
git -C $autoWsgr rev-parse --show-toplevel
git -C $meta branch --show-current
git -C $autoWsgr branch --show-current

# 2. 确认当前新 Agent 尚未绑定其他任务。
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" show

# 3. 一次性注册两个仓库；不要拆成两次 bind。
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" bind `
  --task-id $taskId `
  --worktree $meta `
  --worktree $autoWsgr

# 4. 注册后立即验证两个写入目标。
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" verify --cwd $meta
python "$env:CODEX_HOME\scripts\agent_worktree_binding.py" verify --cwd $autoWsgr

# 5. 开始工作前保留现场状态。
git -C $meta status --short --branch
git -C $autoWsgr status --short --branch
```

注册成功的必要条件：

- 当前 Agent 没有其他 active binding；
- 两个 worktree 都存在且未 detached；
- 每个 worktree 的分支都等于 `codex/<taskId>`；
- 每个 worktree 属于不同 Git 仓库；
- 旧 Agent 已经释放相同的 worktree/分支绑定。

## 交接顺序

```text
旧 Agent 停止写入
    -> 记录 status、未提交文件和下一步
    -> 旧 Agent 执行 release --confirm RELEASE
    -> 新 Agent 执行 bind --task-id ... --worktree meta --worktree AutoWSGR
    -> 新 Agent 分别执行 verify
    -> 新 Agent 继续原有未提交工作
```

遇到 `already bound to another agent` 时，先让原 Agent 执行释放；不要手工
删除 `$env:CODEX_HOME\agent-worktree-bindings` 中的 JSON，也不要创建第二个
分支覆盖当前进度。遇到分支名不匹配时，应修正任务 ID 或选择实际对应的
worktree，不能用强制参数绕过绑定校验。

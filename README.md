# 家庭账本后端

FastAPI + SQLAlchemy 模块化单体，为个人或家庭的账单、收入、核销、交易复盘和月度统计提供接口。前端仓库在本次工作区的 `finance_manager/finance-manager`。

本次实现：独立支出发生日期及旧数据迁移、可管理的支出分类、个人消费一次支付、完整快照备份与空账本原子恢复。旧接口保持兼容，前端通过 `/ledger/capabilities` 启用新增能力。

## 本地运行

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
export DATABASE_URL='sqlite:////tmp/household-ledger.db'
export APP_TIMEZONE='Asia/Shanghai'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

通过环境变量明确配置数据库，避免本地命令使用已有远程默认配置。API 文档位于 `http://localhost:8000/docs`。当前账本日期采用 `APP_TIMEZONE`，默认 `Asia/Shanghai`。

## 部署与迁移

先备份目标数据库，明确设置目标 `DATABASE_URL`，执行 `alembic upgrade head` 后再部署新版应用。新增迁移：

| 迁移 | 内容 |
| --- | --- |
| `20261006_0004` | 支出发生日期、索引和旧日期估算标记 |
| `20261006_0005` | 分类、默认分类和账单分类引用 |
| `20261006_0006` | 账本锁与恢复幂等记录 |

新版写入需要账本锁记录，必须完整迁移到 head。回退会删除新增日期、分类及恢复元数据，不能用回退代替备份恢复。

## 新增接口

- `GET /ledger/capabilities`：发生日期、分类、一次支付、完整备份及恢复的可用性。
- `/expense_categories/`：新增与查询分类，`PUT /{id}` 重命名、停用或启用，`DELETE /{id}` 软停用；分类分组与账单的 work / personal 必须一致，历史引用保留。
- `/transactions/` 创建、读取、更新支持 `occurred_at`、`expense_category_id`；旧记录回填日期带 `occurred_at_inferred`，用户修改后取消估算。新增个人消费可传 `payment_salary_log_id` 创建并全额核销，单事务完成，可通过历史撤销。
- `/summary?month=YYYY-MM`：支出按发生日期分月，收入按归属月份；`period_outstanding` 表示期间工作账单未关联金额，`current_debt` 表示全账本当前待回款。可分配收入和未结账单始终为当前存量。
- `GET /ledger/backup`：版本 2 原始账本快照，包括分类、全部账单、收入、交易及核销历史，不受默认分页限制，Decimal 数字保留精度。
- `POST /ledger/restore/preview`：校验摘要、金额、状态与引用，给出数量及空账本校验结果。
- `POST /ledger/restore`：只向空账本恢复，映射新 ID，失败整体回滚。已恢复过的相同摘要不重复写入。

恢复默认关闭。启用时为后端设置 `LEDGER_RESTORE_TOKEN`，请求通过 `X-Ledger-Restore-Key` 提供相同密钥；未启用返回 403，错误密钥返回 401，已有账本拒绝恢复并返回 409。预检后确认仍会在写入锁内重新检查，所有日常写入和快照使用同一账本锁。

版本 1 的旧前端导出不能作为完整账本恢复输入。版本 2 允许前端追加设备模板等元数据，服务器账本摘要仅覆盖 ledger；模板由前端在恢复后按分类名称匹配。

## 验证

```bash
.venv/bin/pip install pytest
DATABASE_URL=sqlite:////tmp/isolated-ledger-test.db .venv/bin/python -m pytest -q
```

43 项测试，包含接口持久化、分类改名与停用、日期分月、一次支付与撤销、恢复幂等及回滚、超过 100 条的备份、旧核销历史迁移与回退。测试使用独立 SQLite；MySQL 迁移已生成离线 SQL，尚未在真实 MySQL / TiDB 执行。浏览器使用两个本地 SQLite 服务完成记录、备份与恢复联调，未修改线上账本。

跨模块修改限定在发生日期共享契约、消费与核销的联合事务，以及备份恢复所需的共同写入锁。业务规则位于 service，持久化位于 repository，统计聚合位于 summary/queries，router 保持薄层。

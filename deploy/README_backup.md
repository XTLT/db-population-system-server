# 数据库备份、恢复演练与数据体检

覆盖三件事：每日自动备份、备份可恢复性演练、全库身份证体检。

## 一、备份机制（已不再直接拷库文件）

`excel_importer.backup_database(manual=False)` 现在的流程：

1. **`Connection.backup()` 生成一致快照** —— 不再用 `shutil.copy2` 拷 `population.db`。
   WAL 模式下已提交但还没 checkpoint 的事务只存在于 `population.db-wal` 里，
   直接拷主库会漏掉这些写入（50 上实测：`cp` 得到 0 条，`.backup` 得到 1 条）。
2. **`PRAGMA integrity_check`** —— 备份完立刻校验；不是 `ok` 就删掉这份半成品并返回失败。
3. 照片打包 `photos.tar.gz`（有照片时）。
4. **先算 `db_hash` 再加密** —— `_encrypt_backup` 会把 `population.db` 换成 `.enc`，
   顺序反了会导致设置库密码的服务器上备份整体失败。
5. 写 `backup_complete.txt`（manifest），字段含
   `timestamp / manual / db_hash / encrypted / integrity / method / complete`。
6. `_cleanup_old_backups()` 按天数清理。

自动备份额外规则：**只轮转自动备份，保留最近 14 份**（`KEEP_AUTO=14`），手工备份不参与轮转。

失败时整个 `backup_<时间戳>/` 目录会被删除：没有 manifest 的目录既不会被备份列表列出，
也不会被 `_cleanup_old_backups` 删除（后者要求 manifest 存在），留着只会永久占盘。

相关配置（`database/_base.py`，每个物理连接都生效）：

| PRAGMA | 值 | 说明 |
|---|---|---|
| `journal_mode` | `WAL` | 读写不互相阻塞 |
| `synchronous` | `NORMAL` | 事务提交仍是原子的 |
| `busy_timeout` | `30000` | 与 `connect_args={"timeout": 30}` 一致 |
| `journal_size_limit` | `67108864` | `-wal` 上限 64MB，checkpoint 后自动截断 |
| `mmap_size` | **刻意不开（0）** | 多进程写入 + mmap 会放大 WAL reset 竞态，出现过 `database disk image is malformed` |
| `foreign_keys` | **刻意不开** | 现有软删除/迁移路径有先删后插，开启可能拒绝历史数据写入；属独立行为变更 |

## 二、安装（systemd timer）

```bash
# 1) 代码已同步到 /root/population-system/server（含 deploy/ 目录）
chmod +x /root/population-system/server/deploy/backup_daily.sh

# 2) 安装 unit（26 用 /root/... 路径；50 测试机需把路径 sed 成 /home/z/population-test）
cp /root/population-system/server/deploy/population-backup.service /etc/systemd/system/
cp /root/population-system/server/deploy/population-backup.timer  /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now population-backup.timer
```

## 三、验证备份

```bash
systemctl start population-backup.service
systemctl status population-backup.service --no-pager
tail -n 5 /root/population-system/server/backups/auto_backup.log
ls -lt /root/population-system/server/backups/ | head
systemctl list-timers --all | grep population-backup
```

期望：日志行为
`2026-11-07 22:24:51 OK timestamp=20261107_222451 integrity=ok method=sqlite_backup_api error= removed=0`，
manifest 里 `"integrity": "ok"`、`"method": "sqlite_backup_api"`。

## 四、恢复演练（月度检查用）

```bash
cd /root/population-system/server

# 列出可用备份
venv/bin/python deploy/restore_drill.py --list

# 演练最近一份（默认不与线上库比对则跳过 --no-compare 去掉）
venv/bin/python deploy/restore_drill.py

# 指定某份 / 加密备份 / 保留临时解压目录
venv/bin/python deploy/restore_drill.py --backup backup_20261107_222451
venv/bin/python deploy/restore_drill.py --password 你的库密码
venv/bin/python deploy/restore_drill.py --keep
```

演练做的事：把备份里的库文件复制到临时目录（**不碰线上库**）→ 加密则解密 →
`PRAGMA integrity_check` → 统计人员与 6 张补贴表行数 → 与线上库比对差异 →
输出控制台表格 + `logs/restore_drill_<时间>.json`。

- 退出码 0 = PASS，1 = FAIL，可直接接监控。
- `差异` 列是 `线上行数 - 备份行数`，正数表示备份之后新增的业务数据，属正常；负数说明线上比备份还少，需要查。
- PASS 的条件是：manifest 标记完整、能打开、`integrity_check == ok`、关键表可读。行数差异本身不判 FAIL。
- 以普通用户手动跑时 `logs/` 可能无写权限，报告会自动改写到 `/tmp/` 并打印实际路径。

## 五、全库身份证体检

```bash
cd /root/population-system/server

# 扫线上库，问题清单写到 logs/
venv/bin/python deploy/check_id_cards.py

# 指定输出 / 指定库 / 只扫前 N 条自测
venv/bin/python deploy/check_id_cards.py --output /tmp/id_check.csv
venv/bin/python deploy/check_id_cards.py --db /path/to/population.db
venv/bin/python deploy/check_id_cards.py --limit 50
```

- **只读不改数据**：只 `SELECT`，不修正、不回写。
- 合法性判定复用 `utils/common/validate_id_card.py`，与三端录入校验同一套规则，不另写一套。
- 检查项：缺失、位数错误、前 17 位非数字、末位非法、校验位错误、出生年份/月份/日期无效，
  以及"存储值含空白字符或小写 x"（清洗后合法但库里存得不规范，会影响查询与比对）。
- 输出 CSV（`utf-8-sig`，Excel 双击不乱码）：姓名、户号、身份证原文、问题类型、说明、是否死亡、推算性别、内部 ID。
- 控制台给总数、合法数、各问题类型计数、按身份证推算的性别分布。
- **不做"第 17 位与性别一致性"断言**：`persons` 表没有 `gender` 字段，没有可比对的库内列；
  推算性别只作参考输出，供人工核对。

## 六、恢复现网库（Web 端 / 手工）

`excel_importer.restore_database` 与 `api/backup/api_backup_restore` 都已在覆盖前做了两件事：

1. **`PRAGMA integrity_check` 校验备份本身** —— 不是 `ok`（或根本不是 SQLite 文件）就直接拒绝，
   不停服、不动现网库。50 上实测：损坏备份返回
   `备份文件无法校验（可能已损坏）: file is not a database`，现网库一行未变。
2. **覆盖前删除 `population.db-wal` / `population.db-shm`** —— 旧 WAL 属于旧库，
   不删会被重放进恢复后的新库，造成数据错乱。50 上实测：恢复后 `-wal`/`-shm` 均已清除，
   库内容为备份内容，同时生成 `population.db.before_restore`。

## 七、回滚

```bash
systemctl disable --now population-backup.timer
rm -f /etc/systemd/system/population-backup.{service,timer}
systemctl daemon-reload
```

已生成的备份目录不受影响。

## 八、注意

- 部署顺序：先在 192.168.9.50 验证，通过后再上 26（教训库 F7）。
- 定时时间 02:30（**表达式里必须写 `Asia/Shanghai`**：26 的系统时区是 UTC，不写时区会在北京时间上午 10:30 触发），带 10 分钟随机延迟，避开整点任务堆积。
- `backup_daily.sh` 会优先用 `<部署目录>/venv/bin/python`，不存在则退回系统 `python3`。
- 磁盘占用：每份备份含数据库全量 + 照片打包；14 份是上限，若照片体积大需重新评估 `KEEP_AUTO`。
- `student_importer/backup_database.py` 里还有一份旧的 `shutil.copy2` 拷库实现（返回裸 `.db` 路径），
  当前无调用点，未纳入本轮改造；若以后启用，必须同样改成 `Connection.backup()`。

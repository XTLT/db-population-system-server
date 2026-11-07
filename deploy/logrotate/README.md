# 日志轮转

## 解决什么

`access.log`、`error.log`、`app.log`、`server_update.log`、`auto_backup.log` 原本没有任何轮转，
按访问量估算跑一年会到几个 G，且没有任何上限。本配置让它们每周切一次、保留 8 份、压缩存档。

26 生产上这些文件分布在两个目录（这是 unit 与 `config.py` 各自指定的结果，不要想当然认为在同一处）：

| 文件 | 实际路径 | 由谁决定 |
|---|---|---|
| access.log / error.log | `/root/population-system/data/logs/` | unit 的 `--access-logfile` / `--error-logfile` |
| app.log / server_update.log | `/root/population-system/server/logs/` | `config.LOG_DIR`（`DATA_DIR` = server 目录） |
| auto_backup.log | `/root/population-system/server/backups/` | `deploy/backup_daily.py` 的 `BACKUP_DIR` |

## 安装

```bash
# 26 生产（配置里的路径就是按 26 实际目录写的，直接用）
install -m 644 deploy/logrotate/population /etc/logrotate.d/population

# 50 测试机：日志与备份都在测试目录下
sed -e 's#/root/population-system/data/logs#/home/z/population-test/logs#g' \
    -e 's#/root/population-system/server/logs#/home/z/population-test/logs#g' \
    -e 's#/root/population-system/server/backups#/home/z/population-test/backups#g' \
    deploy/logrotate/population | sudo tee /etc/logrotate.d/population >/dev/null
sudo chmod 644 /etc/logrotate.d/population
```

26 上原来已有一份 `/etc/logrotate.d/population`（只覆盖 access/error，策略 `daily` + `size 20M` + `rotate 7`），
安装时会被这份覆盖：策略统一为 `weekly` + `rotate 8` + `maxsize 100M`，并补上漏掉的 app.log、server_update.log、
auto_backup.log。覆盖前先备份旧文件：

```bash
cp /etc/logrotate.d/population /root/_bak_logrotate_population.$(date +%Y%m%d_%H%M)
```

不需要重启服务，也不需要改代码。轮转由系统自带的 `/etc/cron.daily/logrotate` 每天触发，
`weekly` 的周期判断记录在 `/var/lib/logrotate/status`。

## 验证

```bash
# 1) 语法与路径检查（不会真的切）
logrotate -d /etc/logrotate.d/population

# 2) 强制切一次，看是否生成 .1、原文件是否归零
logrotate -f /etc/logrotate.d/population
ls -lh /root/population-system/data/logs/*.log* \
       /root/population-system/server/logs/*.log* \
       /root/population-system/server/backups/auto_backup.log*

# 3) 再切一次，验证压缩（第一次的 .1 变成 .2.gz）
logrotate -f /etc/logrotate.d/population

# 4) 发一个请求，确认进程没重启也能继续写
curl -sk --cert /root/population-system/data/certs/client.crt \
     --key /root/population-system/data/certs/client.key \
     https://127.0.0.1:5000/api/health
ls -l /root/population-system/data/logs/access.log

# 5) 跑一次自动备份，确认 auto_backup.log 恢复写入
systemctl start population-backup.service
cat /root/population-system/server/backups/auto_backup.log
```

50 上实测结果（2026-11-07）：

| 文件 | 轮转前 | 第一次切后 | 第二次切后 |
|---|---|---|---|
| access.log | 22K | 0（.1 = 22K） | 0（.1 = 308B，.2.gz = 1.7K） |
| app.log | 5.8K | 0（.1 = 5.8K） | 0（.1 = 100B，.2.gz = 817B） |
| error.log | 335K | 0（.1 = 335K） | 0（.1 = 335K，空文件不推 .2） |
| auto_backup.log | 340B | 0（.1 = 340B） | 104B（备份写回） |

轮转后 `MainPID` 始终为 5162，服务未重启；`curl` 一次 health 后 access.log 写回 207 字节，
登录失败一次后 app.log 写回 100 字节（`[登录失败][用户名不存在]`）。

## 回滚

```bash
rm -f /etc/logrotate.d/population
# 如需恢复 26 原来的那份
cp /root/_bak_logrotate_population.<时间> /etc/logrotate.d/population
```

已生成的 `.1` / `.2.gz` 不受影响；不装回该文件即恢复"永不轮转"的原状。

## 为什么用 copytruncate 而不是 create + USR1

- gunicorn 的 access/error 日志句柄由 master 长期持有，且本服务**没有 pid 文件**
  （unit 里没有 `PIDFile`，只有 `/root/.gunicorn/gunicorn.ctl`），无法可靠地定位 master 发 USR1；
- `systemctl kill -s USR1` 默认发给 cgroup 内**所有**进程（`--kill-who=all`），
  worker 收到 USR1 可能直接退出，必须显式 `--kill-who=main`，风险大于收益；
- 应用日志 `app.log` 由 `app_modular.py` 的 `logging.FileHandler` 打开，**即使 master 收到 USR1 也不会重开它**，
  `create` 模式下这个句柄会一直写已改名的旧文件，新的 app.log 永远是空的。

`copytruncate` 是"复制一份再原地清空"，持有句柄的进程不用重启就能继续写。
代价是截断瞬间可能丢几行日志，对运维日志可以接受。

## 注意

- 配置用显式文件名列表，不是 `*.log` 通配，避免把 `logs/` 里的 `restore_drill_*.json` 报告当成日志切掉。
- `notifempty`：空日志不切。所以长期为空的 `error.log` 不会把上一份 `.1` 推到 `.2.gz`，
  那份 `.1` 会一直留到下次有内容为止（体积可控，不影响功能）。
- `maxsize 100M`：即使不到一周，单份超过 100MB 也会提前切，防止异常刷日志打满盘。
- `su root root`：日志目录属 root 时必须写，否则 logrotate 报 `insecure permissions`；
  50 的目录属 z 时同样需要它。
- 新增任何日志文件后，记得加进这份配置，否则它仍是"永不轮转"。

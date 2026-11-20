"""备份恢复演练：解备份 → integrity_check → 比对各表行数 → 输出报告。

函数实现已按一函数一文件拆到 restore_drill_funcs/，本文件只保留命令行入口。

用法：
    python deploy/restore_drill.py                     # 演练最近一份完整备份
    python deploy/restore_drill.py --list               # 列出可用备份
    python deploy/restore_drill.py --backup backup_20261107_214248
    python deploy/restore_drill.py --password 你的库密码  # 加密备份（默认取库密码）
    python deploy/restore_drill.py --no-compare         # 不与线上库比对行数
    python deploy/restore_drill.py --keep               # 保留临时目录

退出码：0 = PASS，1 = FAIL。
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from deploy.restore_drill_funcs import main
except ImportError:
    from restore_drill_funcs import main

if __name__ == "__main__":
    sys.exit(main())

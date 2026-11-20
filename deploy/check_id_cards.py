"""全库身份证体检：格式 / 校验位 / 出生日期，输出问题清单。

函数实现已按一函数一文件拆到 check_id_cards_funcs/，本文件只保留命令行入口。
**只读不改数据**。

用法：
    python deploy/check_id_cards.py                    # 扫线上库，输出 CSV 到 logs/
    python deploy/check_id_cards.py --output x.csv
    python deploy/check_id_cards.py --db /path/to/population.db
    python deploy/check_id_cards.py --limit 50         # 只扫前 50 条（自测用）
    python deploy/check_id_cards.py --include-ok       # CSV 里也写入合法行
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from deploy.check_id_cards_funcs import main
except ImportError:
    from check_id_cards_funcs import main

if __name__ == "__main__":
    sys.exit(main())

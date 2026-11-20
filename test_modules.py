#!/usr/bin/env python3
"""模块验证脚本入口（函数实现见 test_modules_funcs/）。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_modules_funcs import main

if __name__ == '__main__':
    sys.exit(main())

import os
import sys

# 兼容直接以脚本方式运行：把 server 目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from . import main

if __name__ == "__main__":
    main()

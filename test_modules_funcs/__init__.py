"""模块验证函数的统一调度出口。"""

from .check_syntax import check_syntax
from .check_structure import check_structure
from .check_config import check_config
from .main import main

__all__ = ['check_syntax', 'check_structure', 'check_config', 'main']

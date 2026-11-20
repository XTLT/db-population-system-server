"""模块结构验证函数的统一调度出口。"""

from .check_syntax import check_syntax
from .check_blueprint_definition import check_blueprint_definition
from .main import main

__all__ = ['check_syntax', 'check_blueprint_definition', 'main']

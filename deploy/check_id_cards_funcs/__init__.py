"""身份证体检函数的统一调度出口。"""

from .constants import PROBLEM_BY_MSG
from .gender_from_id import gender_from_id
from .scan import scan
from .write_csv import write_csv
from .main import main

__all__ = ['PROBLEM_BY_MSG', 'gender_from_id', 'scan', 'write_csv', 'main']

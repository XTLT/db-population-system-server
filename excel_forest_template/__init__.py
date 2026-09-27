# excel_forest_template 包 — 向后兼容 shim
from ._constants import FOREST_COLUMNS
from .generate_forest_template import generate_forest_template

__all__ = [
    'FOREST_COLUMNS',
    'generate_forest_template',
]

"""POST /api/export/excel 的路由注册入口（函数实现见 export_excel_funcs/）。"""

from . import bp
from .export_excel_funcs import export_excel

bp.add_url_rule('/export/excel', endpoint='export_excel', view_func=export_excel,
                methods=['POST'])

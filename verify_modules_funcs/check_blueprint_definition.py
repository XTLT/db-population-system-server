"""检查文件内是否定义了 Blueprint 与路由。"""


def check_blueprint_definition(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    has_bp = "bp = Blueprint(" in content
    has_routes = "@bp.route" in content
    route_count = content.count("@bp.route")

    return has_bp, has_routes, route_count

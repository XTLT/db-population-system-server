#!/usr/bin/env python3
"""
模块验证脚本 - 检查所有模块是否正常
"""
import sys
import os
import ast

def check_syntax(filepath):
    """检查 Python 文件语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)


def check_blueprint_definition(filepath):
    """检查 Blueprint 定义"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_bp = "bp = Blueprint(" in content
    has_routes = "@bp.route" in content
    route_count = content.count("@bp.route")
    
    return has_bp, has_routes, route_count


def main():
    print("=" * 60)
    print("模块结构验证")
    print("=" * 60)
    
    api_dir = os.path.join(os.path.dirname(__file__), 'api')
    utils_dir = os.path.join(os.path.dirname(__file__), 'utils')
    
    errors = []
    total_routes = 0
    
    # 检查工具模块
    print("\n### 工具模块 ###")
    for name in ['security.py', 'response.py', 'common.py']:
        filepath = os.path.join(utils_dir, name)
        if not os.path.exists(filepath):
            print(f"  ✗ {name}: 文件不存在")
            errors.append(name)
            continue
        ok, err = check_syntax(filepath)
        if ok:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}: {err}")
            errors.append(name)
    
    # 检查 API 模块
    print("\n### API 模块 ###")
    modules = [
        'auth.py', 'users.py', 'persons.py', 'students.py',
        'photos.py', 'statistics.py', 'import_export.py',
        'backup.py', 'logs.py', 'notifications.py', 'reports.py'
    ]
    
    for name in modules:
        filepath = os.path.join(api_dir, name)
        ok, err = check_syntax(filepath)
        if not ok:
            print(f"  ✗ {name}: {err}")
            errors.append(name)
            continue
        
        has_bp, has_routes, route_count = check_blueprint_definition(filepath)
        total_routes += route_count
        
        status = "✓" if (has_bp and has_routes) else "✗"
        print(f"  {status} {name}: Blueprint={has_bp}, 路由数={route_count}")
    
    # 检查主入口
    print("\n### 主入口 ###")
    main_file = os.path.join(os.path.dirname(__file__), 'app_modular.py')
    ok, err = check_syntax(main_file)
    if ok:
        with open(main_file, 'r') as f:
            content = f.read()
        bp_count = content.count("register_blueprint")
        print(f"  ✓ app_modular.py: 注册 {bp_count} 个 Blueprint")
    else:
        print(f"  ✗ app_modular.py: {err}")
        errors.append('app_modular.py')
    
    # 检查 __init__.py
    print("\n### 包初始化 ###")
    init_file = os.path.join(api_dir, '__init__.py')
    ok, err = check_syntax(init_file)
    if ok:
        with open(init_file, 'r') as f:
            content = f.read()
        exports = content.count("_bp")
        print(f"  ✓ api/__init__.py: 导出 {exports // 2} 个 Blueprint")
    else:
        print(f"  ✗ api/__init__.py: {err}")
        errors.append('__init__.py')
    
    # 总结
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ 发现 {len(errors)} 个问题: {', '.join(errors)}")
        return 1
    else:
        print("✅ 所有模块检查通过")
        print(f"   - API 模块: {len(modules)} 个")
        print(f"   - 总路由数: {total_routes} 个")
        print("   - 工具模块: 3 个")
        print("")
        print("运行方式:")
        print("   cd server && python app_modular.py")
        return 0


if __name__ == '__main__':
    sys.exit(main())

"""递归编译 server/ 下所有 .py（排除 legacy 单体与 venv/备份）。"""

import os
import py_compile


def check_syntax():
    print("=== 语法检查 ===")
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exclude_dirs = {'venv', '__pycache__', 'config_test_bak'}
    exclude_files = {'web_app.py'}  # 旧单体，已被 api/ + app_modular.py 取代
    ok = fail = 0
    for root, dirs, files in os.walk(server_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for name in files:
            if not name.endswith('.py') or name in exclude_files:
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, server_dir)
            try:
                py_compile.compile(path, doraise=True)
                ok += 1
            except py_compile.PyCompileError as e:
                print(f"  ✗ {rel}: {e}")
                fail += 1
    print(f"  编译完成: OK={ok} FAIL={fail}")
    return fail == 0

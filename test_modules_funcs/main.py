"""模块验证脚本入口。"""

from .check_syntax import check_syntax
from .check_structure import check_structure
from .check_config import check_config


def main():
    print("=" * 50)
    print("模块验证脚本")
    print("=" * 50)

    if not check_syntax():
        print("\n❌ 语法检查失败")
        return 1

    try:
        if not check_structure():
            print("\n❌ 结构检查失败")
            return 1
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    try:
        if not check_config():
            print("\n❌ 配置检查失败")
            return 1
    except ImportError as e:
        print(f"\n❌ 配置导入失败: {e}")
        return 1

    print("\n" + "=" * 50)
    print("✅ 所有模块检查通过")
    print("=" * 50)
    return 0

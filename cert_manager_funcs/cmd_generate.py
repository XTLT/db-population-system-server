"""生成新证书（已存在时按 --force 先备份再重建）。"""

import os
import shutil
from datetime import datetime

from .cert_env import CERT_DIR, generate_self_signed_cert
from .get_cert_files import get_cert_files


def cmd_generate(args):
    """生成新证书"""
    cert_file, key_file = get_cert_files()

    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("⚠️  证书已存在！")
        print(f"   证书位置: {cert_file}")
        print(f"   私钥位置: {key_file}")

        if not args.force:
            print("\n如需重新生成，请使用 --force 参数")
            return False

        # 备份旧证书
        backup_dir = os.path.join(os.path.dirname(cert_file), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.path.exists(cert_file):
            shutil.copy2(cert_file, os.path.join(backup_dir, f"server_{timestamp}.crt"))
            os.remove(cert_file)  # 删除旧证书
        if os.path.exists(key_file):
            shutil.copy2(key_file, os.path.join(backup_dir, f"server_{timestamp}.key"))
            os.remove(key_file)  # 删除旧私钥

        print(f"✓ 旧证书已备份到: {backup_dir}")

    # 生成证书
    print("\n正在生成证书...")
    os.makedirs(CERT_DIR, exist_ok=True)

    try:
        cert_file, key_file = generate_self_signed_cert()
        if cert_file and key_file:
            print("\n✓ 证书生成成功！")
            print(f"   证书位置: {cert_file}")
            print(f"   私钥位置: {key_file}")
            print("   有效期: 10 年")
            print("\n⚠️  请立即备份证书文件！")
            print("   私钥文件请妥善保管，不要上传到代码仓库！")
            return True
        else:
            print("✗ 证书生成失败")
            return False
    except Exception as e:
        print(f"✗ 证书生成失败: {e}")
        return False

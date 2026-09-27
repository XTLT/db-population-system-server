import os
import sys
import subprocess
from ._constants import AUTO_UPDATE_ENABLED
from ._validate_path_for_shell import _validate_path_for_shell


def apply_update(filepath: str):
    """
    应用更新 - 自动安装已禁用，需手动确认

    Args:
        filepath: 更新文件路径

    Returns:
        (是否成功, 错误信息)

    安全说明：
        为了防止供应链攻击，自动执行脚本已禁用。
        用户需要手动验证并执行更新。
    """
    if not getattr(sys, 'frozen', False):
        return False, "非打包环境，请使用 upgrade.sh 升级"

    # 自动更新已禁用，返回提示信息
    if not AUTO_UPDATE_ENABLED:
        current_exe = sys.executable
        app_dir = os.path.dirname(current_exe)

        info_msg = f"""
====================================
安全更新提示
====================================
更新文件已下载到：{filepath}

请手动执行以下步骤：
1. 关闭当前程序
2. 备份重要数据
3. 手动替换程序文件
4. 重新启动程序

Linux系统可使用：
  cp {filepath} {current_exe}
  chmod +x {current_exe}

Windows系统请手动替换文件。
====================================
"""
        return False, info_msg

    # 以下是原有的自动更新逻辑（已禁用）
    current_exe = sys.executable
    app_dir = os.path.dirname(current_exe)
    new_exe = filepath

    # 安全检查：验证路径不包含危险字符
    if not _validate_path_for_shell(current_exe) or not _validate_path_for_shell(new_exe):
        return False, "安全错误：更新路径包含不安全字符，拒绝自动更新"

    if sys.platform == 'win32':
        bat_path = os.path.join(app_dir, '_auto_update.bat')
        # 使用安全验证过的路径
        exe_name = os.path.basename(current_exe)
        bat_content = f'''@echo off
chcp 65001 >nul
title 自动更新中...
echo 正在关闭程序...
taskkill /f /t /im "{exe_name}" >nul 2>&1
echo 等待文件释放...
:wait_loop
timeout /t 2 /nobreak >nul
copy /y "{new_exe}" "{current_exe}" >nul 2>&1
if errorlevel 1 goto wait_loop
echo 更新完成，正在启动...
del "{new_exe}" >nul 2>&1
start "" "{current_exe}"
timeout /t 3 /nobreak >nul
del "%~f0"
'''
        with open(bat_path, 'w', encoding='gbk') as f:
            f.write(bat_content)

        os.startfile(bat_path)
        return True, ""
    else:
        script_path = os.path.join(app_dir, '_auto_update.sh')
        # 安全检查：验证脚本路径
        if not _validate_path_for_shell(script_path):
            return False, "安全错误：脚本路径包含不安全字符，拒绝自动更新"

        exe_name = os.path.basename(current_exe)
        script_content = f'''#!/bin/bash
sleep 2
killall "{exe_name}" 2>/dev/null
sleep 1
cp -f "{new_exe}" "{current_exe}"
chmod +x "{current_exe}"
rm -f "{new_exe}"
"{current_exe}" &
rm -f "{script_path}"
'''
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        # 使用 subprocess 替代 os.system 防止命令注入
        subprocess.Popen(['nohup', script_path], start_new_session=True)
        return True, ""

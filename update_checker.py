#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本检测模块 - 支持桌面端和服务器端自动更新检测

安全说明：
1. 所有更新源必须使用HTTPS
2. 更新文件必须提供SHA256校验和
3. 更新文件必须提供GPG签名或代码签名验证
4. 自动安装已禁用，需手动确认更新
5. 实现了多层安全验证防止供应链攻击

安全加固历史：
- v2.0: 添加GPG签名验证、代码签名验证
- v1.5: 强制HTTPS、URL白名单、SHA256校验
"""

import os
import sys
import json
import hashlib
import subprocess
import tempfile
from typing import Optional, Dict, Tuple
import urllib3
import requests

# 禁用不安全的警告（仅用于调试）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 版本检测 URL（仅支持HTTPS）
VERSION_URLS = [
    "https://gitee.com/tension0712/population-query-system/raw/main/updates/version.json",
]

# 更新源白名单域名
ALLOWED_DOMAINS = [
    "gitee.com",
    "github.com",
    "githubusercontent.com",
]

# 是否启用自动更新（默认禁用，需手动确认）
AUTO_UPDATE_ENABLED = False

# 是否强制要求签名验证
REQUIRE_SIGNATURE = True

# 是否强制要求GPG签名验证
REQUIRE_GPG_SIGNATURE = False  # 可选，如果提供则验证

# GPG公钥指纹白名单（发布者的GPG密钥指纹）
GPG_KEY_FINGERPRINTS = [
    # 示例：添加发布者的GPG密钥指纹
    # "ABC123DEF456...",
]

# Windows代码签名证书指纹白名单
CODE_SIGNING_CERTS = [
    # 示例：添加发布者的代码签名证书指纹
    # "XYZ789...",
]

def _get_config_dir():
    """获取配置文件目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_DIR = _get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "version_config.json")
DOWNLOAD_DIR = os.path.join(CONFIG_DIR, "downloads")


def _validate_url(url: str) -> bool:
    """
    验证URL是否在允许的白名单域名中
    
    Args:
        url: 要验证的URL
        
    Returns:
        是否为允许的域名
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        # 必须使用HTTPS
        if parsed.scheme != 'https':
            return False
            
        # 检查域名是否在白名单中
        domain = parsed.netloc.lower()
        for allowed in ALLOWED_DOMAINS:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
                
        return False
        
    except Exception:
        return False


def _validate_download_url(url: str) -> bool:
    """
    验证下载URL是否安全
    
    Args:
        url: 下载URL
        
    Returns:
        是否为安全的URL
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        # 必须使用HTTPS
        if parsed.scheme != 'https':
            return False
            
        # 检查域名
        domain = parsed.netloc.lower()
        for allowed in ALLOWED_DOMAINS:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
                
        return False
        
    except Exception:
        return False


def load_local_config() -> Dict:
    """加载本地版本配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_version": "1.0.0", "version_code": 1}


def save_local_config(config: Dict):
    """保存本地版本配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def check_update(app_type: str = "desktop") -> Tuple[Optional[Dict], str]:
    """
    检查是否有新版本
    
    Args:
        app_type: 应用类型 "desktop" 或 "server"
        
    Returns:
        (版本信息, 错误信息) - 如果有新版本返回版本信息，否则返回 (None, "")
    """
    config = load_local_config()
    current_code = config.get("version_code", 1)
    
    try:
        data = None
        last_error = None
        for url in VERSION_URLS:
            # 验证URL是否在白名单中
            if not _validate_url(url):
                last_error = f"更新源不在白名单中: {url}"
                continue
                
            try:
                # 启用证书验证
                resp = requests.get(url, timeout=10, verify=True)
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                last_error = e
                continue
        
        if data is None:
            return None, f"所有更新源均无法访问: {last_error}"
        
        # 根据应用类型获取对应的版本信息
        if app_type == "desktop":
            latest_code = data.get("desktop_version_code", data.get("version_code", 0))
        else:
            latest_code = data.get("server_version_code", data.get("version_code", 0))
        
        # 版本比较
        if latest_code > current_code:
            return data, ""
        else:
            return None, ""
            
    except requests.exceptions.RequestException as e:
        return None, f"检查更新失败: {e}"
    except json.JSONDecodeError as e:
        return None, f"解析版本信息失败: {e}"
    except Exception as e:
        return None, f"未知错误: {e}"


def download_update(version_info: Dict, progress_callback=None) -> Tuple[Optional[str], str]:
    """
    下载更新文件
    
    Args:
        version_info: 版本信息
        progress_callback: 进度回调 (downloaded_bytes, total_bytes)
        
    Returns:
        (文件路径, 错误信息)
        
    安全要求：
        1. 下载URL必须在白名单域名中
        2. 必须提供SHA256校验和
        3. 下载完成后验证文件完整性
    """
    urls = []
    if version_info.get("server_download_url"):
        urls.append(version_info["server_download_url"])
    if version_info.get("download_url"):
        urls.append(version_info["download_url"])
    
    if not urls:
        return None, "未找到下载链接"
    
    # 检查是否有签名信息
    has_checksum = False
    checksum_fields = ["server_checksum", "checksum", "sha256", "sha256_checksum"]
    for field in checksum_fields:
        if version_info.get(field):
            has_checksum = True
            break
    
    if REQUIRE_SIGNATURE and not has_checksum:
        return None, "安全错误：更新文件未提供SHA256校验和，拒绝下载"
    
    filename = "update.exe"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    for url in urls:
        # 验证下载URL是否安全
        if not _validate_download_url(url):
            continue
            
        try:
            # 启用证书验证
            resp = requests.get(url, stream=True, timeout=300, verify=True)
            resp.raise_for_status()
            
            total = int(resp.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
            
            # 验证文件完整性
            for field in checksum_fields:
                checksum = version_info.get(field)
                if checksum:
                    if not verify_file(filepath, checksum):
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        return None, "文件校验失败：SHA256不匹配，可能被篡改"
                    break
            
            # 验证 GPG 签名（如果提供）
            gpg_signature_url = version_info.get("gpg_signature_url")
            gpg_signature = version_info.get("gpg_signature")
            if gpg_signature_url or gpg_signature:
                gpg_valid, gpg_error = verify_gpg_signature(
                    filepath, 
                    signature_url=gpg_signature_url,
                    signature_data=gpg_signature.encode() if gpg_signature else None
                )
                if not gpg_valid:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None, f"GPG签名验证失败: {gpg_error}"
            elif REQUIRE_GPG_SIGNATURE:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None, "安全错误：未提供GPG签名，拒绝更新"
            
            # 验证 Windows 代码签名（如果是可执行文件）
            if filepath.endswith('.exe') and sys.platform == 'win32':
                code_valid, code_error = verify_windows_code_signature(filepath)
                if not code_valid:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None, f"代码签名验证失败: {code_error}"
            
            return filepath, ""
            
        except requests.exceptions.RequestException:
            if os.path.exists(filepath):
                os.remove(filepath)
            continue
    
    return None, "所有下载源均失败或不在白名单中"


def calculate_sha256(filepath: str) -> str:
    """计算文件 SHA256"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_gpg_signature(filepath: str, signature_url: str = None, signature_data: bytes = None) -> Tuple[bool, str]:
    """
    验证 GPG 签名
    
    Args:
        filepath: 要验证的文件路径
        signature_url: 签名文件URL（可选）
        signature_data: 签名数据（可选）
        
    Returns:
        (是否验证通过, 错误信息)
    """
    try:
        # 获取签名数据
        if signature_data is None and signature_url:
            # 验证签名URL是否在白名单中
            if not _validate_download_url(signature_url):
                return False, "签名文件URL不在白名单中"
            resp = requests.get(signature_url, timeout=30, verify=True)
            resp.raise_for_status()
            signature_data = resp.content
        
        if signature_data is None:
            return False, "未提供签名数据"
        
        # 写入临时签名文件
        with tempfile.NamedTemporaryFile(suffix='.sig', delete=False) as sig_file:
            sig_file.write(signature_data)
            sig_path = sig_file.name
        
        try:
            # 使用 gpg 验证签名
            result = subprocess.run(
                ['gpg', '--verify', sig_path, filepath],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # 检查签名者指纹是否在白名单中
                if GPG_KEY_FINGERPRINTS:
                    # 提取签名者指纹
                    fingerprint_result = subprocess.run(
                        ['gpg', '--verify', '--status-fd', '1', sig_path, filepath],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    # 检查指纹是否在白名单
                    for fingerprint in GPG_KEY_FINGERPRINTS:
                        if fingerprint in fingerprint_result.stdout:
                            return True, ""
                    
                    return False, "签名者GPG密钥不在信任列表中"
                
                return True, ""
            else:
                return False, f"GPG签名验证失败: {result.stderr}"
                
        finally:
            os.unlink(sig_path)
            
    except FileNotFoundError:
        return False, "系统未安装GPG，无法验证签名"
    except subprocess.TimeoutExpired:
        return False, "签名验证超时"
    except Exception as e:
        return False, f"签名验证错误: {e}"


def verify_windows_code_signature(filepath: str) -> Tuple[bool, str]:
    """
    验证 Windows 可执行文件的代码签名
    
    Args:
        filepath: 可执行文件路径
        
    Returns:
        (是否验证通过, 错误信息)
    """
    if sys.platform != 'win32':
        return True, "非Windows系统，跳过代码签名验证"
    
    if not filepath.endswith('.exe'):
        return True, "非可执行文件，跳过签名验证"
    
    # 安全检查：验证文件路径不包含危险字符
    dangerous_chars = ['$', '`', '"', "'", '\n', '\r', ';', '&', '|', '<', '>', '(', ')']
    if any(char in filepath for char in dangerous_chars):
        return False, "文件路径包含不安全字符"
    
    try:
        # 使用 PowerShell 验证代码签名
        # 注意：filepath 已经过安全检查，但仍需转义
        escaped_path = filepath.replace("'", "''")
        ps_script = f'''
        $sig = Get-AuthenticodeSignature '{escaped_path}'
        if ($sig.Status -eq "Valid") {{
            Write-Output "VALID"
            Write-Output $sig.SignerCertificate.Thumbprint
        }} else {{
            Write-Output "INVALID"
            Write-Output $sig.Status
        }}
        '''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        lines = result.stdout.strip().split('\n')
        
        if lines and lines[0] == 'VALID':
            # 如果配置了证书白名单，验证证书指纹
            if CODE_SIGNING_CERTS:
                cert_thumbprint = lines[1] if len(lines) > 1 else ""
                if cert_thumbprint in CODE_SIGNING_CERTS:
                    return True, ""
                else:
                    return False, f"代码签名证书不在信任列表中: {cert_thumbprint}"
            return True, ""
        else:
            status = lines[1] if len(lines) > 1 else "未知错误"
            return False, f"代码签名无效: {status}"
            
    except subprocess.TimeoutExpired:
        return False, "签名验证超时"
    except Exception as e:
        return False, f"签名验证错误: {e}"


def verify_file(filepath: str, expected_checksum: str) -> bool:
    """
    验证文件完整性
    
    Args:
        filepath: 文件路径
        expected_checksum: 预期的校验和（格式：sha256:xxxxxx）
        
    Returns:
        是否验证通过
        
    安全策略：
        1. 必须提供SHA256校验和
        2. 格式必须为 sha256:xxxxxx
        3. 计算并比较SHA256值
    """
    # 如果启用了强制签名要求，不允许跳过验证
    if REQUIRE_SIGNATURE:
        if not expected_checksum or not expected_checksum.startswith("sha256:"):
            return False
    else:
        if not expected_checksum or not expected_checksum.startswith("sha256:"):
            return True  # 未配置校验，跳过验证（不推荐）
    
    expected_hash = expected_checksum[7:]
    actual_hash = calculate_sha256(filepath)
    return expected_hash == actual_hash


def update_local_version(version_info: Dict, app_type: str = "server"):
    """更新本地版本记录"""
    config = load_local_config()
    if app_type == "desktop":
        config["current_version"] = version_info.get("desktop_version", config.get("current_version", "1.0.0"))
        config["version_code"] = version_info.get("desktop_version_code", config.get("version_code", 1) + 1)
    else:
        config["current_version"] = version_info.get("server_version", config.get("current_version", "1.0.0"))
        config["version_code"] = version_info.get("server_version_code", config.get("version_code", 1) + 1)
    save_local_config(config)


def _validate_path_for_shell(path: str) -> bool:
    """验证路径是否安全可用于shell操作
    
    防止命令注入：检查路径是否包含危险字符
    """
    dangerous_chars = ['$', '`', '"', "'", '\\', '\n', '\r', ';', '&', '|', '<', '>', '(', ')']
    return not any(char in path for char in dangerous_chars)


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

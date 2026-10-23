"""send_file 自动清理临时文件工具

所有生成 Excel 后 send_file 下载的接口都应使用 send_file_auto_cleanup，
确保临时文件在响应发送时被删除，避免 _tmp_*.xlsx 在服务端目录无限积累。

实现说明：
- 使用 after_this_request 钩子：视图返回后（send_file 已打开文件、fd 有效）
  立即 unlink 磁盘文件。Linux 下已打开文件的 fd 不受 unlink 影响，
  响应可正常流式发送，同时磁盘文件不残留。
- 相比 call_on_close，after_request 在 gunicorn 下必定执行，更可靠。
"""
import os

from flask import after_this_request, send_file


def _safe_remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def send_file_auto_cleanup(path, **kwargs):
    """send_file 并在响应发送阶段删除临时文件。

    用法与 flask.send_file 完全一致，可传 as_attachment / download_name 等参数。
    """
    @after_this_request
    def _cleanup(resp):
        _safe_remove(path)
        return resp

    return send_file(path, **kwargs)


def cleanup_temp(path):
    """主动清理临时文件（生成失败等场景），调用方需确保 path 可能不存在。

    用法: cleanup_temp(tmp_path)
    """
    _safe_remove(path)

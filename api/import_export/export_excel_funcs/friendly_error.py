"""把导出时的底层异常翻译成用户能看懂的话。"""


def friendly_error(exc):
    msg = str(exc or '').strip()
    low = msg.lower()
    if 'no space left' in low or 'errno 28' in low or 'disk full' in low:
        return '服务器存储空间不足，导出失败，请联系管理员清理后重试'
    if 'permission denied' in low or 'errno 13' in low:
        return '服务器无权限写入导出文件，请联系管理员'
    if 'io_write' in low or 'io_read' in low or 'sslerror' in low or 'ssl' in low:
        return '导出过程中连接中断，请重试'
    if 'errno 122' in low or 'disk quota' in low:
        return '服务器存储配额不足，导出失败，请联系管理员'
    if msg and len(msg) <= 120:
        return '导出失败：%s' % msg
    return '导出失败，请重试或联系管理员'

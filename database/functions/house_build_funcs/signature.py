"""申请人手写签名数据处理：校验 base64、限制体积、去掉 data URI 前缀。"""

import base64
import binascii
import re

MAX_SIGNATURE_BYTES = 2 * 1024 * 1024
_PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
_JPEG_MAGIC = b'\xff\xd8\xff'
_WS_RE = re.compile(r'\s+')


def normalize_signature(value) -> str:
    """把 data:image/png;base64,... 或纯 base64 规范成纯 base64。

    空值返回空串。非法数据抛 ValueError，由接口返回 400，不能把坏图片落库。
    """
    if value is None:
        return ''
    text = str(value).strip()
    if not text:
        return ''
    if text.startswith('data:'):
        if ',' not in text:
            raise ValueError('签名图片数据格式不正确')
        text = text.split(',', 1)[1]
    text = _WS_RE.sub('', text)
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('签名图片数据不是有效的 base64')
    if len(raw) > MAX_SIGNATURE_BYTES:
        raise ValueError('签名图片不能超过 2MB')
    if not (raw.startswith(_PNG_MAGIC) or raw.startswith(_JPEG_MAGIC)):
        raise ValueError('签名图片仅支持 PNG 或 JPEG')
    return text

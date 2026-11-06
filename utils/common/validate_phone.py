# -*- coding: utf-8 -*-
"""电话校验（三端统一口径的基准实现）。

规则（desktop / mobile 必须与此一致）：
    1. 去掉首尾空白，并剔除所有 "-" 与空白字符
    2. 清洗后为空 -> 放行（电话是可选字段）
    3. 仅接受 11 位手机号 ^1[3-9]\\d{9}$
    4. 座机、带区号或分机的号码一律拒绝（业务上只录手机号）

返回 (ok, msg)。本文件的提示文案是全项目基准。
"""

import re


def validate_phone(phone: str) -> tuple[bool, str]:
    phone = re.sub(r'[-\s]', '', (phone or '').strip())

    if not phone:
        return True, ""

    if re.match(r'^1[3-9]\d{9}$', phone):
        return True, ""

    return False, "电话号码格式无效，请输入11位手机号或座机号码"

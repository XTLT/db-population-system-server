# -*- coding: utf-8 -*-
"""把权威校验向量同步到 desktop / mobile 两端，并校验三份 sha256 一致。

权威源：本目录的 validation_vectors.json（随 server 仓库走）
副本：  desktop/tests/vectors/validation_vectors.json
        mobile/test/vectors/validation_vectors.json

用法：
    python tests/vectors/sync_vectors.py          # 复制并校验
    python tests/vectors/sync_vectors.py --check  # 只校验，不写盘（改完向量的自检）
"""

import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'validation_vectors.json')
SPLIT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # ...\split

TARGETS = [
    os.path.join(SPLIT, 'db-population-system-desktop', 'tests', 'vectors', 'validation_vectors.json'),
    os.path.join(SPLIT, 'db-population-system-mobile', 'test', 'vectors', 'validation_vectors.json'),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    check_only = '--check' in sys.argv

    if not os.path.exists(SRC):
        print('FAIL: 权威向量不存在: %s' % SRC)
        return 1

    src_hash = sha256(SRC)
    print('source  %s  %s' % (src_hash[:16], SRC))

    if not check_only:
        for t in TARGETS:
            os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copyfile(SRC, t)
            print('copied  -> %s' % t)

    bad = 0
    for t in TARGETS:
        if not os.path.exists(t):
            print('MISSING %s' % t)
            bad += 1
            continue
        h = sha256(t)
        ok = h == src_hash
        print('%s %s  %s' % ('MATCH  ' if ok else 'DIFFERS', h[:16], t))
        if not ok:
            bad += 1

    if bad:
        print('RESULT: %d 份副本与权威源不一致' % bad)
        return 1
    print('RESULT: 3 份向量一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())

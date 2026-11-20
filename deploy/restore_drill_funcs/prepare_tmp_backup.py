"""把备份里的库文件复制到临时目录（只复制 db / enc / manifest，照片不参与演练）。"""

import os
import shutil
import tempfile

from .constants import DB_FILE_NAME, ENC_FILE_NAME, MANIFEST_NAME


def prepare_tmp_backup(src_dir):
    tmp_dir = tempfile.mkdtemp(prefix="restore_drill_")
    for name in (DB_FILE_NAME, ENC_FILE_NAME, MANIFEST_NAME):
        src = os.path.join(src_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(tmp_dir, name))
    return tmp_dir

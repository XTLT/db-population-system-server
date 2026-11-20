"""把身份证体检结果写成 CSV（默认只写问题行）。"""

import csv
import os


def write_csv(results, output, include_ok=False):
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
    written = 0
    # utf-8-sig：Excel 直接双击打开不乱码
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["姓名", "户号", "身份证（库中原文）", "问题类型", "说明",
                         "是否死亡", "推算性别", "内部ID"])
        for r in results:
            if not include_ok and r["valid"] and not r["problem"]:
                continue
            writer.writerow([r["name"], r["hu_hao"], r["id_card"], r["problem"],
                             r["detail"], r["is_dead"], r["gender_by_id"], r["id"]])
            written += 1
    return written

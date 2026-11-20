"""把恢复演练报告打印到终端。"""


def print_report(report):
    print(f"备份: {report['backup']}  时间戳: {report.get('backup_timestamp', '-')}")
    print(f"加密: {'是' if report.get('encrypted') else '否'}  "
          f"integrity_check: {report.get('integrity', '-')}")
    print("")
    print(f"{'表':28s}{'备份行数':>10s}{'线上行数':>10s}{'差异':>10s}  说明")
    print("-" * 78)
    for row in report.get("tables", []):
        left = row["backup_rows"]
        right = row["live_rows"]
        delta = row.get("delta_since_backup")
        left_s = "-" if left is None else str(left)
        right_s = "-" if right is None else str(right)
        delta_s = "-" if delta is None else f"{delta:+d}"
        print(f"{row['label'] + '(' + row['table'] + ')':28s}{left_s:>10s}{right_s:>10s}{delta_s:>10s}")
    print("")
    if report.get("problems"):
        print("问题:")
        for p in report["problems"]:
            print(f"  - {p}")
    print(f"结论: {report['result']}")

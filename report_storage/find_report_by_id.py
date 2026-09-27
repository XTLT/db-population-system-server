from .list_all_reports import list_all_reports


def find_report_by_id(report_id: str) -> dict | None:
    all_reports = list_all_reports()
    for r in all_reports:
        if r.get("report_id") == report_id:
            return r
    return None

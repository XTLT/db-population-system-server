"""报表口径说明：随报表一起返回，说明统计时点、范围和分母。"""
from datetime import datetime

_TYPE_TEXT = {
    "person": (
        "人员类报表",
        "仅统计在世人员（排除 is_dead='是'，空值视为在世）",
        "person 表全部在世记录",
    ),
    "student": (
        "学生类报表",
        "学生状态为「在读 / 跳级 / 留级」的记录",
        "student_education 表按状态过滤后的记录",
    ),
    "subsidy": (
        "补贴类报表",
        "地力补贴全部发放记录（不区分人员状态）",
        "land_subsidy 表按年份过滤后的记录",
    ),
}


def build_report_scope(report_type: str, start_date: str = "", end_date: str = "", total: int = 0) -> dict:
    name, range_text, denominator = _TYPE_TEXT.get(
        report_type, (report_type, "未定义", "未定义")
    )
    return {
        "报表类型": name,
        "统计时点": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "统计区间": f"{start_date or '不限'} ~ {end_date or '不限'}",
        "统计范围": range_text,
        "分母口径": denominator,
        "总记录数": total,
        "一致性说明": (
            "人员类报表与系统统计页使用同一口径（都排除已死亡人员），可直接对照；"
            "学生类和补贴类报表只统计各自业务表，不涉及人员死亡状态。"
        ),
    }

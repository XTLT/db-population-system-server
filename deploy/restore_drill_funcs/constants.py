"""恢复演练的必检表、附加表与备份文件名常量。"""

# 用户口径的必检表：人员 + 6 张补贴表
CORE_TABLES = [
    ("persons", "人员"),
    ("land_subsidy", "地力补贴"),
    ("dibao_payment", "低保"),
    ("tekun_payment", "特困"),
    ("elderly_allowance", "高龄补贴"),
    ("disability_care_payment", "残疾人护理补贴"),
    ("pension_insurance", "养老保险"),
]

# 附加信息（报告里展示，不影响 PASS/FAIL 判定）
EXTRA_TABLES = [
    ("users", "用户"),
    ("student_education", "就读信息"),
    ("education_history", "就读历史"),
    ("operation_logs", "操作日志"),
    ("report_operation_logs", "报表日志"),
    ("deleted_persons", "已删除人员"),
]

MANIFEST_NAME = "backup_complete.txt"
DB_FILE_NAME = "population.db"
ENC_FILE_NAME = "population.db.enc"

# -*- coding: utf-8 -*-
"""人口通服务端数据库层（由原 database.py 拆分而来的包）。

本文件是向后兼容 shim：原 `from database import X` 的所有调用点无需改动。
导入顺序：先 _base（Base/引擎/session），再全部模型（让 metadata 注册完整），
最后业务函数。
"""

# ---- _base：常量 / Base / 密码加解密 / 引擎 / session / 初始化 ----
from ._base import (
    SERVICE_NAME,
    Base,
    set_db_password,
    get_db_password,
    _derive_key,
    encrypt_database,
    decrypt_database,
    is_database_encrypted,
    get_engine,
    reset_engine,
    get_session,
    init_db,
    _migrate_db,
)

# ---- 模型（必须在函数之前全部导入，metadata 才完整）----
from .models.person import Person
from .models.student_education import StudentEducation
from .models.land_subsidy import LandSubsidy
from .models.treatment_payment import TreatmentPayment
from .models.pension_insurance import PensionInsurance
from .models.dibao_payment import DibaoPayment
from .models.tekun_payment import TekunPayment
from .models.disability_care_payment import DisabilityCarePayment
from .models.elderly_allowance import ElderlyAllowance
from .models.education_history import EducationHistory
from .models.user import User
from .models.operation_log import OperationLog
from .models.token import Token
from .models.deleted_person import DeletedPerson
from .models.report_operation_log import ReportOperationLog
from .models.report_file import ReportFile
from .models.notification import Notification
from .models.custom_report import CustomReport

# ---- 业务函数 ----
from .functions.validate_password import validate_password
from .functions.create_user import create_user
from .functions.authenticate_user import authenticate_user
from .functions.add_operation_log import add_operation_log
from .functions.get_operation_logs import get_operation_logs
from .functions.get_operation_types import get_operation_types
from .functions.get_operation_log_stats import get_operation_log_stats
from .functions.get_all_users import get_all_users
from .functions.delete_user import delete_user
from .functions.update_user import update_user
from .functions.change_user_password import change_user_password
from .functions.search_by_name import search_by_name
from .functions.search_persons_advanced import search_persons_advanced
from .functions.get_family_members import get_family_members
from .functions.add_person import add_person
from .functions.update_person import update_person
from .functions.get_person_count import get_person_count
from .functions.check_duplicate_id_card import check_duplicate_id_card
from .functions.id_card_exists import id_card_exists
from .functions.generate_new_hu_hao import generate_new_hu_hao
from .functions.split_household import split_household
from .functions.merge_household import merge_household
from .functions.add_new_household import add_new_household
from .functions.migrate_person import migrate_person
from .functions.delete_person import delete_person
from .functions.recover_person import recover_person
from .functions.get_deleted_persons import get_deleted_persons
from .functions.get_report_logs import get_report_logs
from .functions.create_report_file import create_report_file
from .functions.get_report_files import get_report_files
from .functions.get_report_file import get_report_file
from .functions.delete_report_file import delete_report_file
from .functions.add_report_log import add_report_log
from .functions.get_student_education import get_student_education
from .functions.save_student_education import save_student_education
from .functions.delete_student_education import delete_student_education
from .functions.get_education_history import get_education_history
from .functions.get_all_students import get_all_students
from .functions.search_students import search_students
from .functions.batch_update_school import batch_update_school
from .functions.batch_set_left_behind import batch_set_left_behind
from .functions.promote_all_grades import promote_all_grades
from .functions.create_notification import create_notification
from .functions.get_notifications import get_notifications
from .functions.mark_notification_read import mark_notification_read
from .functions.get_unread_count import get_unread_count
from .functions.get_person_trend_data import get_person_trend_data
from .functions.get_person_distribution import get_person_distribution
from .functions.get_person_comparison import get_person_comparison
from .functions.create_custom_report import create_custom_report
from .functions.get_custom_reports import get_custom_reports
from .functions.get_custom_report import get_custom_report
from .functions.update_custom_report import update_custom_report
from .functions.delete_custom_report import delete_custom_report
from .functions.generate_report_data import generate_report_data

__all__ = [
    # 常量 / Base
    "SERVICE_NAME",
    "Base",
    # 密码 / 加解密 / 引擎 / session / 初始化
    "set_db_password",
    "get_db_password",
    "_derive_key",
    "encrypt_database",
    "decrypt_database",
    "is_database_encrypted",
    "get_engine",
    "reset_engine",
    "get_session",
    "init_db",
    "_migrate_db",
    # 模型
    "Person",
    "StudentEducation",
    "LandSubsidy",
    "TreatmentPayment",
    "PensionInsurance",
    "DibaoPayment",
    "TekunPayment",
    "DisabilityCarePayment",
    "ElderlyAllowance",
    "EducationHistory",
    "User",
    "OperationLog",
    "Token",
    "DeletedPerson",
    "ReportOperationLog",
    "ReportFile",
    "Notification",
    "CustomReport",
    # 函数
    "validate_password",
    "create_user",
    "authenticate_user",
    "add_operation_log",
    "get_operation_logs",
    "get_operation_types",
    "get_operation_log_stats",
    "get_all_users",
    "delete_user",
    "update_user",
    "change_user_password",
    "search_by_name",
    "search_persons_advanced",
    "get_family_members",
    "add_person",
    "update_person",
    "get_person_count",
    "check_duplicate_id_card",
    "id_card_exists",
    "generate_new_hu_hao",
    "split_household",
    "merge_household",
    "add_new_household",
    "migrate_person",
    "delete_person",
    "recover_person",
    "get_deleted_persons",
    "get_report_logs",
    "create_report_file",
    "get_report_files",
    "get_report_file",
    "delete_report_file",
    "add_report_log",
    "get_student_education",
    "save_student_education",
    "delete_student_education",
    "get_education_history",
    "get_all_students",
    "search_students",
    "batch_update_school",
    "batch_set_left_behind",
    "promote_all_grades",
    "create_notification",
    "get_notifications",
    "mark_notification_read",
    "get_unread_count",
    "get_person_trend_data",
    "get_person_distribution",
    "get_person_comparison",
    "create_custom_report",
    "get_custom_reports",
    "get_custom_report",
    "update_custom_report",
    "delete_custom_report",
    "generate_report_data",
]

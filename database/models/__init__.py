"""SQLAlchemy 模型定义：导入即注册到 Base.metadata。"""

from .person import Person
from .student_education import StudentEducation
from .land_subsidy import LandSubsidy
from .treatment_payment import TreatmentPayment
from .pension_insurance import PensionInsurance
from .dibao_payment import DibaoPayment
from .tekun_payment import TekunPayment
from .education_history import EducationHistory
from .user import User
from .operation_log import OperationLog
from .token import Token
from .deleted_person import DeletedPerson
from .report_operation_log import ReportOperationLog
from .report_file import ReportFile
from .notification import Notification
from .custom_report import CustomReport

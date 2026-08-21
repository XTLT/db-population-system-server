import os
import sys
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

APP_NAME = "人口信息查询系统"
APP_VERSION = "2.3.12"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "win32":
    APPDATA_DIR = os.path.join(os.environ.get("APPDATA", BASE_DIR), APP_NAME)
else:
    APPDATA_DIR = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)

CONFIG_FILE = os.path.join(APPDATA_DIR, "data_path.conf")
_SALT = b'population_config_salt_v1'


def _get_machine_key():
    if sys.platform == "win32":
        info = (os.environ.get("COMPUTERNAME", "") + os.environ.get("USERNAME", "")).encode()
    else:
        info = (os.environ.get("HOSTNAME", "") + os.environ.get("USER", "")).encode()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(info))
    return key


def _get_fernet():
    key = _get_machine_key()
    return Fernet(key)


def encrypt_path(path):
    fernet = _get_fernet()
    encrypted = fernet.encrypt(path.encode("utf-8"))
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_path(token):
    fernet = _get_fernet()
    encrypted = base64.b64decode(token)
    return fernet.decrypt(encrypted).decode("utf-8")


def get_data_dir():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                token = f.read().strip()
            if token:
                path = decrypt_path(token)
                if os.path.isdir(path):
                    return path
        except Exception:
            pass
    return BASE_DIR


DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "population.db")
PHOTOS_DIR = os.path.join(DATA_DIR, "Photos")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LOG_DIR = os.path.join(DATA_DIR, "logs")
CERT_DIR = os.path.join(DATA_DIR, "certs")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

BACKUP_RETENTION_DAYS = 60
BACKUP_SCHEDULE_DAY = 4
BACKUP_SCHEDULE_HOUR = 22
BACKUP_SCHEDULE_MINUTE = 0

LOGIN_LOCK_ATTEMPTS = 5
LOGIN_LOCK_MINUTES = 15
TOKEN_EXPIRY_HOURS = 2

DISK_SPACE_ALERT_GB = 10

EXCEL_TEMPLATE_COLUMNS = [
    "户号", "身份证号", "姓名", "地址", "与户主关系", "是否死亡",
    "电话", "备注", "脱贫户或监测户", "残疾", "残疾等级",
    "低保", "是否计生家庭", "社保卡号1", "社保卡号2", "社保卡号3", "土地面积"
]

STUDENT_EDUCATION_COLUMNS = [
    "身份证号", "学校名称", "年级", "班级", "监护人", "监护人电话",
    "是否留守儿童", "学生状态", "入学日期"
]

GRADES = [
    "T1",
    "K1", "K2", "K3",
    "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12",
    "V1", "V2", "V3",
    "J1", "J2", "J3",
    "C1", "C2", "C3",
    "Z1", "Z2", "Z3",
    "U1", "U2", "U3", "U4", "U5",
    "M1", "M2", "M3",
    "D1", "D2", "D3", "D4",
    "GRADUATED"
]

GRADE_DISPLAY = {
    "T1": "托班",
    "K1": "幼儿园小班", "K2": "幼儿园中班", "K3": "幼儿园大班",
    "G1": "小学1年级", "G2": "小学2年级", "G3": "小学3年级", "G4": "小学4年级", "G5": "小学5年级", "G6": "小学6年级",
    "G7": "初中1年级", "G8": "初中2年级", "G9": "初中3年级",
    "G10": "高中1年级", "G11": "高中2年级", "G12": "高中3年级",
    "V1": "职高1年级", "V2": "职高2年级", "V3": "职高3年级",
    "J1": "技校1年级", "J2": "技校2年级", "J3": "技校3年级",
    "C1": "中专1年级", "C2": "中专2年级", "C3": "中专3年级",
    "Z1": "专科1年级", "Z2": "专科2年级", "Z3": "专科3年级",
    "U1": "大学1年级", "U2": "大学2年级", "U3": "大学3年级", "U4": "大学4年级", "U5": "大学5年级",
    "M1": "硕士1年级", "M2": "硕士2年级", "M3": "硕士3年级",
    "D1": "博士1年级", "D2": "博士2年级", "D3": "博士3年级", "D4": "博士4年级",
    "GRADUATED": "已毕业"
}

GRADE_PROMOTION_MAP = {
    "T1": "K1",
    "K1": "K2", "K2": "K3", "K3": "G1",
    "G1": "G2", "G2": "G3", "G3": "G4", "G4": "G5", "G5": "G6", "G6": "G7",
    "G7": "G8", "G8": "G9", "G9": "G10",
    "G10": "G11", "G11": "G12", "G12": "U1",
    "V1": "V2", "V2": "V3", "V3": "GRADUATED",
    "J1": "J2", "J2": "J3", "J3": "GRADUATED",
    "C1": "C2", "C2": "C3", "C3": "GRADUATED",
    "Z1": "Z2", "Z2": "Z3", "Z3": "U3",
    "U1": "U2", "U2": "U3", "U3": "U4", "U4": "U5", "U5": "GRADUATED",
    "M1": "M2", "M2": "M3", "M3": "GRADUATED",
    "D1": "D2", "D2": "D3", "D3": "D4", "D4": "GRADUATED"
}


GRADUATION_GRADES = {"V3", "J3", "C3", "U5", "M3", "D4"}

STUDENT_STATUSES = ["在读", "留级", "跳级", "休学", "转学", "毕业"]

BLOCKED_PROMOTION_STATUSES = {"留级", "休学", "转学"}

DB_FIELD_MAP = {
    "户号": "hu_hao",
    "身份证号": "id_card",
    "姓名": "name",
    "地址": "address",
    "与户主关系": "relation",
    "是否死亡": "is_dead",
    "电话": "phone",
    "备注": "remark",
    "脱贫户或监测户": "poor_type",
    "残疾": "disability",
    "残疾等级": "dis_level",
    "低保": "dibao",
    "是否计生家庭": "jisheng",
    "社保卡号1": "social_card1",
    "社保卡号2": "social_card2",
    "社保卡号3": "social_card3",
    "土地面积": "land_area",
}

PHOTO_TYPES = ["身份证", "社保卡1", "社保卡2", "社保卡3"]
PHOTO_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]
MATCHES_PER_COLUMN = 15
MAX_COLUMNS = 18
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_EXCEL_UPLOAD_SIZE = 50 * 1024 * 1024
BTN_SAVE_COLOR = "#4472C4"
BTN_ADD_COLOR = "#00994C"
BTN_CANCEL_COLOR = "#C8C8C8"
FONT_NAME = "微软雅黑"
FONT_SIZE = 10


def ensure_dirs():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

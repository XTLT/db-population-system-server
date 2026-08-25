from sqlalchemy import create_engine, Column, String, Index, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import DB_PATH
import os
import hashlib
import secrets
import logging

from utils.security import hash_password, verify_password

SERVICE_NAME = "population-query-system"
logger = logging.getLogger('population_system')

Base = declarative_base()

_db_password = None


def set_db_password(password: str):
    global _db_password
    _db_password = password
    try:
        import keyring
        keyring.set_password(SERVICE_NAME, "db_password", password)
    except Exception as e:
        logger.warning(f"无法保存密码到系统密钥环: {e}")


def get_db_password() -> str:
    global _db_password
    if _db_password:
        return _db_password
    try:
        import keyring
        pw = keyring.get_password(SERVICE_NAME, "db_password")
        if pw:
            _db_password = pw
            return pw
    except Exception as e:
        logger.warning(f"无法从系统密钥环读取密码: {e}")
    return ""


def clear_db_password():
    global _db_password
    _db_password = None
    try:
        import keyring
        keyring.delete_password(SERVICE_NAME, "db_password")
    except Exception as e:
        logger.warning(f"无法从系统密钥环删除密码: {e}")


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)


def encrypt_database(password: str):
    if not os.path.exists(DB_PATH):
        return
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except Exception as e:
        logger.warning(f"数据库检查点失败: {e}")
    salt = secrets.token_bytes(32)
    key = _derive_key(password, salt)
    with open(DB_PATH, 'rb') as f:
        data = f.read()

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce, data, None)

    with open(DB_PATH + '.enc', 'wb') as f:
        f.write(salt + nonce + encrypted)

    os.remove(DB_PATH)
    for ext in ['-wal', '-shm']:
        p = DB_PATH + ext
        if os.path.exists(p):
            os.remove(p)

    key_path = DB_PATH + '.key'
    if os.path.exists(key_path):
        os.remove(key_path)


def decrypt_database(password: str) -> bool:
    enc_path = DB_PATH + '.enc'
    if not os.path.exists(enc_path):
        return True
    try:
        with open(enc_path, 'rb') as f:
            content = f.read()

        if len(content) < 44:
            return False

        salt = content[:32]
        nonce = content[32:44]
        encrypted = content[44:]

        key = _derive_key(password, salt)

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        data = aesgcm.decrypt(nonce, encrypted, None)

        with open(DB_PATH, 'wb') as f:
            f.write(data)
        return True
    except Exception:
        return False


def is_database_encrypted() -> bool:
    return os.path.exists(DB_PATH + '.enc')


class Person(Base):
    __tablename__ = "persons"

    id = Column(String, primary_key=True)
    hu_hao = Column(String, nullable=False, index=True)
    id_card = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    age = Column(String, default="")
    address = Column(String, default="")
    relation = Column(String, default="")
    is_dead = Column(String, default="否")
    phone = Column(String, default="")
    remark = Column(String, default="")
    poor_type = Column(String, default="")
    disability = Column(String, default="")
    disability_type = Column(String, default="")
    dis_level = Column(String, default="")
    dibao = Column(String, default="")
    jisheng = Column(String, default="")
    social_card1 = Column(String, default="")
    social_card2 = Column(String, default="")
    social_card3 = Column(String, default="")
    is_migrated = Column(String, default="否")
    migration_date = Column(String, default="")
    migration_place = Column(String, default="")
    migration_reason = Column(String, default="")
    updated_at = Column(String, default="")
    land_area = Column(String, default="")
    land_area_change_reason = Column(String, default="")
    land_area_change_time = Column(String, default="")

    __table_args__ = (
        Index("idx_name_hu_hao", "name", "hu_hao"),
    )


class StudentEducation(Base):
    __tablename__ = "student_education"

    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    id_card = Column(String, nullable=False, index=True)
    school_name = Column(String, default="")
    grade = Column(String, default="")
    class_name = Column(String, default="")
    guardian = Column(String, default="")
    guardian_phone = Column(String, default="")
    is_left_behind = Column(String, default="否")
    student_status = Column(String, default="在读")
    enrollment_date = Column(String, default="")
    graduation_date = Column(String, default="")


class LandSubsidy(Base):
    __tablename__ = "land_subsidy"

    id = Column(String, primary_key=True)
    person_id = Column(String, default="")
    id_card = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    year = Column(String, default="", index=True)  # 补贴年份
    land_area = Column(String, default="")  # 土地面积
    subsidy_amount = Column(String, default="")  # 补贴金额
    certified_area = Column(String, default="")  # 确权面积
    subsidy_area = Column(String, default="")  # 补贴面积
    base_standard = Column(String, default="")  # 基础标准
    rape_area = Column(String, default="")  # 油菜面积
    rape_amount = Column(String, default="")  # 油菜金额
    total_amount = Column(String, default="")  # 总金额
    created_at = Column(String, default="")  # 创建时间
    import_time = Column(String, default="")


class TreatmentPayment(Base):
    __tablename__ = "treatment_payment"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    id_card = Column(String, default="", index=True)
    town = Column(String, default="")  # 所属乡镇
    village = Column(String, default="")  # 所属村
    period = Column(String, default="", index=True)  # 费款所属期/年月
    payment_status = Column(String, default="")  # 支付标志
    personal_code = Column(String, default="")  # 个人编号
    bank_account = Column(String, default="")
    amount = Column(String, default="")
    subsidy_type = Column(String, default="")  # 救助类型(低保/特困等)
    relation = Column(String, default="")  # 和申请人关系
    fail_reason = Column(String, default="")  # 失败原因
    import_time = Column(String, default="")
    import_source = Column(String, default="")  # 导入来源文件名


class PensionInsurance(Base):
    __tablename__ = "pension_insurance"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    id_card = Column(String, default="", index=True)
    town = Column(String, default="")  # 所属乡镇
    village = Column(String, default="")  # 所属村
    period = Column(String, default="", index=True)  # 费款所属期/年月
    payment_status = Column(String, default="")  # 支付标志
    personal_code = Column(String, default="")  # 个人编号
    person_id = Column(String, default="")  # 享受定期待遇人员ID
    bank_account = Column(String, default="")
    amount = Column(String, default="")
    fail_reason = Column(String, default="")  # 失败原因
    import_time = Column(String, default="")
    import_source = Column(String, default="")  # 导入来源文件名


class EducationHistory(Base):
    __tablename__ = "education_history"

    id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False, index=True)
    id_card = Column(String, nullable=False)
    school_name = Column(String, default="")
    grade = Column(String, default="")
    class_name = Column(String, default="")
    student_status = Column(String, default="")
    change_date = Column(String, default="")
    change_reason = Column(String, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    real_name = Column(String, default="")
    role = Column(String, default="user")
    is_active = Column(String, default="是")
    is_default = Column(String, default="否")
    created_at = Column(String, default="")
    last_login = Column(String, default="")
    login_attempts = Column(String, default="0")
    locked_until = Column(String, default="")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)
    operation_target = Column(String, default="")
    ip_address = Column(String, default="")
    client_type = Column(String, default="")
    created_at = Column(String, nullable=False)
    is_high_risk = Column(String, default="否")


class Token(Base):
    __tablename__ = "tokens"

    token = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    user_data = Column(String, nullable=False)  # JSON 格式的用户数据
    expires_at = Column(String, nullable=False)
    created_at = Column(String, default="")
    ip = Column(String, default="")


class DeletedPerson(Base):
    __tablename__ = "deleted_persons"

    id = Column(String, primary_key=True)
    original_id = Column(String, nullable=False)
    hu_hao = Column(String, nullable=False)
    id_card = Column(String, nullable=False)
    name = Column(String, nullable=False)
    age = Column(String, default="")
    address = Column(String, default="")
    relation = Column(String, default="")
    is_dead = Column(String, default="否")
    phone = Column(String, default="")
    remark = Column(String, default="")
    poor_type = Column(String, default="")
    disability = Column(String, default="")
    disability_type = Column(String, default="")
    dis_level = Column(String, default="")
    dibao = Column(String, default="")
    jisheng = Column(String, default="")
    social_card1 = Column(String, default="")
    social_card2 = Column(String, default="")
    social_card3 = Column(String, default="")
    is_migrated = Column(String, default="否")
    migration_date = Column(String, default="")
    migration_place = Column(String, default="")
    migration_reason = Column(String, default="")
    deleted_at = Column(String, nullable=False)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    return _engine


class ReportOperationLog(Base):
    __tablename__ = "report_operation_logs"
    id = Column(String, primary_key=True)
    report_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)
    operation_detail = Column(String, default="")
    ip_address = Column(String, default="")
    client_type = Column(String, default="")
    created_at = Column(String, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    notification_type = Column(String, default="system")  # system, business
    target_user = Column(String, default="")  # 空=所有用户，指定用户名=特定用户
    sender_id = Column(String, default="")
    sender_name = Column(String, default="")
    is_read = Column(String, default="否")
    created_at = Column(String, nullable=False)
    read_at = Column(String, default="")


class CustomReport(Base):
    __tablename__ = "custom_reports"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    report_type = Column(String, nullable=False)  # person, student, subsidy
    dimensions = Column(String, default="")  # JSON: 统计维度列表
    date_range = Column(String, default="")  # JSON: {start, end}
    chart_type = Column(String, default="bar")  # bar, line, pie, radar
    filters = Column(String, default="")  # JSON: 筛选条件
    created_at = Column(String, nullable=False)
    updated_at = Column(String, default="")


_engine = None
_SessionFactory = None


def reset_engine():
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None


def get_session() -> Session:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    _migrate_db(engine)


def _migrate_db(engine):
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN updated_at VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_default VARCHAR DEFAULT '否'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN land_area VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN land_area_change_reason VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN land_area_change_time VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        # treatment_payment 表新增字段
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN id_card VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN town VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN village VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN period VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN payment_status VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN personal_code VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN subsidy_type VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN relation VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN fail_reason VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE treatment_payment ADD COLUMN import_source VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        # land_subsidy 表迁移：subsidy_year -> year，添加新字段
        try:
            conn.execute(text("ALTER TABLE land_subsidy RENAME COLUMN subsidy_year TO year"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN year VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN land_area VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN subsidy_amount VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN created_at VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not any(c.isalpha() for c in password):
        return False, "密码必须包含字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    return True, ""


def create_user(username: str, password: str, real_name: str = "", role: str = "user") -> User:
    import hashlib
    import secrets
    from datetime import datetime
    valid, msg = validate_password(password)
    if not valid:
        raise ValueError(msg)
    session = get_session()
    try:
        existing = session.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("用户名已存在")
        salt = secrets.token_hex(16)
        # 使用双重哈希：sha256(salt + sha256(原始密码))
        password_sha256 = hashlib.sha256(password.encode()).hexdigest()
        password_hash = hashlib.sha256((salt + password_sha256).encode()).hexdigest()
        user = User(
            id=f"user_{secrets.token_hex(8)}",
            username=username,
            password_hash=f"{salt}:{password_hash}",
            real_name=real_name,
            role=role,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(user)
        session.commit()
        return user
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def authenticate_user(username: str, password: str, ip_address: str = "", client_type: str = "") -> User | None:
    import hashlib
    from datetime import datetime, timedelta
    session = get_session()
    try:
        user = session.query(User).filter(User.username == username, User.is_active == "是").first()
        if not user:
            return None
        if user.locked_until:
            try:
                lock_time = datetime.strptime(user.locked_until, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < lock_time:
                    return None
                user.locked_until = ""
                user.login_attempts = "0"
            except Exception:
                user.locked_until = ""
                user.login_attempts = "0"
        salt, stored_hash = user.password_hash.split(":")
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        if password_hash != stored_hash:
            attempts = int(user.login_attempts or "0") + 1
            user.login_attempts = str(attempts)
            if attempts >= 5:
                user.locked_until = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            return None
        user.login_attempts = "0"
        user.locked_until = ""
        user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        result = type('UserResult', (), {
            'id': user.id, 'username': user.username, 'real_name': user.real_name,
            'role': user.role, 'is_active': user.is_active
        })()
        return result
    finally:
        session.close()


def add_operation_log(user_id: str, username: str, operation_type: str, operation_target: str = "", ip_address: str = "", client_type: str = "", is_high_risk: str = "否"):
    from datetime import datetime
    import secrets
    session = get_session()
    try:
        log = OperationLog(
            id=f"log_{secrets.token_hex(8)}",
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            operation_target=operation_target,
            ip_address=ip_address,
            client_type=client_type,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_high_risk=is_high_risk
        )
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_operation_logs(limit: int = 100, username: str = None, operation_type: str = None, start_date: str = None, end_date: str = None) -> list:
    session = get_session()
    try:
        query = session.query(OperationLog)
        
        # 应用筛选条件
        if username:
            query = query.filter(OperationLog.username == username)
        
        if operation_type:
            query = query.filter(OperationLog.operation_type == operation_type)
        
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        
        if end_date:
            # 结束日期包含当天的所有记录
            end_datetime = f"{end_date} 23:59:59"
            query = query.filter(OperationLog.created_at <= end_datetime)
        
        # 按时间倒序排列
        query = query.order_by(OperationLog.created_at.desc())
        
        # 限制返回数量
        return query.limit(limit).all()
    finally:
        session.close()


def get_operation_types() -> list:
    session = get_session()
    try:
        from sqlalchemy import func
        result = session.query(
            OperationLog.operation_type
        ).distinct().order_by(OperationLog.operation_type).all()
        return [r[0] for r in result if r[0]]
    finally:
        session.close()


def get_operation_log_stats() -> dict:
    session = get_session()
    try:
        from sqlalchemy import func
        from datetime import datetime, date
        
        # 总记录数
        total = session.query(func.count(OperationLog.id)).scalar()
        
        # 今日记录数
        today_str = date.today().strftime("%Y-%m-%d")
        today = session.query(func.count(OperationLog.id)).filter(
            OperationLog.created_at >= today_str
        ).scalar()
        
        # 高风险操作数
        high_risk = session.query(func.count(OperationLog.id)).filter(
            OperationLog.is_high_risk == "是"
        ).scalar()
        
        # 按操作类型统计（前10）
        by_type_result = session.query(
            OperationLog.operation_type,
            func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.operation_type).order_by(
            func.count(OperationLog.id).desc()
        ).limit(10).all()
        
        by_type = {r[0]: r[1] for r in by_type_result}
        
        # 按用户统计（前5）
        by_user_result = session.query(
            OperationLog.username,
            func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.username).order_by(
            func.count(OperationLog.id).desc()
        ).limit(5).all()
        
        by_user = {r[0]: r[1] for r in by_user_result}
        
        return {
            'total': total or 0,
            'today': today or 0,
            'high_risk': high_risk or 0,
            'by_type': by_type,
            'by_user': by_user
        }
    finally:
        session.close()


def get_all_users(limit: int = None) -> list:
    session = get_session()
    try:
        query = session.query(User)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    finally:
        session.close()


def delete_user(user_id: str):
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_user(user_id: str, **kwargs):
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def change_user_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    valid, msg = validate_password(new_password)
    if not valid:
        return False, msg
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        
        is_valid, needs_rehash = verify_password(old_password, user.password_hash)
        if not is_valid:
            return False, "原密码错误"
        
        user.password_hash = hash_password(new_password)
        session.commit()
        return True, ""
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def search_by_name(name: str) -> list[Person]:
    import re
    session = get_session()
    try:
        # 转义LIKE特殊字符: % 匹配任意字符, _ 匹配单个字符
        escaped_name = re.sub(r'([%_])', r'\\\1', name)
        return session.query(Person).filter(Person.name.like(f"%{escaped_name}%", escape='\\')).all()
    finally:
        session.close()


def search_persons_advanced(
    name: str = "",
    id_card: str = "",
    hu_hao: str = "",
    address: str = "",
    age_min: int = None,
    age_max: int = None,
    disability: str = "",
    dibao: str = "",
    is_dead: str = "",
    limit: int = 100
) -> list:
    import re
    
    def escape_like(value: str) -> str:
        return re.sub(r'([%_])', r'\\\1', value)
    
    session = get_session()
    try:
        query = session.query(Person)
        
        # 应用筛选条件（使用参数化查询和转义）
        if name:
            escaped_name = escape_like(name)
            query = query.filter(Person.name.like(f"%{escaped_name}%", escape='\\'))
        
        if id_card:
            # 支持后6位查询
            if len(id_card) <= 6:
                escaped_id = escape_like(id_card)
                query = query.filter(Person.id_card.like(f"%{escaped_id}%", escape='\\'))
            else:
                query = query.filter(Person.id_card == id_card)
        
        if hu_hao:
            query = query.filter(Person.hu_hao == hu_hao)
        
        if address:
            escaped_address = escape_like(address)
            query = query.filter(Person.address.like(f"%{escaped_address}%", escape='\\'))
        
        if age_min is not None:
            query = query.filter(Person.age >= str(age_min))
        
        if age_max is not None:
            query = query.filter(Person.age <= str(age_max))
        
        if disability:
            query = query.filter(Person.disability == disability)
        
        if dibao:
            query = query.filter(Person.dibao == dibao)
        
        if is_dead:
            query = query.filter(Person.is_dead == is_dead)
        
        return query.limit(limit).all()
    finally:
        session.close()


def get_family_members(hu_hao: str) -> list[Person]:
    session = get_session()
    try:
        return session.query(Person).filter(Person.hu_hao == hu_hao).all()
    finally:
        session.close()


def get_person_by_id(person_id: str) -> Person | None:
    session = get_session()
    try:
        return session.query(Person).filter(Person.id == person_id).first()
    finally:
        session.close()


def add_person(person: Person):
    session = get_session()
    try:
        session.add(person)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_person(person: Person):
    from datetime import datetime
    session = get_session()
    try:
        person.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.merge(person)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_persons(limit: int = None, offset: int = None) -> list[Person]:
    session = get_session()
    try:
        query = session.query(Person)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query.all()
    finally:
        session.close()


def get_person_count() -> int:
    session = get_session()
    try:
        return session.query(Person).count()
    finally:
        session.close()


def check_duplicate_id_card(hu_hao: str, id_card: str, exclude_id: str = None) -> bool:
    session = get_session()
    try:
        q = session.query(Person).filter(Person.hu_hao == hu_hao, Person.id_card == id_card)
        if exclude_id:
            q = q.filter(Person.id != exclude_id)
        return q.first() is not None
    finally:
        session.close()


def update_all_ages():
    from utils import calculate_age
    session = get_session()
    try:
        persons = session.query(Person).all()
        for p in persons:
            p.age = calculate_age(p.id_card)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def generate_new_hu_hao() -> str:
    session = get_session()
    try:
        persons = session.query(Person).all()
        max_num = 0
        for p in persons:
            try:
                num = int(p.hu_hao)
                if num > max_num:
                    max_num = num
            except (ValueError, TypeError):
                pass
        return str(max_num + 1)
    finally:
        session.close()


def split_household(person_ids: list, new_hu_hao: str = None) -> str:
    if not person_ids:
        raise ValueError("请选择要分户的人员")
    if not new_hu_hao:
        new_hu_hao = generate_new_hu_hao()
    session = get_session()
    try:
        for pid in person_ids:
            p = session.query(Person).filter(Person.id == pid).first()
            if p:
                p.hu_hao = new_hu_hao
                p.relation = "户主"
                from datetime import datetime
                p.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        return new_hu_hao
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def merge_household(target_hu_hao: str, person_ids: list):
    if not person_ids:
        raise ValueError("请选择要合户的人员")
    session = get_session()
    try:
        for pid in person_ids:
            p = session.query(Person).filter(Person.id == pid).first()
            if p:
                p.hu_hao = target_hu_hao
                from datetime import datetime
                p.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_new_household(hu_hao: str, name: str, id_card: str, relation: str = "户主", **kwargs) -> Person:
    session = get_session()
    try:
        # 验证身份证号格式
        from utils import validate_id_card, validate_phone
        valid, msg = validate_id_card(id_card)
        if not valid:
            raise ValueError(msg)
        
        # 验证电话号码（如果提供）
        phone = kwargs.get("phone", "")
        if phone:
            valid, msg = validate_phone(phone)
            if not valid:
                raise ValueError(f"电话号码: {msg}")
        
        existing = session.query(Person).filter(Person.hu_hao == hu_hao).first()
        if existing:
            raise ValueError(f"户号 {hu_hao} 已存在")
        from utils import calculate_age
        person = Person(
            id=f"p_{hu_hao}_{secrets.token_hex(4)}",  # 使用随机ID，避免可预测性
            hu_hao=hu_hao,
            id_card=id_card,
            name=name,
            age=calculate_age(id_card),
            relation=relation,
            address=kwargs.get("address", ""),
            phone=phone,
            land_area=kwargs.get("land_area", ""),
        )
        session.add(person)
        session.commit()
        return person
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def migrate_person(person_id: str, migration_date: str, migration_place: str, migration_reason: str):
    session = get_session()
    try:
        person = session.query(Person).filter(Person.id == person_id).first()
        if person:
            person.is_migrated = "是"
            person.migration_date = migration_date
            person.migration_place = migration_place
            person.migration_reason = migration_reason
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_person(person_id: str):
    from datetime import datetime
    import uuid
    session = get_session()
    try:
        person = session.query(Person).filter(Person.id == person_id).first()
        if person:
            # 先删除关联的就读信息
            session.query(StudentEducation).filter(
                StudentEducation.person_id == person.id
            ).delete()

            deleted = DeletedPerson(
                id=f"del_{uuid.uuid4().hex[:8]}",
                original_id=person.id,
                hu_hao=person.hu_hao,
                id_card=person.id_card,
                name=person.name,
                age=person.age,
                address=person.address,
                relation=person.relation,
                is_dead=person.is_dead,
                phone=person.phone,
                remark=person.remark,
                poor_type=person.poor_type,
                disability=person.disability,
                disability_type=person.disability_type,
                dis_level=person.dis_level,
                dibao=person.dibao,
                jisheng=person.jisheng,
                social_card1=person.social_card1,
                social_card2=person.social_card2,
                social_card3=person.social_card3,
                is_migrated=person.is_migrated,
                migration_date=person.migration_date,
                migration_place=person.migration_place,
                migration_reason=person.migration_reason,
                deleted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(deleted)
            session.delete(person)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def recover_person(deleted_id: str):
    session = get_session()
    try:
        deleted = session.query(DeletedPerson).filter(DeletedPerson.id == deleted_id).first()
        if deleted:
            person = Person(
                id=deleted.original_id,
                hu_hao=deleted.hu_hao,
                id_card=deleted.id_card,
                name=deleted.name,
                age=deleted.age,
                address=deleted.address,
                relation=deleted.relation,
                is_dead=deleted.is_dead,
                phone=deleted.phone,
                remark=deleted.remark,
                poor_type=deleted.poor_type,
                disability=deleted.disability,
                dis_level=deleted.dis_level,
                dibao=deleted.dibao,
                jisheng=deleted.jisheng,
                social_card1=deleted.social_card1,
                social_card2=deleted.social_card2,
                social_card3=deleted.social_card3,
                is_migrated=deleted.is_migrated,
                migration_date=deleted.migration_date,
                migration_place=deleted.migration_place,
                migration_reason=deleted.migration_reason
            )
            session.add(person)
            session.delete(deleted)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_deleted_persons(limit: int = None) -> list:
    session = get_session()
    try:
        query = session.query(DeletedPerson)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    finally:
        session.close()


def add_report_log(report_id: str, user_id: str, username: str, operation_type: str, detail: str = "", ip_address: str = "", client_type: str = ""):
    from datetime import datetime
    import secrets
    session = get_session()
    try:
        log = ReportOperationLog(
            id=f"rlog_{secrets.token_hex(8)}",
            report_id=report_id,
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            operation_detail=detail,
            ip_address=ip_address,
            client_type=client_type,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_report_logs(report_id: str) -> list:
    session = get_session()
    try:
        return session.query(ReportOperationLog).filter(
            ReportOperationLog.report_id == report_id
        ).order_by(ReportOperationLog.created_at.desc()).all()
    finally:
        session.close()


def get_all_report_logs(limit: int = 200) -> list:
    session = get_session()
    try:
        return session.query(ReportOperationLog).order_by(
            ReportOperationLog.created_at.desc()
        ).limit(limit).all()
    finally:
        session.close()


def get_student_education(person_id: str) -> 'StudentEducation | None':
    session = get_session()
    try:
        return session.query(StudentEducation).filter(StudentEducation.person_id == person_id).first()
    finally:
        session.close()


def get_student_education_by_id_card(id_card: str) -> 'StudentEducation | None':
    session = get_session()
    try:
        return session.query(StudentEducation).filter(StudentEducation.id_card == id_card).first()
    finally:
        session.close()


def save_student_education(education: StudentEducation):
    session = get_session()
    try:
        existing = session.query(StudentEducation).filter(
            StudentEducation.person_id == education.person_id
        ).first()
        if existing:
            existing.school_name = education.school_name
            existing.grade = education.grade
            existing.class_name = education.class_name
            existing.guardian = education.guardian
            existing.guardian_phone = education.guardian_phone
            existing.is_left_behind = education.is_left_behind
            existing.student_status = education.student_status
            existing.enrollment_date = education.enrollment_date
        else:
            session.add(education)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_student_education(person_id: str):
    session = get_session()
    try:
        edu = session.query(StudentEducation).filter(StudentEducation.person_id == person_id).first()
        if edu:
            session.delete(edu)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_education_history(history: EducationHistory):
    session = get_session()
    try:
        session.add(history)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_education_history(person_id: str) -> list:
    session = get_session()
    try:
        return session.query(EducationHistory).filter(
            EducationHistory.person_id == person_id
        ).order_by(EducationHistory.change_date.desc()).all()
    finally:
        session.close()


def get_all_students() -> list:
    session = get_session()
    try:
        return session.query(StudentEducation).filter(
            StudentEducation.student_status.in_(["在读", "留级", "跳级"])
        ).all()
    finally:
        session.close()


def search_students(school: str = None, grade: str = None, class_name: str = None, is_left_behind: str = None) -> list:
    session = get_session()
    try:
        q = session.query(StudentEducation)
        if school:
            q = q.filter(StudentEducation.school_name == school)
        if grade:
            q = q.filter(StudentEducation.grade == grade)
        if class_name:
            q = q.filter(StudentEducation.class_name == class_name)
        if is_left_behind:
            q = q.filter(StudentEducation.is_left_behind == is_left_behind)
        return q.all()
    finally:
        session.close()


def batch_update_school(person_ids: list, school_name: str):
    session = get_session()
    try:
        for pid in person_ids:
            edu = session.query(StudentEducation).filter(StudentEducation.person_id == pid).first()
            if edu:
                edu.school_name = school_name
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def batch_set_left_behind(person_ids: list, is_left_behind: str):
    session = get_session()
    try:
        for pid in person_ids:
            edu = session.query(StudentEducation).filter(StudentEducation.person_id == pid).first()
            if edu:
                edu.is_left_behind = is_left_behind
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def promote_all_grades():
    from config import GRADE_PROMOTION_MAP, GRADUATION_GRADES, BLOCKED_PROMOTION_STATUSES
    from datetime import datetime
    session = get_session()
    try:
        students = session.query(StudentEducation).filter(
            StudentEducation.student_status.in_(["在读", "跳级"])
        ).all()
        count = 0
        for s in students:
            if s.student_status in BLOCKED_PROMOTION_STATUSES:
                continue
            new_grade = GRADE_PROMOTION_MAP.get(s.grade)
            if new_grade:
                history = EducationHistory(
                    id=f"hist_{datetime.now().strftime('%Y%m%d%H%M%S')}_{s.person_id}",
                    person_id=s.person_id,
                    id_card=s.id_card,
                    school_name=s.school_name,
                    grade=s.grade,
                    class_name=s.class_name,
                    student_status=s.student_status,
                    change_date=datetime.now().strftime("%Y-%m-%d"),
                    change_reason="自动升年级"
                )
                session.add(history)
                s.grade = new_grade
                if new_grade == "GRADUATED" or new_grade in GRADUATION_GRADES:
                    s.student_status = "毕业"
                count += 1
        session.commit()
        return count
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_notification(title: str, content: str, notification_type: str = "system",
                        target_user: str = "", sender_id: str = "", sender_name: str = "") -> dict:
    from datetime import datetime
    import secrets
    session = get_session()
    try:
        notification = Notification(
            id=f"notif_{secrets.token_hex(8)}",
            title=title,
            content=content,
            notification_type=notification_type,
            target_user=target_user,
            sender_id=sender_id,
            sender_name=sender_name,
            is_read="否",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            read_at=""
        )
        session.add(notification)
        session.commit()
        return {
            "id": notification.id,
            "title": notification.title,
            "content": notification.content,
            "notification_type": notification.notification_type,
            "target_user": notification.target_user,
            "sender_name": notification.sender_name,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_notifications(username: str = "", limit: int = 50) -> list:
    session = get_session()
    try:
        query = session.query(Notification)
        if username:
            # 获取发给所有人的和发给特定用户的
            query = query.filter(
                (Notification.target_user == "") | (Notification.target_user == username)
            )
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "notification_type": n.notification_type,
                "target_user": n.target_user,
                "sender_name": n.sender_name,
                "is_read": n.is_read,
                "created_at": n.created_at,
                "read_at": n.read_at
            }
            for n in notifications
        ]
    finally:
        session.close()


def mark_notification_read(notification_id: str) -> bool:
    from datetime import datetime
    session = get_session()
    try:
        notification = session.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = "是"
            notification.read_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_unread_count(username: str) -> int:
    session = get_session()
    try:
        count = session.query(Notification).filter(
            Notification.is_read == "否",
            ((Notification.target_user == "") | (Notification.target_user == username))
        ).count()
        return count
    finally:
        session.close()


def get_person_trend_data(start_date: str, end_date: str, group_by: str = 'month') -> dict:
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    session = get_session()
    try:
        # 解析日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now() - timedelta(days=365)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
        
        # 生成时间标签
        labels = []
        current = start_dt
        while current <= end_dt:
            if group_by == 'day':
                labels.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            elif group_by == 'week':
                # 按周分组（使用周一日期）
                week_start = current - timedelta(days=current.weekday())
                labels.append(week_start.strftime('%Y-%m-%d'))
                current += timedelta(weeks=1)
            elif group_by == 'month':
                labels.append(current.strftime('%Y-%m'))
                # 移动到下个月
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)
            elif group_by == 'year':
                labels.append(current.strftime('%Y'))
                current = current.replace(year=current.year + 1, day=1)
            else:
                labels.append(current.strftime('%Y-%m'))
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)
        
        # 统计新增人员（通过操作日志）
        addition_counts = {label: 0 for label in labels}
        additions = session.query(OperationLog).filter(
            OperationLog.operation_type == "添加人员",
            OperationLog.created_at >= start_dt.strftime('%Y-%m-%d'),
            OperationLog.created_at <= end_dt.strftime('%Y-%m-%d') + ' 23:59:59'
        ).all()
        
        for log in additions:
            if log.created_at:
                date_str = log.created_at.split()[0]  # 取日期部分
                try:
                    log_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    if group_by == 'day':
                        key = log_dt.strftime('%Y-%m-%d')
                    elif group_by == 'week':
                        week_start = log_dt - timedelta(days=log_dt.weekday())
                        key = week_start.strftime('%Y-%m-%d')
                    elif group_by == 'month':
                        key = log_dt.strftime('%Y-%m')
                    elif group_by == 'year':
                        key = log_dt.strftime('%Y')
                    else:
                        key = log_dt.strftime('%Y-%m')
                    
                    if key in addition_counts:
                        addition_counts[key] += 1
                except Exception:
                    pass
        
        # 统计删除人员
        deletion_counts = {label: 0 for label in labels}
        deletions = session.query(DeletedPerson).filter(
            DeletedPerson.deleted_at >= start_dt.strftime('%Y-%m-%d'),
            DeletedPerson.deleted_at <= end_dt.strftime('%Y-%m-%d') + ' 23:59:59'
        ).all()
        
        for deleted in deletions:
            if deleted.deleted_at:
                date_str = deleted.deleted_at.split()[0] if ' ' in deleted.deleted_at else deleted.deleted_at
                try:
                    del_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    if group_by == 'day':
                        key = del_dt.strftime('%Y-%m-%d')
                    elif group_by == 'week':
                        week_start = del_dt - timedelta(days=del_dt.weekday())
                        key = week_start.strftime('%Y-%m-%d')
                    elif group_by == 'month':
                        key = del_dt.strftime('%Y-%m')
                    elif group_by == 'year':
                        key = del_dt.strftime('%Y')
                    else:
                        key = del_dt.strftime('%Y-%m')
                    
                    if key in deletion_counts:
                        deletion_counts[key] += 1
                except Exception:
                    pass
        
        return {
            'labels': labels,
            'additions': [addition_counts.get(label, 0) for label in labels],
            'deletions': [deletion_counts.get(label, 0) for label in labels],
            'total_additions': sum(addition_counts.values()),
            'total_deletions': sum(deletion_counts.values())
        }
    finally:
        session.close()


def get_person_distribution(field: str) -> dict:
    from sqlalchemy import func
    
    session = get_session()
    try:
        result = {}
        
        if field == 'disability':
            # 残疾情况分布
            counts = session.query(
                Person.disability,
                func.count(Person.id).label('count')
            ).group_by(Person.disability).all()
            
            for disability, count in counts:
                label = disability if disability else '无'
                result[label] = count
        
        elif field == 'dibao':
            # 低保情况分布
            counts = session.query(
                Person.dibao,
                func.count(Person.id).label('count')
            ).group_by(Person.dibao).all()
            
            for dibao, count in counts:
                label = dibao if dibao else '无'
                result[label] = count
        
        elif field == 'age_group':
            # 年龄段分布
            persons = session.query(Person.age).all()
            
            age_groups = {
                '0-17岁': 0,
                '18-35岁': 0,
                '36-50岁': 0,
                '51-65岁': 0,
                '66-80岁': 0,
                '80岁以上': 0
            }
            
            for p in persons:
                try:
                    age = int(p.age) if p.age else 0
                    if age <= 17:
                        age_groups['0-17岁'] += 1
                    elif age <= 35:
                        age_groups['18-35岁'] += 1
                    elif age <= 50:
                        age_groups['36-50岁'] += 1
                    elif age <= 65:
                        age_groups['51-65岁'] += 1
                    elif age <= 80:
                        age_groups['66-80岁'] += 1
                    else:
                        age_groups['80岁以上'] += 1
                except Exception:
                    age_groups['0-17岁'] += 1
            
            result = age_groups
        
        elif field == 'gender':
            # 性别分布（从身份证号推断）
            persons = session.query(Person.id_card).all()
            
            male = 0
            female = 0
            unknown = 0
            
            for p in persons:
                if p.id_card and len(p.id_card) >= 2:
                    try:
                        # 身份证倒数第二位：奇数为男，偶数为女
                        gender_digit = int(p.id_card[-2])
                        if gender_digit % 2 == 1:
                            male += 1
                        else:
                            female += 1
                    except Exception:
                        unknown += 1
                else:
                    unknown += 1
            
            result = {
                '男性': male,
                '女性': female
            }
            if unknown > 0:
                result['未知'] = unknown
        
        else:
            # 通用字段统计
            if hasattr(Person, field):
                counts = session.query(
                    getattr(Person, field),
                    func.count(Person.id).label('count')
                ).group_by(getattr(Person, field)).all()
                
                for value, count in counts:
                    label = value if value else '无'
                    result[label] = count
        
        return result
    finally:
        session.close()


def get_person_comparison(dimensions: list) -> dict:
    from sqlalchemy import func
    
    session = get_session()
    try:
        total = session.query(func.count(Person.id)).scalar() or 1
        
        result = {
            'dimensions': [],
            'values': [],
            'raw_values': [],
            'total': total
        }
        
        for dim in dimensions:
            count = 0
            
            if dim == 'age':
                # 平均年龄
                persons = session.query(Person.age).all()
                ages = []
                for p in persons:
                    try:
                        if p.age:
                            ages.append(int(p.age))
                    except Exception:
                        pass
                
                if ages:
                    avg_age = sum(ages) / len(ages)
                    # 归一化：假设最大年龄100
                    normalized = min(100, (avg_age / 100) * 100)
                    count = avg_age
                else:
                    normalized = 0
                    count = 0
                
                result['dimensions'].append('平均年龄')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(round(count, 1))
            
            elif dim == 'disability':
                # 残疾人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.disability != '',
                    Person.disability != '无'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('残疾人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'dibao':
                # 低保人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.dibao != '',
                    Person.dibao != '无'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('低保人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'migration':
                # 迁出人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.is_migrated == '是'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('迁出人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'death':
                # 去世人员比例
                count = session.query(func.count(Person.id)).filter(
                    Person.is_dead == '是'
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('去世人员')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'student':
                # 在读学生比例
                count = session.query(func.count(StudentEducation.id)).filter(
                    StudentEducation.student_status.in_(['在读', '跳级', '留级'])
                ).scalar() or 0
                normalized = (count / total) * 100
                
                result['dimensions'].append('在读学生')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(count)
            
            elif dim == 'gender_male':
                # 男性比例
                persons = session.query(Person.id_card).all()
                male = 0
                for p in persons:
                    if p.id_card and len(p.id_card) >= 2:
                        try:
                            gender_digit = int(p.id_card[-2])
                            if gender_digit % 2 == 1:
                                male += 1
                        except Exception:
                            pass
                normalized = (male / total) * 100
                
                result['dimensions'].append('男性比例')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(male)
            
            elif dim == 'gender_female':
                # 女性比例
                persons = session.query(Person.id_card).all()
                female = 0
                for p in persons:
                    if p.id_card and len(p.id_card) >= 2:
                        try:
                            gender_digit = int(p.id_card[-2])
                            if gender_digit % 2 == 0:
                                female += 1
                        except Exception:
                            pass
                normalized = (female / total) * 100
                
                result['dimensions'].append('女性比例')
                result['values'].append(round(normalized, 2))
                result['raw_values'].append(female)
            
            else:
                # 默认统计非空值
                if hasattr(Person, dim):
                    count = session.query(func.count(Person.id)).filter(
                        getattr(Person, dim) != '',
                        getattr(Person, dim) != '无'
                    ).scalar() or 0
                    normalized = (count / total) * 100
                    
                    result['dimensions'].append(dim)
                    result['values'].append(round(normalized, 2))
                    result['raw_values'].append(count)
        
        return result
    finally:
        session.close()


# ==================== Custom Report Management Functions ====================

def create_custom_report(user_id: str, title: str, report_type: str, 
                         dimensions: list = None, date_range: dict = None,
                         chart_type: str = "bar", filters: dict = None) -> dict:
    from datetime import datetime
    import json
    import secrets
    
    session = get_session()
    try:
        report = CustomReport(
            id=f"report_{secrets.token_hex(8)}",
            title=title,
            user_id=user_id,
            report_type=report_type,
            dimensions=json.dumps(dimensions or [], ensure_ascii=False),
            date_range=json.dumps(date_range or {}, ensure_ascii=False),
            chart_type=chart_type,
            filters=json.dumps(filters or {}, ensure_ascii=False),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=""
        )
        session.add(report)
        session.commit()
        
        return {
            "id": report.id,
            "title": report.title,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "dimensions": json.loads(report.dimensions),
            "date_range": json.loads(report.date_range),
            "chart_type": report.chart_type,
            "filters": json.loads(report.filters),
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_custom_reports(user_id: str = None, report_type: str = None, limit: int = 50) -> list:
    import json
    
    session = get_session()
    try:
        query = session.query(CustomReport)
        
        if user_id:
            query = query.filter(CustomReport.user_id == user_id)
        
        if report_type:
            query = query.filter(CustomReport.report_type == report_type)
        
        reports = query.order_by(CustomReport.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "title": r.title,
                "user_id": r.user_id,
                "report_type": r.report_type,
                "dimensions": json.loads(r.dimensions) if r.dimensions else [],
                "date_range": json.loads(r.date_range) if r.date_range else {},
                "chart_type": r.chart_type,
                "filters": json.loads(r.filters) if r.filters else {},
                "created_at": r.created_at,
                "updated_at": r.updated_at
            }
            for r in reports
        ]
    finally:
        session.close()


def get_custom_report(report_id: str) -> dict | None:
    import json
    
    session = get_session()
    try:
        report = session.query(CustomReport).filter(CustomReport.id == report_id).first()
        if not report:
            return None
        
        return {
            "id": report.id,
            "title": report.title,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "dimensions": json.loads(report.dimensions) if report.dimensions else [],
            "date_range": json.loads(report.date_range) if report.date_range else {},
            "chart_type": report.chart_type,
            "filters": json.loads(report.filters) if report.filters else {},
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    finally:
        session.close()


def update_custom_report(report_id: str, **kwargs) -> dict | None:
    from datetime import datetime
    import json
    
    session = get_session()
    try:
        report = session.query(CustomReport).filter(CustomReport.id == report_id).first()
        if not report:
            return None
        
        # 处理 JSON 字段
        if 'dimensions' in kwargs and isinstance(kwargs['dimensions'], list):
            kwargs['dimensions'] = json.dumps(kwargs['dimensions'], ensure_ascii=False)
        if 'date_range' in kwargs and isinstance(kwargs['date_range'], dict):
            kwargs['date_range'] = json.dumps(kwargs['date_range'], ensure_ascii=False)
        if 'filters' in kwargs and isinstance(kwargs['filters'], dict):
            kwargs['filters'] = json.dumps(kwargs['filters'], ensure_ascii=False)
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        
        report.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        
        return {
            "id": report.id,
            "title": report.title,
            "user_id": report.user_id,
            "report_type": report.report_type,
            "dimensions": json.loads(report.dimensions) if report.dimensions else [],
            "date_range": json.loads(report.date_range) if report.date_range else {},
            "chart_type": report.chart_type,
            "filters": json.loads(report.filters) if report.filters else {},
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_custom_report(report_id: str) -> bool:
    session = get_session()
    try:
        report = session.query(CustomReport).filter(CustomReport.id == report_id).first()
        if report:
            session.delete(report)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def generate_report_data(report_type: str, dimensions: list, 
                         date_range: dict = None, filters: dict = None) -> dict:
    import json
    
    start_date = date_range.get('start', '') if date_range else ''
    end_date = date_range.get('end', '') if date_range else ''
    
    result = {
        'report_type': report_type,
        'dimensions': dimensions,
        'date_range': date_range or {},
        'filters': filters or {},
        'labels': [],
        'values': [],
        'summary': {},
        'total': 0
    }
    
    if report_type == 'person':
        # 人员统计报表
        for dim in dimensions:
            if dim == 'age_group':
                data = get_person_distribution('age_group')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'gender':
                data = get_person_distribution('gender')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'disability':
                data = get_person_distribution('disability')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'dibao':
                data = get_person_distribution('dibao')
                result['labels'] = list(data.keys())
                result['values'] = list(data.values())
                result['summary'][dim] = data
            elif dim == 'trend':
                group_by = filters.get('group_by', 'month') if filters else 'month'
                data = get_person_trend_data(start_date, end_date, group_by)
                result['labels'] = data.get('labels', [])
                result['values'] = [
                    data.get('additions', []),
                    data.get('deletions', [])
                ]
                result['summary'][dim] = data
            elif dim == 'comparison':
                data = get_person_comparison(dimensions)
                result['labels'] = data.get('dimensions', [])
                result['values'] = data.get('values', [])
                result['summary'][dim] = data
        
        # 获取总数
        result['total'] = get_person_count()
    
    elif report_type == 'student':
        # 学生统计报表
        session = get_session()
        try:
            from sqlalchemy import func
            
            # 应用筛选条件
            query = session.query(StudentEducation)
            if filters:
                if filters.get('school'):
                    query = query.filter(StudentEducation.school_name == filters['school'])
                if filters.get('grade'):
                    query = query.filter(StudentEducation.grade == filters['grade'])
                if filters.get('is_left_behind'):
                    query = query.filter(StudentEducation.is_left_behind == filters['is_left_behind'])
            
            students = query.filter(
                StudentEducation.student_status.in_(['在读', '跳级', '留级'])
            ).all()
            
            result['total'] = len(students)
            
            for dim in dimensions:
                if dim == 'grade':
                    # 年级分布
                    grade_counts = {}
                    for s in students:
                        grade = s.grade or '未知'
                        grade_counts[grade] = grade_counts.get(grade, 0) + 1
                    result['labels'] = list(grade_counts.keys())
                    result['values'] = list(grade_counts.values())
                    result['summary'][dim] = grade_counts
                
                elif dim == 'school':
                    # 学校分布
                    school_counts = {}
                    for s in students:
                        school = s.school_name or '未知'
                        school_counts[school] = school_counts.get(school, 0) + 1
                    result['labels'] = list(school_counts.keys())
                    result['values'] = list(school_counts.values())
                    result['summary'][dim] = school_counts
                
                elif dim == 'left_behind':
                    # 留守儿童分布
                    lb_counts = {'留守儿童': 0, '非留守儿童': 0}
                    for s in students:
                        if s.is_left_behind == '是':
                            lb_counts['留守儿童'] += 1
                        else:
                            lb_counts['非留守儿童'] += 1
                    result['labels'] = list(lb_counts.keys())
                    result['values'] = list(lb_counts.values())
                    result['summary'][dim] = lb_counts
        
        finally:
            session.close()
    
    elif report_type == 'subsidy':
        # 补贴统计报表
        session = get_session()
        try:
            from sqlalchemy import func
            
            query = session.query(LandSubsidy)
            
            # 应用日期筛选
            if start_date:
                query = query.filter(LandSubsidy.year >= start_date[:4])
            if end_date:
                query = query.filter(LandSubsidy.year <= end_date[:4])
            
            subsidies = query.all()
            result['total'] = len(subsidies)
            
            for dim in dimensions:
                if dim == 'year':
                    # 年度分布
                    year_counts = {}
                    year_amounts = {}
                    for s in subsidies:
                        year = s.subsidy_year or '未知'
                        year_counts[year] = year_counts.get(year, 0) + 1
                        amount = float(s.total_amount) if s.total_amount else 0
                        year_amounts[year] = year_amounts.get(year, 0) + amount
                    result['labels'] = list(year_counts.keys())
                    result['values'] = list(year_amounts.values())
                    result['summary'][dim] = {
                        'counts': year_counts,
                        'amounts': year_amounts
                    }
                
                elif dim == 'amount_distribution':
                    # 金额分布
                    amount_ranges = {
                        '0-500': 0,
                        '500-1000': 0,
                        '1000-2000': 0,
                        '2000以上': 0
                    }
                    for s in subsidies:
                        try:
                            amount = float(s.total_amount) if s.total_amount else 0
                            if amount < 500:
                                amount_ranges['0-500'] += 1
                            elif amount < 1000:
                                amount_ranges['500-1000'] += 1
                            elif amount < 2000:
                                amount_ranges['1000-2000'] += 1
                            else:
                                amount_ranges['2000以上'] += 1
                        except Exception:
                            pass
                    result['labels'] = list(amount_ranges.keys())
                    result['values'] = list(amount_ranges.values())
                    result['summary'][dim] = amount_ranges
        
        finally:
            session.close()
    
    return result

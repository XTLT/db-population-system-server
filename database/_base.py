"""database 包基础：Base、服务名、密码加解密、引擎/session、初始化与迁移。"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import DB_PATH
import os
import hashlib
import secrets
import logging

SERVICE_NAME = "population-query-system"
logger = logging.getLogger('population_system')

Base = declarative_base()

_db_password = None
_engine = None
_SessionFactory = None

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


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    return _engine


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
    # 确保所有模型类已注册到 Base.metadata 后再建表
    from . import models  # noqa: F401
    engine = get_engine()
    # 多进程并发启动（gunicorn 多 worker）时串行化建表/迁移，避免建表竞态
    lock_path = os.path.join(os.path.dirname(os.path.abspath(DB_PATH)), '.init_db.lock')
    try:
        import fcntl
        with open(lock_path, 'w') as _lock_file:
            fcntl.flock(_lock_file, fcntl.LOCK_EX)
            Base.metadata.create_all(engine)
            _migrate_db(engine)
    except ImportError:
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
            conn.execute(text("ALTER TABLE persons ADD COLUMN tekun VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN tekun_type VARCHAR DEFAULT ''"))
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
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN local_welfare_forest_area VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN local_welfare_forest_change_reason VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN local_welfare_forest_change_time VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN national_welfare_forest_area VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN national_welfare_forest_change_reason VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN national_welfare_forest_change_time VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN commercial_forest_area VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN commercial_forest_change_reason VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN commercial_forest_change_time VARCHAR DEFAULT ''"))
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
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN phone VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN bank_name VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN land_time VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN bank_account VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE land_subsidy ADD COLUMN rape_standard VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN social_card2_source VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE persons ADD COLUMN social_card3_source VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN gender VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN family_members VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN family_count VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN base_amount VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN special_amount VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN adjust_amount VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN special_situation VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN special_subsidy VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN start_time VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE dibao_payment ADD COLUMN issue_month VARCHAR DEFAULT ''"))
            conn.commit()
        except Exception:
            pass


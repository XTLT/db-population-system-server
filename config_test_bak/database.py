"""
数据库配置模块
支持 SQLite 和 PostgreSQL 的无缝切换
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional
import os

from .settings import get_config

Base = declarative_base()

_engine = None
_SessionFactory = None


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, db_type: Optional[str] = None):
        """
        初始化数据库配置
        
        Args:
            db_type: 数据库类型 ('sqlite' 或 'postgresql')
                    如果为 None，则从配置文件读取
        """
        if db_type is None:
            db_type = get_config('database.type', 'sqlite')
        
        self.db_type = db_type
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """创建数据库引擎"""
        if self.db_type == 'sqlite':
            return self._create_sqlite_engine()
        elif self.db_type == 'postgresql':
            return self._create_postgresql_engine()
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")
    
    def _create_sqlite_engine(self):
        """创建 SQLite 引擎"""
        db_path = get_config('database.sqlite.path', 'data/population.db')
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # SQLite 优化配置
        @event.listens_for(engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.close()
        
        return engine
    
    def _create_postgresql_engine(self):
        """创建 PostgreSQL 引擎"""
        host = get_config('database.postgresql.host', 'localhost')
        port = get_config('database.postgresql.port', 5432)
        database = get_config('database.postgresql.database', 'population')
        user = get_config('database.postgresql.user', 'postgres')
        password = get_config('database.postgresql.password', '')
        pool_size = get_config('database.postgresql.pool_size', 10)
        max_overflow = get_config('database.postgresql.max_overflow', 20)
        
        connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        
        engine = create_engine(
            connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # 自动检测连接是否有效
            echo=False
        )
        
        return engine
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        SessionLocal = sessionmaker(bind=self.engine)
        return SessionLocal()
    
    def init_db(self):
        """初始化数据库（创建所有表）"""
        Base.metadata.create_all(self.engine)
    
    def drop_all(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(self.engine)


def get_engine():
    """获取全局数据库引擎"""
    global _engine
    if _engine is None:
        db_config = DatabaseConfig()
        _engine = db_config.engine
    return _engine


def get_session() -> Session:
    """获取数据库会话"""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


def init_db():
    """初始化数据库"""
    engine = get_engine()
    Base.metadata.create_all(engine)


def reset_engine():
    """重置数据库引擎（切换数据库后使用）"""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None

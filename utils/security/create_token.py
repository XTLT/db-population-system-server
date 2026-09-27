import secrets
import json
from datetime import datetime, timedelta
from flask import request
from ._base import MAX_CONCURRENT_SESSIONS, logger
from ._hash_token import _hash_token


def create_token(user_data: dict, expiry_hours: int = 24) -> str:
    """创建 Token 并存储到数据库（存储哈希值而非明文）"""
    from database import get_session, Token

    token = secrets.token_hex(32)
    token_hash = _hash_token(token)  # 存储 token 的哈希值
    user_id = user_data.get('id')
    ip = request.remote_addr if request else 'unknown'
    expires_at = datetime.now() + timedelta(hours=expiry_hours)

    session = get_session()
    try:
        # 删除该用户的旧 token（超过最大并发数）
        existing_tokens = session.query(Token).filter(
            Token.user_id == user_id
        ).order_by(Token.created_at.desc()).all()

        if len(existing_tokens) >= MAX_CONCURRENT_SESSIONS:
            for old_token in existing_tokens[MAX_CONCURRENT_SESSIONS - 1:]:
                session.delete(old_token)

        # 创建新 token（存储哈希值）
        new_token = Token(
            token=token_hash,  # 存储哈希值
            user_id=user_id,
            user_data=json.dumps(user_data, ensure_ascii=False),
            expires_at=expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ip=ip
        )
        session.add(new_token)
        session.commit()

        logger.info(f"用户 {user_id} 创建新Token")
    except Exception as e:
        session.rollback()
        logger.error(f"创建Token失败: {e}")
        raise
    finally:
        session.close()

    return token  # 返回原始 token 给客户端

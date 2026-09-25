# 配置模块初始化
from .settings import config, get_config
from .domains import domain_manager, get_available_domain

__all__ = ['config', 'get_config', 'domain_manager', 'get_available_domain']

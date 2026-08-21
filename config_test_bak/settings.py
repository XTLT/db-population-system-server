"""
统一配置管理模块
支持从 YAML 文件读取配置，支持动态修改域名
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    _config_file: Path = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if not self._config:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 查找配置文件
        config_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("../config.yaml"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                self._config_file = config_path
                break
        else:
            raise FileNotFoundError("未找到配置文件 config.yaml")
        
        # 读取配置
        with open(self._config_file, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # 替换环境变量
        self._replace_env_vars(self._config)
    
    def _replace_env_vars(self, config: Dict):
        """递归替换环境变量"""
        for key, value in config.items():
            if isinstance(value, dict):
                self._replace_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var, "")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的多层键）
        
        示例:
            config.get('app.name')
            config.get('database.postgresql.host')
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_api_url(self) -> str:
        """获取 API 域名"""
        return self.get('domains.api.url', 'http://localhost:5000')
    
    def get_backup_urls(self) -> list:
        """获取备用域名列表"""
        return self.get('domains.backup_urls', [])
    
    def update_domain(self, domain_type: str, new_url: str):
        """
        更新域名配置
        
        Args:
            domain_type: 域名类型（api, files, web）
            new_url: 新的域名 URL
        """
        if domain_type not in ['api', 'files', 'web']:
            raise ValueError(f"不支持的域名类型: {domain_type}")
        
        if 'domains' not in self._config:
            self._config['domains'] = {}
        if domain_type not in self._config['domains']:
            self._config['domains'][domain_type] = {}
        
        self._config['domains'][domain_type]['url'] = new_url
        self._save_config()
    
    def add_backup_url(self, url: str):
        """添加备用域名"""
        if 'domains' not in self._config:
            self._config['domains'] = {}
        if 'backup_urls' not in self._config['domains']:
            self._config['domains']['backup_urls'] = []
        
        if url not in self._config['domains']['backup_urls']:
            self._config['domains']['backup_urls'].append(url)
            self._save_config()
    
    def _save_config(self):
        """保存配置到文件"""
        with open(self._config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
    
    @property
    def debug(self) -> bool:
        """是否调试模式"""
        return self.get('app.debug', False)
    
    @property
    def app_name(self) -> str:
        """应用名称"""
        return self.get('app.name', '人口信息查询系统')
    
    @property
    def version(self) -> str:
        """应用版本"""
        return self.get('app.version', '1.0.0')


# 全局配置实例
config = Config()


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config.get(key, default)


def get_api_url() -> str:
    """获取 API 域名"""
    return config.get_api_url()


def update_domain(domain_type: str, new_url: str):
    """更新域名"""
    config.update_domain(domain_type, new_url)

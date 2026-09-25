"""
域名管理模块
支持域名健康检查、自动切换、动态更新
"""
import requests
from typing import List, Tuple
from datetime import datetime
import time

from .settings import get_config, update_domain


class DomainManager:
    """域名管理器"""
    
    def __init__(self):
        self.current_domain = None
        self.domain_status = {}  # 域名状态缓存
        self.check_interval = 300  # 检查间隔（秒）
        self.last_check_time = None
    
    def get_available_domain(self) -> str:
        """
        获取可用的域名
        
        优先级：
        1. 当前域名（如果可用）
        2. 主域名
        3. 备用域名
        """
        # 检查当前域名
        if self.current_domain and self._is_domain_available(self.current_domain):
            return self.current_domain
        
        # 检查主域名
        main_domain = get_config('domains.api.url')
        if self._is_domain_available(main_domain):
            self.current_domain = main_domain
            return main_domain
        
        # 检查备用域名
        backup_urls = get_config('domains.backup_urls', [])
        for url in backup_urls:
            if self._is_domain_available(url):
                self.current_domain = url
                print(f"⚠️ 主域名不可用，切换到备用域名: {url}")
                return url
        
        raise Exception("所有域名均不可用")
    
    def _is_domain_available(self, url: str, timeout: int = 5) -> bool:
        """
        检查域名是否可用
        
        Args:
            url: 域名 URL
            timeout: 超时时间（秒）
        
        Returns:
            bool: 域名是否可用
        """
        try:
            # 检查缓存
            if url in self.domain_status:
                cached_status, cached_time = self.domain_status[url]
                # 缓存 5 分钟
                if time.time() - cached_time < 300:
                    return cached_status
            
            # 发送健康检查请求
            health_url = f"{url.rstrip('/')}/api/health"
            response = requests.get(
                health_url,
                timeout=timeout,
                verify=False  # 忽略 SSL 证书验证（测试环境）
            )
            
            is_available = response.status_code == 200
            
            # 缓存结果
            self.domain_status[url] = (is_available, time.time())
            
            return is_available
            
        except Exception as e:
            print(f"域名检查失败 {url}: {e}")
            self.domain_status[url] = (False, time.time())
            return False
    
    def check_all_domains(self) -> List[Tuple[str, bool, float]]:
        """
        检查所有域名状态
        
        Returns:
            List[Tuple[str, bool, float]]: [(域名, 是否可用, 响应时间), ...]
        """
        results = []
        
        # 检查主域名
        main_domain = get_config('domains.api.url')
        status, response_time = self._check_domain_with_time(main_domain)
        results.append((main_domain, status, response_time))
        
        # 检查备用域名
        backup_urls = get_config('domains.backup_urls', [])
        for url in backup_urls:
            status, response_time = self._check_domain_with_time(url)
            results.append((url, status, response_time))
        
        return results
    
    def _check_domain_with_time(self, url: str) -> Tuple[bool, float]:
        """检查域名并返回响应时间"""
        try:
            start_time = time.time()
            is_available = self._is_domain_available(url)
            response_time = (time.time() - start_time) * 1000  # 毫秒
            return is_available, response_time
        except Exception:
            return False, 0
    
    def add_backup_domain(self, url: str):
        """添加备用域名"""
        update_domain('backup_urls', url)
        print(f"✓ 已添加备用域名: {url}")
    
    def get_domain_status_report(self) -> str:
        """生成域名状态报告"""
        results = self.check_all_domains()
        
        report = ["域名状态报告", "=" * 40]
        for url, status, response_time in results:
            status_str = "✓ 可用" if status else "✗ 不可用"
            time_str = f"{response_time:.0f}ms" if response_time > 0 else "超时"
            report.append(f"{url}: {status_str} ({time_str})")
        
        return "\n".join(report)


# 全局域名管理器
domain_manager = DomainManager()


def get_available_domain() -> str:
    """获取可用域名"""
    return domain_manager.get_available_domain()


def check_domain_health(url: str) -> bool:
    """检查域名健康状态"""
    return domain_manager._is_domain_available(url)

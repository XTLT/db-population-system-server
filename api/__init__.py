# API 模块
from .auth import bp as auth_bp
from .users import bp as users_bp
from .persons import bp as persons_bp
from .students import bp as students_bp
from .photos import bp as photos_bp
from .statistics import bp as statistics_bp
from .import_export import bp as import_export_bp
from .backup import bp as backup_bp
from .logs import bp as logs_bp
from .notifications import bp as notifications_bp
from .reports import bp as reports_bp
from .land_subsidy import bp as land_subsidy_bp
from .treatment_payment import bp as treatment_payment_bp

__all__ = [
    'auth_bp',
    'users_bp', 
    'persons_bp',
    'students_bp',
    'photos_bp',
    'statistics_bp',
    'import_export_bp',
    'backup_bp',
    'logs_bp',
    'notifications_bp',
    'reports_bp',
    'land_subsidy_bp',
    'treatment_payment_bp'
]

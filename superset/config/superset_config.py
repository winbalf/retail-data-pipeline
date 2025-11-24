"""
Superset configuration for Retail Analytics Data Pipeline
"""
import os

# Database connection string for Superset metadata
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
# Use SUPERSET_DB_USER if set, otherwise fall back to POSTGRES_USER or default
SUPERSET_DB_USER = os.getenv("SUPERSET_DB_USER") or os.getenv("POSTGRES_USER", "superset_user")
SUPERSET_DB_PASSWORD = os.getenv("SUPERSET_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "superset_password_123")

# Superset metadata database (uses separate database)
# Use postgresql+psycopg2:// to explicitly use psycopg2 driver
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{SUPERSET_DB_USER}:{SUPERSET_DB_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/superset"
)

# Secret key for session management
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "your-super-secret-key-change-in-production-12345")

# Session configuration to handle stale sessions
# This helps prevent issues with invalid user sessions
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_SAMESITE = "Lax"
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ENABLE_TEMPLATE_REMOVE_FILTERS": True,
}

# Row limit for queries
ROW_LIMIT = 50000

# Timeout for queries (in seconds)
SQLLAB_TIMEOUT = 300

# Enable CORS if needed
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": ["*"],
}

# Cache configuration (optional - can use Redis in production)
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# Enable scheduled queries
ENABLE_SCHEDULED_QUERIES = True

# Enable SQL Lab
ENABLE_SQL_LAB = True

# Enable dashboard export
ENABLE_DASHBOARD_EXPORT = True

# Enable dashboard import
ENABLE_DASHBOARD_IMPORT = True

# Custom app initialization hook to patch user loader
# This is called by Superset after the app is created
def init_app(app):
    """
    Custom initialization to fix user loading issues.
    Patches Flask-AppBuilder's user loader to handle None users gracefully.
    """
    from flask_login import LoginManager
    from flask_appbuilder.security.sqla.models import User
    from superset import db
    
    # Get the original user loader
    original_user_loader = None
    if hasattr(app, 'login_manager') and app.login_manager._user_callback:
        original_user_loader = app.login_manager._user_callback
    
    def safe_user_loader(user_id):
        """
        Safe user loader that handles None users and missing users gracefully.
        This prevents AttributeError: 'NoneType' object has no attribute 'is_active'
        """
        try:
            if user_id is None:
                return None
            
            # Try to load the user using the original loader if available
            if original_user_loader:
                try:
                    user = original_user_loader(user_id)
                    if user is None or not hasattr(user, 'is_active') or not user.is_active:
                        return None
                    return user
                except Exception:
                    pass
            
            # Fallback: query directly
            try:
                user = db.session.query(User).filter_by(id=user_id).first()
                if user and hasattr(user, 'is_active') and user.is_active:
                    return user
            except Exception:
                pass
            
            return None
        except Exception:
            # If there's any error, return None to clear the session
            return None
    
    # Replace the user loader
    app.login_manager.user_loader(safe_user_loader)
    
    # Also patch Flask-AppBuilder's security manager user loader if available
    if hasattr(app, 'appbuilder') and hasattr(app.appbuilder, 'sm'):
        original_fab_user_loader = app.appbuilder.sm.load_user
        
        def safe_fab_user_loader(user_id):
            """Safe FAB user loader"""
            try:
                if user_id is None:
                    return None
                user = original_fab_user_loader(user_id)
                if user is None or not hasattr(user, 'is_active') or not user.is_active:
                    return None
                return user
            except (AttributeError, Exception):
                return None
        
        app.appbuilder.sm.load_user = safe_fab_user_loader


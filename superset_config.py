import os

# Configuración de uploads
UPLOAD_FOLDER = "/app/superset_home/uploads/"
CSV_EXTENSIONS = {"csv"}
EXCEL_EXTENSIONS = {"xls", "xlsx"}
ALLOWED_EXTENSIONS = CSV_EXTENSIONS | EXCEL_EXTENSIONS

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Feature flags principales
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "UPLOAD_ENABLED": True,
    "CSV_UPLOAD": True,
    "EXCEL_UPLOAD": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ALERT_REPORTS": False,  # Desactivar para evitar errores
}

# Configuración de base de datos
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# Configuración de CSV upload
CSV_TO_HIVE_UPLOAD_S3_BUCKET = None
CSV_TO_HIVE_UPLOAD_DIRECTORY = UPLOAD_FOLDER

# Configuración de seguridad MUY PERMISIVA para desarrollo local
WTF_CSRF_ENABLED = False
WTF_CSRF_EXEMPT_LIST = []
SECRET_KEY = "supersecretkey"

# Configuración de autenticación más permisiva
AUTH_TYPE = 1  # AUTH_DB
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Admin"

# Configuración CORS permisiva para API
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['*']
}

# Configuración de logging
import logging
logging.basicConfig(level=logging.INFO)

# Configuración adicional para uploads  
UPLOAD_CHUNK_SIZE = 4096
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# Permitir conexiones SQLite (SOLO PARA DESARROLLO)
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Configuración de caché simple
CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
}

# Configuración de sesiones más permisiva
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = None

# Configuración adicional para automatización
SUPERSET_WEBSERVER_TIMEOUT = 300
SUPERSET_WEBSERVER_WORKERS = 1

# Deshabilitar verificaciones que pueden causar problemas
TALISMAN_ENABLED = False
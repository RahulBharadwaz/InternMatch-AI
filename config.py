import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database Configuration (supports SQLite by default for zero-friction setup, or MySQL)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'internmatch_db')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite').lower()
    
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    elif DB_ENGINE == 'mysql':
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    else:
        _instance_dir = os.path.join(BASE_DIR, 'instance')
        os.makedirs(_instance_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(_instance_dir, "internmatch.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@internmatch.local')
    
    # Application & Recommendation
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@internmatch.local')
    RECOMMENDATION_ALGORITHM_VERSION = os.environ.get('RECOMMENDATION_ALGORITHM_VERSION', '2.0-hybrid-sbert')
    
    # SBERT Model Configuration
    SBERT_MODEL_NAME = os.environ.get('SBERT_MODEL_NAME', 'all-MiniLM-L6-v2')
    
    # Configurable Recommendation Weights (sum = 1.0)
    RECOMMENDATION_WEIGHTS = {
        'skills_match': float(os.environ.get('WEIGHT_SKILLS', 0.30)),
        'semantic_similarity': float(os.environ.get('WEIGHT_SEMANTIC', 0.25)),
        'text_similarity': float(os.environ.get('WEIGHT_TEXT_TFIDF', 0.15)),
        'education_compatibility': float(os.environ.get('WEIGHT_EDUCATION', 0.15)),
        'preference_match': float(os.environ.get('WEIGHT_PREFERENCE', 0.10)),
        'location_match': float(os.environ.get('WEIGHT_LOCATION', 0.05)),
    }
    
    # Pagination
    OPPORTUNITIES_PER_PAGE = 10
    APPLICATIONS_PER_PAGE = 20
    
    # Items per page
    ITEMS_PER_PAGE = 20

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jemtech-event-hub-secret-key-2023'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'jemtech_event_hub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-secret-key-2023'

    # Upload settings
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@jemtech.com')

    # QR settings
    QR_TOKEN_EXPIRY = timedelta(hours=48)

    # Celery settings
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Analytics settings
    REPORT_FOLDER = os.path.join(basedir, 'reports')

    # App settings
    APP_NAME = "JemTech Event Hub"
    APP_THEME = {
        'primary': '#005EB8',
        'secondary': '#FF8F1C',
        'success': '#28a745',
        'danger': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40'
    }
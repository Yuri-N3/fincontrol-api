import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fincontrol-dev-secret")
    JWT_SECRET = os.environ.get("JWT_SECRET", "fincontrol-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'fincontrol.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION = timedelta(hours=8)

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY               = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI  = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG                    = os.getenv("FLASK_DEBUG", "0") == "1"

    # JWT
    JWT_SECRET_KEY           = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 8))
    )
    JWT_TOKEN_LOCATION       = ["headers"]
    JWT_HEADER_NAME          = "Authorization"
    JWT_HEADER_TYPE          = "Bearer"
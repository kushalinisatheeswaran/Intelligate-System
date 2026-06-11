from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase

# 1. Provide explicit metadata structural hooks for code linters (Pyrefly)
class Base(DeclarativeBase):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# 2. Declare global instances for application context mapping
db = SQLAlchemy(model_class=Base)
migrate = Migrate()  
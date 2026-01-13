from sqlalchemy import Column, Integer, String
from flask_login import UserMixin
# from database import Base
from utils.database_utils import Base
class User(UserMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")

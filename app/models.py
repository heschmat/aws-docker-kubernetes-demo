from datetime import datetime
from config import db
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    tokens = relationship("Token", backref="user")

class Token(db.Model):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

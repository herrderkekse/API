from sqlalchemy import Column, Integer, Numeric, String, DateTime, Boolean
from datetime import datetime, timezone

from .base import Base

class User(Base):
    __tablename__ = "user"
    
    uid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    cash = Column(Numeric(10, 2))
    creation_time = Column(DateTime, default=datetime.now(timezone.utc))
    hashed_password = Column(String(255))
    is_admin = Column(Boolean, default=False)
    key_card_hash = Column(String(255), nullable=True)
    pin_hash = Column(String(255), nullable=True)

    def _tojson(self):
        return {
            "uid": self.uid,
            "name": self.name,
            "cash": float(self.cash),
            "creation_time": self.creation_time,
            "is_admin": self.is_admin,
            "has_keycard": self.key_card_hash is not None and self.pin_hash is not None
        }

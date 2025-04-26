from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone

from .base import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    
    key = Column(String(255), primary_key=True)
    endpoint = Column(String(255), nullable=False)
    response = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
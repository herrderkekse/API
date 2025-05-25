from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime, timezone

from .base import Base

class Device(Base):
    __tablename__ = "device"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    hourly_cost = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("user.uid"), nullable=True)
    end_time = Column(DateTime, nullable=True)

    def _tojson(self):
        time_left = 0
        if self.end_time:
            if self.end_time.tzinfo is None:
                end_time = self.end_time.replace(tzinfo=timezone.utc)
            else:
                end_time = self.end_time
            time_left = max(0, (end_time - datetime.now(timezone.utc)).total_seconds())

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "hourly_cost": self.hourly_cost,
            "user_id": self.user_id,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "time_left": time_left
        }

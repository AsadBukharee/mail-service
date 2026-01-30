from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True)
    sender_email = Column(String)
    receiver_email = Column(String)
    subject = Column(String)
    status = Column(String, default="pending")
    response = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

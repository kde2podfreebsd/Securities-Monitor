from sqlalchemy import Column, Integer, String, DateTime, Float, Date

from src.database import Base


class EndpointsDelay(Base):
    __tablename__ = "endpoints_delay"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    ts = Column(DateTime, nullable=False)
    systime = Column(DateTime, nullable=False)
    market = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    delay = Column(Float, nullable=True)
# app/models/system.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from .base import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(
        String(20), nullable=False, index=True
    )  # DEBUG, INFO, WARNING, ERROR
    logger_name = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Context
    correlation_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(50), nullable=True, index=True)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)

    # Additional data
    extra_data = Column(JSON, nullable=True)
    exception_info = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # OK, WARNING, ERROR

    # Metrics
    response_time_ms = Column(Integer, nullable=True)
    cpu_usage_percent = Column(Integer, nullable=True)
    memory_usage_mb = Column(Integer, nullable=True)

    # Details
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Status
    is_healthy = Column(Boolean, default=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

"""SQLAlchemy ORM 模型 — 可审计日志与业务数据"""
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    actor = Column(String(128), default="system")
    action = Column(String(128), nullable=False, index=True)
    resource = Column(String(256))
    detail = Column(JSON)
    ip_address = Column(String(64))

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "detail": self.detail,
            "ip_address": self.ip_address,
        }


class EventRecord(Base):
    __tablename__ = "event_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(256), nullable=False)
    segment_id = Column(String(64), index=True)
    segment_name = Column(String(128))
    status = Column(String(32), default="pending")
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_name": self.event_name,
            "segment_id": self.segment_id,
            "segment_name": self.segment_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MeetingLog(Base):
    __tablename__ = "meeting_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(String(128), index=True)
    meeting_code = Column(String(64))
    action = Column(String(64), nullable=False)
    participant_id = Column(String(128))
    participant_name = Column(String(256))
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "meeting_code": self.meeting_code,
            "action": self.action,
            "participant_id": self.participant_id,
            "participant_name": self.participant_name,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ScoreRecord(Base):
    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(128), nullable=False, index=True)
    segment_id = Column(String(64))
    total_score = Column(Float, default=0.0)
    task_completion = Column(Float, default=0.0)
    accuracy = Column(Float, default=0.0)
    time_bonus = Column(Float, default=0.0)
    penalty = Column(Float, default=0.0)
    detections = Column(JSON)
    video_path = Column(String(512))
    map_roi_used = Column(String(256))
    reviewed = Column(Boolean, default=False)
    reviewer = Column(String(128))
    review_notes = Column(Text)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "team_name": self.team_name,
            "segment_id": self.segment_id,
            "total_score": self.total_score,
            "task_completion": self.task_completion,
            "accuracy": self.accuracy,
            "time_bonus": self.time_bonus,
            "penalty": self.penalty,
            "detections": self.detections,
            "video_path": self.video_path,
            "map_roi_used": self.map_roi_used,
            "reviewed": self.reviewed,
            "reviewer": self.reviewer,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

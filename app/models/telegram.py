"""Telegram bot models for user registration, polls, and feedback."""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, ARRAY

from app.core.database import Base


class TelegramUser(Base):
    """Stores Telegram user information for bot notifications."""

    __tablename__ = "telegram_users"

    alias = Column(String(255), primary_key=True, index=True)
    chat_id = Column(BigInteger, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Poll(Base):
    """Stores active polls sent to users for feedback collection."""

    __tablename__ = "polls"

    poll_id = Column(String(255), primary_key=True, index=True)
    question = Column(Text, nullable=False)
    options = Column(ARRAY(String), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """Stores user feedback responses to polls."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(String(255), index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

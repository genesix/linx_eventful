from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP, DateTime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_creator = Column(Boolean, default=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    details = Column(String)
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    creator_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE'), nullable=False)
    creator_name = Column(String, index=True)
    available_tickets = Column(Integer)
    creator = relationship('User')
    link = Column(String, nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"

    attendee_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE'), primary_key=True)
    event_id = Column(Integer, ForeignKey(
        "events.id", ondelete='CASCADE'), primary_key=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    reminder_day = Column(TIMESTAMP(timezone=True), nullable=False)
    message = Column(String)
    user_email = Column(String, nullable=False)
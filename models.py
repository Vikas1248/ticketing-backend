from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# =========================
# User Model
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Auth fields
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin / agent / user

    # Relationships
    created_tickets = relationship(
        "Ticket",
        back_populates="user",
        foreign_keys="Ticket.user_id"
    )

    assigned_tickets = relationship(
        "Ticket",
        back_populates="agent",
        foreign_keys="Ticket.assigned_to"
    )

    comments = relationship("Comment", back_populates="user")


# =========================
# Ticket Model
# =========================
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # Temporary (can remove later once fully user-based)
    email = Column(String)

    status = Column(String, default="Open")
    priority = Column(String, default="Medium")
    category = Column(String, default="Other")

    # 👇 KEY RELATIONSHIPS
    user_id = Column(Integer, ForeignKey("users.id"))          # creator
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # agent

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship(
        "User",
        back_populates="created_tickets",
        foreign_keys=[user_id]
    )

    agent = relationship(
        "User",
        back_populates="assigned_tickets",
        foreign_keys=[assigned_to]
    )

    comments = relationship(
        "Comment",
        back_populates="ticket",
        cascade="all, delete"
    )


# =========================
# Comment Model
# =========================
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User", back_populates="comments")

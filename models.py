from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
category = Column(String, default="Other")
priority = Column(String, default="Medium")


result = json.loads(response.choices[0].message.content)

ticket.category = result.get("category", "Other")
ticket.priority = result.get("priority", "Medium")

db.commit()
db.refresh(ticket)

return result


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    email = Column(String)

    status = Column(String, default="Open")
    priority = Column(String, default="Medium")   # ✅ NEW
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # ✅ NEW

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    comments = relationship("Comment", back_populates="ticket", cascade="all, delete")  # ✅ FIXED


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="comments")

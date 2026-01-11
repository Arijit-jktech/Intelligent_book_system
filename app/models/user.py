from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="valid_roles"),
        # Composite index for efficient queries on role-based lookups
        Index('idx_users_role_created', 'role', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(10), default="user", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    books = relationship(
        "Book",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Book.user_id",
        lazy="select"
    )
    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Review.user_id",
        lazy="select"
    )
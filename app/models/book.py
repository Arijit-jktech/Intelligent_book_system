from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("year_published >= 1000 AND year_published <= 2100", name="valid_year"),
        # Composite indexes for efficient filtering and sorting
        Index('idx_books_user_created', 'user_id', 'created_at'),
        Index('idx_books_title_author', 'title', 'author'),
        Index('idx_books_genre_year', 'genre', 'year_published'),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", name="fk_books_user_id"),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), index=True)
    year_published = Column(Integer)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship(
        "User",
        back_populates="books",
        foreign_keys=[user_id],
        lazy="select"
    )
    reviews = relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan",
        foreign_keys="Review.book_id",
        lazy="select"
    )

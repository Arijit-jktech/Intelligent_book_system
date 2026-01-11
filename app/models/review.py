from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="valid_rating"),
        # Composite indexes for efficient queries
        Index('idx_reviews_book_created', 'book_id', 'created_at'),
        Index('idx_reviews_user_created', 'user_id', 'created_at'),
        Index('idx_reviews_book_user', 'book_id', 'user_id'),
        Index('idx_reviews_rating', 'rating'),
    )

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(
        Integer,
        ForeignKey("books.id", ondelete="CASCADE", name="fk_reviews_book_id"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", name="fk_reviews_user_id"),
        nullable=False,
        index=True
    )
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    book = relationship(
        "Book",
        back_populates="reviews",
        foreign_keys=[book_id],
        lazy="select"
    )
    user = relationship(
        "User",
        back_populates="reviews",
        foreign_keys=[user_id],
        lazy="select"
    )

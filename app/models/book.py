from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    genre = Column(String(100))
    year_published = Column(Integer)
    summary = Column(Text)

    user = relationship("User", backref="books")

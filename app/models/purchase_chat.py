from sqlalchemy import Column, BigInteger, Text, VARCHAR

from app.models.base import Base


class PurchaseChat(Base):
    __tablename__ = 'purchases_chat'

    Id = Column('id', VARCHAR(255), unique=True, primary_key=True)
    Answer = Column('answer', Text)
    UserId = Column('user_id', BigInteger)

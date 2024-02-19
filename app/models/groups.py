from sqlalchemy import Column, String, Boolean, BigInteger

from app.models.base import Base


class Group(Base):
    __tablename__ = 'groups'

    Id = Column('id', BigInteger, primary_key=True)
    ChatTitle = Column('chat_title', String)
    status = Column('status', Boolean, default=True)

    def __repr__(self):
        return f"обяз. подписка {self.Id}"

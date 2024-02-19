from sqlalchemy import Column, BigInteger, Integer, Text

from app.models.base import Base


class Messages(Base):
    __tablename__ = 'messages'

    Id = Column('id', BigInteger, primary_key=True)
    user_id = Column('user_id', BigInteger)
    text = Column('text', Text)
    CreatedAt = Column('created_at', Integer)

    def __repr__(self):
        return f"сообщение {self.Id}"

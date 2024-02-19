from sqlalchemy import Column, BigInteger, Integer, String, TEXT

from app.models.base import Base


class Shows(Base):
    __tablename__ = 'shows'

    Id = Column('id', Integer, unique=True, primary_key=True, autoincrement=True)
    Message = Column('text_message', String)
    Count = Column('count', BigInteger, default=0)
    Total = Column('total', BigInteger, default=0)
    Buttons = Column('buttons', TEXT)

    def __repr__(self):
        return f"показ {self.Id}"

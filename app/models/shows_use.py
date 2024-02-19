from sqlalchemy import Column, BigInteger, Integer

from app.models.base import Base


class ShowsUse(Base):
    __tablename__ = 'shows_use'

    Id = Column('id', BigInteger, nullable=False, primary_key=True, autoincrement=True)
    ShowId = Column('show_id', Integer)
    UserId = Column('user_id', BigInteger)


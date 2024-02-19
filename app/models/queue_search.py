from sqlalchemy import Column, BigInteger, Integer, String

from app.models.base import Base


class QueueSearch(Base):
    __tablename__ = 'queue_search'

    Id = Column('id', BigInteger, nullable=False, primary_key=True, autoincrement=True)
    UserId = Column('user_id', BigInteger)
    Gender = Column('gender', Integer, default=0)
    SearchGender = Column('gender_search', Integer, default=0)
    Age = Column('age', Integer, default=0)
    UserName = Column('username', String)
    AgeGender = Column('age_search', Integer, default=0)
    Status = Column('status', Integer, default=0)
    SearchType = Column('search_type', String)

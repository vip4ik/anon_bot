from sqlalchemy import Column, BigInteger, Integer, String

from app.models.base import Base


class ChannelRequest(Base):
    __tablename__ = 'request_channels'

    Id = Column('id', Integer, unique=True, primary_key=True, autoincrement=True)
    ChannelId = Column('channel_id', BigInteger)
    ChannelTitle = Column('channel_title', String)
    CountJoin = Column('count_join', Integer, default=0)
    CountOldUser = Column('count_old_user', Integer, default=0)
    CountError = Column('count_error', Integer, default=0)
    CountNewUser = Column('count_new_user', Integer, default=0)
    CountBlackList = Column('count_black_list', Integer, default=0)

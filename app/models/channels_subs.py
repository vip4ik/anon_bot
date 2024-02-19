import time

from sqlalchemy import Column, BigInteger, Integer, SmallInteger

from app.models.base import Base


class ChannelSubs(Base):
    __tablename__ = 'channels_subs'

    Id = Column('id', BigInteger, primary_key=True, autoincrement=True)
    SubId = Column('sub_id', Integer)
    ChannelId = Column('channel_id', BigInteger)
    Userid = Column('user_id', BigInteger, index=True)
    Status = Column('status', SmallInteger, default=0)
    Created_at = Column('created', Integer, default=int(time.time()))
    Updated_at = Column('updated', Integer, default=int(time.time()))

    def __repr__(self):
        return f"channels_subs: {self.Id}"

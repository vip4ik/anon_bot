from sqlalchemy import Column, BigInteger, Integer, String, Boolean

from app.models.base import Base


class Channel(Base):
    __tablename__ = 'channels'

    Id = Column('id', Integer, unique=True, primary_key=True, autoincrement=True)
    ChannelId = Column('channel_id', BigInteger)
    ChannelTitle = Column('channel_title', String)
    ChannelLink = Column('channel_link', String)
    # Enabled = Column('enabled', Boolean, default=False)
    IsBot = Column('is_bot', Boolean, default=False)
    BotToken = Column('bot_token', String, default=None)

    def __repr__(self):
        return f"обяз. подписка {self.Id}"

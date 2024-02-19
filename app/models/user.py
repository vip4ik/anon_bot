from sqlalchemy import Column, BigInteger, Integer, String, Boolean

from app.models.base import Base


class User(Base):
    __tablename__ = 'users'

    UserId = Column('id', BigInteger, unique=True, primary_key=True)
    LanguageCode = Column('language_code', String(10))
    Subscription = Column('subscription_at', Integer, default=0)
    Gender = Column('gender', Integer, default=0)
    Age = Column('age', Integer, default=0)
    SendCount = Column('send_count', Integer, default=0)
    OpenDialogs = Column('open_dialogs', Integer, default=0)
    TimeChats = Column('time_chats', Integer, default=0)
    Deactivated = Column('deactivated', Boolean, default=False)
    RefLink = Column('ref_link', String, default=None)
    StealerFrom = Column('stealer_from', BigInteger, default=None)
    CreatedAt = Column('created_at', Integer)
    is_banned = Column('is_banned', Boolean, default=False)

    def __repr__(self):
        return f"пользователь {self.UserId}"

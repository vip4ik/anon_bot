from sqlalchemy import Column, Integer, String

from app.models.base import Base


class Mail(Base):
    __tablename__ = 'mails'

    MessageId = Column('message_id', Integer, unique=True, primary_key=True)
    Text = Column('text', String)
    Buttons = Column('buttons', String, default=None)
    FileId = Column('file_id', String, default=None)
    ContentType = Column('content_type', String)

    def __repr__(self):
        return f"рассылка поста {self.PostId}"

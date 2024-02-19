from sqlalchemy import Column, Integer, String

from app.models.base import Base


class Link(Base):
    __tablename__ = 'links'

    Id = Column('id', Integer, unique=True, primary_key=True, autoincrement=True)
    LinkTitle = Column('link_title', String)
    Price = Column('price', Integer, default=0)
    NewJoins = Column('new_joins', Integer, default=0)
    OldJoins = Column('old_joins', Integer, default=0)
    LastJoin = Column('last_join_at', Integer, default=0)
    CreatedAt = Column('created_at', Integer)

    def __repr__(self):
        return f"реф. ссылка {self.LinkTitle}"

from sqlalchemy import Column, BigInteger, Integer

from app.models.base import Base


class Reports(Base):
    __tablename__ = 'reports'

    Id = Column('id', BigInteger, nullable=False, primary_key=True, autoincrement=True)
    suspect_id = Column('suspect_id', BigInteger)
    reported_by = Column('reported_by', BigInteger)
    CreatedAt = Column('created_at', Integer)

    def __repr__(self):
        return f"репорт {self.Id}"

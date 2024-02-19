from sqlalchemy import Column, Integer, BigInteger, Boolean, VARCHAR

from app.models.base import Base


class Purchase(Base):
    __tablename__ = 'purchases'

    Id = Column('id', VARCHAR(255), unique=True, primary_key=True)
    OwnerId = Column('owner_id', BigInteger)
    Sum = Column('sum', Integer)
    Status = Column('status', Boolean, default=False)
    CreatedAt = Column('created_at', Integer)

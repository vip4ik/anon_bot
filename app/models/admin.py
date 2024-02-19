from sqlalchemy import Column, String

from app.models.base import Base


class Admin(Base):
    __tablename__ = 'admins'

    AdminId = Column('admin_id', String, unique=True, primary_key=True)
    FullName = Column('full_name', String)

    def __repr__(self):
        return f"админ {self.AdminId}"

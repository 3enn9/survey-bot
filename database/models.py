from sqlalchemy import String, Text, Float, Integer, DateTime, func, Numeric, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Appeals(Base):
    __tablename__ = 'appeals'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(150), nullable=False)
    user_id: Mapped[str] = mapped_column(String(150), nullable=False)
    district: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)


from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()


class Meets(Base):
    __tablename__ = 'meets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    time: Mapped[str] = mapped_column(String(50), nullable=False)
    place: Mapped[str] = mapped_column(String(150), nullable=False)

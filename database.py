from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, BigInteger

engine = create_async_engine('sqlite+aiosqlite:///trains.db')
async_session = async_sessionmaker(engine, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class Train(Base):
    __tablename__ = 'trains'
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(10))
    route: Mapped[str] = mapped_column(String(100))
    arrival_time: Mapped[str] = mapped_column(String(20))
    departure_time: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50), default="За розкладом")
    duration: Mapped[str] = mapped_column(String(50), default="Невідомо")
    wagon_types: Mapped[str] = mapped_column(String(100), default="Плацкарт, Купе")
    stops: Mapped[str] = mapped_column(String(200), default="Без проміжних зупинок")
    days_of_week: Mapped[str] = mapped_column(String(50), default="Щодня") # НОВЕ ПОЛЕ

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    train_number: Mapped[str] = mapped_column(String(10))

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
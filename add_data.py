import asyncio
from database import async_session, Train, init_db

async def add_fake_trains():
    await init_db()
    async with async_session() as session:
        train1 = Train(number="098", route="Ковель - Київ", arrival_time="10:00", departure_time="10:30", status="За розкладом", duration="11 годин 30 хвилин", wagon_types="Плацкарт, Купе, Люкс", stops="Ківерці, Луцьк, Рівне, Шепетівка", days_of_week="Пн, Ср, Пт")
        train2 = Train(number="131", route="Львів - Луцьк", arrival_time="18:00", departure_time="18:00", status="За розкладом", duration="3 години 20 хвилин", wagon_types="Загальний, Плацкарт", stops="Підзамче, Радехів, Горохів", days_of_week="Вт, Чт, Сб")
        train3 = Train(number="266", route="Луцьк - Ужгород", arrival_time="08:15", departure_time="08:45", status="Запізнюється на 5 хв", duration="10 годин 10 хвилин", wagon_types="Плацкарт, Купе", stops="Львів, Стрий, Мукачево", days_of_week="Ср, Нд")
        train4 = Train(number="107", route="Луцьк - Ківерці", arrival_time="12:40", departure_time="13:00", status="За розкладом", duration="20 хвилин", wagon_types="Приміський (6 вагонів)", stops="Луцьк, Ківерці", days_of_week="Щодня")
        train5 = Train(number="088", route="Луцьк - Одеса", arrival_time="21:00", departure_time="21:30", status="За розкладом", duration="14 годин 20 хвилин", wagon_types="Плацкарт, Купе", stops="Рівне, Тернопіль, Жмеринка", days_of_week="Пт, Сб, Нд")

        session.add_all([train1, train2, train3, train4, train5])
        await session.commit()
        print("Базу оновлено: додано графік курсування по днях тижня!")

if __name__ == "__main__":
    asyncio.run(add_fake_trains())
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database import init_db, async_session, Train, Subscription

ADMIN_ID = 1583126842
bot = Bot(token="8778590068:AAGPkU4tKtJ8bYLpw724eXIBGldGSbU3xtM")
dp = Dispatcher()

class Form(StatesGroup):
    search_query = State()
    track_number = State()
    admin_train_number = State()
    admin_new_status = State()

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    buttons = [[KeyboardButton(text="🚉 Онлайн-табло")], [KeyboardButton(text="🔍 Пошук"), KeyboardButton(text="🔔 Відстежувати")]]
    if message.from_user.id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙️ Адмін-панель")])
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Привіт! Я інформаційна система залізничного вокзалу. Оберіть дію:", reply_markup=keyboard)

@dp.message(StateFilter("*"), F.text == "🔙 Головне меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await start_cmd(message, state)

@dp.message(StateFilter("*"), F.text == "🚉 Онлайн-табло")
async def show_scoreboard(message: types.Message, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        result = await session.execute(select(Train))
        trains = result.scalars().all()
        if not trains:
            await message.answer("📭 Наразі немає інформації про потяги.")
            return
        
        text = "<b>🚉 Онлайн-табло вокзалу:</b>\n\n"
        inline_buttons = []
        for t in trains:
            text += f"🚆 <b>Потяг {t.number}</b> ({t.route})\n   🗓 Курсує: <b>{t.days_of_week}</b>\n   Відправлення: {t.departure_time} | Прибуття: {t.arrival_time}\n   Статус: <i>{t.status}</i>\n\n"
            inline_buttons.append([InlineKeyboardButton(text=f"ℹ️ Деталі {t.number}", callback_data=f"info_{t.number}")])
            
        markup = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
        await message.answer(text, reply_markup=markup, parse_mode="HTML")

@dp.message(StateFilter("*"), F.text == "🔍 Пошук")
async def search_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Введіть назву міста або номер потяга для пошуку:")
    await state.set_state(Form.search_query)

@dp.message(Form.search_query)
async def search_process(message: types.Message, state: FSMContext):
    query = message.text
    async with async_session() as session:
        result = await session.execute(
            select(Train).where(
                Train.route.contains(query) | 
                Train.number.contains(query) | 
                Train.stops.contains(query)
            )
        )
        trains = result.scalars().all()
        if not trains:
            await message.answer("🔍 Нічого не знайдено.")
        else:
            text = "<b>Результати пошуку:</b>\n\n"
            inline_buttons = []
            for t in trains:
                text += f"🚆 <b>{t.number}</b> {t.route}\n   🗓 Курсує: <b>{t.days_of_week}</b>\n   Статус: {t.status}\n\n"
                inline_buttons.append([InlineKeyboardButton(text=f"ℹ️ Деталі {t.number}", callback_data=f"info_{t.number}")])
                
            markup = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
            await message.answer(text, reply_markup=markup, parse_mode="HTML")
    await state.clear()

@dp.message(StateFilter("*"), F.text == "🔔 Відстежувати")
async def track_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Введіть номер потяга, щоб отримувати сповіщення про зміну його статусу:")
    await state.set_state(Form.track_number)

@dp.message(Form.track_number)
async def track_process(message: types.Message, state: FSMContext):
    train_num = message.text
    async with async_session() as session:
        check_res = await session.execute(select(Subscription).where(Subscription.user_id == message.from_user.id, Subscription.train_number == train_num))
        if check_res.scalars().first():
            await message.answer(f"ℹ️ Ви вже підписані на оновлення потяга {train_num}.")
        else:
            sub = Subscription(user_id=message.from_user.id, train_number=train_num)
            session.add(sub)
            await session.commit()
            await message.answer(f"✅ Ви підписалися на оновлення потяга {train_num}. Як тільки статус зміниться, я вам напишу!")
    await state.clear()

@dp.message(StateFilter("*"), F.text == "⚙️ Адмін-панель")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✏️ Змінити статус")], [KeyboardButton(text="🔙 Головне меню")]], resize_keyboard=True)
        await message.answer("🛠 Панель адміністратора:", reply_markup=keyboard)

@dp.message(StateFilter("*"), F.text == "✏️ Змінити статус")
async def admin_edit_start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        await message.answer("Введіть номер потяга:")
        await state.set_state(Form.admin_train_number)

@dp.message(Form.admin_train_number)
async def admin_edit_num(message: types.Message, state: FSMContext):
    await state.update_data(num=message.text)
    await message.answer("Введіть новий статус:")
    await state.set_state(Form.admin_new_status)

@dp.message(Form.admin_new_status)
async def admin_edit_status(message: types.Message, state: FSMContext):
    new_status = message.text
    data = await state.get_data()
    train_num = data['num']
    async with async_session() as session:
        res = await session.execute(select(Train).where(Train.number == train_num))
        train = res.scalars().first()
        if train:
            train.status = new_status
            await session.commit()
            await message.answer(f"✅ Статус оновлено.")
            subs_res = await session.execute(select(Subscription).where(Subscription.train_number == train_num))
            subs = subs_res.scalars().all()
            notified_users = set()
            for s in subs:
                if s.user_id not in notified_users:
                    try:
                        await bot.send_message(s.user_id, f"🔔 <b>Увага!</b> Статус потяга {train_num} змінено на: <b>{new_status}</b>", parse_mode="HTML")
                        notified_users.add(s.user_id)
                    except:
                        pass
        else:
            await message.answer("❌ Потяг не знайдено.")
    await state.clear()
    await admin_panel(message, state)

@dp.callback_query(F.data.startswith("info_"))
async def train_info_callback(callback: types.CallbackQuery):
    train_num = callback.data.split("_")[1]
    async with async_session() as session:
        result = await session.execute(select(Train).where(Train.number == train_num))
        train = result.scalars().first()
        if train:
            text = f"🚆 <b>Деталі маршруту {train.number}</b>\n\n"
            text += f"🛤 <b>Напрямок:</b> {train.route}\n"
            text += f"🗓 <b>Дні курсування:</b> {train.days_of_week}\n"
            text += f"📍 <b>Зупинки:</b> {train.stops}\n"
            text += f"⏱ <b>Час у дорозі:</b> {train.duration}\n"
            text += f"💺 <b>Вагони:</b> {train.wagon_types}\n"
            await callback.message.answer(text, parse_mode="HTML")
            await callback.answer()
        else:
            await callback.answer("⚠️ Цей маршрут більше не актуальний або був видалений з розкладу.", show_alert=True)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
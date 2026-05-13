from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from database.models import AsyncSessionLocal, User

router = Router()

WELCOME_TEXT = """
Привет. Я ИИ-стратег <b>FOCUS MEDIA PRODUCTION</b>.

За 2 минуты покажу:
— где у тебя сейчас утекает <b>50–300к ₽/мес</b> дохода
— почему контент и реклама не приводят платящих клиентов
— что конкретно сделать в ближайшие 30 дней

Без воды и без «у вас большой потенциал». Разбор под твою ситуацию.

<b>Поехали — кто ты?</b>
"""

SEGMENT_KB_TEXTS = {
    "expert": "🧠 Эксперт / Коуч",
    "blogger": "📱 Блогер / Инфлюенсер",
    "business": "💼 Предприниматель",
}


def get_segment_keyboard():
    builder = InlineKeyboardBuilder()
    for key, text in SEGMENT_KB_TEXTS.items():
        builder.button(text=text, callback_data=f"segment_{key}")
    builder.adjust(1)
    return builder.as_markup()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        stmt = sqlite_insert(User).values(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        ).on_conflict_do_nothing(index_elements=["telegram_id"])
        await session.execute(stmt)
        await session.commit()
    
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_segment_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_segment_keyboard(),
        parse_mode="HTML"
    )

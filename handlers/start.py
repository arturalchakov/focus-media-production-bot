from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from database.models import AsyncSessionLocal, User

router = Router()

WELCOME_TEXT = """
🎯 <b>Добро пожаловать в Focus Media Production!</b>

Я — твой персональный AI-стратег по digital-маркетингу и онлайн-запускам.

За несколько минут я:
✅ Проанализирую твою ситуацию
✅ Найду точки роста конкретно для тебя
✅ Дам персональную стратегию

<b>Скажи, кто ты?</b>
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
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            session.add(user)
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

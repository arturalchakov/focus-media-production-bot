from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import update
from database.models import AsyncSessionLocal, User
from services.openai_service import get_ai_diagnosis

router = Router()

class SegmentStates(StatesGroup):
    waiting_niche = State()
    waiting_current_state = State()
    waiting_goal = State()

SEGMENT_NAMES = {"expert": "Эксперт/Коуч", "blogger": "Блогер/Инфлюенсер", "business": "Предприниматель"}

NICHE_Q = {
    "expert": "🧠 Отлично! В какой нише ты работаешь?\n\nНапример: психология, коучинг, нутрициология, фитнес, бизнес-консалтинг...",
    "blogger": "📱 Круто! В какой нише твой контент?\n\nНапример: лайфстайл, бизнес, здоровье, путешествия, образование...",
    "business": "💼 Бизнес — это масштаб! В какой сфере твой бизнес?\n\nНапример: онлайн-образование, услуги, e-commerce, консалтинг..."
}

STATE_Q = {
    "expert": "Есть ли уже продукт или услуга? Как сейчас приходят клиенты? Примерный доход в месяц?",
    "blogger": "Сколько подписчиков? Есть ли уже монетизация? Какие форматы контента используешь?",
    "business": "Какой примерный оборот? Есть онлайн-присутствие? Что уже пробовали в digital-маркетинге?"
}

@router.callback_query(F.data.startswith("segment_"))
async def process_segment(callback: CallbackQuery, state: FSMContext):
    segment = callback.data.replace("segment_", "")
    await state.update_data(segment=segment)
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == callback.from_user.id).values(segment=segment))
        await session.commit()
    await callback.message.edit_reply_markup()
    await callback.message.answer(NICHE_Q[segment], parse_mode="HTML")
    await state.set_state(SegmentStates.waiting_niche)
    await callback.answer()

@router.message(SegmentStates.waiting_niche)
async def process_niche(message: Message, state: FSMContext):
    await state.update_data(niche=message.text)
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(niche=message.text))
        await session.commit()
    await message.answer(f"<b>{STATE_Q[data.get('segment','expert')]}</b>", parse_mode="HTML")
    await state.set_state(SegmentStates.waiting_current_state)

@router.message(SegmentStates.waiting_current_state)
async def process_current_state(message: Message, state: FSMContext):
    await state.update_data(current_state=message.text)
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(current_state=message.text))
        await session.commit()
    await message.answer("🎯 <b>И последний вопрос:</b>\n\nКакая твоя главная цель на ближайшие 3-6 месяцев? Что конкретно хочешь достичь?", parse_mode="HTML")
    await state.set_state(SegmentStates.waiting_goal)

@router.message(SegmentStates.waiting_goal)
async def process_goal(message: Message, state: FSMContext):
    await state.update_data(main_goal=message.text)
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(main_goal=message.text))
        await session.commit()
    thinking = await message.answer("🔄 <i>Анализирую твою ситуацию... Формирую персональную стратегию...</i>", parse_mode="HTML")
    diagnosis = await get_diagnosis(
        segment=SEGMENT_NAMES.get(data.get("segment", "expert")),
        niche=data.get("niche", ""),
        current_state=data.get("current_state", ""),
        main_goal=message.text
    )
    await thinking.delete()
    await message.answer(f"🎯 <b>Твоя персональная диагностика:</b>\n\n{diagnosis}", parse_mode="HTML")
    await state.set_state(None)
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Записаться на стратегическую сессию", callback_data="cta_book")
    builder.button(text="📚 Получить бесплатный материал", callback_data="cta_magnet")
    builder.button(text="💬 Задать вопрос AI-консультанту", callback_data="cta_ask")
    builder.adjust(1)
    await message.answer("\n🚀 <b>Что хочешь сделать дальше?</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import update
from database.models import AsyncSessionLocal, User
from services.openai_service import get_ai_diagnosis, transcribe_voice
from services.followup import schedule_followups

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


async def get_text_from_message(message: Message) -> str:
    """Extract text from message: text or voice transcription."""
    if message.voice:
        file = await message.bot.get_file(message.voice.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        text = await transcribe_voice(file_bytes.read(), "voice.ogg")
        return text
    return message.text or ""


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
    text = await get_text_from_message(message)
    if not text:
        await message.answer("Не удалось распознать голос. Попробуй ещё раз или напиши текстом.")
        return
    await state.update_data(niche=text)
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(niche=text))
        await session.commit()
    await message.answer(f"<b>{STATE_Q[data.get('segment','expert')]}</b>", parse_mode="HTML")
    await state.set_state(SegmentStates.waiting_current_state)

@router.message(SegmentStates.waiting_current_state)
async def process_current_state(message: Message, state: FSMContext):
    text = await get_text_from_message(message)
    if not text:
        await message.answer("Не удалось распознать голос. Попробуй ещё раз или напиши текстом.")
        return
    await state.update_data(current_state=text)
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(current_state=text))
        await session.commit()
    await message.answer("🎯 <b>И последний вопрос:</b>\n\nКакая твоя главная цель на ближайшие 3-6 месяцев? Что конкретно хочешь достичь?", parse_mode="HTML")
    await state.set_state(SegmentStates.waiting_goal)

@router.message(SegmentStates.waiting_goal)
async def process_goal(message: Message, state: FSMContext):
    text = await get_text_from_message(message)
    if not text:
        await message.answer("Не удалось распознать голос. Попробуй ещё раз или напиши текстом.")
        return
    await state.update_data(main_goal=text)
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(main_goal=text))
        await session.commit()
    thinking = await message.answer("🔄 <i>Анализирую твою ситуацию... Формирую персональную стратегию...</i>", parse_mode="HTML")
    diagnosis = await get_ai_diagnosis({
        "segment": data.get("segment", "expert"),
        "answers": [
            data.get("niche", ""),
            data.get("current_state", ""),
            text
        ]
    })
    await thinking.delete()
    # Diagnosis + main CTA button attached directly
    primary = InlineKeyboardBuilder()
    primary.button(text="📞 Записаться на стратсессию — бесплатно", callback_data="cta_book")
    primary.adjust(1)
    await message.answer(
        f"🎯 <b>Твоя персональная диагностика:</b>\n\n{diagnosis}",
        parse_mode="HTML",
        reply_markup=primary.as_markup(),
    )
    await state.set_state(None)
    # Secondary menu
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Скачать PDF-разбор по твоей нише", callback_data="cta_magnet")
    builder.button(text="💬 Задать вопрос AI-консультанту", callback_data="cta_ask")
    builder.adjust(1)
    await message.answer("Или возьми материалы и подумай:", reply_markup=builder.as_markup(), parse_mode="HTML")
    # Arm follow-up sequence (cancelled if user becomes a lead)
    await schedule_followups(message.from_user.id)

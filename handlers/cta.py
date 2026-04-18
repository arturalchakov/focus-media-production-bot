from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update
from database.models import AsyncSessionLocal, User
from config import MANAGER_CHAT_ID

router = Router()

LEAD_MAGNETS = {
    "expert": """📋 <b>5-шаговая формула запуска первого продукта</b>

1️⃣ <b>Распаковка экспертизы</b> — выяви 3 ключевые трансформации, которые ты даёшь клиентам
2️⃣ <b>Формула оффера</b> — "[Кто] + [Цель] + [Срок] + [Без [боли]]"
3️⃣ <b>Валидация</b> — продай 3 клиентам до создания продукта
4️⃣ <b>Минимальный продукт</b> — 4-6 модулей, живые эфиры, без перфекционизма
5️⃣ <b>Запуск</b> — прогрев 21 день + вебинар + окно продаж 5-7 дней

💡 Формула позиционирования: "Я помогаю [кому] достичь [результата] за [срок] с помощью [метода]"

Хочешь разобрать твою ситуацию детальнее? Запишись на стратегическую сессию👇""",

    "blogger": """📱 <b>Матрица монетизации блогера</b>

💰 <b>3 уровня монетизации:</b>

<b>Уровень 1 (от 1000 подписчиков):</b>
• Реклама у блогеров
• Партнёрские программы  
• Продажа чек-листов/гайдов

<b>Уровень 2 (от 5000 подписчиков):</b>
• Мини-курсы (3000-15000₽)
• Закрытый клуб/канал
• Консультации

<b>Уровень 3 (от 20000 подписчиков):</b>
• Флагманский курс (30000-150000₽)
• Менторство/мастермайнд
• Корпоративные тренинги

🎯 Ключевой принцип: аудитория — это актив. Монетизируй через доверие, а не охваты.

Хочешь построить систему монетизации? Запишись на стратсессию👇""",

    "business": """📊 <b>Чек-лист аудита digital-присутствия</b>

✅ <b>Сайт/лендинг</b>
□ Есть ли чёткий оффер на главной?
□ Есть ли социальные доказательства?
□ Работает ли форма захвата?

✅ <b>Трафик</b>
□ Настроена ли сквозная аналитика?
□ Знаете ли стоимость лида по каждому каналу?
□ Есть ли ретаргетинг?

✅ <b>Воронка</b>
□ Есть ли email/telegram рассылка?
□ Какова конверсия лид→продажа?
□ Есть ли upsell/cross-sell?

✅ <b>Контент</b>
□ Есть ли контент-план?
□ Публикуетесь ли регулярно?
□ Есть ли SEO-стратегия?

🔥 Если больше 5 "нет" — у вас серьёзные точки роста.

Запишитесь на аудит вашего маркетинга👇"""
}

class LeadState(StatesGroup):
    waiting_phone = State()

@router.callback_query(F.data == "cta_book")
async def cta_book(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📞 <b>Отлично! Запишем тебя на стратегическую сессию.</b>\n\nКак тебя зовут и как с тобой связаться? (Telegram @username или номер телефона)",
        parse_mode="HTML"
    )
    await state.set_state(LeadState.waiting_phone)
    await callback.answer()

@router.message(LeadState.waiting_phone)
async def process_lead_contact(message: Message, state: FSMContext):
    from aiogram import Bot
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            await session.execute(update(User).where(User.telegram_id == message.from_user.id).values(is_lead=True, lead_at=datetime.utcnow()))
            await session.commit()
    
    await message.answer(
        "✅ <b>Отлично! Твоя заявка принята.</b>\n\nМенеджер Focus Media Production свяжется с тобой в ближайшее время для подтверждения времени сессии.\n\n🎁 Пока жди — задай любой вопрос нашему AI-консультанту командой /ask",
        parse_mode="HTML"
    )
    
    bot = message.bot
    if MANAGER_CHAT_ID:
        segment = data.get("segment", "не указан")
        niche = data.get("niche", "не указана")
        try:
            await bot.send_message(
                MANAGER_CHAT_ID,
                f"🔥 <b>Новый лид!</b>\n\n👤 {message.from_user.full_name} (@{message.from_user.username})\n📞 Контакт: {message.text}\n🏷 Сегмент: {segment}\n💼 Ниша: {niche}\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await state.clear()

@router.callback_query(F.data == "cta_magnet")
async def cta_magnet(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    segment = data.get("segment", "expert")
    magnet = LEAD_MAGNETS.get(segment, LEAD_MAGNETS["expert"])
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Записаться на стратегическую сессию", callback_data="cta_book")
    builder.adjust(1)
    await callback.message.answer(magnet, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "cta_ask")
async def cta_ask(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "💬 <b>AI-консультант готов!</b>\n\nЗадай любой вопрос по маркетингу, запускам, личному бренду или монетизации — отвечу развёрнуто и конкретно.\n\nПросто напиши свой вопрос:",
        parse_mode="HTML"
    )
    await state.set_state("ai_chat")
    await callback.answer()

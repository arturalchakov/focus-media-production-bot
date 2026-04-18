import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.models import AsyncSessionLocal, User, Message as DBMessage
from services.openai_service import get_ai_response

logger = logging.getLogger(__name__)
router = Router()


class AIChatStates(StatesGroup):
    ai_chat = State()


@router.message(F.text & ~F.text.startswith("/"))
async def ai_chat(message: Message, state: FSMContext):
    # Only respond if user has completed segmentation (has a segment)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            user = result.scalar_one_or_none()
            if not user or not user.segment:
                return  # Not started yet, ignore

        # Save message to DB
        async with AsyncSessionLocal() as session:
            db_msg = DBMessage(
                user_id=message.from_user.id,
                role="user",
                content=message.text
            )
            session.add(db_msg)
            await session.commit()

        # Get recent context (last 6 messages)
        context = []
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(DBMessage)
                    .where(DBMessage.user_id == message.from_user.id)
                    .order_by(DBMessage.id.desc())
                    .limit(6)
                )
                messages = result.scalars().all()
                context = [{"role": m.role, "content": m.content} for m in reversed(messages)]
        except Exception:
            context = []

        typing = await message.answer("⌛ <i>Думаю над ответом...</i>", parse_mode="HTML")
        reply = await get_ai_response(message.text, context)
        await typing.delete()
        await message.answer(reply, parse_mode="HTML")

        # Save bot reply to DB
        try:
            async with AsyncSessionLocal() as session:
                db_reply = DBMessage(
                    user_id=message.from_user.id,
                    role="assistant",
                    content=reply
                )
                session.add(db_reply)
                await session.commit()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"AI chat error: {e}")
        await message.answer("Произошла ошибка. Попробуйте ещё раз или введите /start")

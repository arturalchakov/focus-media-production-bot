import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.models import AsyncSessionLocal, User, Message as DBMessage
from services.openai_service import get_ai_response, transcribe_voice

logger = logging.getLogger(__name__)
router = Router()


class AIChatStates(StatesGroup):
    ai_chat = State()


async def get_text_from_message(message: Message) -> str:
    """Extract text from message: text or voice transcription."""
    if message.voice:
        file = await message.bot.get_file(message.voice.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        text = await transcribe_voice(file_bytes.read(), "voice.ogg")
        return text
    return message.text or ""


@router.message((F.text & ~F.text.startswith("/")) | F.voice)
async def ai_chat(message: Message, state: FSMContext):
    # Only respond if user has completed segmentation (has a segment)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            user = result.scalar_one_or_none()
            if not user or not user.segment:
                return  # Not started yet, ignore

        # Get text from message (text or voice)
        user_text = await get_text_from_message(message)
        if not user_text:
            return

        # Save message to DB
        async with AsyncSessionLocal() as session:
            db_msg = DBMessage(
                user_id=message.from_user.id,
                role="user",
                content=user_text
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
        except Exception as e:
            logger.error(f"Failed to load context: {e}")

        # Generate AI response
        await message.bot.send_chat_action(message.chat.id, "typing")
        response = await get_ai_response(user_text, context)

        # Save AI response to DB
        try:
            async with AsyncSessionLocal() as session:
                db_msg = DBMessage(
                    user_id=message.from_user.id,
                    role="assistant",
                    content=response
                )
                session.add(db_msg)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save AI response: {e}")

        await message.answer(response)

    except Exception as e:
        logger.error(f"AI chat error: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

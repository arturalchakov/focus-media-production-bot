from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, insert
from database.models import AsyncSessionLocal, User, Message as DBMessage
from services.openai_service import get_consultant_reply

router = Router()

@router.message(F.text & ~F.text.startswith("/"))
async def ai_chat(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    # Only respond in ai_chat state OR if user has completed segmentation
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user or not user.segment:
            return
        
        # Get last 8 messages for context
        msg_result = await session.execute(
            select(DBMessage).where(DBMessage.user_id == user.id).order_by(DBMessage.created_at.desc()).limit(8)
        )
        history = [{"role": m.role, "content": m.content} for m in reversed(msg_result.scalars().all())]
        
        user_profile = {
            "segment": user.segment,
            "niche": user.niche or "",
            "main_goal": user.main_goal or ""
        }
    
    if current_state != "ai_chat":
        return
    
    typing_msg = await message.answer("Думаю...")
    
    reply = await get_consultant_reply(
        user_message=message.text,
        chat_history=history,
        user_profile=user_profile
    )
    
    await typing_msg.delete()
    await message.answer(reply)
    
    # Save messages to DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            session.add(DBMessage(user_id=user.id, role="user", content=message.text))
            session.add(DBMessage(user_id=user.id, role="assistant", content=reply))
            await session.commit()

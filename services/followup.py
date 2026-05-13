import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, delete

from database.models import AsyncSessionLocal, User, FollowUpTask
from config import FOLLOWUP_DELAYS

logger = logging.getLogger(__name__)

FOLLOWUP_MESSAGES = {
    "fu_1": (
        "Привет, это снова FOCUS MEDIA PRODUCTION.\n\n"
        "Вчера прошёл диагностику в боте, но до стратсессии не дошёл. Это нормально — "
        "большинство ставят на паузу.\n\n"
        "Только пауза = упущенные деньги. Каждый день без системы — это лиды, "
        "которые уходят к тем, кто докрутил воронку первым.\n\n"
        "60 минут с командой — бесплатно. Не зайдёт — никто не обидится."
    ),
    "fu_2": (
        "Возвращаюсь.\n\n"
        "По опыту нашей команды: эксперт без упакованного оффера теряет "
        "60–80% потенциальных клиентов. Они уходят не к лучшему — а к тому, "
        "кто понятнее объясняет ценность.\n\n"
        "На стратсессии разложим, где конкретно у тебя эта утечка и что закрыть "
        "в первую очередь. 60 минут, бесплатно."
    ),
    "fu_3": (
        "Последнее сообщение от меня. Спамить не хочу.\n\n"
        "Если сейчас не время — не вопрос, жми /restart когда созреешь, "
        "разберём заново.\n\n"
        "Если время — кнопка ниже."
    ),
}


def _cta_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📞 Записаться на стратсессию", callback_data="cta_book")
    kb.adjust(1)
    return kb.as_markup()


async def schedule_followups(telegram_id: int) -> None:
    """Schedule 3 follow-up messages for user (after diagnosis, if not yet a lead)."""
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if not user or user.is_lead:
            return
        # idempotent: drop any pending ones first
        await session.execute(delete(FollowUpTask).where(
            FollowUpTask.user_id == user.id,
            FollowUpTask.sent == False,
        ))
        now = datetime.utcnow()
        for i, hours in enumerate(FOLLOWUP_DELAYS[:3], start=1):
            session.add(FollowUpTask(
                user_id=user.id,
                scheduled_at=now + timedelta(hours=hours),
                message_type=f"fu_{i}",
                sent=False,
            ))
        await session.commit()
        logger.info(f"Scheduled {len(FOLLOWUP_DELAYS[:3])} followups for telegram_id={telegram_id}")


async def cancel_followups(telegram_id: int) -> None:
    """Cancel pending follow-ups (called when user becomes a lead)."""
    async with AsyncSessionLocal() as session:
        uid = (await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if not uid:
            return
        await session.execute(delete(FollowUpTask).where(
            FollowUpTask.user_id == uid,
            FollowUpTask.sent == False,
        ))
        await session.commit()
        logger.info(f"Cancelled pending followups for telegram_id={telegram_id}")


async def _send_followup(bot: Bot, telegram_id: int, message_type: str) -> None:
    text = FOLLOWUP_MESSAGES.get(message_type)
    if not text:
        return
    try:
        await bot.send_message(telegram_id, text, reply_markup=_cta_kb())
    except Exception as e:
        logger.warning(f"Followup {message_type} to {telegram_id} failed: {type(e).__name__}: {e}")


async def followup_loop(bot: Bot, poll_sec: int = 60) -> None:
    """Background loop: every poll_sec seconds, scan due tasks and send."""
    logger.info(f"Followup loop started (poll={poll_sec}s, delays={FOLLOWUP_DELAYS}h)")
    while True:
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()
                rows = (await session.execute(
                    select(FollowUpTask, User)
                    .join(User, User.id == FollowUpTask.user_id)
                    .where(FollowUpTask.sent == False, FollowUpTask.scheduled_at <= now)
                )).all()
                for task, user in rows:
                    if not user.is_lead:
                        await _send_followup(bot, user.telegram_id, task.message_type)
                    task.sent = True
                if rows:
                    await session.commit()
        except Exception:
            logger.exception("Followup loop tick failed")
        await asyncio.sleep(poll_sec)

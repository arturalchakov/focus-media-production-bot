from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select, func
from database.models import AsyncSessionLocal, User
from config import ADMIN_IDS

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("No access.")
        return
    async with AsyncSessionLocal() as session:
        total = (await session.execute(select(func.count(User.id)))).scalar()
        leads = (await session.execute(select(func.count(User.id)).where(User.is_lead == True))).scalar()
        experts = (await session.execute(select(func.count(User.id)).where(User.segment == "expert"))).scalar()
        bloggers = (await session.execute(select(func.count(User.id)).where(User.segment == "blogger"))).scalar()
        business = (await session.execute(select(func.count(User.id)).where(User.segment == "business"))).scalar()
    conversion = round((leads / total * 100), 1) if total > 0 else 0
    await message.answer(
        f"STATS FocusMediaProd Bot\n\nUsers: {total}\nLeads: {leads}\nConversion: {conversion}%\n\nExperts: {experts}\nBloggers: {bloggers}\nBusiness: {business}"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("/start - Start funnel\n/restart - Restart\n/stats - Statistics (admins)\n/help - Help")

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.segmentation import router as segment_router
from handlers.ai_consultant import router as ai_router
from handlers.cta import router as cta_router
from handlers.admin import router as admin_router
from database.models import init_db

logging.basicConfig(
    level=logging.INFO,ef main():
        bot = Bot(token=BOT_TOKEN)
            storage = MemoryStorage()
                dp = Dispatcher(storage=storage)

                    dp.include_router(start_router)
                        dp.include_router(segment_router)
                            dp.include_router(ai_router)
                                dp.include_router(cta_router)
                                    dp.include_router(admin_router)

                                        await init_db()
                                            logger.info("Focus Media Production Bot started!")

                                                try:
                                                        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
                                                            finally:
                                                                    await bot.session.close()


                                                                    if __name__ == "__main__":
                                                                        asyncio.run(main())
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logger = logging.getLogger(__name__)


        async d

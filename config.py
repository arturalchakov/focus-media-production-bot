import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
MANAGER_CHAT_ID: int = int(os.getenv("MANAGER_CHAT_ID", "0"))
ADMIN_IDS: list = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x]
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_TOKENS_DIAGNOSIS: int = int(os.getenv("MAX_TOKENS_DIAGNOSIS", "800"))
MAX_TOKENS_CONTENT: int = int(os.getenv("MAX_TOKENS_CONTENT", "1200"))
FOLLOWUP_DELAYS: list = [int(x) for x in os.getenv("FOLLOWUP_DELAYS_HOURS", "24,48,72").split(",")]

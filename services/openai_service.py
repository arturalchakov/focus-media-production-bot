import logging
from groq import Groq
import config

logger = logging.getLogger(__name__)

# Groq client (synchronous, we'll run in executor)
_client = Groq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты — опытный эксперт по цифровому маркетингу и онлайн-запускам с 15+ летним стажем.
Твоя специализация: распаковка личного бренда, создание воронок продаж, запуски онлайн-продуктов.
Ты помогаешь экспертам, блогерам и предпринимателям монетизировать свои знания и выстраивать системные продажи.

Отвечай конкретно, по делу, с практическими советами. Не упоминай никаких имён маркетологов или экспертов.
Говори от своего лица как консультант FOCUS MEDIA PRODUCTION.
Пиши на русском языке."""


async def get_ai_diagnosis(user_data: dict) -> str:
    """Generate AI diagnosis based on user segment and answers."""
    import asyncio

    segment = user_data.get("segment", "expert")
    answers = user_data.get("answers", [])

    segment_names = {
        "expert": "эксперт/коуч",
        "blogger": "блогер",
        "entrepreneur": "предприниматель"
    }

    segment_label = segment_names.get(segment, "специалист")
    answers_text = "\n".join([f"- {a}" for a in answers]) if answers else "Нет данных"

    prompt = f"""Проанализируй ситуацию пользователя и дай краткую, точную диагностику (3-4 предложения).

Сегмент: {segment_label}
Ответы пользователя:
{answers_text}

Выдели 1-2 ключевые проблемы и намекни на решение. Заверши призывом к разговору с командой.
Будь конкретным и мотивирующим."""

    def _call():
        response = _client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.MAX_TOKENS_DIAGNOSIS,
            temperature=0.7
        )
        return response.choices[0].message.content

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _call)
        return result
    except Exception as e:
        logger.error(f"Groq API error in diagnosis: {e}")
        return ("На основе ваших ответов я вижу потенциал для роста. "
                "Наша команда поможет выстроить систему продаж под ваш профиль. "
                "Давайте обсудим это на стратегической сессии!")


async def get_ai_response(user_message: str, context: list = None) -> str:
    """Generate AI response for consultation chat."""
    import asyncio

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        for msg in context[-6:]:  # last 6 messages for context
            messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    def _call():
        response = _client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            max_tokens=config.MAX_TOKENS_CONTENT,
            temperature=0.7
        )
        return response.choices[0].message.content

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _call)
        return result
    except Exception as e:
        logger.error(f"Groq API error in chat: {e}")
        return ("Отличный вопрос! Для детального ответа лучше поговорить лично. "
                "Запишитесь на бесплатную стратегическую сессию с нашей командой.")

import logging
import httpx
from groq import AsyncGroq
import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — опытный эксперт по цифровому маркетингу и онлайн-запускам с 15+ летним стажем.
Твоя специализация: распаковка личного бренда, создание воронок продаж, запуски онлайн-продуктов.
Ты помогаешь экспертам, блогерам и предпринимателям монетизировать свои знания и выстраивать системные продажи.

Отвечай конкретно, по делу, с практическими советами. Не упоминай никаких имён маркетологов или экспертов.
Говори от своего лица как консультант FOCUS MEDIA PRODUCTION.
Пиши на русском языке."""


def _get_client():
    """Create AsyncGroq client with explicit httpx client to avoid proxies issue."""
    http_client = httpx.AsyncClient()
    return AsyncGroq(api_key=config.GROQ_API_KEY, http_client=http_client)


async def get_ai_diagnosis(user_data: dict) -> str:
    """Generate AI diagnosis based on user segment and answers."""
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

    try:
        async with _get_client() as client:
            response = await client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.MAX_TOKENS_DIAGNOSIS,
                temperature=0.7
            )
            return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error in diagnosis: {e}")
        return ("На основе ваших ответов я вижу потенциал для роста. "
                "Наша команда поможет выстроить систему продаж под ваш профиль. "
                "Давайте обсудим это на стратегической сессии!")


async def get_ai_response(user_message: str, context: list = None) -> str:
    """Generate AI response for consultation chat."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        for msg in context[-6:]:  # last 6 messages for context
            messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    try:
        async with _get_client() as client:
            response = await client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                max_tokens=config.MAX_TOKENS_CONTENT,
                temperature=0.7
            )
            return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error in chat: {e}")
        return ("Отличный вопрос! Для детального ответа лучше поговорить лично. "
                "Запишитесь на бесплатную стратегическую сессию с нашей командой.")


async def transcribe_voice(file_bytes, filename: str = "voice.ogg") -> str:
    """Transcribe voice message using Groq Whisper API."""
    import io
    try:
        # Ensure we have bytes (handle both bytes and BytesIO)
        if hasattr(file_bytes, 'read'):
            data = file_bytes.read()
        else:
            data = file_bytes

        logger.info(f"Transcribing voice: {len(data)} bytes, filename={filename}")

        client = _get_client()
        transcription = await client.audio.transcriptions.create(
            file=(filename, data),
            model="whisper-large-v3-turbo",
            language="ru",
        )
        result = transcription if isinstance(transcription, str) else transcription.text
        logger.info(f"Transcription result: {repr(result)}")
        return result or ""
    except Exception as e:
        logger.error(f"Groq Whisper error: {type(e).__name__}: {e}")
        return ""

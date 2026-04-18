import asyncio
import logging
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS_DIAGNOSIS, MAX_TOKENS_CONTENT

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

DIAGNOSIS_SYSTEM_PROMPT = """Ты — опытный стратег по цифровому маркетингу и запускам онлайн-продуктов с 15-летним опытом. Работаешь в команде Focus Media Production.
Твоя задача — провести экспресс-диагностику ситуации клиента и дать конкретные, практические рекомендации.

Правила:
1. Отвечай на русском языке
2. Используй конкретные цифры и примеры
3. Структурируй ответ: Анализ → 3 точки роста → Первый шаг
4. Объём: 200-300 слов
5. Тон: профессиональный, живой. Как умный старший партнёр
6. Никогда не упоминай что ты AI
7. В конце: один конкретный вопрос для углубления диалога"""

CONSULTANT_SYSTEM_PROMPT = """Ты — персональный AI-стратег Focus Media Production.
Специализация: digital-маркетинг, продюсирование онлайн-курсов, личный бренд, воронки продаж, запуски.
Правила:
1. Отвечай конкретно, без воды
2. Давай примеры из реального рынка (Россия, СНГ)
3. Максимум 250 слов на ответ
4. Если видишь что нужна глубокая работа — предложи стратегическую сессию с командой FMP"""


async def get_diagnosis(segment: str, niche: str, current_state: str, main_goal: str) -> str:
    user_prompt = f"""Сегмент: {segment}
Ниша: {niche}
Текущая ситуация: {current_state}
Главная цель: {main_goal}

Проведи диагностику и дай персональные рекомендации."""

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS_DIAGNOSIS,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI diagnosis error: {e}")
        return "Извини, произошла техническая ошибка. Попробуй чуть позже или напиши нам напрямую."


async def get_consultant_reply(user_message: str, chat_history: list, user_profile: dict) -> str:
    profile_summary = f"Сегмент: {user_profile.get('segment', 'не указан')}, Ниша: {user_profile.get('niche', 'не указана')}"
    
    system = CONSULTANT_SYSTEM_PROMPT + f"\n\nПрофиль клиента: {profile_summary}"
    
    messages = [{"role": "system", "content": system}]
    for msg in chat_history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS_CONTENT,
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI consultant error: {e}")
        return "Произошла техническая ошибка. Попробуй ещё раз."

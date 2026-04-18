# 🎯 Focus Media Production Bot

**Telegram AI-бот** для экспертов, блогеров и предпринимателей.  
Анализирует нишу, даёт персональную стратегию через GPT-4o и конвертирует в лиды.

## 🤖 [@FocusMediaProd_bot](https://t.me/FocusMediaProd_bot)

---

## 🗺️ Воронка

```
/start
  ↓ Выбор сегмента (Эксперт / Блогер / Предприниматель)
  ↓ 3 вопроса (ниша / ситуация / цель)
  ↓ GPT-4o Диагностика (персональная стратегия)
  ↓ Лид-магнит (PDF-чеклист по сегменту)
  ↓ Кнопка записи на стратегическую сессию
  ↓ Свободный AI-чат (GPT-4o консультант 24/7)
```

---

## 🚀 Деплой на Render.com (5 минут, бесплатно)

### 1. [Зарегистрируйся на render.com](https://render.com) → Sign Up with GitHub

### 2. New → Background Worker → Connect repo: `arturalchakov/focus-media-production-bot`

### 3. Настройки сервиса:
| Поле | Значение |
|------|---------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bot.py` |

### 4. Environment Variables (добавить в настройках):
| Key | Value |
|-----|-------|
| `BOT_TOKEN` | `8737690833:AAHmb9a6YZdiBbgB0TUhC0HwCxM2ZxkvQSE` |
| `OPENAI_API_KEY` | _(ключ из platform.openai.com/api-keys)_ |
| `MANAGER_CHAT_ID` | _(твой Telegram ID — узнай у @userinfobot)_ |
| `ADMIN_IDS` | _(твой Telegram ID)_ |
| `DATABASE_URL` | `sqlite+aiosqlite:///./bot.db` |
| `OPENAI_MODEL` | `gpt-4o` |
| `MAX_TOKENS_DIAGNOSIS` | `800` |
| `MAX_TOKENS_CONTENT` | `1200` |

### 5. → Deploy! Бот запустится через 2-3 минуты.

---

## 💻 Локальный запуск

```bash
git clone https://github.com/arturalchakov/focus-media-production-bot
cd focus-media-production-bot
pip install -r requirements.txt
cp .env.example .env
# Отредактируй .env — добавь BOT_TOKEN и OPENAI_API_KEY
python bot.py
```

---

## 📁 Структура

```
├── bot.py                    # Точка входа
├── config.py                 # Загрузка .env переменных
├── requirements.txt          # Зависимости Python
├── Procfile                  # worker: python bot.py
├── runtime.txt               # python-3.11.0
├── render.yaml               # Авто-конфиг Render
├── .env.example              # Шаблон переменных окружения
├── database/
│   ├── __init__.py
│   └── models.py             # User, Message (SQLAlchemy async)
├── handlers/
│   ├── __init__.py
│   ├── start.py              # /start — регистрация + сегменты
│   ├── segmentation.py       # 3 вопроса + GPT диагностика
│   ├── ai_consultant.py      # Свободный AI-чат
│   ├── cta.py                # Лид-магниты + запись на звонок
│   └── admin.py              # /stats — статистика для админов
└── services/
    ├── __init__.py
    └── openai_service.py     # GPT-4o интеграция (диагностика + чат)
```

---

## ⚠️ Перед запуском

1. Пополни баланс OpenAI: [platform.openai.com/billing](https://platform.openai.com/billing) (от $5)
2. Узнай свой Telegram ID: напиши [@userinfobot](https://t.me/userinfobot)
3. Подставь ID в `MANAGER_CHAT_ID` и `ADMIN_IDS`

---

## 🛠️ Стек

- **Python 3.11**
- **aiogram 3.7** — async Telegram bot framework
- **OpenAI API (GPT-4o)** — AI диагностика и консультации
- **SQLAlchemy 2.0 + aiosqlite** — async база данных
- **python-dotenv** — управление конфигурацией

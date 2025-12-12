import os
import logging
import uuid
import sqlite_utils
from sqlite_utils.db import NotFoundError

# Импорт executor работает корректно с aiogram==2.25.1
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- КОНФИГУРАЦИЯ БОТА ---
API_TOKEN = '8597302676:AAH6sOqnLONNdboRPwfYhmzk_fkL4sFRDo0' 
YOUR_TELEGRAM_ID = 7227557185 
BOT_USERNAME = 'MTGASKBot' 
# -------------------------

if not API_TOKEN or YOUR_TELEGRAM_ID is None:
    logging.error("❌ Критическая ошибка: Отсутствует BOT_TOKEN или YOUR_ID.")
    exit(1)


# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage()) 
DB_NAME = 'anon_bot.db'
db = sqlite_utils.Database(DB_NAME)

# --- Инициализация таблицы БД ---
# Мы поместим создание таблицы в отдельную функцию, чтобы быть уверенными, 
# что она выполнится перед использованием БД.
def initialize_db():
    if 'users' not in db.table_names():
        logging.info("Создание таблицы 'users'...")
        db["users"].create(
            {"id": int, "link_token": str},
            pk="id",
            if_not_exists=True
        )

# --- FSM (Конечный автомат) для отслеживания состояния отправки ---
class AnonMessage(StatesGroup):
    recipient_id = State() 
    waiting_for_message = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_or_create_user_token(user_id: int) -> str:
    """Получает токен пользователя из БД или создает новый, используя try/except."""
    
    # 1. Попытка получить данные
    user_data = None
    try:
        user_data = db["users"].get(user_id)
    except NotFoundError:
        # Это нормально, если пользователь не найден, мы его создадим
        pass
    except Exception as e:
        # Перехват других возможных ошибок БД, на всякий случай
        logging.error(f"Ошибка при получении данных пользователя {user_id}: {e}")
        pass
        
    # 2. Если данные найдены, возвращаем токен
    if user_data:
        return user_data["link_token"]
    
    # 3. Если не найдены (или возникла NotFoundError), создаем нового
    new_token = str(uuid.uuid4())[:8] 
    db["users"].insert({"id": user_id, "link_token": new_token}, alter=True)
    return new_token


def get_user_id_by_token(token: str) -> int or None:
    """Находит Telegram ID по уникальному токену."""
    result = db.query("SELECT id FROM users WHERE link_token = ?", (token,)).fetchone()
    return result[0] if result else None

# --- ХЕНДЛЕРЫ ---

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message, state: FSMContext):
    """
    Обрабатывает /start. Если есть токен в аргументах, переводит в режим отправки, 
    иначе - выдает персональную ссылку.
    """
    await state.finish() 
    args = message.get_args() 
    
    # Сначала убедимся, что таблица существует для нового пользователя
    initialize_db() 
    
    if args:
        # Сценарий 1: Переход по ссылке (начинаем анонимную отправку)
        recipient_id = get_user_id_by_token(args)
        
        if recipient_id:
            await state.set_state(AnonMessage.recipient_id.state)
            await state.update_data(recipient_id=recipient_id)
            
            await message.reply(
                "🤫 **Режим анонимного сообщения**\n\n"
                "Напишите и отправьте ваше сообщение. Получатель не узнает, кто вы.",
                parse_mode="Markdown"
            )
            await AnonMessage.waiting_for_message.set() 
        else:
            await message.reply("⚠️ Ссылка недействительна. Отправьте /start, чтобы получить свою ссылку.")

    else:
        # Сценарий 2: Обычный /start (выдача личной ссылки)
        user_id = message.from_user.id
        token = get_or_create_user_token(user_id)
        
        # Генерация ссылки с именем вашего бота
        link = f"https://t.me/{BOT_USERNAME}?start={token}"
        
        await message.reply(
            "🌟 **Ваша персональная ссылка для анонимных посланий:**\n\n"
            f"`{link}`\n\n"
            "Разместите ее в профиле, чтобы начать сбор сообщений!",
            parse_mode="Markdown"
        )

@dp.message_handler(commands=['cancel'], state='*')
async def handle_cancel(message: types.Message, state: FSMContext):
    """Отмена текущего процесса отправки."""
    await state.finish()
    await message.reply("❌ **Отправка сообщения отменена.**", parse_mode="Markdown")

@dp.message_handler(content_types=types.ContentTypes.TEXT, state=AnonMessage.waiting_for_message)
async def handle_anon_message(message: types.Message, state: FSMContext):
    """
    Обработка текста сообщения с реализацией двойной логики анонимности.
    """
    data = await state.get_data()
    recipient_id = data.get("recipient_id")
    sender_user = message.from_user 
    
    # --- ДВОЙНАЯ ЛОГИКА ---
    
    # 1. Если получатель - это АДМИНИСТРАТОР (ВЫ)
    if recipient_id == YOUR_TELEGRAM_ID:
        
        # Собираем все доступные данные об отправителе
        sender_info = (
            f"👤 **Отправитель:** {sender_user.full_name} "
            f"(@{sender_user.username or 'нет username'})"
            f" (ID: `{sender_user.id}`)"
        )
        
        admin_message = (
            "💌 **Новое СЕКРЕТНОЕ сообщение для ВАС!**\n"
            f"{sender_info}\n\n"
            "--- Сообщение ---\n"
            f"{message.text}"
        )
        
        # Отправляем ВАМ с информацией об отправителе
        await bot.send_message(recipient_id, admin_message, parse_mode="Markdown")

    # 2. Если получатель - ОБЫЧНЫЙ пользователь
    else:
        anon_message = (
            "🤫 **Новое анонимное сообщение!**\n\n"
            "--- Сообщение ---\n"
            f"{message.text}"
        )
        
        # Отправляем получателю (полностью анонимно)
        await bot.send_message(recipient_id, anon_message, parse_mode="Markdown")
    
    # Подтверждение отправки отправителю
    await message.reply("✅ **Сообщение успешно отправлено!**", parse_mode="Markdown")
    
    await state.finish()


# --- ЗАПУСК БОТА ---

if __name__ == '__main__':
    logging.info("Starting bot...")
    
    # 1. Инициализация таблицы БД перед началом работы executor
    initialize_db()
    
    # 2. Инициализация первой записи для администратора
    # Теперь эта функция более устойчива к ошибкам NotFoundError
    get_or_create_user_token(YOUR_TELEGRAM_ID) 
    
    executor.start_polling(dp, skip_updates=True)
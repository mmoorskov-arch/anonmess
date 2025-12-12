import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

API_TOKEN = "8597302676:AAH6sOqnLONNdboRPwfYhmzk_fkL4sFRDo0"      # вставь токен от @BotFather
ADMIN_ID = 7227557185               # сюда вставь свой Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ============================================================
# /start
# ============================================================
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    # создаём персональную ссылку в формате:
    # https://t.me/ИмяБота?start=USER_ID
    bot_username = (await bot.get_me()).username
    personal_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        "hey! твоя персональная ссылка для анонимок ↓\n"
        f"{personal_link}\n\n"
        "скинь её кому хочешь — тебе будут писать анонимно 💌"
    )

    await message.answer(text)


# ============================================================
# при переходе по персональной ссылке: /start 123456789
# ============================================================
@dp.message()
async def anon_message_handler(message: types.Message):

    # Если это /start с аргументом — человек зашёл по персональной ссылке
    if message.text.startswith("/start"):
        parts = message.text.split()

        if len(parts) == 2:
            receiver_id = parts[1]   # ID того, кому уйдёт анонимка

            # запоминаем получателя в "сессии" пользователя
            message.from_user.receiver_for = receiver_id

            await message.answer(
                "ок, напиши свою анонимку ✨\n"
                "я отправлю её тому, чей линк ты открыл"
            )
            return
        else:
            # обычный /start без ID → просто выдаём ссылку
            await start_cmd(message)
            return

    # человек пишет анонимку
    # ------------------------------------------------------------

    # проверяем, есть ли у него сохранённый receiver_id
    try:
        receiver_id = int(message.from_user.receiver_for)
    except:
        await message.answer("ты зашёл без персональной ссылки 😅")
        return

    sender = message.from_user

    # ============================================================
    # ЛОГИКА: раскрывать автора только тебе (ADMIN_ID)
    # ============================================================

    if receiver_id == ADMIN_ID:
        # тебе — показываем автора
        username = sender.username or "no_username"

        text = (
            "📩 Новое сообщение\n\n"
            f"👤 Автор: @{username}\n"
            f"🆔 ID: {sender.id}\n"
            f"Имя: {sender.first_name}\n"
            f"Фамилия: {sender.last_name}\n\n"
            f"💬 Текст:\n{message.text}"
        )
    else:
        # другим — полностью анонимно
        text = (
            "💌 Анонимка:\n"
            f"{message.text}"
        )

    # отправляем сообщение получателю
    await bot.send_message(receiver_id, text)

    # отправителю говорим, что отправлено
    await message.answer("готово ✔️")


# ============================================================
# Старт бота
# ============================================================
async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
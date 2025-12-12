Если получатель - это АДМИНИСТРАТОР (ВЫ)
    if recipient_id == YOUR_TELEGRAM_ID:
        
        # Собираем все доступные данные об отправителе
        sender_info = (
            f"👤 Отправитель: {sender_user.full_name} "
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

if name == '__main__':
    logging.info("Starting bot...")
    get_or_create_user_token(YOUR_TELEGRAM_ID) 
    
    executor.start_polling(dp, skip_updates=True)
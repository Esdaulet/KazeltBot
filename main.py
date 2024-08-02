from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from handlers.common_handlers import start, process_go, receive_receipt, full_name, work_place, age, teaching_experience, city, confirm_subscription, broadcast_message
from handlers.start import button
from handlers.think_handler import think, reminder_response

# Определяем состояния
START, SEND_RECEИПТ, FULL_NAME, WORK_PLACE, AGE, TEACHING_EXPERИENCE, CITY, CONFIRM_SUBSCRIPTION = range(8)

# Список администраторов (добавьте сюда Telegram ID администраторов)
ADMIN_IDS = [864464357]  # замените на реальные ID администраторов

async def delete_webhook(application):
    await application.bot.delete_webhook()

# Команда для отправки рассылок
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("❗️ Message text is empty. Please provide the message text.")
        return

    message_template = " ".join(context.args)
    await broadcast_message(context, message_template)
    await update.message.reply_text("Broadcast message sent!")

# Команда для получения ID пользователя
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(f"Your Telegram ID is: {user_id}")

def main() -> None:
    application = ApplicationBuilder().token("7242950496:AAHlNr4SGLVrawrDBUYTh19gLZaZnc-cp-M").read_timeout(20).write_timeout(20).build()
    job_queue = application.job_queue

    # Удаление вебхука перед началом работы бота
    job_queue.run_once(delete_webhook, 0)

    # Установка команд для бота
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="broadcast", description="Send broadcast message"),
        BotCommand(command="myid", description="Get your Telegram ID")
    ]
    application.bot.set_my_commands(commands)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [
                CallbackQueryHandler(button, pattern='^.*$'),
                CallbackQueryHandler(think, pattern='^think$'),
                CallbackQueryHandler(reminder_response, pattern='^reminder_yes|reminder_no$')
            ],
            SEND_RECEИПТ: [MessageHandler(filters.Document.PDF, receive_receipt)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            WORK_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_place)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            TEACHING_EXPERИENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, teaching_experience)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            CONFIRM_SUBSCRIPTION: [CallbackQueryHandler(confirm_subscription, pattern='^confirm_now$')]
        },
        fallbacks=[CommandHandler('start', start)],
        per_chat=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("broadcast", send_broadcast))
    application.add_handler(CommandHandler("myid", my_id))
    application.run_polling()

if __name__ == '__main__':
    main()

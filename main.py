from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from handlers.common_handlers import start, process_go, receive_receipt, full_name, work_place, age, teaching_experience, city, confirm_subscription
from handlers.start import button
from handlers.think_handler import think, reminder_response

# Определяем состояния
START, SEND_RECEIPT, FULL_NAME, WORK_PLACE, AGE, TEACHING_EXPERIENCE, CITY, CONFIRM_SUBSCRIPTION = range(8)

async def delete_webhook(application):
    await application.bot.delete_webhook()

def main() -> None:
    application = ApplicationBuilder().token("7242950496:AAHlNr4SGLVrawrDBUYTh19gLZaZnc-cp-M").read_timeout(20).write_timeout(20).build()
    job_queue = application.job_queue

    # Удаление вебхука перед началом работы бота
    job_queue.run_once(delete_webhook, 0)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [
                CallbackQueryHandler(button, pattern='^.*$'),
                CallbackQueryHandler(think, pattern='^think$'),
                CallbackQueryHandler(reminder_response, pattern='^reminder_yes|reminder_no$')
            ],
            SEND_RECEIPT: [MessageHandler(filters.Document.PDF, receive_receipt)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            WORK_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_place)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            TEACHING_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, teaching_experience)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            CONFIRM_SUBSCRIPTION: [CallbackQueryHandler(confirm_subscription, pattern='^confirm_now$')]
        },
        fallbacks=[CommandHandler('start', start)],
        per_chat=True
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()

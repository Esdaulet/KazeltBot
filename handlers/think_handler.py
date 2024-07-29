# think_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from .common_handlers import process_go, receive_receipt, full_name, work_place, age, teaching_experience, city, confirm_subscription

START, SEND_RECEIPT, FULL_NAME, WORK_PLACE, AGE, TEACHING_EXPERIENCE, CITY, CONFIRM_SUBSCRIPTION = range(8)

async def think(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Сообщение пользователю
    await query.edit_message_text(text="Take your time. Let us know when you're ready to join.")
    
    # Установка напоминания через 10 секунд
    context.job_queue.run_once(remind_user, 10, data={'chat_id': query.message.chat_id})
    
    return START

async def remind_user(context: CallbackContext) -> None:
    job_data = context.job.data
    chat_id = job_data['chat_id']
    keyboard = [
        [InlineKeyboardButton("Да", callback_data='reminder_yes')],
        [InlineKeyboardButton("Нет", callback_data='reminder_no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(chat_id=chat_id, text="Прошел день. Вы готовы присоединиться?", reply_markup=reply_markup)

async def reminder_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'reminder_yes':
        return await process_go(query, context)
    else:
        # Установка следующего напоминания через 20 секунд
        context.job_queue.run_once(remind_user, 20, data={'chat_id': query.message.chat_id})
        await query.edit_message_text(text="Хорошо, я напомню вам позже.")
        return START

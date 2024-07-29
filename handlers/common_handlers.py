# common_handlers.py
import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

START, SEND_RECEIPT, FULL_NAME, WORK_PLACE, AGE, TEACHING_EXPERIENCE, CITY, CONFIRM_SUBSCRIPTION, CHECK_SUBSCRIPTIONS = range(9)

required_channels = [
    "@channel1",
    "@channel2",
    "@channel3",
    "@channel4",
    "@channel5",
    "@channel6"
]

main_channel = "@mainchannel"  # Главный канал, доступ к которому будет предоставлен после проверки

async def check_subscriptions(user_id: int, bot) -> bool:
    for channel in required_channels:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            return False
    return True

def save_member_data(telegram_id, full_name, work_place, age, teaching_experience, city, receipt_file_path):
    try:
        conn = sqlite3.connect('members.db')
        cursor = conn.cursor()
        
        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
        INSERT INTO members (telegram_id, full_name, work_place, age, teaching_experience, city, receipt_file_path, registration_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (telegram_id, full_name, work_place, age, teaching_experience, city, receipt_file_path, registration_date))
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Exception in save_member_data: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    welcome_message = (
        "Welcome to the Association for the Professional Development of English Teachers in Kazakhstan!\n"
        "We're glad to have you here.\n"
        "Do YOU want to become a member of KAZAELT?"
    )
    
    keyboard = [
        [InlineKeyboardButton("Yes!", callback_data='yes')],
        [InlineKeyboardButton("No", callback_data='no')],
        [InlineKeyboardButton("Want to know more...", callback_data='more')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return START

async def process_go(query, context):
    payment_info = (
        "Great! Please proceed with the payment through the following link:\n"
        "https://kaspi.kz\n"
        "After you complete the payment, please send us the receipt."
    )
    
    keyboard = [
        [InlineKeyboardButton("Pay Now", url='https://kaspi.kz')],
        [InlineKeyboardButton("I have paid", callback_data='paid')],
        [InlineKeyboardButton("Back", callback_data='back_detailed')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=payment_info, reply_markup=reply_markup)
    return START

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if document.mime_type == 'application/pdf':
        os.makedirs('receipts', exist_ok=True)
        
        file = await context.bot.get_file(document.file_id)
        file_path = os.path.join('receipts', document.file_name)
        
        bytearray_content = await file.download_as_bytearray()
        
        with open(file_path, 'wb') as f:
            f.write(bytearray_content)
        
        context.user_data['receipt_file_path'] = file_path
        context.user_data['telegram_id'] = update.message.from_user.id
        
        await update.message.reply_text("Thank you for the receipt! Now, please provide the following information.")
        await update.message.reply_text("Write me your full name?")
        return FULL_NAME
    else:
        await update.message.reply_text("Please send the receipt in PDF format.")
        return SEND_RECEIPT

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Where do you work?")
    return WORK_PLACE

async def work_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['work_place'] = update.message.text
    await update.message.reply_text("How old are you?")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text("How long have you been teaching?")
    return TEACHING_EXPERIENCE

async def teaching_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['teaching_experience'] = update.message.text
    await update.message.reply_text("Which city are you from?")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['city'] = update.message.text
    
    save_member_data(
        context.user_data['telegram_id'],
        context.user_data['full_name'],
        context.user_data['work_place'],
        context.user_data['age'],
        context.user_data['teaching_experience'],
        context.user_data['city'],
        context.user_data['receipt_file_path']
    )
    
    await update.message.reply_text(
        "Congratulations! You are now a member of the Association for the Professional Development of English Teachers in Kazakhstan."
    )
    


async def confirm_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm_yes':
        user_id = query.from_user.id
        if await check_subscriptions(user_id, context.bot):
            await query.edit_message_text(text=f"Thank you for confirming! You are now an official member and have access to {main_channel}.")
            return ConversationHandler.END
        else:
            await query.edit_message_text(text="You are not subscribed to all the required channels. Please subscribe and try again.")
            return CONFIRM_SUBSCRIPTION
    
    elif query.data == 'confirm_now':
        await query.edit_message_text(text="Please subscribe to all the links and confirm when done.")
        return CONFIRM_SUBSCRIPTION



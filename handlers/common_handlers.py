import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest, ChatMigrated, RetryAfter, TelegramError, Forbidden, TimedOut
from telegram.constants import ParseMode

START, SEND_RECEIPT, FULL_NAME, WORK_PLACE, AGE, TEACHING_EXPERИENCE, CITY, CONFIRM_SUBSCRIPTION = range(8)

required_channels = [
    "@testtwoss",
    "@testtwoos"
]

main_channel_invite_link = "https://t.me/+5KNZ7EsefSIxODdi"

async def check_subscriptions(user_id: int, bot) -> bool:
    for channel in required_channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except BadRequest as e:
            print(f"Failed to get chat member for {channel}: {e}")
            if 'user not found' in str(e).lower():
                print("User not found in the channel. Make sure the bot is an admin in the channel.")
            elif 'chat not found' in str(e).lower():
                print("Chat not found. Make sure the channel username is correct.")
            else:
                print(f"Unexpected error: {e}")
            return False
        except ChatMigrated as e:
            print(f"Chat {channel} has migrated: {e}")
            return False
        except RetryAfter as e:
            print(f"Retry after {e.retry_after} seconds for {channel}: {e}")
            return False
        except TelegramError as e:
            print(f"Telegram error for {channel}: {e}")
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
        "👋 *Welcome to the Association for the Professional Development of English Teachers in Kazakhstan!*\n"
        "We're glad to have you here.\n"
        "Do _YOU_ want to become a member of KAZAELT?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes!", callback_data='yes')],
        [InlineKeyboardButton("❌ No", callback_data='no')],
        [InlineKeyboardButton("ℹ️ Want to know more...", callback_data='more')],
        [InlineKeyboardButton("👤 I'm already member", callback_data='already_member')]  # Новая кнопка
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return START

async def process_go(query, context):
    payment_info = (
        "💳 *Great!* Please proceed with the payment through the following link:\n"
        "[Kaspi](https://kaspi.kz/pay/_gate?action=service_with_subservice&service_id=3025&subservice_id=18043&region_id=19)\n"
        "After you complete the payment, please send us the receipt."
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Pay Now", url='https://kaspi.kz/pay/_gate?action=service_with_subservice&service_id=3025&subservice_id=18043&region_id=19')],
        [InlineKeyboardButton("📤 I have paid", callback_data='paid')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_detailed')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=payment_info, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return START

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if document.mime_type == 'application/pdf':
        os.makedirs('receipts', exist_ok=True)
        
        file = await context.bot.get_file(document.file_id)
        file_path = os.path.join('receipts', document.file_name)
        
        try:
            bytearray_content = await file.download_as_bytearray()
        except TimedOut:
            await update.message.reply_text("❗️ The download timed out. Please try again.")
            return SEND_RECEIPT
        
        with open(file_path, 'wb') as f:
            f.write(bytearray_content)
        
        context.user_data['receipt_file_path'] = file_path
        context.user_data['telegram_id'] = update.message.from_user.id
        
        await update.message.reply_text("🧾 Thank you for the receipt! Now, please provide the following information.")
        await update.message.reply_text("📝 Write me your full name?")
        return FULL_NAME
    else:
        await update.message.reply_text("❗️ Please send the receipt in PDF format.")
        return SEND_RECEIPT

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("🏢 Where do you work?")
    return WORK_PLACE

async def work_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['work_place'] = update.message.text
    await update.message.reply_text("🔢 How old are you?")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text("📚 How long have you been teaching?")
    return TEACHING_EXPERИENCE

async def teaching_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['teaching_experience'] = update.message.text
    await update.message.reply_text("🏙️ Which city are you from?")
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
    
    # Предложение подписаться на каналы
    await update.message.reply_text(
        "🎉 *Congratulations!* You are now a member of the Association for the Professional Development of English Teachers in Kazakhstan.\n"
        "To complete your registration, please subscribe to the following channels.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    keyboard = [[InlineKeyboardButton(channel, url=f"https://t.me/{channel[1:]}")] for channel in required_channels]
    keyboard.append([InlineKeyboardButton("✅ I have subscribed", callback_data='confirm_now')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Please subscribe to all required channels and then confirm your subscription.",
        reply_markup=reply_markup
    )
    
    return CONFIRM_SUBSCRIPTION

async def confirm_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm_now':
        user_id = query.from_user.id
        if await check_subscriptions(user_id, context.bot):
            await query.edit_message_text(text=f"🎉 Thank you for confirming! You are now an official member. Use the following link to join the main channel: {main_channel_invite_link}")
            return ConversationHandler.END
        else:
            # Повторное отображение кнопок каналов
            keyboard = [[InlineKeyboardButton(channel, url=f"https://t.me/{channel[1:]}")] for channel in required_channels]
            keyboard.append([InlineKeyboardButton("✅ I have subscribed", callback_data='confirm_now')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    text="❗️ You are not subscribed to all the required channels. Please subscribe and try again.",
                    reply_markup=reply_markup
                )
            except BadRequest as e:
                if 'Message is not modified' in str(e):
                    print("Message is not modified. Skipping update.")
                else:
                    raise e

            return CONFIRM_SUBSCRIPTION

# Функция для отправки персонализированных и общих сообщений всем зарегистрированным пользователям
async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, message_template: str):
    try:
        conn = sqlite3.connect('members.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT telegram_id, full_name FROM members")
        members = cursor.fetchall()
        conn.close()

        for member in members:
            telegram_id, full_name = member
            if "{name}" in message_template:
                message = message_template.replace("{name}", full_name)
            else:
                message = message_template
            try:
                await context.bot.send_message(chat_id=telegram_id, text=message, parse_mode=ParseMode.MARKDOWN)
            except Forbidden:
                print(f"Bot was blocked by the user {telegram_id}.")
            except TelegramError as e:
                print(f"Failed to send message to {telegram_id}: {e}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Exception in broadcast_message: {e}")

DATABASE_PATH = 'members.db'
RECEIPTS_PATH = 'receipts'

# Список администраторов (добавьте сюда Telegram ID администраторов)
ADMIN_IDS = [864464357]  # замените на реальные ID администраторов

async def send_receipt_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Проверяем, что команда вызвана администратором
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    # Проверяем, что передан ID пользователя
    if not context.args:
        await update.message.reply_text("❗️ Please provide the user ID.")
        return

    try:
        # Преобразуем аргумент в целое число (ID пользователя)
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❗️ Invalid user ID format. Please provide a valid user ID.")
        return

    # Получаем имя файла чека из базы данных
    file_name = get_receipt_file_name(user_id)

    if file_name:
        file_path = os.path.join(RECEIPTS_PATH, file_name)
        # Проверяем существование файла
        if os.path.exists(file_path):
            try:
                # Отправляем файл администратору
                await context.bot.send_document(chat_id=update.message.chat_id, document=open(file_path, 'rb'))
                await update.message.reply_text("✅ Receipt sent successfully.")
            except Exception as e:
                await update.message.reply_text(f"❗️ Error sending file: {e}")
        else:
            await update.message.reply_text("❗️ Receipt file not found on the server.")
    else:
        await update.message.reply_text("❗️ No receipt found for this user ID in the database.")

def get_receipt_file_name(user_id: int) -> str:
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Выполняем запрос к базе данных
        cursor.execute("SELECT receipt_file_path FROM members WHERE telegram_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        # Возвращаем имя файла
        if row:
            return row[0]
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

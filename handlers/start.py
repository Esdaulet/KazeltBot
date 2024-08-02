from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from .common_handlers import save_member_data, check_subscriptions, required_channels, main_channel_invite_link
from .think_handler import think, reminder_response
from telegram.constants import ParseMode
from telegram.error import BadRequest
import os

# Определяем состояния
START, SEND_RECEIPТ, FULL_NAME, WORK_PLACE, AGE, TEACHING_EXPERИENCE, CITY, CONFIRM_SUBSCRIPTION = range(8)

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
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    return START

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'yes':
        return await detailed_info_step(update, context)
    
    elif query.data == 'no':
        await query.edit_message_text(text="Take your time. Let us know when you're ready to join.")
        return START
    
    elif query.data == 'more':
        await query.edit_message_text(text="Here's more information about the association: ...")
        return START
    
    elif query.data == 'already_member':
        # Обработка для кнопки "I'm already member"
        await query.edit_message_text(text="Вы уже являетесь участником! Спасибо за вашу поддержку!")
        return ConversationHandler.END  # Завершаем диалог, так как нет дальнейших действий

    elif query.data == 'go':
        return await process_go(query, context)
    
    elif query.data == 'think':
        return await think(update, context)
    
    elif query.data == 'reminder_yes' or query.data == 'reminder_no':
        return await reminder_response(update, context)

    elif query.data == 'paid':
        await query.edit_message_text(text="Thank you for your payment! Please send us the receipt in PDF format.")
        return SEND_RECEIPТ

    elif query.data == 'back_start':
        return await return_to_start(update, context)
    
    elif query.data == 'back_detailed':
        return await return_to_detailed(update, context)

async def detailed_info_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    detailed_info = (
        "📚 The Association for the Professional Development of English Teachers in Kazakhstan aims to support and enhance the skills "
        "and knowledge of English teachers across the country. We offer workshops, seminars, and a network of professionals to help "
        "you grow and succeed in your career.\n"
        "Would you like to join us now?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 GO", callback_data='go')],
        [InlineKeyboardButton("🤔 Let me think...", callback_data='think')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=detailed_info, reply_markup=reply_markup, parse_mode='Markdown')
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
    
    await query.edit_message_text(text=payment_info, reply_markup=reply_markup, parse_mode='Markdown')
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
        
        await update.message.reply_text("🧾 Thank you for the receipt! Now, please provide the following information.")
        await update.message.reply_text("📝 Write me your full name?")
        return FULL_NAME
    else:
        await update.message.reply_text("❗️ Please send the receipt in PDF format.")
        return SEND_RECEIPТ

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

async def return_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
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
        
        await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    return START

async def return_to_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        detailed_info = (
            "📚 The Association for the Professional Development of English Teachers in Kazakhstan aims to support and enhance the skills "
            "and knowledge of English teachers across the country. We offer workshops, seminars, and a network of professionals to help "
            "you grow and succeed in your career.\n"
            "Would you like to join us now?"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 GO", callback_data='go')],
            [InlineKeyboardButton("🤔 Let me think...", callback_data='think')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=detailed_info, reply_markup=reply_markup, parse_mode='Markdown')
    return START

# Определение ConversationHandler
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        START: [CallbackQueryHandler(button)],
        SEND_RECEIPТ: [MessageHandler(filters.Document.PDF, receive_receipt)],
        FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
        WORK_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_place)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
        TEACHING_EXPERИENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, teaching_experience)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
        CONFIRM_SUBSCRIPTION: [CallbackQueryHandler(confirm_subscription)]
    },
    fallbacks=[CommandHandler('start', start)]
)

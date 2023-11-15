import re
import os
import json
import uuid
import random
import asyncio
import logging
import datetime
from telegram import Update
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler , JobQueue



logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


your_username = ''
api_id = ''
api_hash = ''
your_phone = ''



client = TelegramClient(your_username, api_id, api_hash)
client.start()

if not client.is_user_authorized():
    client.send_code_request(your_phone)
    try:
        client.sign_in(your_phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=input('Password: '))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('چه کاری می خواید انجام بدید : ', reply_markup=reply_markup)




async def main_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    keyboard = [[InlineKeyboardButton(
        "بازگشت به منوی اصلی", callback_data="back_home")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    start_keyboard = []
    




def main() -> None:
    application = Application.builder().token("").build()



    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()

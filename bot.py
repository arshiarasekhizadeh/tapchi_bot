import re
import os
import json
import uuid
import random
import asyncio
import logging
import datetime
from telegram import Update , Bot
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler , JobQueue

load_dotenv()

API_HASH , API_ID , PHONE_NUMBER , USER_NAME , PASSWORLD , VERFIVATION_CODE  = range(6)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


add_account_data = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global keyboard
    keyboard = [[InlineKeyboardButton('اضافه کردن شماره' , callback_data='add_account') ,
                 InlineKeyboardButton('دیدن شماره ها' , callback_data='see_accounts')]]
    global reply_markup
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('چه کاری می خواید انجام بدید : ', reply_markup=reply_markup)


async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    global cancel_keybord
    cancel_keybord = [[InlineKeyboardButton('کنسل' , callback_data='cancel')]]
    global cancel_reply_markup
    cancel_reply_markup = InlineKeyboardMarkup(cancel_keybord)
    await update.message.reply_text('لطفا شماره موبایل را با کد کشور وارد کنید' , reply_markup=cancel_reply_markup)
    return PHONE_NUMBER


async def get_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    phone_number = update.message.text
    add_account_data.append(phone_number)
    await update.message.reply_text('لطفا یوزر نیم اکانت رو بدمن @ وارد کنید' , reply_markup=cancel_reply_markup)
    return USER_NAME


async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    user_name = update.message.text
    add_account_data.append(user_name)
    await update.message.reply_text('لطفا api hash را وارد کنید' , reply_markup=cancel_reply_markup)
    return API_HASH

async def get_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    api_hash = update.message.text
    add_account_data.append(api_hash)
    await update.message.reply_text('لطفا api id را وارد کنید' , reply_markup=cancel_reply_markup)
    return API_ID

async def get_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    api_id = update.message.text
    add_account_data.append(api_id)
    await update.message.reply_text('لطفا پسورد اکانت را وارد کنید و در صورت نداشتن پسورد دستور /skip را وارد کتید' , reply_markup=cancel_reply_markup)
    return PASSWORLD

async def skip_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    back_keybord = [[InlineKeyboardButton('بازگشت' , callback_data='back')]]
    back_reply_markup = InlineKeyboardMarkup(back_keybord)
    global client
    client = TelegramClient(f"session_files/{add_account_data[1]}", add_account_data[3], add_account_data[2])
    assert await client.connect()
    if await client.is_user_authorized() :
        add_account_data.clear()
        await update.message.reply_text('این اکانت قبلا ثپت شده است.' , reply_markup=back_reply_markup)
        return ConversationHandler.END
    await client.send_code_request(add_account_data[0])
    await update.message.reply_text('لطفا کد دریافت شده از تلگرام را وارد کنید' , reply_markup=cancel_reply_markup)
    return VERFIVATION_CODE

async def get_vervication_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    back_keybord = [[InlineKeyboardButton('بازگشت' , callback_data='back')]]
    back_reply_markup = InlineKeyboardMarkup(back_keybord)
    passworld = update.message.text
    add_account_data.append(passworld)
    global client
    client = TelegramClient(f"session_files/{add_account_data[1]}", add_account_data[3], add_account_data[2])
    await client.connect()
    if await client.is_user_authorized() :
        add_account_data.clear()
        await update.message.reply_text('این اکانت قبلا ثپت شده است.', reply_markup=back_reply_markup)
        return ConversationHandler.END
    res = await client.send_code_request(add_account_data[0])
    phone_cash = res.phone_code_hash
    add_account_data.append(phone_cash)
    await update.message.reply_text('لطفا کد دریافت شده از تلگرام را وارد کنید' , reply_markup=cancel_reply_markup)
    return VERFIVATION_CODE

async def finsh_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    code = update.message.text
    code = code.replace('_' , '')
    try :
        await client.sign_in(add_account_data[0], code=code , phone_code_hash=add_account_data[5])
    except SessionPasswordNeededError :
        await client.sign_in(password=add_account_data[4] , phone_code_hash=add_account_data[5])
    await update.message.reply_text('اکانت با موفقیت اضافه شد')
    with open('acoounts.json' , 'r') as account_file :
        accounts = json.load(account_file)
    accounts[add_account_data[1]] = add_account_data[0]
    with open('acoounts.json' , 'w') as account_file_2 :
        json.dump(accounts , account_file_2)
    add_account_data.clear()
    return ConversationHandler.END



async def main_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    back_keybord = [[InlineKeyboardButton('بازگشت' , callback_data='back')]]
    back_reply_markup = InlineKeyboardMarkup(back_keybord)
    match data :
        case 'add_account' :
            await query.message.reply_text('برای اضافه کردن شماره دستور /add_account را وارد کنید')
        case 'see_accounts' : 
            if os.path.getsize('acoounts.json') <= 3 :
                await query.message.reply_text('شما هیچ اکانتی ثپت نکردید' , reply_markup=back_reply_markup)
            else :
                with open('acoounts.json' , 'r') as account_file :
                    accounts = json.load(account_file)
                account_keybord = []
                for k, v in accounts.items():
                    account_keybord.append([InlineKeyboardButton(text=k , callback_data=v)])
                account_reply_markup = InlineKeyboardMarkup(account_keybord)
                await query.message.reply_text('اکانت های شما :‌ ' , reply_markup=account_reply_markup)
        case "back" :
            await query.message.edit_text('چه کاری می خواید انجام بدید : ' , reply_markup=reply_markup)
        case 'cancel' : 
            add_account_data.clear()
            await query.message.reply_text('فرایند کنسل شد.')
            return ConversationHandler.END




def main() -> None:
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    start_handler = CommandHandler('start' , start)
    add_account_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_account' , add_account)] ,
        states={
            PHONE_NUMBER : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_user_name)] , 
            USER_NAME : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_phone_number)] ,
            API_HASH : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_api_hash)] ,
            API_ID : [MessageHandler(filters.TEXT & ~ filters.COMMAND, get_api_id)] ,
            PASSWORLD : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_vervication_code) ,
                         CommandHandler('skip' , skip_password)] ,
            VERFIVATION_CODE : [MessageHandler(filters.TEXT & ~ filters.COMMAND , finsh_add_account)]
        } , 
        fallbacks=[] , allow_reentry=True
    )

    
    application.add_handler(start_handler)
    application.add_handler(add_account_conv_handler)
    application.add_handler(CallbackQueryHandler(main_menu_button))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()

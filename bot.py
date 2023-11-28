import re
import os
import json
import uuid
import random
import asyncio
import logging
import datetime
from telegram import Update
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler , JobQueue

load_dotenv()

API_HASH , API_ID , PHONE_NUMBER , USER_NAME , PASSWORLD , VERFIVATION_CODE  = range(6)
DELETE_ACCOUNT = 7
PATTERN_FORMAT , PATTERN_TIME ,GET_MESSAGE = 8 , 9 , 10
TOPIC_TO_CHANGE , NEW_PATTERN_VALUE= 11 , 12

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


add_account_data = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton('اضافه کردن شماره' , callback_data='add_account') ,
                 InlineKeyboardButton('دیدن شماره ها' , callback_data='see_accounts')],
                 [InlineKeyboardButton('حذف کردن شماره' , callback_data='delete_account')]]
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
    back_keybord = [[InlineKeyboardButton('بازگشت به منوی اصلی' , callback_data='back')]]
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
    back_keybord = [[InlineKeyboardButton('بازگشت به منوی اصلی' , callback_data='back')]]
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
    accounts[add_account_data[0]] = [add_account_data[1]]
    with open('acoounts.json' , 'w') as account_file_2 :
        json.dump(accounts , account_file_2)
    add_account_data.clear()
    return ConversationHandler.END

async def show_accounts(query):
    with open('acoounts.json' , 'r') as account_file :
        accounts = json.load(account_file)
    account_keybord = []
    for k, v in accounts.items():
        account_keybord.append([InlineKeyboardButton(text=k , callback_data=k)])
        account_reply_markup = InlineKeyboardMarkup(account_keybord)
        await query.message.reply_text('اکانت های شما :‌ ' , reply_markup=account_reply_markup)

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cancel_keybord = [[InlineKeyboardButton('کنسل' , callback_data='cancel')]]
    cancel_reply_markup = InlineKeyboardMarkup(cancel_keybord)
    await update.message.reply_text('لطفا شماره اکانتی را که میخواهید پاک کنید روبفرستید.' , reply_markup=cancel_reply_markup)
    return DELETE_ACCOUNT

async def delete_phonenumber_from_json (update: Update, context: ContextTypes.DEFAULT_TYPE):
    back_keybord = [[InlineKeyboardButton('بازگشت به منوی اصلی' , callback_data='back')]]
    back_reply_markup = InlineKeyboardMarkup(back_keybord)
    phone_number = update.message.text
    with open('acoounts.json' , 'r') as account_file :
        accounts = json.load(account_file)
    file_name = accounts[phone_number][0]
    accounts.pop(phone_number)
    with open('acoounts.json' , 'w') as account_file_after_pop :
        json.dump(accounts, account_file_after_pop)
    os.remove(f'session_files/{file_name}.session')
    await update.message.reply_text("اکانت با موفقیت حذف شد", reply_markup=back_reply_markup)
    return ConversationHandler.END

async def set_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    global cancel_keybord
    cancel_keybord = [[InlineKeyboardButton('کنسل' , callback_data='cancel')]]
    global cancel_reply_markup
    cancel_reply_markup = InlineKeyboardMarkup(cancel_keybord)
    await update.message.reply_text('لطفا عدد فرمت مورد نظر رو بفرستید :\n1 - هر چند ساعت یکبار\n2 - در ساعت های مشخص شده\n3 - آخرین پیام در گروه')
    return PATTERN_FORMAT

async def get_pattern_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    global pattern_format
    pattern_format = update.message.text
    if pattern_format == '1' :
        await update.message.reply_text('هر چند ساعت یکبار پیام رو بفرستم')
    elif pattern_format == '2' :
        await update.message.reply_text('لطفا لیست ساعت ها رو برام بفرستید')
    elif pattern_format == '3':
        await update.message.reply_text('لطفا پیامی که میخواید فرستاده شه رو برام بفرست')
    else :
        await  update.message.reply_text('لطفا ایدی صحیح رو وارد کنید')
        return ConversationHandler.END
    return PATTERN_TIME

async def get_pattern_time(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    back_account_keybord = [[InlineKeyboardButton('بازگشت به منوی اکانت' , callback_data='back_menu')]]
    back_account_keybord_markup = InlineKeyboardMarkup(back_account_keybord)
    global pattern_time
    pattern_time = update.message.text
    if pattern_format == '1' :
        await update.message.reply_text('لطفا پیامی که میخواید فرستاده شه رو برام بفرست')
        return GET_MESSAGE
    elif pattern_format == '2' :
        await update.message.reply_text('لطفا پیامی که میخواید فرستاده شه رو برام بفرست')
        return GET_MESSAGE
    elif pattern_format == '3' :
        message = pattern_time
        with open('acoounts.json' , 'r') as account_file :
            accounts = json.load(account_file)
        accounts[selected_phone] += ['last_message_in_group' , message]
        with open('acoounts.json' , 'w') as account_file_1 :
            json.dump(accounts , account_file_1)
        await update.message.reply_text('فرمت با موفقیت اضافه شد.' , reply_markup=back_account_keybord_markup)
        return ConversationHandler.END

async def get_messgae(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    back_account_keybord = [[InlineKeyboardButton('بازگشت به منوی اکانت' , callback_data='back_menu')]]
    back_account_keybord_markup = InlineKeyboardMarkup(back_account_keybord)
    if pattern_format == '1' :
        message = update.message.text
        with open('acoounts.json' , 'r') as account_file :
            accounts = json.load(account_file)
        accounts[selected_phone] += ['every_n_houer' , pattern_time ,message]
        with open('acoounts.json' , 'w') as account_file_1 :
            json.dump(accounts , account_file_1)
    elif pattern_format == '2' :
        message = update.message.text
        with open('acoounts.json' , 'r') as account_file :
            accounts = json.load(account_file)
        accounts[selected_phone] += ['in_set_hours' , pattern_time , message]
        with open('acoounts.json' , 'w') as account_file_1 :
            json.dump(accounts , account_file_1)
    await update.message.reply_text('فرمت با موفقیت اضافه شد.' , reply_markup=back_account_keybord_markup)
    return ConversationHandler.END

async def edit_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    global cancel_keybord
    cancel_keybord = [[InlineKeyboardButton('کنسل' , callback_data='cancel')]]
    global cancel_reply_markup
    cancel_reply_markup = InlineKeyboardMarkup(cancel_keybord)
    await update.message.reply_text('چه چیزی را می خواهید تغیر بدید :\n[message - pattertn format]')
    return TOPIC_TO_CHANGE

async def get_topic_to_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int :
    back_account_keybord = [[InlineKeyboardButton('بازگشت به منوی اکانت' , callback_data='back_menu')]]
    back_account_keybord_markup = InlineKeyboardMarkup(back_account_keybord)
    global pattern_time
    global topic_to_change
    topic_to_change = update.message.text
    if topic_to_change == 'message' :
        await update.message.reply_text('پیام جدید رو بفرستید')
    elif topic_to_change == 'pattertn format' :
        await update.message.reply_text('لطفا فرمت جدید رو به این صورت برام بفرست :\n2\n9-13-18-21')
    else : 
        await update.message.reply_text('مضوعی که می خواهید تغیر کند را به درستی وارد نکردید.' , reply_markup=back_account_keybord_markup)
        return ConversationHandler.END
    return NEW_PATTERN_VALUE

async def get_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    back_account_keybord = [[InlineKeyboardButton('بازگشت به منوی اکانت' , callback_data='back_menu')]]
    back_account_keybord_markup = InlineKeyboardMarkup(back_account_keybord)
    with open('acoounts.json' , 'r') as account_file :
        accounts = json.load(account_file)
    if topic_to_change == 'message' :
        new_messgae = update.message.text
        accounts[selected_phone][-1] = new_messgae
        await update.message.reply_text('مسیج با موفقیت تغیر کرد.',reply_markup=back_account_keybord_markup)
    elif topic_to_change == 'pattertn format' :
        new_pattern_format = update.message.text.split('\n')
        if new_pattern_format[0] == '1' :
            accounts[selected_phone][1] = 'every_n_houer'
            accounts[selected_phone][2] = new_pattern_format[1]
            await update.message.reply_text('فرمت با موفقیت تغیر کرد.',reply_markup=back_account_keybord_markup)
        elif new_pattern_format[0] == '2' :
            accounts[selected_phone][1] = 'in_set_hours'
            accounts[selected_phone][2] = new_pattern_format[1]
            await update.message.reply_text('فرمت با موفقیت تغیر کرد.',reply_markup=back_account_keybord_markup)
        elif new_pattern_format[0] == '3' :
            accounts[selected_phone][1] = 'last_message_in_group'
            await update.message.reply_text('فرمت با موفقیت تغیر کرد.',reply_markup=back_account_keybord_markup)
        else : 
            await update.message.reply_text('لطفا ایدی صحیح رو وارد کنید',reply_markup=back_account_keybord_markup)
            return ConversationHandler.END
    with open('acoounts.json' , 'w') as account_file1 :
        json.dump(accounts , account_file1)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    add_account_data.clear()
    await update.message.reply_text('فرایند کنسل شد.')
    return ConversationHandler.END



async def main_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    keyboard = [[InlineKeyboardButton('اضافه کردن شماره' , callback_data='add_account') ,
                 InlineKeyboardButton('دیدن شماره ها' , callback_data='see_accounts')],
                 [InlineKeyboardButton('حذف کردن شماره' , callback_data='delete_account')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    back_keybord = [[InlineKeyboardButton('بازگشت به منوی اصلی' , callback_data='back')]]
    back_reply_markup = InlineKeyboardMarkup(back_keybord)
    account_keybord = [[InlineKeyboardButton('دیدن اطلاعات اکانت' , callback_data='see_account_detail')],
                        [InlineKeyboardButton('ست کردن فرمت' , callback_data='set_pattern') , 
                        InlineKeyboardButton('تغیر فرمت' , callback_data='change_pattern')] ,
                        [InlineKeyboardButton('فعال کردن فرستادن پیام به دایرکت' , callback_data='acrive_send_message_to_dm'),
                        InlineKeyboardButton('غیر فغال کردن فرستادن پیام به دایرکت' , callback_data="diactive_send_message_to_dm")],
                        [InlineKeyboardButton('فعال کردن اکانت' , callback_data='active_account'),
                        InlineKeyboardButton('غیرفعال کردن اکانت' , callback_data='diactive_account')],
                        [InlineKeyboardButton('بازگشت به منوی اصلی' , callback_data='back')]]
    account_keybord_markup = InlineKeyboardMarkup(account_keybord)
    with open('acoounts.json' , 'r') as account_file :
        accounts = json.load(account_file)
    phones = list(accounts)
    if data == 'add_account' :
        await query.message.reply_text('برای اضافه کردن شماره دستور /add_account را وارد کنید')
    elif data == 'see_accounts' : 
        if os.path.getsize('acoounts.json') <= 3 :
            await query.message.reply_text('شما هیچ اکانتی ثپت نکردید' , reply_markup=back_reply_markup)
        else :
            await show_accounts(query)
    elif data == "delete_account":
        await query.message.reply_text('برای حذف کردن شماره دستور /delete_account را وارد کنید')
    elif data in phones :
        global selected_phone
        selected_phone = data
        await query.message.reply_text('چه کاری میخواید رو اکانت بدید : ' , reply_markup=account_keybord_markup)
    elif data == "back" :
        await query.message.edit_text('چه کاری می خواید انجام بدید : ' , reply_markup=reply_markup)
    elif data == 'cancel' : 
        await query.message.reply_text('برای کنسل کردن دستور /cancel را وارد کنید')
    elif data == 'set_pattern' :
        await query.message.reply_text('برای اضافه کردن فرمت دستور /set_pattern را وارد کنید')
    elif data == 'change_pattern' :
        await query.message.reply_text('برای تقیر فرمت دستور /edit_pattern را وارد کنید.')
    elif data == 'back_menu' : 
        await query.message.reply_text('چه کاری میخواید رو اکانت بدید : ' , reply_markup=account_keybord_markup)
    elif data == 'see_account_detail' :
        account_data = accounts[selected_phone]
        if len(account_data) == 1 :
            await query.message.reply_text(f'اسم اکانت :{account_data[0]}\nفرمت ست شده :‌ فرمتی ست نشده')
        elif len(account_data) == 3 :
            await query.message.reply_text(f'اسم اکانت :{account_data[0]}\nفرمت ست شده : {account_data[1]}\nپیام ست شده برای فرمت: {account_data[2]}')
        elif len(account_data) == 4 :
            await query.message.reply_text(f'اسم اکانت :{account_data[0]}\nفرمت ست شده : {account_data[1]}\nساعت فرستادن پیام: {account_data[2]}\nپیام ست شده برای فرمت :{account_data[3]}')

def main() -> None:
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    start_handler = CommandHandler('start' , start)
    delete_account_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_account' , delete_account)] ,
        states={
            DELETE_ACCOUNT: [MessageHandler(filters.TEXT & ~ filters.COMMAND , delete_phonenumber_from_json)]
        },
        fallbacks=[CommandHandler('cancel' , cancel)] , allow_reentry=True
        )
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
        fallbacks=[CommandHandler('cancel' , cancel)] , allow_reentry=True
    )
    set_pattern_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('set_pattern' , set_pattern)] ,
        states={
            PATTERN_FORMAT : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_pattern_format)] ,
            PATTERN_TIME : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_pattern_time)] ,
            GET_MESSAGE : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_messgae)]
        },
        fallbacks=[CommandHandler('cancel' , cancel)], allow_reentry=True
    )
    edit_pattern_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_pattern' , edit_pattern)] ,
        states={
            TOPIC_TO_CHANGE : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_topic_to_change)] , 
            NEW_PATTERN_VALUE : [MessageHandler(filters.TEXT & ~ filters.COMMAND , get_new_value)]
        } ,
        fallbacks=[CommandHandler('cancel' , cancel)] , allow_reentry=True
    )


    
    application.add_handler(start_handler)
    application.add_handler(add_account_conv_handler)
    application.add_handler(delete_account_conv_handler)
    application.add_handler(set_pattern_conv_handler)
    application.add_handler(edit_pattern_conv_handler)
    application.add_handler(CallbackQueryHandler(main_menu_button))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()

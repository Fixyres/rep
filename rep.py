import telebot
import json
import random
import string
from telebot import types

TOKEN = '7012769971:AAH5KU5l4CNx-4Jt9U03ao77v1MlRq2JdXI'
REPORT_GROUP_ID = -4254204574
ARCHIVE_CHAT_ID = -4280913932
REPORTS_FILE = 'reports.json'

bot = telebot.TeleBot(TOKEN)

def load_reports(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_reports(reports, file_path):
    with open(file_path, 'w') as file:
        json.dump(reports, file, indent=4)

def generate_unique_report_id(reports):
    while True:
        report_id = generate_report_id()
        if report_id not in reports:
            return report_id

def generate_report_id():
    letters = string.ascii_uppercase
    digits = string.digits
    return ''.join(random.choices(letters, k=random.randint(2, 3))) + ''.join(random.choices(digits, k=random.randint(2, 4)))

reports = load_reports(REPORTS_FILE)

@bot.message_handler(commands=['report'])
def handle_report(message):
    if message.reply_to_message:
        reported_message = message.reply_to_message

        if len(message.text.split()) > 1:
            reason = " ".join(message.text.split()[1:])
            comment_text = f"✍️ Комментарий: {reason}\n\n"
        else:
            comment_text = ""

        reporting_user = message.from_user
        reporting_user_link = f"[{reporting_user.first_name}](tg://user?id={reporting_user.id})"

        reported_user = reported_message.from_user
        reported_user_link = f"[{reported_user.first_name}](tg://openmessage?user_id={reported_user.id})"

        chat_id = reported_message.chat.id
        message_id = reported_message.message_id
        message_link = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"

        report_id = generate_unique_report_id(reports)
        report_text = (
                       f"😡 {reporting_user_link} сообщил о нарушении от {reported_user_link}:\n\n"
                       f"{comment_text}"
                       f"[📖 Посмотреть]({message_link})\n"
                       f"**🗄️ #{report_id}**")

        keyboard = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton("🧐 Подтвердить выполнение", callback_data=f"confirm_{report_id}")
        keyboard.add(confirm_button)

        sent_message = bot.send_message(REPORT_GROUP_ID, report_text, reply_markup=keyboard, parse_mode='Markdown')

        bot.pin_chat_message(REPORT_GROUP_ID, sent_message.message_id, disable_notification=True)

        bot.reply_to(message, "СЭР ДА СЭР!")

        reports[report_id] = {"message_id": sent_message.message_id, "chat_id": REPORT_GROUP_ID, "text": report_text}

        save_reports(reports, REPORTS_FILE)
    else:
        return None

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def confirm_report_execution(call):
    report_id = call.data.split('_')[1]
    report = reports.get(report_id)
    if report:
        try:
            bot.send_message(ARCHIVE_CHAT_ID, report['text'] + "\n\n✅ Выполнено", parse_mode='Markdown')
            bot.edit_message_reply_markup(REPORT_GROUP_ID, report['message_id'], reply_markup=None)
            bot.answer_callback_query(call.id, "СЭР ДА СЭР!")
            bot.unpin_chat_message(REPORT_GROUP_ID, report['message_id'])
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("✅ Выполнено", callback_data='completed'))
            bot.edit_message_reply_markup(REPORT_GROUP_ID, report['message_id'], reply_markup=keyboard)
            pinned_message_id = report['message_id']
            pinned_message = bot.get_chat(REPORT_GROUP_ID).pinned_message
            if pinned_message and pinned_message.message_id == pinned_message_id:
                bot.unpin_chat_message(REPORT_GROUP_ID, pinned_message_id)
            bot.delete_message(REPORT_GROUP_ID, pinned_message_id + 1)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка при архивации сообщения: {e}")
        del reports[report_id]
        save_reports(reports, REPORTS_FILE)

bot.polling(none_stop=True)

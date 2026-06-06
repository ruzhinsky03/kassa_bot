import os
import json
import re
from datetime import datetime, timedelta

import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler

# =========================
# ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# =========================

TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")

if not TOKEN:
    raise Exception("Не найдена переменная BOT_TOKEN")

if not SPREADSHEET_ID:
    raise Exception("Не найдена переменная GOOGLE_SHEET_ID")

if not os.getenv("GOOGLE_CREDS"):
    raise Exception("Не найдена переменная GOOGLE_CREDS")

# =========================
# BOT
# =========================

bot = telebot.TeleBot(TOKEN)

# =========================
# GOOGLE SHEETS
# =========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(os.environ["GOOGLE_CREDS"]),
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    SPREADSHEET_ID
).worksheet("Операции")

day_sheet = client.open_by_key(
    SPREADSHEET_ID
).worksheet("День")

week_sheet = client.open_by_key(
    SPREADSHEET_ID
).worksheet("Неделя")

# =========================
# ОТЧЁТЫ
# =========================

CHAT_ID = -1003516318079

def send_daily_report():

    income = day_sheet.acell("B1").value
    expense = day_sheet.acell("B2").value
    profit = day_sheet.acell("B3").value

    bank = day_sheet.acell("B5").value
    cash = day_sheet.acell("B6").value
    total = day_sheet.acell("B7").value

    text = (
        f"📅 Ежедневный отчёт\n\n"
        f"💰 Доход: {income} ₽\n"
        f"💸 Расход: {expense} ₽\n"
        f"📈 Чистыми: {profit} ₽\n\n"
        f"🏦 Банк: {bank} ₽\n"
        f"💵 Наличные: {cash} ₽\n\n"
        f"📊 Общий остаток: {total} ₽"
    )

    bot.send_message(CHAT_ID, text)

def send_weekly_report():

    income = week_sheet.acell("B1").value
    expense = week_sheet.acell("B2").value
    profit = week_sheet.acell("B3").value

    bank = week_sheet.acell("B5").value
    cash = week_sheet.acell("B6").value
    total = week_sheet.acell("B7").value

    per_person = week_sheet.acell("B9").value

    azs = week_sheet.acell("B12").value
    food = week_sheet.acell("B13").value
    rent = week_sheet.acell("B14").value
    profi = week_sheet.acell("B15").value
    other = week_sheet.acell("B16").value

    text = (
        f"📊 Недельный отчёт\n\n"
        f"💰 Доход: {income} ₽\n"
        f"💸 Расход: {expense} ₽\n"
        f"📈 Чистыми: {profit} ₽\n\n"
        f"🏦 Банк: {bank} ₽\n"
        f"💵 Наличные: {cash} ₽\n"
        f"📊 Общий остаток: {total} ₽\n\n"
        f"👷 Каждому из трёх: {per_person} ₽\n\n"
        f"📉 Аналитика расходов:\n"
        f"⛽ АЗС: {azs}\n"
        f"🍔 Еда: {food}\n"
        f"🏠 Аренда: {rent}\n"
        f"🔧 Профи: {profi}\n"
        f"📦 Прочее: {other}"
    )

    bot.send_message(CHAT_ID, text)

# =========================
# ОБРАБОТКА СООБЩЕНИЙ
# =========================

@bot.message_handler(commands=['id'])
def get_chat_id(message):
    bot.reply_to(message, f"Chat ID: {message.chat.id}")


@bot.message_handler(commands=['report'])
def report(message):

    send_daily_report()

    bot.reply_to(
        message,
        "✅ Отчёт отправлен"
    )


@bot.message_handler(commands=['weekreport'])
def weekreport(message):

    send_weekly_report()

    bot.reply_to(
        message,
        "✅ Недельный отчёт отправлен"
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):

    text = message.text.strip()

    pattern = r'^([+-])(\d+)\s+(.+)\s+(банк|наличные)$'

    match = re.match(pattern, text, re.IGNORECASE)

    if not match:
        return

    sign = match.group(1)
    amount = int(match.group(2))
    category = match.group(3)
    payment = match.group(4)

    operation_type = "Доход" if sign == "+" else "Расход"

    # Время UTC+3
    now = (
        datetime.utcnow() + timedelta(hours=3)
    ).strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row(
        [
            now,
            operation_type,
            amount,
            category,
            payment
        ],
        value_input_option="USER_ENTERED"
    )

    bot.reply_to(message, "✅ Записано")

# =========================
# ПЛАНИРОВЩИК
# =========================

scheduler = BackgroundScheduler(
    timezone="Europe/Moscow"
)

scheduler.add_job(
    send_daily_report,
    "cron",
    hour=23,
    minute=0,
    second=0
)

scheduler.start()

# =========================
# ЗАПУСК
# =========================

print("BOT STARTED")

bot.infinity_polling()

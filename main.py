import os
import json
import re
from datetime import datetime

import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

# =========================
# ОБРАБОТКА СООБЩЕНИЙ
# =========================

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

    from datetime import datetime, timedelta

now = (datetime.utcnow() + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

    sheet.append_row([
        now,
        operation_type,
        amount,
        category,
        payment
    ])

    bot.reply_to(message, "✅ Записано")

# =========================
# ЗАПУСК
# =========================

print("BOT STARTED")

bot.infinity_polling()

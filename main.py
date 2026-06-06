import re
from datetime import datetime

import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# TOKEN БОТА
# =========================

TOKEN = "8623435509:AAHbAc_eZwHKbA_ePa025t6Dd4GbPSllqcc"

bot = telebot.TeleBot(TOKEN)

# =========================
# GOOGLE SHEETS
# =========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "brigada-kassa.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key("1GIwRD_ITRu2vnHuCedzkFNOelDv5M5sFQWs3HfzbL1E").worksheet("Операции")

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

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

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
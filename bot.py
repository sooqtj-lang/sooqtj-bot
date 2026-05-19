import os
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7555325054"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
DRIVER_IDS = set(
    int(x.strip())
    for x in os.getenv("DRIVER_IDS", "").split(",")
    if x.strip().isdigit()
)

bot = telebot.TeleBot(TOKEN)


def is_admin(message):
    return message.chat.id == ADMIN_ID


def is_driver(message):
    return message.chat.id in DRIVER_IDS


def make_webapp_markup(label):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if WEBAPP_URL:
        markup.add(types.KeyboardButton(label, web_app=types.WebAppInfo(url=WEBAPP_URL)))
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    if is_admin(message):
        bot.send_message(
            message.chat.id,
            "👑 Добро пожаловать, администратор!\n\nНажмите кнопку для открытия панели:",
            reply_markup=make_webapp_markup("📊 Открыть панель управления"),
        )
    elif is_driver(message):
        bot.send_message(
            message.chat.id,
            "🚚 Добро пожаловать!\n\nНажмите кнопку для просмотра доставок:",
            reply_markup=make_webapp_markup("🚚 Мои доставки"),
        )
    else:
        bot.send_message(
            message.chat.id,
            "Салом! 👋 Хуш омадед ба SOOQ.TJ!\n\nЭлектроника и бытовая техника из Китая 🇨🇳\n\nНажмите кнопку для открытия магазина:",
            reply_markup=make_webapp_markup("🛍 Открыть магазин SOOQ"),
        )


if __name__ == "__main__":
    print("🤖 SOOQ.TJ Bot запущен (polling mode)...")
    bot.polling(none_stop=True)

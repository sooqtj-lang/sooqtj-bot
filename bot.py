import telebot
from telebot import types
from datetime import datetime

TOKEN = "8001018826:AAHHjX1M02nMVNSd9uBLly6f83ihli1cp68"
ADMIN_ID = 8442941172

bot = telebot.TeleBot("8001018826:AAHGn3ZBHhx8YEzsfeu3O0S690Vyyjh8y0Q")

orders = []
user_data = {}

def is_admin(message):
    return message.chat.id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    if is_admin(message):
        admin_panel(message)
    else:
        client_menu(message)

def client_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚡ Электрочайники", "👟 Роликовые кроссовки")
    markup.add("📱 Электроника", "❓ Задать вопрос")
    bot.send_message(message.chat.id,
    "Салом! 👋 Хуш омадед ба SOOQ.TJ!\n\nВыберите категорию:",
    reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "⚡ Электрочайники" and not is_admin(m))
def chainik(message):
    bot.send_message(message.chat.id,
    "⚡ Электрочайники от 150 сомони\n\nЧтобы заказать напишите /order")

@bot.message_handler(func=lambda m: m.text == "👟 Роликовые кроссовки" and not is_admin(m))
def rolik(message):
    bot.send_message(message.chat.id,
    "👟 Роликовые кроссовки от 200 сомони\n\nЧтобы заказать напишите /order")

@bot.message_handler(func=lambda m: m.text == "📱 Электроника" and not is_admin(m))
def elektro(message):
    bot.send_message(message.chat.id,
    "📱 Электроника — напишите название товара\n\nЧтобы заказать напишите /order")

@bot.message_handler(func=lambda m: m.text == "❓ Задать вопрос" and not is_admin(m))
def question(message):
    bot.send_message(message.chat.id,
    "❓ Напишите ваш вопрос — мы ответим в течение 30 минут!")

@bot.message_handler(commands=['order'])
def order(message):
    user_data[message.chat.id] = {'source': 'client'}
    bot.send_message(message.chat.id, "📦 Оформляем заказ!\n\nНапишите название товара:")
    bot.register_next_step_handler(message, get_product)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    today = datetime.now().strftime('%d.%m.%Y')
    today_orders = [o for o in orders if o['date'] == today]
    today_sum = sum(o.get('price', 0) for o in today_orders)
    month = datetime.now().strftime('%m.%Y')
    month_orders = [o for o in orders if o['date'].endswith(month[2:])]
    month_sum = sum(o.get('price', 0) for o in month_orders)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Новый заказ", "📋 Все заказы")
    markup.add("📊 Статистика", "🔙 Выход")
    bot.send_message(message.chat.id,
    f"👑 АДМИН ПАНЕЛЬ — SOOQ.TJ\n\n"
    f"📦 Заказов сегодня: {len(today_orders)}\n"
    f"💰 Сумма сегодня: {today_sum} сомони\n\n"
    f"📦 Заказов за месяц: {len(month_orders)}\n"
    f"💰 Сумма за месяц: {month_sum} сомони",
    reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Новый заказ" and is_admin(m))
def admin_new_order(message):
    user_data[message.chat.id] = {'source': 'admin'}
    bot.send_message(message.chat.id, "📦 Новый заказ\n\nНазвание товара:")
    bot.register_next_step_handler(message, get_product)

@bot.message_handler(func=lambda m: m.text == "📋 Все заказы" and is_admin(m))
def all_orders(message):
    if not orders:
        bot.send_message(message.chat.id, "📋 Заказов пока нет")
        return
    text = "📋 ВСЕ ЗАКАЗЫ:\n\n"
    for i, o in enumerate(orders[-10:], 1):
        text += f"{i}. {o['date']} — {o['product']} — {o['name']} — {o['phone']}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m))
def stats(message):
    admin_panel(message)

@bot.message_handler(func=lambda m: m.text == "🔙 Выход" and is_admin(m))
def exit_admin(message):
    bot.send_message(message.chat.id, "Вышел из админ панели")
    client_menu(message)

def get_product(message):
    user_data[message.chat.id]['product'] = message.text
    bot.send_message(message.chat.id, "Имя клиента:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data[message.chat.id]['name'] = message.text
    bot.send_message(message.chat.id, "Номер телефона:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_data[message.chat.id]['phone'] = message.text
    bot.send_message(message.chat.id, "Адрес доставки:")
    bot.register_next_step_handler(message, get_address)

def get_address(message):
    user_data[message.chat.id]['address'] = message.text
    bot.send_message(message.chat.id, "Сумма заказа (в сомони):")
    bot.register_next_step_handler(message, get_price)

def get_price(message):
    try:
        price = int(message.text)
    except:
        price = 0
    data = user_data[message.chat.id]
    data['price'] = price
    data['date'] = datetime.now().strftime('%d.%m.%Y')
    data['time'] = datetime.now().strftime('%H:%M')
    orders.append(data)
    bot.send_message(ADMIN_ID,
    f"🛒 НОВЫЙ ЗАКАЗ!\n\n"
    f"👤 Имя: {data['name']}\n"
    f"📱 Телефон: {data['phone']}\n"
    f"📦 Товар: {data['product']}\n"
    f"📍 Адрес: {data['address']}\n"
    f"💰 Сумма: {data['price']} сомони\n"
    f"🕐 Время: {data['time']}")
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Заказ добавлен!")
        admin_panel(message)
    else:
        bot.send_message(message.chat.id,
        "✅ Заказ принят!\n\nМы свяжемся с вами в течение 30 минут. Спасибо! 🙏")

bot.polling()

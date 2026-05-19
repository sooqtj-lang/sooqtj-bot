import os
import csv
import io
import telebot
from telebot import types
from datetime import datetime
import requests

# ==================== КОНФИГ ====================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7555325054"))
SHEETS_ID = os.getenv("SPREADSHEET_ID", "1RoLKPZQY675Bv16GoMZDW7Sv_s77s0lKu-s2mVj3qA8")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
DRIVER_IDS = set(
    int(x.strip())
    for x in os.getenv("DRIVER_IDS", "").split(",")
    if x.strip().isdigit()
)

bot = telebot.TeleBot(TOKEN)

# В памяти — только для сессий оформления заказа через бот
orders = []
user_data = {}

# ==================== GOOGLE SHEETS ====================
def get_products():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEETS_ID}/export?format=csv&sheet=Товары%20SOOQ"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        content = response.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        products = []
        for row in reader:
            if not any(row.values()):
                continue
            products.append(dict(row))
        return products
    except Exception as e:
        print(f"get_products error: {e}")
        return []


def save_order_to_sheets(order_data):
    try:
        import sheets as sh
        sh.create_order(
            order_data.get("chat_id"),
            order_data.get("name", ""),
            order_data.get("phone", ""),
            order_data.get("address", ""),
            "",
            order_data.get("product", ""),
            1,
            order_data.get("price", 0),
        )
    except Exception as e:
        print(f"save_order_to_sheets error: {e}")


# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def is_admin(message):
    return message.chat.id == ADMIN_ID


def is_driver(message):
    return message.chat.id in DRIVER_IDS


# ==================== СТАРТ ====================
@bot.message_handler(commands=["start"])
def start(message):
    if is_admin(message):
        admin_panel(message)
    else:
        client_menu(message)


# ==================== КЛИЕНТСКОЕ МЕНЮ ====================
def client_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if WEBAPP_URL:
        web_app_btn = types.KeyboardButton(
            "🛍 Открыть магазин SOOQ",
            web_app=types.WebAppInfo(url=WEBAPP_URL),
        )
        markup.add(web_app_btn)
    markup.add("🛍 Каталог товаров", "❓ Задать вопрос")
    markup.add("📦 Мой заказ")
    bot.send_message(
        message.chat.id,
        "Салом! 👋 Хуш омадед ба SOOQ.TJ!\n\n"
        "Электроника и бытовая техника из Китая 🇨🇳\n\n"
        "Выберите раздел:",
        reply_markup=markup,
    )


# ==================== КАТАЛОГ ====================
@bot.message_handler(func=lambda m: m.text == "🛍 Каталог товаров")
def catalog(message):
    bot.send_message(message.chat.id, "⏳ Загружаю каталог...")
    products = get_products()

    if not products:
        bot.send_message(message.chat.id,
                         "❌ Не удалось загрузить каталог.\nПопробуйте позже.")
        return

    markup = types.InlineKeyboardMarkup()
    for i, p in enumerate(products[:20]):
        name = p.get("Название (RU)") or p.get("col2") or f"Товар {i+1}"
        price = p.get("Продажная цена") or p.get("col6") or "—"
        markup.add(types.InlineKeyboardButton(f"{name} — {price} сом", callback_data=f"product_{i}"))

    bot.send_message(
        message.chat.id,
        f"🛍 *Каталог SOOQ.TJ*\n\n📦 Товаров в наличии: {len(products)}\nВыберите товар:",
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("product_"))
def product_detail(call):
    products = get_products()
    idx = int(call.data.split("_")[1])
    if idx >= len(products):
        bot.answer_callback_query(call.id, "Товар не найден")
        return

    p = products[idx]
    name = p.get("Название (RU)") or p.get("col2") or f"Товар {idx+1}"
    price = p.get("Продажная цена") or p.get("col6") or "—"
    qty = p.get("В наличии (шт)") or p.get("col9") or "—"
    desc = p.get("Категория") or p.get("col3") or ""

    text = (
        f"📦 *{name}*\n\n"
        f"💰 Цена: *{price} сомони*\n"
        f"📊 В наличии: {qty} шт.\n"
    )
    if desc:
        text += f"\n📝 {desc}\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 Заказать", callback_data=f"order_{idx}"))
    markup.add(types.InlineKeyboardButton("◀️ Назад к каталогу", callback_data="back_catalog"))

    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id,
        reply_markup=markup, parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda c: c.data == "back_catalog")
def back_to_catalog(call):
    products = get_products()
    markup = types.InlineKeyboardMarkup()
    for i, p in enumerate(products[:20]):
        name = p.get("Название (RU)") or p.get("col2") or f"Товар {i+1}"
        price = p.get("Продажная цена") or p.get("col6") or "—"
        markup.add(types.InlineKeyboardButton(f"{name} — {price} сом", callback_data=f"product_{i}"))

    bot.edit_message_text(
        f"🛍 *Каталог SOOQ.TJ*\n\n📦 Товаров: {len(products)}\nВыберите товар:",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup, parse_mode="Markdown",
    )


# ==================== ЗАКАЗ ИЗ КАТАЛОГА ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("order_"))
def order_from_catalog(call):
    products = get_products()
    idx = int(call.data.split("_")[1])
    p = products[idx]
    name = p.get("Название (RU)") or p.get("col2") or f"Товар {idx+1}"
    price = p.get("Продажная цена") or p.get("col6") or 0

    user_data[call.message.chat.id] = {"source": "client", "product": name, "price": price}
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✅ Выбран: *{name}*\n\nВведите ваше имя:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_name)


# ==================== ЗАКАЗ ВРУЧНУЮ ====================
@bot.message_handler(commands=["order"])
def order_manual(message):
    user_data[message.chat.id] = {"source": "client"}
    msg = bot.send_message(message.chat.id, "📦 Оформляем заказ!\n\nНапишите название товара:")
    bot.register_next_step_handler(msg, get_product)


@bot.message_handler(func=lambda m: m.text == "📦 Мой заказ" and not is_admin(m))
def my_order(message):
    msg = bot.send_message(message.chat.id, "📦 Напишите название товара:")
    user_data[message.chat.id] = {"source": "client"}
    bot.register_next_step_handler(msg, get_product)


@bot.message_handler(func=lambda m: m.text == "❓ Задать вопрос" and not is_admin(m))
def question(message):
    bot.send_message(message.chat.id, "❓ Напишите ваш вопрос — мы ответим в течение 30 минут!")


# ==================== СБОР ДАННЫХ ЗАКАЗА ====================
def get_product(message):
    user_data[message.chat.id]["product"] = message.text
    msg = bot.send_message(message.chat.id, "👤 Ваше имя:")
    bot.register_next_step_handler(msg, get_name)


def get_name(message):
    user_data[message.chat.id]["name"] = message.text
    msg = bot.send_message(message.chat.id, "📱 Номер телефона:")
    bot.register_next_step_handler(msg, get_phone)


def get_phone(message):
    user_data[message.chat.id]["phone"] = message.text
    msg = bot.send_message(message.chat.id, "📍 Адрес доставки:")
    bot.register_next_step_handler(msg, get_address)


def get_address(message):
    user_data[message.chat.id]["address"] = message.text
    data = user_data[message.chat.id]
    if data.get("price"):
        save_order(message, data["price"])
    else:
        msg = bot.send_message(message.chat.id, "💰 Сумма заказа (в сомони):")
        bot.register_next_step_handler(msg, get_price)


def get_price(message):
    try:
        price = int(message.text)
    except Exception:
        price = 0
    save_order(message, price)


def save_order(message, price):
    data = user_data[message.chat.id]
    data["price"] = price
    data["date"] = datetime.now().strftime("%d.%m.%Y")
    data["time"] = datetime.now().strftime("%H:%M")
    data["status"] = "⏳ В ожидании"
    data["chat_id"] = message.chat.id
    data["order_time"] = datetime.now().timestamp()
    orders.append(data)
    save_order_to_sheets(data)

    order_idx = len(orders) - 1

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.row(
        types.InlineKeyboardButton("⏳ В ожидании", callback_data=f"status_{order_idx}_waiting"),
        types.InlineKeyboardButton("🚚 В пути",     callback_data=f"status_{order_idx}_transit"),
    )
    admin_markup.row(
        types.InlineKeyboardButton("✅ Доставлено",  callback_data=f"status_{order_idx}_delivered"),
        types.InlineKeyboardButton("↩️ Возврат",    callback_data=f"status_{order_idx}_returned"),
    )

    bot.send_message(
        ADMIN_ID,
        f"🛒 *НОВЫЙ ЗАКАЗ #{order_idx + 1}!*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📦 Товар: {data['product']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"💰 Сумма: {data['price']} сомони\n"
        f"🕐 Время: {data['time']}",
        reply_markup=admin_markup,
        parse_mode="Markdown",
    )

    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Заказ добавлен!")
        admin_panel(message)
    else:
        client_markup = types.InlineKeyboardMarkup()
        client_markup.add(
            types.InlineKeyboardButton("🚀 Быстрая доставка (+30 сом)", callback_data=f"express_{order_idx}")
        )
        client_markup.add(
            types.InlineKeyboardButton("❌ Отменить заказ", callback_data=f"cancel_{order_idx}")
        )
        bot.send_message(
            message.chat.id,
            f"🎉 *Спасибо за покупку в SOOQ.TJ!*\n\n"
            f"Ваш заказ принят и будет доставлен в течение 24 часов.\n"
            f"Ожидайте звонка от нашего доставщика! 📦\n\n"
            f"_Отменить заказ можно в течение 1 часа_",
            reply_markup=client_markup,
            parse_mode="Markdown",
        )


# ==================== КНОПКИ КЛИЕНТА ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def cancel_order(call):
    order_idx = int(call.data.split("_")[1])
    if order_idx >= len(orders):
        bot.answer_callback_query(call.id, "Заказ не найден")
        return

    order = orders[order_idx]
    if order.get("chat_id") != call.message.chat.id:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return

    elapsed = datetime.now().timestamp() - order.get("order_time", 0)
    if elapsed > 3600:
        bot.answer_callback_query(call.id, "⏰ Время отмены истекло (1 час)")
        return

    orders[order_idx]["status"] = "❌ Отменён"
    try:
        bot.send_message(
            ADMIN_ID,
            f"❌ *Заказ #{order_idx + 1} отменён клиентом!*\n\n"
            f"👤 {order.get('name', '—')}\n"
            f"📦 {order.get('product', '—')}\n"
            f"📱 {order.get('phone', '—')}",
            parse_mode="Markdown",
        )
    except Exception:
        pass

    bot.answer_callback_query(call.id, "Заказ отменён")
    bot.edit_message_text(
        "❌ *Заказ успешно отменён.*\n\nЕсли передумаете — мы всегда здесь! 😊",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("express_"))
def express_delivery(call):
    order_idx = int(call.data.split("_")[1])
    if order_idx >= len(orders):
        bot.answer_callback_query(call.id, "Заказ не найден")
        return

    order = orders[order_idx]
    if order.get("chat_id") != call.message.chat.id:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return
    if orders[order_idx].get("express"):
        bot.answer_callback_query(call.id, "✅ Быстрая доставка уже активна")
        return

    orders[order_idx]["price"] = int(orders[order_idx].get("price", 0)) + 30
    orders[order_idx]["express"] = True
    orders[order_idx]["status"] = "🚀 Срочный"

    express_text = (
        f"🚀 *СРОЧНЫЙ ЗАКАЗ #{order_idx + 1}!*\n\n"
        f"👤 {order.get('name', '—')}\n"
        f"📱 {order.get('phone', '—')}\n"
        f"📦 {order.get('product', '—')}\n"
        f"📍 {order.get('address', '—')}\n"
        f"💰 {orders[order_idx]['price']} сомони (+30 срочная)"
    )
    try:
        bot.send_message(ADMIN_ID, express_text, parse_mode="Markdown")
    except Exception:
        pass

    bot.answer_callback_query(call.id, "🚀 Быстрая доставка активирована!")


# ==================== СТАТУСЫ (АДМИН) ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("status_"))
def update_status(call):
    if call.message.chat.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return

    parts = call.data.split("_")
    order_idx = int(parts[1])
    new_status = parts[2]

    status_map = {
        "waiting":   "⏳ В ожидании",
        "transit":   "🚚 В пути",
        "delivered": "✅ Доставлено",
        "returned":  "↩️ Возврат",
    }

    if order_idx >= len(orders):
        bot.answer_callback_query(call.id, "Заказ не найден")
        return

    orders[order_idx]["status"] = status_map.get(new_status, "—")
    status_text = status_map.get(new_status, "—")

    client_id = orders[order_idx].get("chat_id")
    if client_id and client_id != ADMIN_ID:
        try:
            bot.send_message(
                client_id,
                f"📦 *Обновление вашего заказа*\n\n"
                f"Товар: {orders[order_idx]['product']}\n"
                f"Статус: {status_text}",
                parse_mode="Markdown",
            )
        except Exception:
            pass

    bot.answer_callback_query(call.id, f"✅ {status_text}")


# ==================== АДМИН ПАНЕЛЬ ====================
@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if not is_admin(message):
        bot.send_message(message.chat.id, f"❌ Нет доступа! Ваш ID: {message.chat.id}")
        return
    admin_panel(message)


def admin_panel(message):
    today = datetime.now().strftime("%d.%m.%Y")
    today_orders = [o for o in orders if o.get("date") == today]
    today_sum = sum(o.get("price", 0) for o in today_orders)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if WEBAPP_URL:
        web_app_btn = types.KeyboardButton(
            "📊 Открыть панель управления",
            web_app=types.WebAppInfo(url=WEBAPP_URL),
        )
        markup.add(web_app_btn)
    markup.add("➕ Новый заказ", "📋 Все заказы")
    markup.add("📊 Статистика", "🛍 Обновить каталог")
    markup.add("🔙 Выход")

    bot.send_message(
        message.chat.id,
        f"👑 *АДМИН ПАНЕЛЬ — SOOQ.TJ*\n\n"
        f"📦 Заказов сегодня: {len(today_orders)}\n"
        f"💰 Сумма сегодня: {today_sum} сомони",
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: m.text == "➕ Новый заказ" and is_admin(m))
def admin_new_order(message):
    user_data[message.chat.id] = {"source": "admin"}
    msg = bot.send_message(message.chat.id, "📦 Новый заказ\n\nНазвание товара:")
    bot.register_next_step_handler(msg, get_product)


@bot.message_handler(func=lambda m: m.text == "📋 Все заказы" and is_admin(m))
def all_orders(message):
    if not orders:
        bot.send_message(message.chat.id, "📋 Заказов пока нет")
        return
    text = "📋 *ВСЕ ЗАКАЗЫ:*\n\n"
    for i, o in enumerate(orders[-15:], 1):
        text += (
            f"*#{i}* {o.get('date','—')} {o.get('time','')}\n"
            f"👤 {o.get('name','—')} | 📱 {o.get('phone','—')}\n"
            f"📦 {o.get('product','—')} | 💰 {o.get('price',0)} сом\n"
            f"📍 {o.get('address','—')}\n"
            f"🔘 {o.get('status','⏳ Новый')}\n\n"
        )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m))
def stats(message):
    admin_panel(message)


@bot.message_handler(func=lambda m: m.text == "🛍 Обновить каталог" and is_admin(m))
def refresh_catalog(message):
    products = get_products()
    bot.send_message(message.chat.id, f"✅ Каталог обновлён!\n📦 Товаров загружено: {len(products)}")


@bot.message_handler(func=lambda m: m.text == "🔙 Выход" and is_admin(m))
def exit_admin(message):
    client_menu(message)


# ==================== ПАНЕЛЬ ВОДИТЕЛЯ ====================
@bot.message_handler(commands=["driver"])
def driver_login(message):
    if message.chat.id in DRIVER_IDS:
        driver_panel(message)
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Нет доступа. Ваш ID: {message.chat.id}\n"
            f"Обратитесь к администратору для получения доступа.",
        )


def driver_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if WEBAPP_URL:
        web_app_btn = types.KeyboardButton(
            "🚚 Мои доставки",
            web_app=types.WebAppInfo(url=WEBAPP_URL),
        )
        markup.add(web_app_btn)
    markup.add("🚪 Выйти")

    bot.send_message(
        message.chat.id,
        f"🚚 *ПАНЕЛЬ ВОДИТЕЛЯ — SOOQ.TJ*\n\nВыберите действие:",
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: m.text == "🚪 Выйти" and is_driver(m))
def driver_logout(message):
    bot.send_message(message.chat.id, "👋 Вышли из панели водителя")
    client_menu(message)


# ==================== ЗАПУСК (только при прямом запуске) ====================
if __name__ == "__main__":
    print("🤖 SOOQ.TJ Bot запущен (polling mode)...")
    bot.polling(none_stop=True)

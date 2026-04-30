import os
import telebot
from telebot import types
from datetime import datetime
import requests
import json

# ==================== КОНФИГ ====================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8442941172
SHEETS_ID = "1cQFtfRJY0n5vb6p19OF96sWmFBffpE01"
DRIVER_PASSWORD = os.getenv("DRIVER_PASSWORD", "1234")  # пароль меняй в Railway Variables

bot = telebot.TeleBot(TOKEN)

# База данных (в памяти)
orders = []
user_data = {}
drivers = set()  # Telegram ID авторизованных доставщиков

# ==================== GOOGLE SHEETS ====================
def get_products():
    """Читаем товары из Google Sheets (публичный доступ)"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEETS_ID}/gviz/tq?tqx=out:json&sheet=Sheet1"
        response = requests.get(url, timeout=10)
        text = response.text
        # Убираем обёртку google.visualization.Query.setResponse(...)
        start = text.find('{')
        end = text.rfind('}') + 1
        data = json.loads(text[start:end])
        
        products = []
        rows = data['table']['rows']
        cols = data['table']['cols']
        
        for row in rows:
            if not row['c'] or not row['c'][0] or not row['c'][0].get('v'):
                continue
            product = {}
            for i, col in enumerate(cols):
                if i < len(row['c']) and row['c'][i]:
                    product[col['label'] or f'col{i}'] = row['c'][i].get('v', '')
                else:
                    product[col['label'] or f'col{i}'] = ''
            products.append(product)
        return products
    except Exception as e:
        print(f"Ошибка чтения таблицы: {e}")
        return []

def save_order_to_sheets(order_data):
    """Записываем заказ в Google Sheets (требует Service Account — пока логируем)"""
    print(f"ЗАКАЗ: {order_data}")
    # TODO: подключить gspread с Service Account для записи

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================
def is_admin(message):
    return message.chat.id == ADMIN_ID

def is_driver(message):
    return message.chat.id in drivers

# ==================== СТАРТ ====================
@bot.message_handler(commands=['start'])
def start(message):
    if is_admin(message):
        admin_panel(message)
    else:
        client_menu(message)

# ==================== КЛИЕНТСКОЕ МЕНЮ ====================
def client_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛍 Каталог товаров", "❓ Задать вопрос")
    markup.add("📦 Мой заказ")
    bot.send_message(
        message.chat.id,
        "Салом! 👋 Хуш омадед ба SOOQ.TJ!\n\n"
        "Электроника и бытовая техника из Китая 🇨🇳\n\n"
        "Выберите раздел:",
        reply_markup=markup
    )

# ==================== КАТАЛОГ ====================
@bot.message_handler(func=lambda m: m.text == "🛍 Каталог товаров" and not is_admin(m))
def catalog(message):
    products = get_products()
    if not products:
        bot.send_message(message.chat.id, "⏳ Загружаем каталог... Попробуйте через минуту.")
        return

    markup = types.InlineKeyboardMarkup()
    
    # Показываем первые 20 товаров кнопками
    for i, p in enumerate(products[:20]):
        # Пробуем разные названия колонок
        name = p.get('Название') or p.get('название') or p.get('name') or p.get('col0') or f"Товар {i+1}"
        price = p.get('Цена') or p.get('цена') or p.get('price') or p.get('col2') or '—'
        
        btn_text = f"{name} — {price} сом"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"product_{i}"))
    
    bot.send_message(
        message.chat.id,
        f"🛍 *Каталог SOOQ.TJ*\n\n📦 Товаров в наличии: {len(products)}\nВыберите товар:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("product_"))
def product_detail(call):
    products = get_products()
    idx = int(call.data.split("_")[1])
    if idx >= len(products):
        bot.answer_callback_query(call.id, "Товар не найден")
        return
    
    p = products[idx]
    name = p.get('Название') or p.get('название') or p.get('col0') or f"Товар {idx+1}"
    price = p.get('Цена') or p.get('цена') or p.get('col2') or '—'
    qty = p.get('Количество') or p.get('количество') or p.get('col3') or '—'
    desc = p.get('Описание') or p.get('описание') or p.get('col4') or ''

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
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "back_catalog")
def back_to_catalog(call):
    products = get_products()
    markup = types.InlineKeyboardMarkup()
    for i, p in enumerate(products[:20]):
        name = p.get('Название') or p.get('col0') or f"Товар {i+1}"
        price = p.get('Цена') or p.get('col2') or '—'
        markup.add(types.InlineKeyboardButton(f"{name} — {price} сом", callback_data=f"product_{i}"))
    
    bot.edit_message_text(
        f"🛍 *Каталог SOOQ.TJ*\n\n📦 Товаров: {len(products)}\nВыберите товар:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ==================== ЗАКАЗ ИЗ КАТАЛОГА ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("order_"))
def order_from_catalog(call):
    products = get_products()
    idx = int(call.data.split("_")[1])
    p = products[idx]
    name = p.get('Название') or p.get('col0') or f"Товар {idx+1}"
    price = p.get('Цена') or p.get('col2') or 0
    
    user_data[call.message.chat.id] = {
        'source': 'client',
        'product': name,
        'price': price
    }
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✅ Выбран: *{name}*\n\nВведите ваше имя:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_name)

# ==================== ЗАКАЗ ВРУЧНУЮ ====================
@bot.message_handler(commands=['order'])
def order_manual(message):
    user_data[message.chat.id] = {'source': 'client'}
    msg = bot.send_message(message.chat.id, "📦 Оформляем заказ!\n\nНапишите название товара:")
    bot.register_next_step_handler(msg, get_product)

@bot.message_handler(func=lambda m: m.text == "📦 Мой заказ" and not is_admin(m))
def my_order(message):
    msg = bot.send_message(message.chat.id, "📦 Напишите название товара который хотите заказать:")
    user_data[message.chat.id] = {'source': 'client'}
    bot.register_next_step_handler(msg, get_product)

@bot.message_handler(func=lambda m: m.text == "❓ Задать вопрос" and not is_admin(m))
def question(message):
    bot.send_message(message.chat.id, "❓ Напишите ваш вопрос — мы ответим в течение 30 минут!")

# ==================== СБОР ДАННЫХ ЗАКАЗА ====================
def get_product(message):
    user_data[message.chat.id]['product'] = message.text
    msg = bot.send_message(message.chat.id, "👤 Ваше имя:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    user_data[message.chat.id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "📱 Номер телефона:")
    bot.register_next_step_handler(msg, get_phone)

def get_phone(message):
    user_data[message.chat.id]['phone'] = message.text
    msg = bot.send_message(message.chat.id, "📍 Адрес доставки:")
    bot.register_next_step_handler(msg, get_address)

def get_address(message):
    user_data[message.chat.id]['address'] = message.text
    data = user_data[message.chat.id]
    
    # Если цена уже известна (из каталога) — сохраняем сразу
    if data.get('price'):
        save_order(message, data['price'])
    else:
        msg = bot.send_message(message.chat.id, "💰 Сумма заказа (в сомони):")
        bot.register_next_step_handler(msg, get_price)

def get_price(message):
    try:
        price = int(message.text)
    except:
        price = 0
    save_order(message, price)

def save_order(message, price):
    data = user_data[message.chat.id]
    data['price'] = price
    data['date'] = datetime.now().strftime('%d.%m.%Y')
    data['time'] = datetime.now().strftime('%H:%M')
    data['status'] = '⏳ Новый'
    data['chat_id'] = message.chat.id
    orders.append(data)
    
    # Сохраняем в Sheets (пока логируем)
    save_order_to_sheets(data)
    
    # Уведомление админу с кнопками статуса
    markup = types.InlineKeyboardMarkup()
    order_idx = len(orders) - 1
    markup.row(
        types.InlineKeyboardButton("🚚 В пути", callback_data=f"status_{order_idx}_transit"),
        types.InlineKeyboardButton("✅ Доставлен", callback_data=f"status_{order_idx}_delivered")
    )
    markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data=f"status_{order_idx}_cancelled"))
    
    bot.send_message(
        ADMIN_ID,
        f"🛒 *НОВЫЙ ЗАКАЗ #{order_idx + 1}!*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📦 Товар: {data['product']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"💰 Сумма: {data['price']} сомони\n"
        f"🕐 Время: {data['time']}",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Заказ добавлен!")
        admin_panel(message)
    else:
        bot.send_message(
            message.chat.id,
            "✅ *Заказ принят!*\n\n"
            "Мы свяжемся с вами в течение 30 минут.\n"
            "Спасибо за покупку! 🙏",
            parse_mode="Markdown"
        )

# ==================== СТАТУСЫ ДОСТАВКИ ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("status_"))
def update_status(call):
    if call.message.chat.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return
    
    parts = call.data.split("_")
    order_idx = int(parts[1])
    new_status = parts[2]
    
    status_map = {
        'transit': '🚚 В пути',
        'delivered': '✅ Доставлен',
        'cancelled': '❌ Отменён'
    }
    
    if order_idx < len(orders):
        orders[order_idx]['status'] = status_map.get(new_status, 'Неизвестно')
        
        # Уведомляем клиента
        client_id = orders[order_idx].get('chat_id')
        if client_id and client_id != ADMIN_ID:
            try:
                bot.send_message(
                    client_id,
                    f"📦 *Обновление заказа*\n\n"
                    f"Товар: {orders[order_idx]['product']}\n"
                    f"Статус: {status_map.get(new_status, '—')}",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        bot.answer_callback_query(call.id, f"Статус обновлён: {status_map.get(new_status)}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

# ==================== АДМИН ПАНЕЛЬ ====================
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    admin_panel(message)

def admin_panel(message):
    today = datetime.now().strftime('%d.%m.%Y')
    today_orders = [o for o in orders if o.get('date') == today]
    today_sum = sum(o.get('price', 0) for o in today_orders)
    month = datetime.now().strftime('%m.%Y')
    month_orders = [o for o in orders if o.get('date', '').endswith(month[2:])]
    month_sum = sum(o.get('price', 0) for o in month_orders)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Новый заказ", "📋 Все заказы")
    markup.add("📊 Статистика", "🛍 Обновить каталог")
    markup.add("🔙 Выход")
    
    bot.send_message(
        message.chat.id,
        f"👑 *АДМИН ПАНЕЛЬ — SOOQ.TJ*\n\n"
        f"📦 Заказов сегодня: {len(today_orders)}\n"
        f"💰 Сумма сегодня: {today_sum} сомони\n\n"
        f"📦 Заказов за месяц: {len(month_orders)}\n"
        f"💰 Сумма за месяц: {month_sum} сомони",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "➕ Новый заказ" and is_admin(m))
def admin_new_order(message):
    user_data[message.chat.id] = {'source': 'admin'}
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

# ==================== ПАНЕЛЬ ДОСТАВЩИКА ====================
@bot.message_handler(commands=['driver'])
def driver_login(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "🔐 Введите пароль:\n/driver <пароль>")
        return
    
    password = parts[1]
    if password == DRIVER_PASSWORD:
        drivers.add(message.chat.id)
        driver_panel(message)
    else:
        bot.send_message(message.chat.id, "❌ Неверный пароль!")

def driver_panel(message):
    # Считаем активные заказы
    active = [o for o in orders if o.get('status') in ['⏳ Новый', '🚚 В пути']]
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Мои заказы", "🔄 Обновить список")
    markup.add("🚪 Выйти")
    
    bot.send_message(
        message.chat.id,
        f"🚚 *ПАНЕЛЬ ДОСТАВЩИКА — SOOQ.TJ*\n\n"
        f"📦 Активных заказов: {len(active)}\n\n"
        f"Выберите действие:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text in ["📋 Мои заказы", "🔄 Обновить список"] and is_driver(m))
def driver_orders(message):
    active = [o for o in orders if o.get('status') in ['⏳ Новый', '🚚 В пути']]
    
    if not active:
        bot.send_message(message.chat.id, "📭 Активных заказов нет")
        return
    
    for i, order in enumerate(active):
        real_idx = orders.index(order)
        
        text = (
            f"📦 *Заказ #{real_idx + 1}*\n\n"
            f"👤 {order.get('name', '—')}\n"
            f"📱 {order.get('phone', '—')}\n"
            f"📍 {order.get('address', '—')}\n"
            f"🛍 {order.get('product', '—')}\n"
            f"💰 {order.get('price', 0)} сомони\n"
            f"🕐 {order.get('date', '')} {order.get('time', '')}\n"
            f"🔘 Статус: {order.get('status', '—')}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⏳ В ожидании", callback_data=f"dstatus_{real_idx}_waiting"),
            types.InlineKeyboardButton("🚚 В пути",     callback_data=f"dstatus_{real_idx}_transit")
        )
        markup.row(
            types.InlineKeyboardButton("✅ Доставлено",  callback_data=f"dstatus_{real_idx}_delivered"),
            types.InlineKeyboardButton("↩️ Возврат",    callback_data=f"dstatus_{real_idx}_returned")
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("dstatus_"))
def driver_update_status(call):
    if call.message.chat.id not in drivers:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return
    
    parts = call.data.split("_")
    order_idx = int(parts[1])
    new_status = parts[2]
    
    status_map = {
        'waiting':   '⏳ В ожидании',
        'transit':   '🚚 В пути',
        'delivered': '✅ Доставлено',
        'returned':  '↩️ Возврат'
    }
    
    if order_idx >= len(orders):
        bot.answer_callback_query(call.id, "Заказ не найден")
        return
    
    orders[order_idx]['status'] = status_map[new_status]
    status_text = status_map[new_status]
    
    # Уведомляем клиента
    client_id = orders[order_idx].get('chat_id')
    if client_id and client_id != ADMIN_ID:
        try:
            bot.send_message(
                client_id,
                f"📦 *Обновление вашего заказа*\n\n"
                f"Товар: {orders[order_idx]['product']}\n"
                f"Статус: {status_text}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    # Уведомляем админа
    try:
        bot.send_message(
            ADMIN_ID,
            f"🔔 *Статус заказа #{order_idx + 1} обновлён*\n\n"
            f"👤 {orders[order_idx].get('name','—')}\n"
            f"📦 {orders[order_idx].get('product','—')}\n"
            f"🔘 {status_text}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    bot.answer_callback_query(call.id, f"✅ {status_text}")
    
    # Обновляем кнопки в сообщении
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⏳ В ожидании", callback_data=f"dstatus_{order_idx}_waiting"),
        types.InlineKeyboardButton("🚚 В пути",     callback_data=f"dstatus_{order_idx}_transit")
    )
    markup.row(
        types.InlineKeyboardButton("✅ Доставлено",  callback_data=f"dstatus_{order_idx}_delivered"),
        types.InlineKeyboardButton("↩️ Возврат",    callback_data=f"dstatus_{order_idx}_returned")
    )
    
    try:
        bot.edit_message_text(
            call.message.text + f"\n\n✅ *Обновлено: {status_text}*",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except:
        pass

@bot.message_handler(func=lambda m: m.text == "🚪 Выйти" and is_driver(m))
def driver_logout(message):
    drivers.discard(message.chat.id)
    bot.send_message(message.chat.id, "👋 Вышли из панели доставщика")
    client_menu(message)

# ==================== ЗАПУСК ====================
print("🤖 SOOQ.TJ Bot запущен!")
bot.polling(none_stop=True)

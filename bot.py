import telebot
import sqlite3
from telebot import types

TOKEN = "8246247372:AAFRE-gWlN4DvQFCRsIyZCvly5dPBBG6Q1U"
bot = telebot.TeleBot(TOKEN)

user_lang = {}
user_data = {}
user_step = {}
user_income_type = {}

# === Инициализация базы данных ===
def init_db():
    db = sqlite3.connect("registratsiya.db")
    c = db.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            birth_year TEXT,
            language TEXT
        )
    """)
    db.commit()
    db.close()

# === Сохранение пользователя ===
def save_user(chat_id, first, last, year, lang):
    db = sqlite3.connect("registratsiya.db")
    c = db.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (telegram_id, first_name, last_name, birth_year, language)
        VALUES (?, ?, ?, ?, ?)
    """, (chat_id, first, last, year, lang))
    db.commit()
    db.close()

# === Проверка существования пользователя ===
def user_exists(chat_id):
    db = sqlite3.connect("registratsiya.db")
    c = db.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (chat_id,))
    result = c.fetchone()
    db.close()
    return result is not None

# === Создание кнопок по языку ===
def get_main_buttons(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "uz":
        markup.add(types.KeyboardButton("Kirim"), types.KeyboardButton("Chiqim"))
        markup.add(types.KeyboardButton("Xisobot"), types.KeyboardButton("Sozlamalar"))
    elif lang == "ru":
        markup.add(types.KeyboardButton("Доход"), types.KeyboardButton("Расход"))
        markup.add(types.KeyboardButton("Отчёт"), types.KeyboardButton("Настройки"))
    else:
        markup.add(types.KeyboardButton("Income"), types.KeyboardButton("Expense"))
        markup.add(types.KeyboardButton("Report"), types.KeyboardButton("Settings"))
    return markup

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("O'zbekcha", callback_data="lang_uz"),
        types.InlineKeyboardButton("Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("English", callback_data="lang_en")
    )

    bot.send_message(
        chat_id,
        f"Добро пожаловать, {message.from_user.first_name}!\n\nВыберите язык:",
        reply_markup=markup
    )

# === Обработка выбора языка ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_lang(call):
    chat_id = call.message.chat.id

    lang_map = {
        "lang_uz": ("uz", "Siz O'zbek tilini tanladingiz"),
        "lang_ru": ("ru", "Вы выбрали Русский язык"),
        "lang_en": ("en", "You selected English")
    }

    lang_code, lang_text = lang_map[call.data]
    user_lang[chat_id] = lang_code
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, lang_text)

    markup = get_main_buttons(lang_code)

    if user_exists(chat_id):
        if lang_code == "uz":
            bot.send_message(chat_id, "Siz allaqachon ro‘yxatdan o‘tgan ekansiz", reply_markup=markup)
        elif lang_code == "ru":
            bot.send_message(chat_id, "Вы уже зарегистрированы", reply_markup=markup)
        else:
            bot.send_message(chat_id, "You are already registered", reply_markup=markup)
        user_step[chat_id] = None  # Сбрасываем шаг
        return

    if lang_code == "uz":
        bot.send_message(chat_id, "Ismingizni kiriting:")
    elif lang_code == "ru":
        bot.send_message(chat_id, "Введите имя:")
    else:
        bot.send_message(chat_id, "Enter your first name:")

    user_step[chat_id] = "first_name"
    user_data[chat_id] = {}

# === Регистрация пользователя ===
@bot.message_handler(func=lambda message: user_step.get(message.chat.id) in ["first_name", "last_name", "birth_year"])
def register(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")
    step = user_step.get(chat_id)

    if step == "first_name":
        user_data[chat_id]["first_name"] = message.text
        user_step[chat_id] = "last_name"
        if lang == "uz":
            bot.send_message(chat_id, "Familiyangizni kiriting:")
        elif lang == "ru":
            bot.send_message(chat_id, "Введите фамилию:")
        else:
            bot.send_message(chat_id, "Enter your last name:")

    elif step == "last_name":
        user_data[chat_id]["last_name"] = message.text
        user_step[chat_id] = "birth_year"
        if lang == "uz":
            bot.send_message(chat_id, "Tug‘ilgan yilingizni kiriting:")
        elif lang == "ru":
            bot.send_message(chat_id, "Введите год рождения:")
        else:
            bot.send_message(chat_id, "Enter your year of birth:")

    elif step == "birth_year":
        if not message.text.isdigit():
            if lang == "uz":
                bot.send_message(chat_id, "Xato! Yil faqat raqam bo‘lishi kerak.")
            elif lang == "ru":
                bot.send_message(chat_id, "Ошибка! Год должен быть числом.")
            else:
                bot.send_message(chat_id, "Error! Year must be numeric.")
            return

        user_data[chat_id]["birth_year"] = message.text
        user_step[chat_id] = None  # Сбрасываем шаг

        first = user_data[chat_id]["first_name"]
        last = user_data[chat_id]["last_name"]
        year = user_data[chat_id]["birth_year"]
        save_user(chat_id, first, last, year, lang)

        markup = get_main_buttons(lang)

        if lang == "uz":
            bot.send_message(chat_id, f"Maʼlumotlaringiz:\nIsm: {first}\nFamiliya: {last}\nTug‘ilgan yil: {year}\nTil: O'zbek", reply_markup=markup)
        elif lang == "ru":
            bot.send_message(chat_id, f"Ваши данные:\nИмя: {first}\nФамилия: {last}\nГод: {year}\nЯзык: Русский", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"Your data:\nFirst name: {first}\nLast name: {last}\nYear: {year}\nLanguage: English", reply_markup=markup)

# === Обработка кнопок главного меню ===
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text.strip()
    lang = user_lang.get(chat_id, "ru")

    if lang == "uz":
        responses = {
            "Kirim": "Siz daromad bo‘limidasiz.",
            "Chiqim": "Siz xarajat bo‘limidasiz.",
            "Xisobot": "Sizning xisobotingiz.",
            "Sozlamalar": "Sozlamalar menyusi."
        }
        income_text = "Daromad turini tanlang:"
        btn_texts = ["Oylik", "Avans", "Qarz", "Yangi"]
    elif lang == "ru":
        responses = {
            "Доход": "Вы находитесь в разделе доходов.",
            "Расход": "Вы находитесь в разделе расходов.",
            "Отчёт": "Ваш отчёт.",
            "Настройки": "Меню настроек."
        }
        income_text = "Выберите тип дохода:"
        btn_texts = ["Зарплата", "Аванс", "Долг", "Новый"]
    else:
        responses = {
            "Income": "You are in the income section.",
            "Expense": "You are in the expense section.",
            "Report": "Your report section.",
            "Settings": "Settings menu."
        }
        income_text = "Select income type:"
        btn_texts = ["Salary", "Advance", "Debt", "New"]

    if text in ["Kirim", "Доход", "Income"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(btn_texts[0], callback_data="income_oylik"),
            types.InlineKeyboardButton(btn_texts[1], callback_data="income_avans")
        )
        markup.add(
            types.InlineKeyboardButton(btn_texts[2], callback_data="income_qarz"),
            types.InlineKeyboardButton(btn_texts[3], callback_data="income_yangi")
        )
        bot.send_message(chat_id, income_text, reply_markup=markup)
        return

    if text in responses:
        bot.send_message(chat_id, responses[text])

# === Главный обработчик сообщений (для зарегистрированных пользователей) ===
@bot.message_handler(func=lambda message: user_exists(message.chat.id) and user_step.get(message.chat.id) is None)
def main_handler(message):
    handle_buttons(message)

# === Обработка выбора типа дохода ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("income_"))
def handle_income_types(call):
    chat_id = call.message.chat.id
    income_type = call.data.split("_")[1]
    lang = user_lang.get(chat_id, "uz")

    income_names = {
        "uz": {"oylik": "Oylik", "avans": "Avans", "qarz": "Qarz", "yangi": "Yangi daromad turi"},
        "ru": {"oylik": "Зарплата", "avans": "Аванс", "qarz": "Долг", "yangi": "Новый тип дохода"},
        "en": {"oylik": "Salary", "avans": "Advance", "qarz": "Debt", "yangi": "New income type"}
    }

    text = income_names.get(lang, income_names["uz"]).get(income_type, "Unknown")
    user_income_type[chat_id] = text
    user_step[chat_id] = "income_sum"

    bot.answer_callback_query(call.id)

    if lang == "uz":
        bot.send_message(chat_id, "Summasini kiriting:")
    elif lang == "ru":
        bot.send_message(chat_id, "Введите сумму:")
    else:
        bot.send_message(chat_id, "Enter the amount:")

# === Обработка ввода суммы ===
@bot.message_handler(func=lambda m: user_step.get(m.chat.id) == "income_sum")
def handle_income_sum(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")

    amount_text = message.text.replace(" ", "").replace(",", "")
    if not amount_text.isdigit():
        if lang == "uz":
            bot.send_message(chat_id, "❌Noto‘g‘ri! Faqat raqam kiriting.")
        elif lang == "ru":
            bot.send_message(chat_id, "❌Ошибка! Введите только число.")
        else:
            bot.send_message(chat_id, "❌Error! Please enter numbers only.")
        return

    amount = int(amount_text)
    income_type = user_income_type.get(chat_id, "Доход")
    user_step[chat_id] = None

    if lang == "uz":
        bot.send_message(chat_id, "✅Summasi muvaffaqiyatli kiritildi.")
    elif lang == "ru":
        bot.send_message(chat_id, "✅Сумма успешно введена.")
    else:
        bot.send_message(chat_id, "✅Amount successfully entered.")

# === Запуск ===
init_db()
print("Bot ishga tushdi...")
bot.polling(none_stop=True)
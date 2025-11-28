import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from db_functions import (
    save_user, init_db, user_exists,
    save_income, get_category_id_by_name, create_category,
    update_user, get_user, get_user_created_categories, delete_category,
    get_user_categories, get_monthly_report_data  # ← вот эти две были пропущены!
)
from buttons import get_main_buttons, handle_buttons
from report import create_report_image  # ← обязательно!
import os  # ← для os.remove()

TOKEN = "8246247372:AAFRE-gWlN4DvQFCRsIyZCvly5dPBBG6Q1U"
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_lang = {}
user_data = {}
user_step = {}


# =============================================
#   КОМАНДЫ — ВСЕ ЧЕРЕЗ СЛЭШ (как /income)
# =============================================

@dp.message(Command("income"))
async def cmd_income(message: Message):
    chat_id = message.chat.id
    if not user_exists(chat_id):
        await message.answer("❗️Сначала пройдите регистрацию: /start")
        return
    
    lang = user_lang.get(chat_id, "ru")
    categories = get_user_categories(chat_id, lang, is_income=True)
    
    rows = []
    temp_row = []
    for cat_id, cat_name in categories:
        temp_row.append(InlineKeyboardButton(text=cat_name, callback_data=f"income_{cat_id}"))
        if len(temp_row) == 2:
            rows.append(temp_row)
            temp_row = []
    if temp_row:
        rows.append(temp_row)
    
    rows.append([InlineKeyboardButton(
        text={"ru": "🆕Новая категория", "uz": "🆕Yangi kategoriya", "en": "🆕New category"}[lang],
        callback_data="income_newcat"
    )])
    
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(
        {"ru": "🫴Выберите категорию дохода:", "uz": "🫴Daromad kategoriyasini tanlang:", "en": "🫴Select income category:"}[lang],
        reply_markup=markup
    )


@dp.message(Command("expense"))
async def cmd_expense(message: Message):
    chat_id = message.chat.id
    if not user_exists(chat_id):
        await message.answer("❗️Сначала пройдите регистрацию: /start")
        return
    
    lang = user_lang.get(chat_id, "ru")
    categories = get_user_categories(chat_id, lang, is_income=False)
    
    rows = []
    temp_row = []
    for cat_id, cat_name in categories:
        temp_row.append(InlineKeyboardButton(text=cat_name, callback_data=f"expense_{cat_id}"))
        if len(temp_row) == 2:
            rows.append(temp_row)
            temp_row = []
    if temp_row:
        rows.append(temp_row)
    
    rows.append([InlineKeyboardButton(
        text={"ru": "🆕Новая категория", "uz": "🆕Yangi kategoriya", "en": "🆕New category"}[lang],
        callback_data="expense_newcat"
    )])
    
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(
        {"ru": "🫴Выберите категорию расхода:", "uz": "🫴Xarajat kategoriyasini tanlang:", "en": "🫴Select expense category:"}[lang],
        reply_markup=markup
    )


@dp.message(Command("report"))
async def cmd_report(message: Message):
    chat_id = message.chat.id
    if not user_exists(chat_id):
        await message.answer("❗️Сначала пройдите регистрацию: /start")
        return
    
    lang = user_lang.get(chat_id, "ru")
    data = get_monthly_report_data(chat_id, lang)
    image_path = create_report_image(data, lang)
    
    await message.answer_photo(
        photo=FSInputFile(image_path),
        caption=f"{'📊Месячный отчёт' if lang=='ru' else '📊Oylik hisobot' if lang=='uz' else '📊Monthly Report'} — {data['month']}"
    )
    os.remove(image_path)


@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    chat_id = message.chat.id
    if not user_exists(chat_id):
        await message.answer("❗️Сначала пройдите регистрацию: /start")
        return
    
    lang = user_lang.get(chat_id, "ru")
    t = {
        "ru": "⚙️Настройки — выберите действие:",
        "uz": "⚙️Sozlamalar — amalni tanlang:",
        "en": "⚙️Settings — choose action:"
    }[lang]
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐Изменить язык" if lang=="ru" else "🌐Tilni o'zgartirish" if lang=="uz" else "🌐Change language", 
                              callback_data="settings_change_lang")],
        [InlineKeyboardButton(text="✍️Изменить данные" if lang=="ru" else "✍️Ma'lumotlarni tahrirlash" if lang=="uz" else "✍️Edit profile", 
                              callback_data="settings_edit_reg")],
        [InlineKeyboardButton(text="📊Управление категориями" if lang=="ru" else "📊Kategoriyalarni boshqarish" if lang=="uz" else "📊Manage categories", 
                              callback_data="settings_manage_cats")],
        [InlineKeyboardButton(text="◀️Назад" if lang=="ru" else "◀️Orqaga" if lang=="uz" else "◀️Back", 
                              callback_data="settings_back")]
    ])
    await message.answer(t, reply_markup=markup)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    lang = user_lang.get(message.chat.id, "ru")
    text = {
        "ru": "*Доступные команды:*\n\n"
              "/income — добавить доход\n"
              "/expense — добавить расход\n"
              "/report — месячный отчёт\n"
              "/settings — настройки\n"
              "/categories — все категории\n"
              "/help — эта справка",
        "uz": "*Mavjud buyruqlar:*\n\n"
              "/income — daromad qo'shish\n"
              "/expense — xarajat qo'shish\n"
              "/report — oylik hisobot\n"
              "/settings — sozlamalar\n"
              "/categories — barcha kategoriyalar\n"
              "/help — ushbu yordam",
        "en": "*Available commands:*\n\n"
              "/income — add income\n"
              "/expense — add expense\n"
              "/report — monthly report\n"
              "/settings — settings\n"
              "/categories — all categories\n"
              "/help — this help"
    }[lang]
    
    await message.answer(text, parse_mode="Markdown")


# =============================================
#   /start — ОБЯЗАТЕЛЬНО ПОСЛЕ ВСЕХ КОМАНД!
# =============================================

@dp.message(Command("start"))
async def start(message: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Uz🇺🇿 ", callback_data="lang_uz"),
            InlineKeyboardButton(text="Ru🇷🇺 ", callback_data="lang_ru"),
            InlineKeyboardButton(text="En🇺🇸 ", callback_data="lang_en")
        ]]
    )
    await message.answer(
        f"Добро пожаловать, {message.from_user.first_name}!🖐\n\n🌐Выберите язык:",
        reply_markup=markup
    )

# ---------------- Выбор языка ----------------
@dp.callback_query(F.data.startswith("lang_"))
async def callback_lang(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang_code = call.data.split("_")[1]

    texts = {
        "uz": "✅ Siz O'zbek tilini tanladingiz!",
        "ru": "✅ Вы выбрали Русский язык!",
        "en": "✅ You selected English!"
    }
    user_lang[chat_id] = lang_code
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(texts.get(lang_code, "Язык выбран"))

    markup = get_main_buttons(lang_code)

    if user_exists(chat_id):
        msg = {
            "ru": "ℹ️ Вы уже зарегистрированы",
            "uz": "ℹ️ Siz allaqachon ro'yxatdan o'tgansiz",
            "en": "ℹ️ You are already registered"
        }[lang_code]
        await call.message.answer(msg, reply_markup=markup)
        user_step[chat_id] = None
        return

    msg = {
        "ru": "Введите имя 📝:",
        "uz": "Ismingizni kiriting 📝:",
        "en": "Enter your first name 📝:"
    }[lang_code]
    await call.message.answer(msg)
    user_step[chat_id] = "first_name"
    user_data[chat_id] = {}

# ---------------- Регистрация ----------------
@dp.message(F.text, lambda m: user_step.get(m.chat.id) in ["first_name", "last_name", "birth_year"])
async def register(message: Message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")
    step = user_step[chat_id]

    if step == "first_name":
        user_data[chat_id]["first_name"] = message.text.strip()
        user_step[chat_id] = "last_name"
        await message.answer({
            "ru": "Введите фамилию 📝:",
            "uz": "Familiyangizni kiriting 📝:",
            "en": "Enter your last name 📝:"
        }[lang])

    elif step == "last_name":
        user_data[chat_id]["last_name"] = message.text.strip()
        user_step[chat_id] = "birth_year"
        await message.answer({
            "ru": "Введите год рождения 🎂:",
            "uz": "Tug‘ilgan yilingizni kiriting 🎂:",
            "en": "Enter your birth year 🎂:"
        }[lang])

    elif step == "birth_year":
        if not message.text.strip().isdigit():
            await message.answer({
                "ru": "Введите число! ⚠️",
                "uz": "Raqam kiriting! ⚠️",
                "en": "Enter a number! ⚠️"
            }[lang])
            return

        user_data[chat_id]["birth_year"] = message.text.strip()
        user_step[chat_id] = None

        save_user(
            chat_id,
            user_data[chat_id]["first_name"],
            user_data[chat_id]["last_name"],
            user_data[chat_id]["birth_year"],
            lang
        )

        await message.answer(
            {
                "ru": "✅ Регистрация завершена!",
                "uz": "✅ Ro'yxatdan o'tish tugadi!",
                "en": "✅ Registration completed!"
            }[lang],
            reply_markup=get_main_buttons(lang)
        )
        user_data.pop(chat_id, None)

# ---------------- Главное меню ----------------
@dp.message(F.text, lambda m: user_exists(m.chat.id) and user_step.get(m.chat.id) is None)
async def main_handler(message: Message):
    await handle_buttons(message, bot, user_lang)

# ---------------- ДОХОД ----------------
@dp.callback_query(F.data.startswith("income_"))
async def income_type(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = user_lang.get(chat_id, "ru")
    code = call.data.split("_")[1]

    await call.message.edit_reply_markup(reply_markup=None)

    if code == "newcat":
        user_step[chat_id] = "new_income_category"
        await call.message.answer({
            "ru": "Введите название новой категории дохода 💵:",
            "uz": "Yangi daromad kategoriyasi nomini kiriting 💵:",
            "en": "Enter the name of the new income category 💵:"
        }[lang])
        return

    user_data.setdefault(chat_id, {})["category_id"] = int(code)
    user_step[chat_id] = "income_sum"

    await call.message.answer({
        "ru": "Введите сумму 💰:",
        "uz": "Summani kiriting 💰:",
        "en": "Enter the amount 💰:"
    }[lang])

# ---------------- РАСХОД ----------------
@dp.callback_query(F.data.startswith("expense_"))
async def expense_type(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = user_lang.get(chat_id, "ru")
    code = call.data.split("_")[1]

    await call.message.edit_reply_markup(reply_markup=None)

    if code == "newcat":
        user_step[chat_id] = "new_expense_category"
        await call.message.answer({
            "ru": "Введите название новой категории расхода 💸:",
            "uz": "Yangi xarajat kategoriyasi nomini kiriting 💸:",
            "en": "Enter the name of the new expense category 💸:"
        }[lang])
        return

    user_data.setdefault(chat_id, {})["category_id"] = int(code)
    user_step[chat_id] = "expense_sum"

    await call.message.answer({
        "ru": "Введите сумму 💸:",
        "uz": "Summani kiriting 💸:",
        "en": "Enter the amount 💸:"
    }[lang])

# ---------------- Новая категория (ДИНАМИЧЕСКАЯ) ----------------
@dp.message(F.text, lambda m: user_step.get(m.chat.id) in ["new_income_category", "new_expense_category"])
async def new_category_handler(message: Message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")
    name = message.text.strip()

    if not name:
        await message.answer({
            "ru": "❌Название не может быть пустым!",
            "uz": "❌Nomi bo'sh bo'lmasligi kerak!",
            "en": "❌Name cannot be empty!"
        }[lang])
        return

    # Создаём новую категорию в базе
    telegram_id = message.from_user.id
    new_id = create_category(name, lang, telegram_id)


    # Сохраняем ID категории для ввода суммы
    user_data.setdefault(chat_id, {})["category_id"] = new_id

    # Переводим пользователя к вводу суммы
    if user_step[chat_id] == "new_income_category":
        user_step[chat_id] = "income_sum"
        await message.answer({
            "ru": "✅Категория дохода создана!\n\nВведите сумму 💸:",
            "uz": "✅Daromad kategoriyasi yaratildi!\n\nSummani kiriting 💸:",
            "en": "✅Income category created!\n\nEnter the amount 💸:"
        }[lang])
    else:
        user_step[chat_id] = "expense_sum"
        await message.answer({
            "ru": "✅Категория расхода создана!\n\nВведите сумму 💸:",
            "uz": "✅Xarajat kategoriyasi yaratildi!\n\nSummani kiriting 💸:",
            "en": "✅Expense category created!\n\nEnter the amount 💸:"
        }[lang])

# ---------------- Сохранение дохода ----------------
@dp.message(F.text, lambda m: user_step.get(m.chat.id) == "income_sum")
async def income_sum(message: Message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")
    text = message.text.replace(" ", "")

    if not text.isdigit():
        await message.answer({
            "ru": "Введите число! ⚠️",
            "uz": "Faqat raqam kiriting! ⚠️",
            "en": "Enter a number! ⚠️"
        }[lang])
        return

    amount = int(text)
    cat_id = user_data[chat_id].get("category_id")
    save_income(chat_id, income=amount, category_id=cat_id)
    user_step[chat_id] = None
    await message.answer({
        "ru": "✅ Доход сохранён!",
        "уз": "✅ Daromad saqlandi!",
        "en": "✅ Income saved!"
    }[lang],
    reply_markup=get_main_buttons(lang))

# ---------------- Сохранение расхода ----------------
@dp.message(F.text, lambda m: user_step.get(m.chat.id) == "expense_sum")
async def expense_sum(message: Message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")
    text = message.text.replace(" ", "")

    if not text.isdigit():
        await message.answer({
            "ru": "Введите число! ⚠️",
            "uz": "Faqat raqam kiriting! ⚠️",
            "en": "Enter a number! ⚠️"
        }[lang])
        return

    amount = int(text)
    cat_id = user_data[chat_id].get("category_id")
    save_income(chat_id, consumption=amount, category_id=cat_id)
    user_step[chat_id] = None
    await message.answer({
        "ru": "✅ Расход сохранён!",
        "uz": "✅ Xarajat saqlandi!",
        "en": "✅ Expense saved!"
    }[lang],
    reply_markup=get_main_buttons(lang))

# ---------------- SETTINGS / НАСТРОЙКИ ----------------
# Вход из handle_buttons: когда пользователь нажмёт кнопку "⚙️" мы будем показывать меню настроек.
# Обработка колбеков настроек:
@dp.callback_query(F.data.startswith("settings_"))
async def settings_callback(call: CallbackQuery):
    chat_id = call.message.chat.id
    lang = user_lang.get(chat_id, "ru")
    code = call.data.split("_", 1)[1]  # после settings_

    await call.message.edit_reply_markup(reply_markup=None)

    texts = {
        "ru": {
            "menu": "⚙️ Настройки — выберите действие:",
            "change_lang": "🌐Изменить язык",
            "edit_reg": "🗂Изменить регистрационные данные",
            "manage_cats": "📊Управление категориями",
            "back": "◀️Назад в меню"
        },
        "uz": {
            "menu": "⚙️ Sozlamalar — amalni tanlang:",
            "change_lang": "🌐Tilni o'zgartirish",
            "edit_reg": "🗂Ro'yxatga olishni tahrirlash",
            "manage_cats": "📊Kategoriyalarni boshqarish",
            "back": "◀️Asosiy menyuga qaytish"
        },
        "en": {
            "menu": "⚙️ Settings — choose action:",
            "change_lang": "🌐Change language",
            "edit_reg": "🗂Edit registration info",
            "manage_cats": "📊Manage categories",
            "back": "◀️Back to menu"
        }
    }
    t = texts.get(lang, texts["ru"])

    # Если пользователь открыл меню (code == "menu"), покажем опции
    if code == "menu":
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["change_lang"], callback_data="settings_change_lang")],
            [InlineKeyboardButton(text=t["edit_reg"], callback_data="settings_edit_reg")],
            [InlineKeyboardButton(text=t["manage_cats"], callback_data="settings_manage_cats")],
            [InlineKeyboardButton(text=t["back"], callback_data="settings_back")]
        ])
        await call.message.answer(t["menu"], reply_markup=markup)
        return

    # Смена языка: показываем те же кнопки языка, но пометим, что это из настроек
    if code == "change_lang":
        markup = InlineKeyboardMarkup(inline_keyboard=[[  # переиспользуем те же callback'ы lang_
            InlineKeyboardButton(text="Uz🇺🇿", callback_data="lang_uz"),
            InlineKeyboardButton(text="Ru🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton(text="En🇺🇸", callback_data="lang_en")
        ]])
        await call.message.answer(t["change_lang"], reply_markup=markup)
        return

    # Редактирование регистрации
    if code == "edit_reg":
        user = get_user(chat_id)
        if not user:
            await call.message.answer({
                "ru": "❌Пользователь не найден в базе.",
                "uz": "❌Foydalanuvchi topilmadi.",
                "en": "❌User not found."
            }[lang])
            return
        # user: (id, telegram_id, first_name, last_name, birth_year, language)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text={"ru":"📝Имя","uz":"📝Ism","en":"📝First name"}[lang], callback_data="settings_edit_first")],
            [InlineKeyboardButton(text={"ru":"📝Фамилия","uz":"📝Familiya","en":"📝Last name"}[lang], callback_data="settings_edit_last")],
            [InlineKeyboardButton(text={"ru":"🎂Год рождения","uz":"🎂Tug'ilgan yil","en":"🎂Birth year"}[lang], callback_data="settings_edit_year")],
            [InlineKeyboardButton(text={"ru":"◀️Назад","uz":"◀️Ortga","en":"◀️Back"}[lang], callback_data="settings_menu")]
        ])
        await call.message.answer({
            "ru": f"🗂Текущие данные:\n📝Имя: {user[2] or '-'}\n📝Фамилия: {user[3] or '-'}\n🎂Год рождения: {user[4] or '-'}\n\n🗳Выберите поле для редактирования:",
            "uz": f"🗂Hozirgi ma'lumotlar:\n📝Ism: {user[2] or '-'}\n📝Familiya: {user[3] or '-'}\n🎂Tug'ilgan yil: {user[4] or '-'}\n\n🗳Tahrirlash uchun maydonni tanlang:",
            "en": f"🗂Current data:\n📝First name: {user[2] or '-'}\n📝Last name: {user[3] or '-'}\n🎂Birth year: {user[4] or '-'}\n\n🗳Choose a field to edit:"
        }[lang], reply_markup=markup)
        return

    # Управление категориями — показать пользовательские категории и дать возможность удалить
    if code == "manage_cats":
        # Получаем категории, созданные пользователем (те, где хотя бы одно языковое поле NULL)
        cats = get_user_created_categories(chat_id, lang)
        if not cats:
            await call.message.answer({
                "ru": "❌Пользовательских категорий не найдено.",
                "uz": "❌Foydalanuvchi tomonidan yaratilgan kategoriya topilmadi.",
                "en": "❌No user-created categories found."
            }[lang])
            return
        rows = []
        for cat_id, name in cats:
            rows.append([InlineKeyboardButton(text=f"🗑 {name}", callback_data=f"settings_delcat_{cat_id}")])
        rows.append([InlineKeyboardButton(text={"ru":"◀️Назад","uz":"◀️Ortga","en":"◀️Back"}[lang], callback_data="settings_menu")])
        markup = InlineKeyboardMarkup(inline_keyboard=rows)
        await call.message.answer({
            "ru": "🫴Нажмите на категорию, чтобы удалить её:",
            "uz": "🫴O'chirish uchun kategoriyani bosing:",
            "en": "🫴Tap a category to delete it:"
        }[lang], reply_markup=markup)
        return

    # Назад в меню
    if code == "back" or code == "menu" or code == "settings_back":
        await call.message.answer(
    {"ru": "📝Главное меню", "uz": "📝Bosh menyu", "en": "📝Main menu"}[lang],
    reply_markup=get_main_buttons(lang)
)
        await call.message.answer({
            "ru": "📝Возвращаемся в главное меню.",
            "uz": "📝Asosiy menyuga qaytilmoqda.",
            "en": "📝Returning to main menu."
        }[lang])
        return

    # Удаление категории
    if code.startswith("delcat_") or call.data.startswith("settings_delcat_"):
        # Поддерживаем оба варианта
        cid = call.data.split("_")[-1]
        try:
            cid_int = int(cid)
        except:
            await call.message.answer({
                "ru": "🆔Некорректный ID категории.",
                "uz": "🆔Kategoriya ID noto'g'ri.",
                "en": "🆔Invalid category ID."
            }[lang])
            return
        telegram_id = call.from_user.id
        delete_category(cid_int, telegram_id)

        await call.message.answer({
            "ru": "🗑Категория удалена.",
            "uz": "🗑Kategoriya o'chirildi.",
            "en": "🗑Category deleted."
        }[lang])
        return

    # Редактирование полей регистрации - обработка нажатий
    if code == "edit_first" or code == "settings_edit_first":
        user_step[chat_id] = "edit_first_name"
        await call.message.answer({
            "ru": "📝Введите новое имя:",
            "uz": "📝Yangi ismni kiriting:",
            "en": "📝Enter new first name:"
        }[lang])
        return

    if code == "edit_last" or code == "settings_edit_last":
        user_step[chat_id] = "edit_last_name"
        await call.message.answer({
            "ru": "📝Введите новую фамилию:",
            "uz": "📝Yangi familiyani kiriting:",
            "en": "📝Enter new last name:"
        }[lang])
        return

    if code == "edit_year" or code == "settings_edit_year":
        user_step[chat_id] = "edit_birth_year"
        await call.message.answer({
            "ru": "🎂Введите новый год рождения:",
            "uz": "🎂Yangi tug'ilgan yilni kiriting:",
            "en": "🎂Enter new birth year:"
        }[lang])
        return

# ---------------- Обработка ввода при редактировании регистрации ----------------
@dp.message(F.text, lambda m: user_step.get(m.chat.id) in ["edit_first_name", "edit_last_name", "edit_birth_year"])
async def edit_registration_handler(message: Message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, "ru")
    step = user_step[chat_id]
    text = message.text.strip()

    user = get_user(chat_id)
    if not user:
        await message.answer({
            "ru": "❌Пользователь не найден в базе.",
            "uz": "❌Foydalanuvchi topilmadi.",
            "en": "❌User not found."
        }[lang])
        user_step[chat_id] = None
        return

    if step == "edit_first_name":
        update_user(chat_id, first_name=text)
        await message.answer({
            "ru": "✅Имя обновлено!",
            "uz": "✅Ism yangilandi!",
            "en": "✅First name updated!"
        }[lang], reply_markup=get_main_buttons(lang))
    elif step == "edit_last_name":
        update_user(chat_id, last_name=text)
        await message.answer({
            "ru": "✅Фамилия обновлена!",
            "uz": "✅Familiya yangilandi!",
            "en": "✅Last name updated!"
        }[lang], reply_markup=get_main_buttons(lang))
    elif step == "edit_birth_year":
        if not text.isdigit():
            await message.answer({
                "ru": "Введите число! ⚠️",
                "uz": "Raqam kiriting! ⚠️",
                "en": "Enter a number! ⚠️"
            }[lang])
            return
        update_user(chat_id, birth_year=text)
        await message.answer({
            "ru": "✅Год рождения обновлён!",
            "uz": "✅Tug'ilgan yil yangilandi!",
            "en": "✅Birth year updated!"
        }[lang], reply_markup=get_main_buttons(lang))

    user_step[chat_id] = None

# ---------------- Запуск бота ----------------
async def main():
    init_db()
    print("Bot запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
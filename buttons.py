from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from db_functions import get_monthly_report_data, get_user_categories  # ← вот так
from report import create_report_image
import os


def get_main_buttons(lang: str):
    texts = {
        "uz": ("Kirim 💵", "Chiqim 💸", "Xisobot 📊", "Sozlamalar ⚙️"),
        "ru": ("Доход 💵", "Расход 💸", "Отчёт 📊", "Настройки ⚙️"),
        "en": ("Income 💵", "Expense 💸", "Report 📊", "Settings ⚙️")
    }
    btns = texts.get(lang, texts["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btns[0]), KeyboardButton(text=btns[1])],
            [KeyboardButton(text=btns[2]), KeyboardButton(text=btns[3])]
        ],
        resize_keyboard=True
    )


# Замени ВЕСЬ handle_buttons на этот код:

async def handle_buttons(message, bot, user_lang: dict):
    chat_id = message.chat.id
    text = message.text.strip()
    lang = user_lang.get(chat_id, "ru")

    prompt_texts = {
        "income": {
            "ru": "🫴Выберите тип дохода:",
            "uz": "🫴Daromad turini tanlang:",
            "en": "🫴Select income type:"
        },
        "expense": {
            "ru": "🫴Выберите тип расхода:",
            "uz": "🫴Xarajat turini tanlang:",
            "en": "🫴Select expense type:"
        }
    }

    text = message.text.strip()

    # ДОХОД
    if text.endswith("💵"):
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
        new_btn_text = {"ru": "🆕Новый", "uz": "🆕Yangi", "en": "🆕New"}[lang]
        rows.append([InlineKeyboardButton(text=new_btn_text, callback_data="income_newcat")])
        markup = InlineKeyboardMarkup(inline_keyboard=rows)
        await message.answer("🫴Выберите тип дохода:", reply_markup=markup)

    # РАСХОД
    elif text.endswith("💸"):
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
        new_btn_text = {"ru": "🆕Новый", "uz": "🆕Yangi", "en": "🆕New"}[lang]
        rows.append([InlineKeyboardButton(text=new_btn_text, callback_data="expense_newcat")])
        markup = InlineKeyboardMarkup(inline_keyboard=rows)
        await message.answer("🫴Выберите тип расхода:", reply_markup=markup)

    # ОТЧЁТ — ВОТ ЭТО ОБЯЗАТЕЛЬНО ДОБАВЬ!
    elif text.endswith("📊") or "Отчёт" in text or "Xisobot" in text or "Report" in text:
        data = get_monthly_report_data(chat_id, lang)
        image_path = create_report_image(data, lang)
        await message.answer_photo(
            photo=FSInputFile(image_path),
            caption=f"📊Месячный отчёт — {data['month']}"
        )
        os.remove(image_path)

    # НАСТРОЙКИ
    elif text.endswith("⚙️"):
        # Покажем меню настроек — вызываем колбек с префиксом settings_
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
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["change_lang"], callback_data="settings_change_lang")],
            [InlineKeyboardButton(text=t["edit_reg"], callback_data="settings_edit_reg")],
            [InlineKeyboardButton(text=t["manage_cats"], callback_data="settings_manage_cats")],
            [InlineKeyboardButton(text=t["back"], callback_data="settings_back")]
        ])
        await message.answer(t["menu"], reply_markup=markup)

    else:
        # На случай иных текстов — ничего не делаем (или можно сообщить)
        await message.answer({
            "ru": "❌Неизвестная команда. Используйте клавиатуру.",
            "uz": "❌Noma'lum buyruq. Iltimos tugmalardan foydalaning.",
            "en": "❌Unknown command. Please use the keyboard."
        }[lang])
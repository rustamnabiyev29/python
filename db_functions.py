import sqlite3
from datetime import datetime

DB_NAME = "registratsiya.db"

def init_db():
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        first_name TEXT, last_name TEXT, birth_year TEXT, language TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        date TEXT,
        type INTEGER,
        category INTEGER,
        amount INTEGER
    )""")

    # ДОБАВЛЕНО: telegram_id для персональных категорий
    c.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        ru_name TEXT,
        uz_name TEXT,
        en_name TEXT
    )""")

    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO categories (telegram_id, ru_name, uz_name, en_name) VALUES (?, ?, ?, ?)", [
            (None, "Зарплата", "Oylik", "Salary"),
            (None, "Аванс", "Avans", "Advance"),
            (None, "Долг", "Qarz", "Debt"),
            (None, "Покупки", "Bozorlik", "Purchases"),
            (None, "Коммунальные услуги", "Kommunalka", "Utilities"),
            (None, "Контракт", "Kontrakt", "Contract")
        ])

    db.commit()
    db.close()

def user_exists(chat_id):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute("SELECT 1 FROM users WHERE telegram_id = ?", (chat_id,))
    res = c.fetchone() is not None
    db.close()
    return res

def save_user(chat_id, first, last, year, lang):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute("INSERT OR IGNORE INTO users (telegram_id, first_name, last_name, birth_year, language) VALUES (?, ?, ?, ?, ?)",
              (chat_id, first, last, year, lang))
    c.execute("UPDATE users SET first_name = ?, last_name = ?, birth_year = ?, language = ? WHERE telegram_id = ?",
              (first, last, year, lang, chat_id))
    db.commit()
    db.close()

def update_user(chat_id, first_name=None, last_name=None, birth_year=None, language=None):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    updates = []
    params = []
    if first_name is not None:
        updates.append("first_name = ?")
        params.append(first_name)
    if last_name is not None:
        updates.append("last_name = ?")
        params.append(last_name)
    if birth_year is not None:
        updates.append("birth_year = ?")
        params.append(birth_year)
    if language is not None:
        updates.append("language = ?")
        params.append(language)
    if updates:
        params.append(chat_id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
        c.execute(sql, tuple(params))
        db.commit()
    db.close()

def get_user(telegram_id):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute("SELECT id, telegram_id, first_name, last_name, birth_year, language FROM users WHERE telegram_id = ?", (telegram_id,))
    row = c.fetchone()
    db.close()
    return row

def save_income(telegram_id, income=None, consumption=None, category_id=None):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d")

    if income is not None:
        type_val = 1
        amount = income
    elif consumption is not None:
        type_val = 2
        amount = consumption
    else:
        return

    c.execute("INSERT INTO income (telegram_id, date, type, category, amount) VALUES (?, ?, ?, ?, ?)",
              (telegram_id, date_now, type_val, category_id, amount))
    db.commit()
    db.close()

def get_category_id_by_name(name, lang):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    col = {"ru": "ru_name", "uz": "uz_name", "en": "en_name"}[lang]
    c.execute(f"SELECT id FROM categories WHERE {col} = ?", (name,))
    row = c.fetchone()
    db.close()
    return row[0] if row else None

# ДОБАВИЛ telegram_id В АРГУМЕНТЫ
def create_category(name, lang, telegram_id):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()

    ru = uz = en = None
    if lang == "ru": ru = name
    elif lang == "uz": uz = name
    else: en = name

    c.execute("INSERT INTO categories (telegram_id, ru_name, uz_name, en_name) VALUES (?, ?, ?, ?)",
              (telegram_id, ru, uz, en))

    db.commit()
    new_id = c.lastrowid
    db.close()
    return new_id

def get_monthly_report_data(telegram_id, lang):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    col = {"ru": "ru_name", "uz": "uz_name", "en": "en_name"}[lang]

    today = datetime.now()
    year_month = today.strftime("%Y-%m")
    start_date = f"{year_month}-01"
    if today.month == 2:
        end_day = 29 if today.year % 4 == 0 else 28
    elif today.month in [4, 6, 9, 11]:
        end_day = 30
    else:
        end_day = 31
    end_date = f"{year_month}-{end_day:02d}"

    c.execute(f"""
        SELECT income.date, income.type, income.amount, categories.{col} AS category_name
        FROM income
        LEFT JOIN categories ON income.category = categories.id
        WHERE income.telegram_id = ? AND income.date BETWEEN ? AND ?
        ORDER BY income.date ASC
    """, (telegram_id, start_date, end_date))

    rows = c.fetchall()

    c.execute("SELECT SUM(amount) FROM income WHERE telegram_id = ? AND type = 1 AND date LIKE ?", (telegram_id, year_month + '%'))
    total_income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM income WHERE telegram_id = ? AND type = 2 AND date LIKE ?", (telegram_id, year_month + '%'))
    total_expense = c.fetchone()[0] or 0

    db.close()

    month_names = {
        "ru": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
        "uz": ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    }
    month_str = month_names.get(lang, month_names["ru"])[today.month - 1] + " " + str(today.year)

    return {
        "rows": rows,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "month": month_str,
        "period": f"1.{today.month:02d}.{today.year} – {today.day:02d}.{today.month:02d}.{today.year}"
    }

def get_user_categories(telegram_id, lang="ru", is_income=True):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    
    col = {"ru": "ru_name", "uz": "uz_name", "en": "en_name"}[lang]

    type_val = 1 if is_income else 2
    c.execute(f"""
        SELECT DISTINCT categories.id, {col}
        FROM income
        JOIN categories ON income.category = categories.id
        WHERE income.telegram_id = ? AND income.type = ?
        ORDER BY categories.id
    """, (telegram_id, type_val))
    
    rows = c.fetchall()

    result = []
    seen_ids = set()

    for cat_id, name in rows:
        if name and name.strip():
            result.append((cat_id, name.strip()))
            seen_ids.add(cat_id)

    default_names = {
        "ru": {1: "Зарплата", 2: "Аванс", 3: "Долг", 4: "Покупки", 5: "Коммунальные услуги", 6: "Контракт"},
        "uz": {1: "Oylik",     2: "Avans",  3: "Qarz",  4: "Bozorlik",   5: "Kommunalka",        6: "Kontrakt"},
        "en": {1: "Salary",    2: "Advance", 3: "Debt", 4: "Purchases",  5: "Utilities",         6: "Contract"}
    }[lang]

    income_ids  = {1, 2, 3}
    expense_ids = {3, 4, 5, 6}
    allowed_ids = income_ids if is_income else expense_ids

    for cat_id in allowed_ids:
        if cat_id not in seen_ids:
            result.append((cat_id, default_names[cat_id]))

    db.close()
    return result

def get_user_created_categories(telegram_id, lang="ru"):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()

    # ТЕПЕРЬ выводим только категории ПОЛЬЗОВАТЕЛЯ
    c.execute("SELECT id, ru_name, uz_name, en_name FROM categories WHERE telegram_id = ? ORDER BY id",
              (telegram_id,))

    rows = c.fetchall()
    result = []
    for r in rows:
        cid, ru, uz, en = r
        name = None
        if lang == "ru" and ru: name = ru
        if lang == "uz" and uz: name = uz
        if lang == "en" and en: name = en
        if not name:
            name = ru or uz or en or f"Категория {cid}"
        result.append((cid, name))

    db.close()
    return result

def delete_category(cat_id, telegram_id):
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()

    c.execute("UPDATE income SET category = NULL WHERE category = ?", (cat_id,))

    # УДАЛЯЕТ только если владелец совпадает
    c.execute("DELETE FROM categories WHERE id = ? AND telegram_id = ?", (cat_id, telegram_id))

    db.commit()
    db.close()

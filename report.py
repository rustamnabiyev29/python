# report.py
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def create_report_image(data, lang="ru"):
    width, height = 1200, 2000
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 60)
        font_header = ImageFont.truetype("arialbd.ttf", 40)
        font_text = ImageFont.truetype("arial.ttf", 36)
    except:
        font_title = font_header = font_text = ImageFont.load_default()

    # Словарь переводов
    translations = {
        "ru": {
            "report_title": "Месячный отчёт",
            "date": "Дата",
            "type": "Тип",
            "amount": "Сумма",
            "category": "Категория",
            "income": "Доход",
            "expense": "Расход",
            "balance": "Остаток",
            "period": "Период"
        },
        "uz": {
            "report_title": "Oylik hisobot",
            "date": "Sana",
            "type": "Tur",
            "amount": "Summasi",
            "category": "Kategoriya",
            "income": "Daromad",
            "expense": "Xarajat",
            "balance": "Qoldiq",
            "period": "Davr"
        },
        "en": {
            "report_title": "Monthly Report",
            "date": "Date",
            "type": "Type",
            "amount": "Amount",
            "category": "Category",
            "income": "Income",
            "expense": "Expense",
            "balance": "Balance",
            "period": "Period"
        }
    }

    tr = translations.get(lang, translations["ru"])

    y = 60

    # Заголовок
    draw.text((width // 2, y), tr["report_title"], font=font_title, fill="black", anchor="mm")
    y += 90
    draw.text((width // 2, y), data["month"], font=font_header, fill="black", anchor="mm")
    y += 120

    # Колонки
    col_date = 60
    col_type = 270
    col_amount = 520
    col_cat = 780
    row_height = 55

    # ------------------------
    # Таблица операций
    # ------------------------
    table_start_y = y
    table_height = row_height * (len(data["rows"]) + 1)
    draw.rectangle((col_date-10, table_start_y-10, col_cat+350, table_start_y + table_height), outline="black", width=3)

    # Заголовки
    draw.text((col_date, y), tr["date"], font=font_header, fill="black")
    draw.text((col_type, y), tr["type"], font=font_header, fill="black")
    draw.text((col_amount, y), tr["amount"], font=font_header, fill="black")
    draw.text((col_cat, y), tr["category"], font=font_header, fill="black")
    y += row_height
    draw.line((col_date-10, y, col_cat+350, y), fill="black", width=3)

    # Вертикальные линии
    draw.line((col_date-10, table_start_y-10, col_date-10, table_start_y + table_height), fill="black", width=3)
    draw.line((col_type-20, table_start_y-10, col_type-20, table_start_y + table_height), fill="black", width=3)
    draw.line((col_amount-20, table_start_y-10, col_amount-20, table_start_y + table_height), fill="black", width=3)
    draw.line((col_cat-20, table_start_y-10, col_cat-20, table_start_y + table_height), fill="black", width=3)
    draw.line((col_cat+350, table_start_y-10, col_cat+350, table_start_y + table_height), fill="black", width=3)

    # Данные
    for date_str, typ, amount, cat in data["rows"]:
        date_disp = f"{date_str[8:10]}.{date_str[5:7]}.{date_str[0:4]}"
        type_disp = tr["income"] if typ == 1 else tr["expense"]

        draw.text((col_date, y), date_disp, font=font_text, fill="black")
        draw.text((col_type, y), type_disp, font=font_text, fill="black")
        draw.text((col_amount, y), f"{amount:,}".replace(",", " "), font=font_text, fill="black")
        draw.text((col_cat, y), cat if cat else "-", font=font_text, fill="black")
        y += row_height
        draw.line((col_date-10, y, col_cat+350, y), fill="black", width=2)

    y += 120

        # ------------------------
    # Итоги (вторая таблица того же размера, что и первая, две колонки)
    # ------------------------
    table2_start_y = y
    rows2 = 4
    table2_height = row_height * (rows2 + 1)

    # Используем те же левые и правые границы, что и для первой таблицы
    table_left = col_date - 10
    table_right = col_cat + 350
    center_split = (table_left + table_right) // 2  # разделение пополам

    # Рисуем рамку
    draw.rectangle((table_left, table2_start_y-10, table_right, table2_start_y + table2_height), outline="black", width=3)

    # Заголовки (2 колонки)
    # Позиции заголовков: немного внутрь от левой/центральной линий
    header_x_left = table_left + 20
    header_x_right = center_split + 20

    draw.text((header_x_left, y), tr["type"], font=font_header, fill="black")
    draw.text((header_x_right, y), tr["amount"], font=font_header, fill="black")
    y += row_height
    draw.line((table_left, y, table_right, y), fill="black", width=3)

    # Вертикальные линии (левая, центральная, правая)
    draw.line((table_left, table2_start_y-10, table_left, table2_start_y + table2_height), fill="black", width=3)
    draw.line((center_split, table2_start_y-10, center_split, table2_start_y + table2_height), fill="black", width=3)
    draw.line((table_right, table2_start_y-10, table_right, table2_start_y + table2_height), fill="black", width=3)

    # Данные для итоговой таблицы (тип | значение)
    vals = [
        (tr["income"], f"{data['total_income']:,}".replace(",", " ")),
        (tr["expense"], f"{data['total_expense']:,}".replace(",", " ")),
        (tr["balance"], f"{data['balance']:,}".replace(",", " ")),
        (tr["period"], data["period"]),
    ]

    for t, v in vals:
        draw.text((header_x_left, y), t, font=font_text, fill="black")
        # Для периода (текст длинный) пусть будет обрезка по правому столбцу — текст начнётс я в правой колонке
        draw.text((header_x_right, y), v, font=font_text, fill="black")
        y += row_height
        draw.line((table_left, y, table_right, y), fill="black", width=2)
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    return filename

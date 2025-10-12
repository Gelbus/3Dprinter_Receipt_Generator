import os
import re
import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A6
from datetime import datetime
from typing import Dict
from config import executor, customer





def extract_filament_weight(gcode_path):
    with open(gcode_path, 'r', encoding='utf-8') as file:
        gcode_content = file.read()

    # Поиск шаблона для веса в граммах
    pattern = r"filament used\s*\[g\]\s*=\s*(\d+\.\d+)"
    match = re.search(pattern, gcode_content)

    if match:
        weight = float(match.group(1))
        return weight
    else:
        return None

def generate_pdf_receipt(data: Dict[str, int],
                         price: float,
                         executor: str,
                         customer: str) -> None:
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        font_name = 'DejaVuSans'
        font_bold = 'DejaVuSans-Bold'
    except:
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'

    title = "Квитанция об оплате"

    total_price = 0
    date = datetime.today().date()

    c = canvas.Canvas(f"{date}.pdf", pagesize=A6)
    width, height = A6
    # Заголовок
    c.setFont(font_bold, 16)
    title_width = c.stringWidth(title, font_bold, 16)
    c.drawString((width - title_width) / 2, height - 20, title)

    # Список изделий
    c.setFont(font_bold, 12)
    c.drawString(15, height - 45, "Список печатаемых изделий")

    # Цена за грамм
    c.setFont(font_name, 10)
    c.drawString(15, height - 65, f"Цена за грамм: {price} руб.")

    # Список деталей
    y_position = height - 85
    for key, value in data.items():

        elem_price = value * price
        total_price += elem_price

        c.setFont(font_name, 10)
        c.drawString(15, y_position, f"{key} - {value} г. - {elem_price} руб.")
        y_position -= 15

    # Итого
    c.setFont(font_bold, 12)
    c.drawString(15, y_position - 10, f"ИТОГО: {total_price} руб.")

    # Надписи внизу справа
    c.setFont(font_name, 10)
    c.drawString(width - 150, 30, f"Исполнитель: {executor}")
    c.drawString(width - 150, 15, f"Заказчик: {customer}")

    c.save()
    print(f"Чек создан: {date}.pdf")

def main():
    path = "./data"
    files = os.listdir(path)

    data = dict()

    for file in files:
        weight = extract_filament_weight(f"{path}/{file}")
        if weight is not None:
            data[file.split("_PETG")[0]] = math.ceil(weight)
            print(f"Вес модели: {math.ceil(weight)} г")
        else:
            print("Данные о весе не найдены в G-code")

    generate_pdf_receipt(
        data,
        2,
        executor,
        customer
    )

if __name__ == "__main__":
    main()

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os


class Receipt:
    def __init__(self):
        self.doc = SimpleDocTemplate("data/reports/output.pdf", pagesize=A4)
        self.styles = getSampleStyleSheet()

        font_path = "C:/Windows/Fonts/arial.ttf"
        pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))

        self.custom_styles = {}

        self.story = []

        self.init_styles()

        self.table = None
        self.table_data = []
        self.table_pref = []
        self.parsed_text = [
            ["d1", "3"],
            ["d2", "3"],
            ["d3", "4"],
            ["d4", "3"],
            ["d5", "5"],
            ["d6", "10"],
            ["d7", "3"],
            ["d8", "1"]
        ]
        self.parts = [
            [0, 2, 3, 4, 1, 6],
            [5, 7]
        ]
        self.parts_materials = [
            "PETG",
            "PLA"
        ]
        self.parts_weight = [
            100,
            250
        ]
        self.material_price = {
            "PETG": 3,
            "PLA": 5
        }
        self.final_sum: int = 0

    def set_table_preferences(self):
        self.table_pref = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'ArialUnicode'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ] + self.table_pref

        self.table.setStyle(TableStyle(self.table_pref))

    def generate_table(self):
        self.table_data = [
            ["Наименование\nизделия",
             "Количество,\n шт.", "Материал",
             "Масса,\n г.",
             "Цена\nза грамм,\nр/г",
             "Цена,\nр.", ],
        ]
        start_pos = 1
        end_pos = 1
        for i in range(len(self.parts)):
            for detail_num in self.parts[i]:
                if detail_num == self.parts[i][0]:

                    price = self.parts_weight[i] * self.material_price[self.parts_materials[i]]
                    self.final_sum += price
                    self.table_data.append(
                        [self.parsed_text[detail_num][0],
                         self.parsed_text[detail_num][1],
                         self.parts_materials[i],
                         self.parts_weight[i],
                         self.material_price[self.parts_materials[i]],
                         price
                         ]
                    )
                    end_pos += 1
                else:
                    self.table_data.append(
                        [self.parsed_text[detail_num][0],
                         self.parsed_text[detail_num][1]
                         ]
                    )
                    end_pos += 1
            self.table_pref.append(('SPAN', (2, start_pos), (2, end_pos - 1)))
            self.table_pref.append(('SPAN', (3, start_pos), (3, end_pos - 1)))
            self.table_pref.append(('SPAN', (4, start_pos), (4, end_pos - 1)))
            self.table_pref.append(('SPAN', (5, start_pos), (5, end_pos - 1)))
            start_pos = end_pos


    def generate_report(self):
        # Заголовок
        self.story.append(Paragraph("Квитанция об оплате", self.custom_styles["title_style"]))
        self.story.append(Paragraph("№ 000.000.000", self.custom_styles["title_style"]))

        # Таблица
        self.generate_table()
        self.table = Table(self.table_data, colWidths=[150, 80, 60, 60, 50])
        self.set_table_preferences()
        self.story.append(self.table)

        # Итог
        self.story.append(Paragraph(f"Итого: {self.final_sum} руб.",  self.custom_styles["bold_style"]))
        self.story.append(Spacer(1, 20))

        # Подписи
        today = datetime.now().strftime("%d.%m.%Y")
        customer = Paragraph(f"Заказчик: {1}",  self.custom_styles["sign_style"])
        executor = Paragraph(f"Исполнитель: {1}", self.custom_styles["sign_style"])
        date = Paragraph(f"Дата печати: {today}", self.custom_styles["sign_style"])
        self.story.append(KeepTogether([executor, customer, date]))

        # Сбор в PDF
        self.doc.build(self.story)

    def init_styles(self):
        self.custom_styles["title_style"] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontName='ArialUnicode',
            fontSize=18,
            spaceAfter=14
        )
        self.custom_styles["normal_style"] = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontName='ArialUnicode',
            fontSize=12,
            spaceAfter=12
        )
        self.custom_styles["sign_style"] = ParagraphStyle(
            'CustomItalic',
            parent=self.styles['Italic'],
            fontName='ArialUnicode',
            fontSize=12,
            spaceAfter=5
        )
        self.custom_styles["bold_style"] = ParagraphStyle(
            'Customh3',
            parent=self.styles['h3'],
            fontName='ArialUnicode',
            fontSize=14,
            spaceAfter=12
        )

if __name__ == "__main__":
    receipt = Receipt()
    receipt.generate_report()

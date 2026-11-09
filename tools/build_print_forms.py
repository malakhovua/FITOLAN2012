"""Будує нові макети друкованих форм (*.mxl) у conf/.

Запуск з кореня репозиторію: python3 tools/build_print_forms.py
Повторний запуск перезаписує макети з цього опису — правки макетів робити тут, а не в Конфігураторі
(або після правки в Конфігураторі перенести їх сюди).

- ПриходнаяНакладнаяЗапасы/АктПриймання.mxl — Додаток 1 до Порядку: акт приймання наркотичних засобів,
  психотропних речовин і прекурсорів у закладах охорони здоров'я (книжкова орієнтація).
- Перемещение/Вимога.mxl — Додаток 2 до Методичних рекомендацій ведення обліку лікарських засобів та
  медичних виробів у закладах охорони здоров'я: накладна (вимога) (альбомна орієнтація).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from mxl_build import Builder  # noqa: E402

DOCS = ROOT / "conf" / "Документы"
BASE = DOCS / "Перемещение" / "Опт_Укр.mxl"  # службові поля файлу (версія 6)

LINE = 13  # висота рядка тексту 10 pt
CAPTION = 9  # висота рядка підпису під полем (7 pt)


def caption(b, row, c1, c2, text):
    b.height(row, CAPTION)
    b.text(row, c1, c2, text, size=7, halign="center", valign="top")


def akt():
    """Акт приймання (ПриходнаяНакладнаяЗапасы). Сітка — 20 колонок по 4.5 символу."""
    b = Builder(BASE, [4.5] * 20)
    L = 19
    r = 0
    b.text(r, 14, L, "Додаток 1"); r += 1
    b.text(r, 14, L, "до Порядку"); r += 2
    b.height(r, 16)
    b.text(r, 0, L, "АКТ", size=12, bold=True, halign="center"); r += 1
    b.height(r, 28)
    b.text(r, 0, L, "приймання наркотичних засобів, психотропних речовин і прекурсорів у закладах охорони здоров'я",
           size=11, bold=True, halign="center", wrap=True); r += 2

    b.text(r, 0, 1, "Комісія")
    b.text(r, 2, L, "Фирма.ПолнНаименование", kind="expr", under=True); r += 1
    caption(b, r, 2, L, "(найменування закладу охорони здоров'я)"); r += 1
    b.text(r, 0, 5, "утворена наказом від")
    b.text(r, 6, 10, "", under=True)
    b.text(r, 11, 11, "№", halign="center")
    b.text(r, 12, 15, "", under=True)
    b.text(r, 16, L, ", у складі"); r += 1
    b.text(r, 0, L, "СкладГолова", kind="expr", under=True); r += 1  # з вкладки «Акт приемки» документа
    caption(b, r, 0, L, "(посада, прізвище та ініціали кожного члена комісії)"); r += 1
    for expr in ["СкладЧлен1", "СкладЧлен2", "СкладЧлен3"]:
        b.text(r, 0, L, expr, kind="expr", under=True); r += 1
    b.height(r, 2 * LINE)
    b.text(r, 0, 3, "провела приймання", valign="bottom")
    b.text(r, 4, L, "ПринятоПоАкту", kind="expr", valign="bottom", wrap=True, under=True); r += 1
    caption(b, r, 4, L, "(назва наркотичних засобів, психотропних речовин чи прекурсорів (лікарських засобів))"); r += 1
    b.text(r, 0, 2, "які отримані")
    b.text(r, 3, 7, 'Формат(ДатаДок, "ДДДММММГГГГ")', kind="expr", under=True, halign="center")
    b.text(r, 8, 8, "від", halign="center")
    b.text(r, 9, L, 'Поставщик', kind="expr", under=True); r += 1
    caption(b, r, 9, L, "(найменування постачальника)"); r += 1
    b.text(r, 0, 3, "згідно з рахунком №")
    b.text(r, 4, 7, "НомерРахунку", kind="expr", under=True, halign="center")
    b.text(r, 8, 8, "від", halign="center")
    b.text(r, 9, 13, "ДатаРахунку", kind="expr", under=True, halign="center"); r += 1  # «Номер/Дата счета поставщика»
    b.height(r, 2 * LINE)
    b.text(r, 0, 8, "Під час проведення перевірки кількості (ваги)", valign="bottom")
    b.text(r, 9, L, "ПроверенныеСредства", kind="expr", valign="bottom", wrap=True, under=True); r += 1
    caption(b, r, 9, L, "(назва наркотичних засобів, психотропних речовин чи прекурсорів (лікарських засобів))"); r += 1
    b.text(r, 0, L, "встановлено такі результати:"); r += 1
    b.section("Шапка", 0, r - 1)

    # таблиця: №, назва, од., за рахунком, фактично, різниця (більше / менше)
    t = r
    b.height(t, 22)
    b.height(t + 1, 14)
    for (c1, c2), h in zip([(0, 1), (2, 9), (10, 11), (12, 13), (14, 15)],
                           ["Порядковий номер", "Назва", "Одиниця виміру", "Кількість, що зазначена в рахунку",
                            "Кількість, що фактично отримана"]):
        b.text(t, c1, c2, h, size=9, halign="center", wrap=True, box=True, rows=2)
    b.text(t, 16, L, "Різниця", size=9, halign="center", box=True)
    b.text(t + 1, 16, 17, "більше", size=9, halign="center", box=True)
    b.text(t + 1, 18, L, "менше", size=9, halign="center", box=True)
    b.section("ШапкаТаблицы", t, t + 1)
    t += 2
    cols = [(0, 1), (2, 9), (10, 11), (12, 13), (14, 15), (16, 17), (18, L)]
    row = ["Ном", "ТМЦ.ПолнНаименование", "Ед", 'Формат(Кво, "Ч15.3")', 'Формат(ФактическиПолучено, "Ч15.3")',
           "РазницаБольше", "РазницаМеньше"]
    align = ["center", "left", "center", "right", "right", "right", "right"]
    for (c1, c2), e, a in zip(cols, row, align):
        b.text(t, c1, c2, e, kind="expr", size=9, halign=a, wrap=(c1 == 2), box=True)
    b.section("Строка", t, t)
    r = t + 2

    # підвал: висновок комісії, підписи (ініціали та прізвище — з вкладки «Акт приемки»)
    p0 = r
    b.text(r, 0, L, "Висновок комісії:"); r += 1
    b.height(r, 3 * LINE)
    b.text(r, 0, L, "Заключение", kind="expr", valign="top", wrap=True, under=True); r += 2
    for who, fio in [("Голова комісії", "ФИОГолова"), ("Члени комісії", "ФИОЧлен1"), ("", "ФИОЧлен2"),
                     ("", "ФИОЧлен3")]:
        b.text(r, 0, 4, who)
        b.text(r, 6, 9, "", under=True)
        b.text(r, 11, 16, fio, kind="expr", under=True, halign="center"); r += 1
        caption(b, r, 6, 9, "(підпис)")
        caption(b, r, 11, 16, "(ініціали та прізвище)"); r += 1
    b.text(r, 0, 1, "М.П."); r += 1
    b.section("Подвал", p0 - 1, r - 1)
    return b


def vymoga():
    """Накладна (вимога) (Перемещение). Сітка — 27 колонок по 4.5 символу, альбомна сторінка."""
    b = Builder(BASE, [4.5] * 27)
    L = 26
    r = 0
    for line in ["Додаток 2", "до Методичних рекомендацій", "ведення обліку лікарських засобів та",
                 "медичних виробів у закладах охорони", "здоров'я", "(пункт 4 розділу III)"]:
        b.height(r, 11)
        b.text(r, 19, L, line, size=8)
        r += 1
    r += 1
    b.text(r, 0, 9, "Фирма.ПолнНаименование", kind="expr", under=True, halign="center"); r += 1
    caption(b, r, 0, 9, "(заклад охорони здоров'я)"); r += 1
    b.text(r, 0, 9, "НовоеМестоХранения", kind="expr", under=True, halign="center"); r += 1
    caption(b, r, 0, 9, "(підрозділ)"); r += 2
    b.height(r, 16)
    b.text(r, 0, L, "Накладна (вимога) № [НомерДок]", kind="template", size=12, bold=True, halign="center"); r += 1
    b.text(r, 0, L, 'за [Формат(ДатаДок, "ДДДММММГГГГ")]', kind="template", halign="center"); r += 2
    b.section("Шапка", 0, r - 1)

    # таблиця: № з/п, найменування, од., ціна, кількість (вимагається, відпущено), сума
    t = r
    b.height(t, 14)
    b.height(t + 1, 14)
    for (c1, c2), h in zip([(0, 1), (2, 11), (12, 14), (15, 17)],
                           ["№\r\nз/п", "Найменування лікарських засобів та медичних виробів", "Одиниця виміру", "Ціна"]):
        b.text(t, c1, c2, h, size=9, halign="center", wrap=True, box=True, rows=2)
    b.text(t, 18, 23, "Кількість", size=9, halign="center", box=True)
    b.text(t + 1, 18, 20, "Вимагається", size=9, halign="center", box=True)
    b.text(t + 1, 21, 23, "Відпущено", size=9, halign="center", box=True)
    b.text(t, 24, L, "Сума", size=9, halign="center", wrap=True, box=True, rows=2)
    b.section("ШапкаТаблицы", t, t + 1)
    t += 2
    cols = [(0, 1), (2, 11), (12, 14), (15, 17), (18, 20), (21, 23), (24, L)]
    row = ["Ном", "ТМЦ.ПолнНаименование", "ЕдПоУмолчанию", 'Формат(ЦенаТребования, "Ч15.2")', 'Формат(Кво, "Ч15.3")',
           'Формат(Кво, "Ч15.3")', 'Формат(СуммаТребования, "Ч15.2")']
    align = ["center", "left", "center", "right", "right", "right", "right"]
    for (c1, c2), e, a in zip(cols, row, align):
        b.text(t, c1, c2, e, kind="expr", size=9, halign=a, wrap=(c1 == 2), box=True)
    b.section("Строка", t, t)
    r = t + 2

    p0 = r
    for who, post, name in [("Відпустив", "ДолжнВыдал", "ФИОВыдал"), ("Отримав", "ДолжнПолучил", "ФИОПолучил"),
                            ("Погоджено", "ДолжнМедДиректор", "ФИОМедДиректор")]:  # реквізит «Медицинский директор»
        b.text(r, 0, 3, who)
        b.text(r, 4, 9, post, kind="expr", under=True, halign="center")
        b.text(r, 11, 16, "", under=True)
        b.text(r, 18, L, name, kind="expr", under=True, halign="center"); r += 1
        caption(b, r, 4, 9, "(посада)")
        caption(b, r, 11, 16, "(підпис)")
        caption(b, r, 18, L, "(прізвище, ім'я, по батькові)"); r += 1
        b.text(r, 0, 9, '"___" ____________ 20__ р.'); r += 2
    b.section("Подвал", p0 - 1, r - 2)
    return b


if __name__ == "__main__":
    for builder, path in [(akt, DOCS / "ПриходнаяНакладнаяЗапасы" / "АктПриймання.mxl"),
                          (vymoga, DOCS / "Перемещение" / "Вимога.mxl")]:
        sh = builder().save(path)
        print(f"{path.relative_to(ROOT)}: рядків {sh.max_row}, колонок {sh.max_col}, "
              f"секції {[s.name for s in sh.row_sections]}")

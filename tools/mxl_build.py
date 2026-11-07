"""Конструктор нових макетів 1С 7.7 (*.mxl) поверх tools/mxl77.py.

Службові поля файлу (заголовок, формат таблиці, колонтитули) беруться з наявного макета-основи,
решта — сітка колонок, рядки, комірки, об'єднання, секції — описується кодом:

    b = Builder("conf/Документы/Перемещение/Опт_Укр.mxl", [4.5] * 20)
    b.text(0, 0, 19, "АКТ", size=12, bold=True, halign="center")
    b.text(5, 0, 1, "Ном", kind="expr", box=True)
    b.section("Строка", 5, 5)
    b.save("conf/Документы/X/Акт.mxl")

Розмітка властивостей комірки (зміщення в 30/32-байтовій структурі) — як у класі Fmt.
"""
from __future__ import annotations

import struct

import mxl77

HALIGN = {"left": 0, "right": 2, "justify": 4, "center": 6}
VALIGN = {"top": 0, "bottom": 0x08, "center": 0x18}
KIND = {"text": 0, "expr": 1, "template": 2}
THIN = 2  # тонка суцільна рамка (так оформлені таблиці наявних макетів)
WRAP = 3  # контроль «Переносить»


def make_fmt(fl, *, size=None, bold=None, halign=None, valign=None, wrap=False, kind="text", text=False,
             left=0, top=0, right=0, bottom=0, row_height=None, col_width=None):
    raw = bytearray(fl)

    def setf(byte, bit):
        raw[byte] |= bit

    if size is not None:
        setf(0, 0x02)
        struct.pack_into("<h", raw, 10, int(round(-size * 4)))
    if bold is not None:
        setf(0, 0x04)
        raw[0x0C] = 7 if bold else 4
    for side, (byte, bit, off) in {"left": (0, 0x20, 0x12), "top": (0, 0x40, 0x13), "right": (0, 0x80, 0x14),
                                    "bottom": (1, 0x01, 0x15)}.items():
        style = {"left": left, "top": top, "right": right, "bottom": bottom}[side]
        if style:
            setf(byte, bit)
            raw[off] = style
    if row_height is not None:
        setf(1, 0x04)
        struct.pack_into("<H", raw, 4, int(round(row_height * 4)))
    if col_width is not None:
        setf(1, 0x08)
        struct.pack_into("<H", raw, 6, int(round(col_width * 8)))
    if halign is not None:
        setf(1, 0x10)
        raw[0x0F] = HALIGN[halign]
    if valign is not None:
        setf(1, 0x20)
        raw[0x10] = VALIGN[valign]
    if wrap:
        setf(2, 0x04)
        raw[0x1A] = WRAP
    if KIND[kind]:
        setf(2, 0x08)
        raw[0x1B] = KIND[kind]
    if text:
        setf(3, 0x80)
    return mxl77.Fmt(bytes(raw))


class Builder:
    def __init__(self, base_path, col_widths, size=10):
        self.base = mxl77.read(base_path)
        if self.base.version not in (6, 7):
            raise mxl77.MxlError("основа має бути макетом версії 6 або 7")
        self.fl = self.base.fl
        self.widths = list(col_widths)
        self.size = size  # розмір шрифту за замовчуванням
        self.cells = {}  # (рядок, колонка) -> Item
        self.heights = {}
        self.merges = []
        self.sections = []

    def height(self, row, pt):
        self.heights[row] = pt

    def text(self, row, c1, c2, text="", *, kind="text", size=None, bold=False, halign="left", valign="center",
             wrap=False, box=False, under=False, rows=1):
        """Текст в області колонок c1..c2 (і rows рядків); область понад одну комірку об'єднується.

        box — рамка навколо області, under — лінія знизу (поле для заповнення від руки або значення).
        """
        r2 = row + rows - 1
        for r in range(row, r2 + 1):
            for c in range(c1, c2 + 1):
                first = (r, c) == (row, c1)
                self.cells[(r, c)] = mxl77.Item(make_fmt(
                    self.fl, size=self.size if size is None else size, bold=bold, halign=halign, valign=valign,
                    wrap=wrap, kind=kind if first else "text", text=first and bool(text),
                    left=THIN if box and c == c1 else 0, right=THIN if box and c == c2 else 0,
                    top=THIN if box and r == row else 0,
                    bottom=THIN if (box or under) and r == r2 else 0), text if first else "")
        if c2 > c1 or r2 > row:
            self.merges.append((c1, row, c2, r2))

    def section(self, name, r1, r2):
        self.sections.append(mxl77.Section(name, r1, r2))

    def build(self) -> mxl77.Sheet:
        b = self.base
        used = {r for r, _ in self.cells} | set(self.heights)
        sh = mxl77.Sheet(b.version, max_col=len(self.widths), max_row=max(used) + 1, head=b.head,
                         tail_ver=b.tail_ver, table_fmt=b.table_fmt, unk_after_fonts=b.unk_after_fonts,
                         footers=b.footers)
        sh.col_nums = list(range(len(self.widths)))
        sh.cols = [make_fmt(self.fl, col_width=w) for w in self.widths]
        for r in sorted(used):
            h = self.heights.get(r)
            row = mxl77.Row(make_fmt(self.fl, row_height=h))
            for c in sorted(c for rr, c in self.cells if rr == r):
                row.cells[c] = self.cells[(r, c)]
            sh.rows[r] = row
        sh.merges = sorted(self.merges, key=lambda m: (m[1], m[0]))
        sh.row_sections = sorted(self.sections, key=lambda s: s.begin)
        return sh

    def save(self, path):
        sh = self.build()
        data = mxl77.dump(sh)
        if mxl77.dump(mxl77.parse(data)) != data:  # самоперевірка: файл читається тим самим парсером
            raise mxl77.MxlError("зібраний макет не проходить повторне читання")
        with open(path, "wb") as f:
            f.write(data)
        return sh

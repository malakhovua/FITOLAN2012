"""Читання і запис табличних документів 1С 7.7 (*.mxl, формат MOXCEL версій 6/7) без втрат.

Формат — серіалізація MFC CArchive об'єкта CSheetDoc (опис: wiki 1С++ «Формат MOXCEL»; парсер
перенесено з 1c83_MNFC/tools/mxl77.py). Кількості пишуться CArchive::WriteCount (2 байти,
0xFFFF -> далі 4), рядки — CString (1 байт довжини, 0xFF -> 2 байти, 0xFFFF -> 4), кодування CP1251.

Модель зберігає все, включно з полями невідомого призначення, тож read() -> write() дає
побайтово той самий файл (перевірка: tools/mxl_roundtrip.py). Номери рядків і колонок — з 0.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

ENC = "cp1251"
ERR = "surrogateescape"  # некоректні байти CP1251 зберігаються як є


class MxlError(Exception):
    pass


@dataclass
class Fmt:
    """Властивості комірки (30 або 32 байти). Флажки — байти 0..3, значення — далі."""
    raw: bytes

    def flag(self, byte, bit):
        return bool(self.raw[byte] & bit)

    # шрифт
    @property
    def font_no(self):
        return struct.unpack_from("<H", self.raw, 8)[0] if self.flag(0, 0x01) else None

    @property
    def font_size(self):
        if not self.flag(0, 0x02):
            return None
        p = struct.unpack_from("<h", self.raw, 10)[0]
        return -p / 4 if p else None

    @property
    def bold(self):
        return (self.raw[0x0C] == 7) if self.flag(0, 0x04) else None

    @property
    def italic(self):
        return bool(self.raw[0x0D]) if self.flag(0, 0x08) else None

    @property
    def underline(self):
        return bool(self.raw[0x0E]) if self.flag(0, 0x10) else None

    # рамки: стиль 0..9 (0 — немає)
    def border(self, side):
        byte, bit, off = {"left": (0, 0x20, 0x12), "top": (0, 0x40, 0x13), "right": (0, 0x80, 0x14),
                          "bottom": (1, 0x01, 0x15)}[side]
        return self.raw[off] if self.flag(byte, bit) else None

    @property
    def halign(self):
        if not self.flag(1, 0x10):
            return None
        return {0: "left", 2: "right", 4: "justify", 6: "center"}.get(self.raw[0x0F] & 0x0F, "left")

    @property
    def across(self):
        """По выделенным столбцам (біт 0x20 значення горизонтального положення)."""
        return bool(self.raw[0x0F] & 0x20) if self.flag(1, 0x10) else None

    @property
    def valign(self):
        if not self.flag(1, 0x20):
            return None
        return {0: "top", 0x08: "bottom", 0x18: "center"}.get(self.raw[0x10], "bottom")

    @property
    def border_color(self):
        return self.raw[0x17] if self.flag(1, 0x02) else None

    @property
    def font_color(self):
        return self.raw[0x18] if self.flag(1, 0x40) else None

    @property
    def back_color(self):
        return self.raw[0x19] if self.flag(1, 0x80) else None

    @property
    def control(self):
        """Контроль: 0 Авто, 1 Обрезать, 2 Забивать, 3 Переносить, 4 Красный, 5 Забивать+Красный."""
        return self.raw[0x1A] if self.flag(2, 0x04) else None

    @property
    def kind(self):
        """Тип: 0 Текст, 1 Выражение, 2 Шаблон, 3 Фикс. шаблон."""
        return self.raw[0x1B] if self.flag(2, 0x08) else 0

    @property
    def has_text(self):
        return self.flag(3, 0x80)

    @property
    def has_decode(self):
        return self.flag(3, 0x40)

    # рядок/колонка
    @property
    def row_height(self):
        """Висота рядка в пунктах (властивості рядка)."""
        return struct.unpack_from("<H", self.raw, 4)[0] / 4 if self.flag(1, 0x04) else None

    @property
    def col_width(self):
        """Ширина колонки в «стандартних символах» (властивості колонки)."""
        return struct.unpack_from("<H", self.raw, 6)[0] / 8 if self.flag(1, 0x08) else None


@dataclass
class Item:
    """Комірка, колонтитул: властивості + текст + розшифровка."""
    fmt: Fmt
    text: str = ""
    decode: str = ""


@dataclass
class Row:
    fmt: Fmt
    cells: dict = field(default_factory=dict)  # колонка -> Item (порядок вставки = порядок у файлі)


@dataclass
class Section:
    name: str
    begin: int
    end: int
    extra: int = 0  # 4 байти невідомого призначення


@dataclass
class Name:
    """Іменована область: kind 1 рядки, 2 колонки, 3 прямокутник; -1 — усі."""
    name: str
    a: int
    b: int
    kind: int
    c1: int
    r1: int
    c2: int
    r2: int


@dataclass
class Sheet:
    version: int
    max_col: int = 0
    max_row: int = 0
    head: bytes = b"\0" * 5  # 5 байтів після сигнатури
    tail_ver: int = 0  # байт після версії
    pictures: int = 0
    table_fmt: Fmt | None = None
    font_nums: list = field(default_factory=list)
    fonts: list = field(default_factory=list)  # LOGFONT, 60 байтів кожен
    unk_after_fonts: bytes = b"\0" * 4
    footers: list = field(default_factory=list)  # 2 × Item (верхній, нижній колонтитул)
    col_nums: list = field(default_factory=list)
    cols: list = field(default_factory=list)  # Fmt у порядку col_nums
    rows: dict = field(default_factory=dict)  # рядок -> Row (порядок вставки = порядок у файлі)
    objects: list = field(default_factory=list)  # рисунки/OLE — сирі байти
    merges: list = field(default_factory=list)  # (col1, row1, col2, row2)
    col_sections: list = field(default_factory=list)
    row_sections: list = field(default_factory=list)
    col_breaks: list = field(default_factory=list)
    row_breaks: list = field(default_factory=list)
    names: list = field(default_factory=list)
    raw: bytes | None = None  # порожня таблиця старого формату (версія 2) — зберігається цілком

    @property
    def fl(self):
        return 30 if self.version == 6 else 32

    def cell(self, row, col):
        r = self.rows.get(row)
        return r.cells.get(col) if r else None


class Reader:
    def __init__(self, data: bytes):
        self.d = data
        self.p = 0

    def take(self, n):
        if self.p + n > len(self.d):
            raise MxlError(f"кінець файлу: потрібно {n} байт з {self.p}")
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack("<H", self.take(2))[0]

    def u32(self):
        return struct.unpack("<I", self.take(4))[0]

    def i32(self):
        return struct.unpack("<i", self.take(4))[0]

    def count(self):
        n = self.u16()
        return self.u32() if n == 0xFFFF else n

    def cstring(self):
        n = self.u8()
        if n == 0xFF:
            n = self.u16()
            if n == 0xFFFF:
                n = self.u32()
        return self.take(n).decode(ENC, errors=ERR)


class Writer:
    def __init__(self):
        self.b = bytearray()

    def put(self, data):
        self.b += data

    def u8(self, v):
        self.b += struct.pack("<B", v)

    def u16(self, v):
        self.b += struct.pack("<H", v)

    def u32(self, v):
        self.b += struct.pack("<I", v)

    def i32(self, v):
        self.b += struct.pack("<i", v)

    def count(self, n):
        if n < 0xFFFF:
            self.u16(n)
        else:
            self.u16(0xFFFF)
            self.u32(n)

    def cstring(self, s):
        data = s.encode(ENC, errors=ERR)
        n = len(data)
        if n < 0xFF:
            self.u8(n)
        elif n < 0xFFFE:
            self.u8(0xFF)
            self.u16(n)
        else:
            self.u8(0xFF)
            self.u16(0xFFFF)
            self.u32(n)
        self.b += data


def _read_item(r, fl):
    it = Item(Fmt(r.take(fl)))
    if it.fmt.has_text:
        it.text = r.cstring()
    if it.fmt.has_decode:
        it.decode = r.cstring()
    return it


def _write_item(w, it):
    w.put(it.fmt.raw)
    if it.fmt.has_text:
        w.cstring(it.text)
    if it.fmt.has_decode:
        w.cstring(it.decode)


def parse(data: bytes) -> Sheet:
    r = Reader(data)
    if r.take(6) != b"MOXCEL":
        raise MxlError("не MOXCEL")
    head = r.take(5)
    ver = r.u8()
    if ver == 2:
        return Sheet(ver, raw=bytes(data))
    if ver not in (6, 7):
        raise MxlError(f"версія {ver} не підтримується")
    sh = Sheet(ver, head=head, tail_ver=r.u8())
    fl = sh.fl
    sh.max_col, sh.max_row, sh.pictures = r.u32(), r.u32(), r.u32()
    sh.table_fmt = Fmt(r.take(fl))
    sh.font_nums = [r.u32() for _ in range(r.count())]
    sh.fonts = [r.take(60) for _ in range(r.count())]
    sh.unk_after_fonts = r.take(4)
    sh.footers = [_read_item(r, fl) for _ in range(2)]
    sh.col_nums = [r.u32() for _ in range(r.count())]
    sh.cols = [Fmt(r.take(fl)) for _ in range(r.count())]
    rnums = [r.u32() for _ in range(r.count())]
    n = r.count()
    if n != len(rnums):
        raise MxlError("кількість рядків не збігається з кількістю номерів")
    for k in range(n):
        row = Row(Fmt(r.take(fl)))
        cnums = [r.u32() for _ in range(r.count())]
        m = r.count()
        if m != len(cnums):
            raise MxlError("кількість комірок не збігається з кількістю номерів")
        for j in range(m):
            row.cells[cnums[j]] = _read_item(r, fl)
        sh.rows[rnums[k]] = row
    for _ in range(r.count()):
        p0 = r.p
        _read_item(r, fl)
        kind = r.u32()
        r.take(36)
        if kind == 5:  # рисунок
            if r.u32() != 0x746C:
                raise MxlError("рисунок: невідома сигнатура")
            r.take(r.u32())
        elif kind == 4:  # OLE / діаграма
            if r.u16() == 0xFFFF:
                r.u16()
                r.take(r.u16())
            r.take(4 * 3 + 2 + 4)
            r.take(r.u32())
        elif kind not in (1, 2, 3):  # графічні об'єкти без додаткових даних
            raise MxlError(f"невідомий вид об'єкта {kind}")
        sh.objects.append(bytes(data[p0:r.p]))
    sh.merges = [struct.unpack("<iiii", r.take(16)) for _ in range(r.count())]
    for lst in (sh.col_sections, sh.row_sections):
        for _ in range(r.count()):
            b, e, x = r.i32(), r.i32(), r.u32()
            lst.append(Section(r.cstring(), b, e, x))
    sh.col_breaks = [r.u32() for _ in range(r.count())]
    sh.row_breaks = [r.u32() for _ in range(r.count())]
    for _ in range(r.u32()):
        name = r.cstring()
        a, b, kind = r.u32(), r.u32(), r.u32()
        sh.names.append(Name(name, a, b, kind, *struct.unpack("<iiii", r.take(16))))
    if r.p != len(data):
        raise MxlError(f"зайві дані в кінці: {len(data) - r.p} байт з {r.p}")
    return sh


def dump(sh: Sheet) -> bytes:
    if sh.raw is not None:
        return sh.raw
    w = Writer()
    w.put(b"MOXCEL")
    w.put(sh.head)
    w.u8(sh.version)
    w.u8(sh.tail_ver)
    w.u32(sh.max_col)
    w.u32(sh.max_row)
    w.u32(sh.pictures)
    w.put(sh.table_fmt.raw)
    w.count(len(sh.font_nums))
    for v in sh.font_nums:
        w.u32(v)
    w.count(len(sh.fonts))
    for lf in sh.fonts:
        w.put(lf)
    w.put(sh.unk_after_fonts)
    for it in sh.footers:
        _write_item(w, it)
    w.count(len(sh.col_nums))
    for v in sh.col_nums:
        w.u32(v)
    w.count(len(sh.cols))
    for f in sh.cols:
        w.put(f.raw)
    w.count(len(sh.rows))
    for v in sh.rows:
        w.u32(v)
    w.count(len(sh.rows))
    for row in sh.rows.values():
        w.put(row.fmt.raw)
        w.count(len(row.cells))
        for c in row.cells:
            w.u32(c)
        w.count(len(row.cells))
        for it in row.cells.values():
            _write_item(w, it)
    w.count(len(sh.objects))
    for o in sh.objects:
        w.put(o)
    w.count(len(sh.merges))
    for m in sh.merges:
        w.put(struct.pack("<iiii", *m))
    for lst in (sh.col_sections, sh.row_sections):
        w.count(len(lst))
        for s in lst:
            w.i32(s.begin)
            w.i32(s.end)
            w.u32(s.extra)
            w.cstring(s.name)
    for lst in (sh.col_breaks, sh.row_breaks):
        w.count(len(lst))
        for v in lst:
            w.u32(v)
    w.u32(len(sh.names))
    for nm in sh.names:
        w.cstring(nm.name)
        w.u32(nm.a)
        w.u32(nm.b)
        w.u32(nm.kind)
        w.put(struct.pack("<iiii", nm.c1, nm.r1, nm.c2, nm.r2))
    return bytes(w.b)


def read(path) -> Sheet:
    with open(path, "rb") as f:
        return parse(f.read())


def write(sh: Sheet, path):
    with open(path, "wb") as f:
        f.write(dump(sh))

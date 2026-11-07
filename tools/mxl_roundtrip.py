"""Перевірка записувача: кожен *.mxl читається і записується назад, результат має побайтово збігатися.

Запуск: python3 tools/mxl_roundtrip.py [каталог]   (за замовчуванням — conf/)
Файли не змінюються: порівняння в пам'яті.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mxl77  # noqa: E402

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "conf")
ok = bad = 0
for f in sorted(root.rglob("*.mxl")):
    data = f.read_bytes()
    try:
        out = mxl77.dump(mxl77.parse(data))
    except Exception as e:  # noqa: BLE001
        bad += 1
        print(f"ПОМИЛКА {f}: {e}")
        continue
    if out == data:
        ok += 1
    else:
        bad += 1
        pos = next((i for i, (a, b) in enumerate(zip(out, data)) if a != b), min(len(out), len(data)))
        print(f"РОЗБІЖНІСТЬ {f}: байт {pos}, довжина {len(out)} проти {len(data)}")
print(f"збіг: {ok}, розбіжностей: {bad}")
sys.exit(1 if bad else 0)

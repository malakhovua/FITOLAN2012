# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **1C:Enterprise 7.7** configuration (based on the typical "Производство + Услуги + Бухгалтерия для Украины") for FITOLAN, kept in git as text via **gcomp 2.2.15** (bundled in `gcomp_bin_2.2.15/`). The binary metadata file `1Cv7.MD` is decompiled into the `conf/` tree; `conf/` is the source of truth for diffs and edits. There is no build system, linter, or test suite — 1C code runs only inside the 1C:Enterprise 7.7 platform on Windows.

## Commands (Windows, run from repo root)

gcomp is a Windows executable; the `.bat` scripts hardcode `cd C:\1C_Base\repository\FITOLAN2012` in some cases. Logs go to `log/` (gitignored).

- **Decompile** `1Cv7.MD` → `conf/`: `decompile.bat`
  (`gcomp.exe -vv -d -F .\1CV7.md -D .\conf`)
- **Compile** `conf/` → `MD_compile\1Cv7.MD`: `compile.bat`
  (`gcomp.exe -vv -c -F .\MD_compile\1Cv7.MD -DD .\conf`; `MD_compile/` is gitignored). The compiled MD is then copied into the 1C infobase to load the changes.
- `compile_decompile_git_script.bat`: decompile → delete `1CV7.md` → `git add . && git commit` → compile → `git push` (the usual "save changes from the Configurator" workflow).
- `pull_compile.bat`: `git pull`, then compile — used to deploy changes made elsewhere.

gcomp options are in `conf/gcomp.ini` (language Rus, form parsing on, etc.); full docs in `gcomp_bin_2.2.15/Documentation/txt/` (`ReadMe.txt`, `MD_Formats.txt`, `DlgForms.txt`). Helper scripts (code beautifier, procedure extractor, etc.) are in `gcomp_bin_2.2.15/scripts/`.

## File encoding — important

All text files under `conf/` (`.1s`, `.mdp`, `.frm`, `.txt`, `.ord`) are **Windows-1251 (cp1251)** — see "1C 7.7 File Rules" below for line endings and the editing workflow. Directory and file names are Cyrillic (use `git -c core.quotepath=off` to read them). Never save these files as UTF-8, or gcomp will compile garbled text into the MD. `.mxl` files (print templates/spreadsheets) are binary and cannot be edited as text.

## Layout of `conf/` (gcomp decompiled format)

Each metadata object is a directory under its class folder:

- `Документы/<Имя>/` — `Структура.mdp` (attributes, journal, posting flags), `МодульФормы.1s` (form module), `МодульПроведения.1s` (document module — posting logic, writes to registers and accounting entries), `Форма.frm` (dialog layout), `*.mxl` (print forms, e.g. `_Укр` / `_2018` variants), `Описание.txt`.
- `Справочники/`, `Отчеты/`, `Обработки/`, `ЖурналыДокументов/` — similar per-object directories with `МодульФормы.1s` / `Форма.frm` / templates.
- `ПараметрыБухгалтерии/` — accounting component: chart of accounts (`Счета`), operations/entries (`Операция`, `Проводка`), and subconto kinds (`*.txt` per subconto type).
- `Регистры/`, `Константы/`, `Перечисления/`, `ОбщиеТаблицы/`, `Права/`, `Интерфейсы/` — the corresponding metadata classes.
- `ГлобальныйМодуль.1s` — the global module (~12k lines, ~200 procedures/functions). Defines exported globals prefixed `гл…` (e.g. `глПользователь`, `глОбщиеУстановки`) plus shared constants (`Да`, `Нет`, `Гривня`, …) and common helpers used from all object modules — check here before adding a new utility.
- `ПорядокОбъектов.ord` files preserve object ordering; `GUIDData`, `TagStream`, `ИдентификаторыКонфигурации.mdp`, `PictureGallery/` are internal data gcomp needs to round-trip — don't hand-edit.

## Working notes

- Code is 1C 7.7 built-in language (Russian keywords: `Процедура … КонецПроцедуры`, `Функция … КонецФункции`, `Перем … Экспорт`). There is no 8.x syntax (no `&НаКлиенте`, no queries language of 8.x; 7.7 uses `Запрос` objects with its own text syntax).
- Adding new metadata objects/attributes by hand in `.mdp` requires unique IDs; prefer making structural changes in the 1C Configurator and decompiling, and limit direct edits to module code (`.1s`).

## Git
- Працюємо в одній гілці `main`, окремі гілки не створювати — репозиторій лише для відстеження власних змін, інших учасників немає.
- Після кожного коміту одразу робити `git push` (для нової гілки — `git push -u origin <гілка>`).
## 1C 7.7 File Rules
All .1s, .frm, .mdp, .ord files use Windows-1251 encoding with CRLF line endings (\r\n).

### Editing workflow
1. Read: `iconv -f CP1251 -t UTF-8 <file> > /tmp/<file>_utf8`
2. Edit the UTF-8 temp file
3. Write back: `iconv -f UTF-8 -t CP1251 /tmp/<file>_utf8 | unix2dos > <original_file>`

Never write files with LF-only line endings — 1C 7.7 configurator requires CRLF.


### Comments
Add comments at the end of a block for conditions, loops, procedures, functions. At the end of specific variables. Edits you make with the mark - // + Малахов

**Коли пишеш щось з нуля** (нову процедуру/функцію повністю, новий модуль): коментар `// + Малахов` ставиш лише на найвищому рівні ієрархії того, що створив — рядок процедури/функції (або модуля, якщо новий увесь модуль). У внутрішніх умовних блоках, циклах тощо всередині цієї нової процедури коментар **не** дублюється.
Ієрархія: Весь модуль → Процедура → умовні блоки/цикли і т.д. — мітка ставиться тільки на верхньому рівні того, що додано.

Коли ж редагуєш/фіксиш окремі існуючі рядки (а не пишеш блок з нуля) — мітку `// + Малахов` ставиш саме на змінених рядках, як і раніше.

## Відомі помилки
- При генерації коду використовувати тільки **кириличні** назви змінних.
  Наприклад: `ДатаДок` (не `ДатаDok`), `ЕфДата`, `СкладКудиСтр` — все кирилицею.
  1С 7.7 чутлива до змішування латиниці і кирилиці в іменах змінних.
  
## Правила синтаксису 1С 7.7
### Дужки в умовах
Завжди використовувати дужки для кожної окремої (якщо їх більше однієї) умови в складених виразах:
- Правильно: `Если (ПустоеЗначение(Х)) = 0 И (Х > 0) Тогда`
- Неправильно: `Если ПустоеЗначение(Х) = 0 И Х > 0 Тогда`


import os
import shutil
import sys
from pathlib import Path
from doit.tools import create_folder, run_once

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
LOCALE_DIR = PROJECT_ROOT / "mood" / "server" / "locale"
POT_FILE = LOCALE_DIR / "messages.pot"
PO_FILE_RU = LOCALE_DIR / "ru" / "LC_MESSAGES" / "messages.po"
MO_FILE_RU = LOCALE_DIR / "ru" / "LC_MESSAGES" / "messages.mo"
I18N_SOURCE_FILES = list(PROJECT_ROOT.glob("mood/server/**/*.py"))

def _clean_file(filepath):
    """Безопасно удаляет файл, если он существует."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Removed: {filepath}")
    except OSError as e:
        print(f"Error removing file {filepath}: {e}")


def task_pot():
    """
    Генерирует шаблон перевода (.pot) из исходных файлов.
    """
    pot_file_path = str(POT_FILE)
    babel_cfg_file_path = str(LOCALE_DIR / "babel.cfg")
    return {
        "actions": [
            (create_folder, [LOCALE_DIR]),
            f'pybabel extract -F {babel_cfg_file_path} -o {pot_file_path} {PROJECT_ROOT / "mood"}',
        ],
        "targets": [pot_file_path],
        "file_dep": I18N_SOURCE_FILES + [babel_cfg_file_path],
        "clean": [(_clean_file, [pot_file_path])],
        "doc": "Generate .pot translation template file.",
    }


def task_po():
    """
    Обновляет файлы переводов (.po) из шаблона (.pot).
    Предполагает, что Русский (ru) язык установлен.
    """
    po_dir_ru = PO_FILE_RU.parent
    po_file_path = str(PO_FILE_RU)
    pot_file_path = str(POT_FILE)
    return {
        "actions": [
            (create_folder, [po_dir_ru]),
            f"pybabel update --ignore-pot-creation-date -i {pot_file_path} -d {LOCALE_DIR} -l ru",
        ],
        "file_dep": [pot_file_path],
        "targets": [po_file_path],
        "clean": True,
        "doc": "Update .po translation file from .pot template.",
    }

def task_mo():
    """
    Компилирует файлы переводов (.po) в бинарном формате (.mo).
    Предполагает, что Русский (ru) язык установлен.
    """
    mo_file_path = str(MO_FILE_RU)
    po_file_path = str(PO_FILE_RU)
    return {
        "actions": [f"pybabel compile -d {LOCALE_DIR} -l ru"],
        "file_dep": [po_file_path],
        "targets": [mo_file_path],
        "clean": [(_clean_file, [mo_file_path])],
        "doc": "Compile .po file into .mo binary format.",
    }

def task_i18n():
    """
    Запускает все шаги перевода: pot -> po -> mo.
    """
    pot_file_path = str(POT_FILE)
    mo_file_path = str(MO_FILE_RU)
    return {
        "actions": None,
        "task_dep": ["mo"],
        "clean": [
            (_clean_file, [pot_file_path]),
            (_clean_file, [mo_file_path])
        ],
        "doc": "Generate all translation files (.pot, .po, .mo).",
    }


babel_cfg_content = """\
[python: mood/**.py]
"""
babel_cfg_path = LOCALE_DIR / "babel.cfg"
if not babel_cfg_path.exists():
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    with open(babel_cfg_path, "w") as f:
        f.write(babel_cfg_content)

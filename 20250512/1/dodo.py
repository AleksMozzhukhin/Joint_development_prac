import os
import shutil
import sys
from pathlib import Path
from doit.tools import create_folder, run_once, CmdAction

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
LOCALE_DIR = PROJECT_ROOT / "mood" / "server" / "locale"
POT_FILE = LOCALE_DIR / "messages.pot"
PO_FILE_RU = LOCALE_DIR / "ru" / "LC_MESSAGES" / "messages.po"
MO_FILE_RU = LOCALE_DIR / "ru" / "LC_MESSAGES" / "messages.mo"
I18N_SOURCE_FILES = list(PROJECT_ROOT.glob("mood/server/**/*.py"))
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_SOURCE_DIR = DOCS_DIR / "source"
DOCS_BUILD_DIR = DOCS_DIR / "build"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
TEST_FILES = list(PROJECT_ROOT.glob("tests/**/*.py"))
SOURCE_FILES = list(PROJECT_ROOT.glob("mood/**/*.py"))
SDIST_SOURCES = (
        list(PROJECT_ROOT.glob("mood/**/*.py")) +
        list(PROJECT_ROOT.glob("tests/**/*.py")) +
        list(PROJECT_ROOT.glob("docs/source/**/*")) +
        [
            PROJECT_ROOT / "dodo.py",
            PROJECT_ROOT / "pyproject.toml",  # Essential for building
            PROJECT_ROOT / "mood" / "server" / "locale" / "babel.cfg",
            PROJECT_ROOT / "mood" / "server" / "locale" / "ru" / "LC_MESSAGES" / "messages.po",
            PROJECT_ROOT / "docs" / "Makefile",
            PROJECT_ROOT / "docs" / "make.bat",
            PROJECT_ROOT / "example_commands.mood",
            PROJECT_ROOT / "Pipfile",
            PROJECT_ROOT / "Pipfile.lock",
        ]
)
WHEEL_FILE_PATTERN = DIST_DIR / f"{PROJECT_ROOT.name.replace('-', '_')}-*-py3-none-any.whl"

DOIT_CONFIG = {'default_tasks': ['html']}


def _clean_file(filepath):
    """Безопасно удаляет файл, если он существует."""
    try:
        filepath_str = str(filepath)
        if os.path.exists(filepath_str):
            os.remove(filepath_str)
            print(f"Removed: {filepath_str}")
    except OSError as e:
        print(f"Error removing file {filepath_str}: {e}")


def _clean_dir(dirpath):
    """Безопасно удаляет каталог, если он существует."""
    try:
        dirpath_str = str(dirpath)
        if os.path.isdir(dirpath_str):
            shutil.rmtree(dirpath_str, ignore_errors=True)
            print(f"Removed directory: {dirpath_str}")
    except OSError as e:
        print(f"Error removing directory {dirpath_str}: {e}")


def task_pot():
    """
    Генерирует шаблон перевода (.pot) из исходных файлов.
    """
    pot_file_path = str(POT_FILE)
    babel_cfg_file_path = str(LOCALE_DIR / "babel.cfg")
    # Ensure babel.cfg is listed as a dependency
    i18n_deps = I18N_SOURCE_FILES + [babel_cfg_file_path]
    return {
        "actions": [
            (create_folder, [LOCALE_DIR]),
            f'pybabel extract -F {babel_cfg_file_path} -k gettext -o {pot_file_path} {PROJECT_ROOT / "mood"}',
        ],
        "targets": [pot_file_path],
        "file_dep": i18n_deps,
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
            f"pybabel update --ignore-pot-creation-date --no-fuzzy-matching -i {pot_file_path} -d {LOCALE_DIR} -l ru",
        ],
        "file_dep": [pot_file_path],
        "targets": [po_file_path],
        "clean": [(_clean_file, [po_file_path])],
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


def task_fix_po():
    """
    Исправляет .po файл, раскомментируя строки переводов.
    """

    def fix_po_file():
        po_file_path = str(PO_FILE_RU)
        if not os.path.exists(po_file_path):
            print(f"PO файл не найден: {po_file_path}")
            return

        # Читаем содержимое файла
        with open(po_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Обрабатываем строки, раскомментируя переводы
        fixed_lines = []
        for line in lines:
            # Раскомментируем строки переводов
            if line.startswith('#~ msgid') or line.startswith('#~ msgstr'):
                fixed_lines.append(line[3:])  # Убираем '#~ '
            elif line.startswith('#~ '):
                # Убираем комментарии с других строк перевода
                stripped = line[3:]
                if stripped.startswith('"') and stripped.endswith('"\n'):
                    fixed_lines.append(stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        # Записываем исправленный файл
        with open(po_file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)

        print(f"Исправлен .po файл: {po_file_path}")

    po_file_path = str(PO_FILE_RU)
    return {
        "actions": [fix_po_file],
        "file_dep": [po_file_path],
        "doc": "Fix .po file by uncommenting translation strings.",
    }


def task_i18n():
    """
    Запускает все шаги перевода: pot -> po -> fix_po -> mo.
    """
    return {
        "actions": None,
        "task_dep": ["pot", "po", "fix_po", "mo"],  # Explicit dependency chain with fix step
        "clean": True,  # Use doit's default clean for task dependencies
        "doc": "Generate all translation files (.pot, .po, .mo) with fixes.",
    }



def task_html():
    """
    Генерация HTML документации с помощью Sphinx.
    """
    html_index_path = str(DOCS_BUILD_DIR / "html" / "index.html")
    build_dir_path = str(DOCS_BUILD_DIR) # This is Sphinx's build dir
    docs_dir_path = str(DOCS_DIR)

    source_files = [str(p) for p in DOCS_SOURCE_DIR.glob("**/*") if p.is_file()]
    mood_files = [str(p) for p in PROJECT_ROOT.glob("mood/**/*.py") if p.is_file()]
    mo_file_path = str(MO_FILE_RU)

    action = CmdAction("make html", cwd=docs_dir_path)

    return {
        "actions": [(create_folder, [DOCS_BUILD_DIR / "html"]), action],
        "file_dep": source_files + mood_files + [mo_file_path],
        "task_dep": ["i18n"],  # Зависимость от локализации
        "targets": [html_index_path],
        "clean": [(_clean_dir, [build_dir_path])],
        "doc": "Generate HTML documentation.",
    }


def task_test():
    """
    Запуск интеграционных тестов сервер-клиент.
    """
    test_paths = [str(p) for p in TEST_FILES]
    source_paths = [str(p) for p in SOURCE_FILES]
    mo_file_path = str(MO_FILE_RU)

    return {
        "actions": ["python -m unittest tests.test_server_commands"],
        "file_dep": test_paths + source_paths + [mo_file_path],
        "task_dep": ["i18n"],
        "clean": True,
        "doc": "Run integration tests.",
    }


def task_sdist():
    """
    Создает исходный дистрибутив (sdist) с использованием python -m build.
    """
    dist_dir_path = str(DIST_DIR)
    build_cmd = f"python -m build --sdist --outdir {dist_dir_path}"

    sdist_dep_files = [str(f) for f in SDIST_SOURCES if f.is_file()]

    return {
        "actions": [(create_folder, [dist_dir_path]), build_cmd],
        "file_dep": sdist_dep_files,
        # "targets": [dist_dir_path],
        "clean": [(_clean_dir, [DIST_DIR]), (_clean_dir, [BUILD_DIR])],
        "doc": "Create a source distribution (sdist) package using 'build'.",
    }


def task_wheel():
    """
    Собирает бинарный дистрибутив (wheel) с использованием python -m build.
    Включает только HTML документацию в пакет.
    """
    import shutil

    def prepare_docs_for_wheel():
        """Копировать только HTML документацию в mood/documentation."""
        # Создаем директорию для документации внутри mood
        docs_target_dir = PROJECT_ROOT / "mood" / "documentation"
        docs_target_dir.mkdir(exist_ok=True)

        # Сохраняем __init__.py файл если он существует
        init_file = docs_target_dir / "__init__.py"
        init_content = None
        if init_file.exists():
            with open(init_file, 'r', encoding='utf-8') as f:
                init_content = f.read()

        # Копируем только HTML документацию
        html_build_dir = DOCS_BUILD_DIR / "html"

        if html_build_dir.exists():
            for item in docs_target_dir.iterdir():
                if item.name != "__init__.py":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()

            # Копируем содержимое HTML директории (не саму директорию)
            for item in html_build_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, docs_target_dir / item.name)
                else:
                    shutil.copy2(item, docs_target_dir / item.name)

            # Восстанавливаем __init__.py файл если он был
            if init_content is not None:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(init_content)


            # Подсчитываем размер
            total_size = sum(f.stat().st_size for f in docs_target_dir.rglob('*') if f.is_file())
        else:
            print("Warning: HTML documentation not found. Run 'doit html' first.")

    dist_dir_path = str(DIST_DIR)
    build_cmd = f"python -m build --wheel --outdir {dist_dir_path}"

    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    source_files = [str(p) for p in SOURCE_FILES]
    html_index_path = str(DOCS_BUILD_DIR / "html" / "index.html")
    init_file_path = str(PROJECT_ROOT / "mood" / "documentation" / "__init__.py")

    return {
        "actions": [
            (create_folder, [dist_dir_path]),
            prepare_docs_for_wheel,
            build_cmd
        ],
        "file_dep": source_files + [str(pyproject_path), html_index_path, init_file_path],
        "task_dep": ["i18n", "html"],
        "clean": [
            (_clean_dir, [DIST_DIR]),
            (_clean_dir, [BUILD_DIR]),
            # НЕ удаляем всю директорию documentation при clean
            lambda: _clean_html_only(PROJECT_ROOT / "mood" / "documentation")
        ],
        "doc": "Create a wheel distribution package with HTML documentation.",
    }


def _clean_html_only(docs_dir):
    """Удалить только HTML файлы из директории документации, оставив __init__.py."""
    import shutil

    if not docs_dir.exists():
        return

    for item in docs_dir.iterdir():
        if item.name != "__init__.py":
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"Removed directory: {item}")
                else:
                    item.unlink()
                    print(f"Removed file: {item}")
            except OSError as e:
                print(f"Error removing {item}: {e}")


def task_show_doc():
    """
    Открыть сгенерированную HTML документацию в браузере по умолчанию.
    """
    import subprocess
    import platform
    import os

    def open_documentation():
        """Открыть документацию в браузере."""
        html_file = DOCS_BUILD_DIR / "html" / "index.html"

        if not html_file.exists():
            print(f"HTML documentation not found: {html_file}")
            print("Run 'doit html' first to generate documentation")
            return False

        try:
            system = platform.system()
            html_path = str(html_file.resolve())

            # Проверяем, работаем ли мы под WSL
            is_wsl = False
            if system == "Linux":
                try:
                    with open('/proc/version', 'r') as f:
                        version_info = f.read().lower()
                        is_wsl = 'microsoft' in version_info or 'wsl' in version_info
                except (FileNotFoundError, PermissionError):
                    pass

            print(f"Opening documentation: {html_path}")

            if is_wsl:
                # WSL: используем Windows команды через wslview или explorer.exe
                wsl_commands = [
                    ["wslview", html_path],  # wslview если установлен
                    ["explorer.exe", html_path],  # стандартный Windows explorer
                    ["cmd.exe", "/c", "start", html_path]  # альтернативный способ
                ]

                success = False
                for cmd in wsl_commands:
                    try:
                        subprocess.run(cmd, check=True,
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                        success = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue

                if not success:
                    # Если ничего не сработало, пробуем конвертировать путь для Windows
                    try:
                        # Конвертируем WSL путь в Windows путь
                        result = subprocess.run(['wslpath', '-w', html_path],
                                                capture_output=True, text=True, check=True)
                        windows_path = result.stdout.strip()
                        subprocess.run(['powershell.exe', '-c', 'Start-Process', f'"{windows_path}"'],
                                       check=True)
                        success = True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        pass

            elif system == "Darwin":  # macOS
                subprocess.run(["open", html_path], check=True)
                success = True
            elif system == "Windows":  # Native Windows
                subprocess.run(["start", html_path], shell=True, check=True)
                success = True
            else:  # Linux и другие Unix-системы
                subprocess.run(["xdg-open", html_path], check=True)
                success = True

            if success:
                print("Documentation opened successfully")
            else:
                print("Failed to open documentation automatically")
                print(f"Please open manually: {html_file}")

            return success

        except subprocess.CalledProcessError as e:
            print(f"Error opening documentation: {e}")
            print(f"Please open manually: {html_file}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(f"Please open manually: {html_file}")
            return False

    html_file_path = str(DOCS_BUILD_DIR / "html" / "index.html")

    return {
        "actions": [open_documentation],
        "file_dep": [html_file_path],
        "task_dep": ["html"],
        "verbosity": 2,
        "doc": "Open generated HTML documentation in default browser.",
    }

babel_cfg_content = """\
[python: mood/**.py]
"""
babel_cfg_path = LOCALE_DIR / "babel.cfg"
if not babel_cfg_path.exists():
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    with open(babel_cfg_path, "w") as f:
        f.write(babel_cfg_content)
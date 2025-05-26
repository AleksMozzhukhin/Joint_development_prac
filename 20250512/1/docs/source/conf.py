import os
import sys

# Добавьте отладочную информацию
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
print(f"DEBUG: Current directory: {current_dir}")
print(f"DEBUG: Project root: {project_root}")

# Добавляем путь к корневой директории проекта
sys.path.insert(0, project_root)

# Проверяем, что директория содержит mood
print(f"DEBUG: Files in project root: {os.listdir(project_root)}")

try:
    import mood
    print(f"DEBUG: Successfully imported mood from {mood.__file__}")
except ImportError as e:
    print(f"DEBUG: Failed to import mood: {e}")

# -- Project information -----------------------------------------------------
project = 'MOOD'
copyright = '2025, Student'
author = 'Student'
release = '0.2.0'
version = '0.2.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Язык документации
language = 'ru'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Настройки темы (упрощенные)
html_theme_options = {
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Кодировка исходных файлов
source_suffix = '.rst'

# Главный документ
master_doc = 'index'
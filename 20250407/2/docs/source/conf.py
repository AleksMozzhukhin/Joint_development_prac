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

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
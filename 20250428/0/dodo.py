from pathlib import Path

DOIT_CONFIG = {'default_tasks': ['docs']}
def task_docs():
    """Builds documentation"""
    return{
        'file_dep': [*Path(".").glob("*.py"), *Path(".").glob("*.py")],
        "actions": ["sphinx-build -M html docs/source _build"],
    }

def task_erase():
    """Erase all generated and new files"""
    return {
        'actions': ['git reset --hard', 'git clean -xdf']
    }

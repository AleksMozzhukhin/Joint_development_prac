def task_docs():
    """Builds documentation"""
    return{
        "actions": ["sphinx-build -M html docs/source _build"],
    }
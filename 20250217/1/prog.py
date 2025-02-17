import os
import sys

def list_branches(git_dir):
    refs_heads = os.path.join(git_dir, "refs", "heads")
    if not os.path.exists(refs_heads):
        print("Ветки не найдены.")
        return
    for root, dirs, files in os.walk(refs_heads):
        for f in files:
            branch = os.path.relpath(os.path.join(root, f), refs_heads)
            print(branch)

if len(sys.argv) < 2:
    sys.exit(1)
repo_path = sys.argv[1]
git_dir = os.path.join(repo_path, ".git")
if not os.path.isdir(git_dir):
    sys.exit("Указанный каталог не является git-репозиторием.")
if len(sys.argv) == 2:
    list_branches(git_dir)
    sys.exit(0)


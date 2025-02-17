import os
import sys
import zlib
import re


def list_branches(git_dir):
    refs_heads = os.path.join(git_dir, "refs", "heads")
    if not os.path.exists(refs_heads):
        print("Ветки не найдены.")
        return
    for root, dirs, files in os.walk(refs_heads):
        for f in files:
            branch = os.path.relpath(os.path.join(root, f), refs_heads)
            print(branch)


def read_object(repo, obj_hash):
    """
    Читает объект по его хешу из .git/objects.
    Возвращает кортеж: (тип объекта, содержимое объекта (bytes))
    """
    path = os.path.join(repo, ".git", "objects", obj_hash[:2], obj_hash[2:])
    try:
        with open(path, "rb") as f:
            compressed = f.read()
    except FileNotFoundError:
        sys.exit(f"Объект {obj_hash} не найден")
    data = zlib.decompress(compressed)
    header, _, content = data.partition(b'\x00')
    header = header.decode()
    obj_type, _ = header.split(" ", 1)
    return obj_type, content


def parse_commit(content):
    text = content.decode("utf-8", errors="replace")
    header_part, _, message = text.partition("\n\n")
    commit_data = {}
    commit_data["message"] = message.strip()
    commit_data["parents"] = []
    for line in header_part.splitlines():
        if line.startswith("tree "):
            commit_data["tree"] = line[len("tree "):].strip()
        elif line.startswith("parent "):
            commit_data["parents"].append(line[len("parent "):].strip())
        elif line.startswith("author "):
            m = re.match(r"^(author\s+)(.+ <[^>]+>)", line)
            if m:
                commit_data["author"] = m.group(2)
            else:
                commit_data["author"] = line[len("author "):].strip()
        elif line.startswith("committer "):
            m = re.match(r"^(committer\s+)(.+ <[^>]+>)", line)
            if m:
                commit_data["committer"] = m.group(2)
            else:
                commit_data["committer"] = line[len("committer "):].strip()
    return commit_data


def print_commit(commit_data):
    print("tree", commit_data.get("tree", ""))
    for parent in commit_data.get("parents", []):
        print("parent", parent)
    print("author", commit_data.get("author", ""))
    print("committer", commit_data.get("committer", ""))
    print()
    print(commit_data.get("message", ""))


if len(sys.argv) < 2:
    sys.exit(1)
repo_path = sys.argv[1]
git_dir = os.path.join(repo_path, ".git")
if not os.path.isdir(git_dir):
    sys.exit("Указанный каталог не является git-репозиторием.")
if len(sys.argv) == 2:
    list_branches(git_dir)
    sys.exit(0)
branch = sys.argv[2]
branch_file = os.path.join(git_dir, "refs", "heads", branch)
if not os.path.exists(branch_file):
    sys.exit(f"Ветка '{branch}' не найдена.")

with open(branch_file, "r") as f:
    commit_hash = f.read().strip()

obj_type, commit_content = read_object(repo_path, commit_hash)
if obj_type != "commit":
    sys.exit("Объект по ссылке не является commit-объектом.")
commit_data = parse_commit(commit_content)
print_commit(commit_data)

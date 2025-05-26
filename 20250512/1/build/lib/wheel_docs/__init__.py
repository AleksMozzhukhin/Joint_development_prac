"""Модуль документации MOOD для wheel пакета."""

import os
import sys
import subprocess
import platform
import webbrowser
from pathlib import Path


def get_docs_path():
    """Получить путь к HTML документации в установленном пакете."""
    current_dir = Path(__file__).parent
    html_index = current_dir / "html" / "index.html"
    return html_index


def open_documentation():
    """Открыть HTML документацию в браузере."""
    html_file = get_docs_path()

    if not html_file.exists():
        print(f"Documentation not found: {html_file}")
        print("Documentation may not be included in this installation.")
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
            # WSL: пробуем различные способы
            wsl_commands = [
                ["wslview", html_path],
                ["explorer.exe", html_path],
                ["cmd.exe", "/c", "start", html_path]
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
                # Пробуем через wslpath + powershell
                try:
                    result = subprocess.run(['wslpath', '-w', html_path],
                                            capture_output=True, text=True, check=True)
                    windows_path = result.stdout.strip()
                    subprocess.run(['powershell.exe', '-c', 'Start-Process', f'"{windows_path}"'],
                                   check=True)
                    success = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Последняя попытка через webbrowser
                    file_url = f"file:///{html_path.replace(os.sep, '/')}"
                    success = webbrowser.open(file_url)

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

    except Exception as e:
        print(f"Error opening documentation: {e}")
        print(f"Please open manually: {html_file}")
        # Fallback to webbrowser
        try:
            file_url = f"file:///{str(html_file).replace(os.sep, '/')}"
            return webbrowser.open(file_url)
        except:
            return False


def main():
    """Главная функция для команды mood-help."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MOOD Game Documentation Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mood-help              # Open HTML documentation
  mood-help --path       # Show path to documentation
  mood-help --version    # Show version information
        """
    )

    parser.add_argument(
        "--path",
        action="store_true",
        help="Show path to documentation directory"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    args = parser.parse_args()

    if args.version:
        print("MOOD Game v0.1.0")
        print("Documentation module")
        return

    if args.path:
        docs_path = get_docs_path()
        print(f"Documentation path: {docs_path}")
        print(f"Exists: {docs_path.exists()}")
        return

    # По умолчанию открываем документацию
    success = open_documentation()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()